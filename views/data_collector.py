# -*- coding: utf-8 -*-
"""
Data Collector REST API 뷰
데이터 수집 작업을 관리하는 API 엔드포인트를 제공합니다.
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging
import time
from extensions import executor
from services.data_collector import DataCollectorService
from models.stock import StockList
from services.stock_service import StockService
from database.transaction import safe_transaction, read_only_transaction

# 로깅 설정
logger = logging.getLogger(__name__)

# 블루프린트 생성
collector_bp = Blueprint('collector', __name__)

# 전역 상태 관리 (프론트엔드 호환성을 위해)
collection_status = {
    'is_running': False,
    'current_phase': 'idle',  # 프론트엔드와 호환
    'current_stock': '',
    'progress': 0,
    'total_stocks': 0,
    'success_count': 0,
    'failed_count': 0,
    'failed_stocks': [],  # 프론트엔드와 호환
    'start_time': None,
    'end_time': None,
    'error_message': '',
    'task_id': None,
    'elapsed_time': None,
    'batches_processed': 0,
    'memory_cleanups': 0,
    'current_batch': 0,
    'total_batches': 0
}

def update_progress(phase, current_stock='', progress=0, success=0, failed=0, error_msg='', failed_stock=None):
    """진행률 업데이트 헬퍼 함수"""
    global collection_status
    
    collection_status.update({
        'current_phase': phase,
        'current_stock': current_stock,
        'progress': progress,
        'success_count': success,
        'failed_count': failed,
        'error_message': error_msg
    })
    
    if failed_stock:
        collection_status['failed_stocks'].append(failed_stock)
    
    # 경과 시간 계산
    if collection_status['start_time']:
        start_time = datetime.fromisoformat(collection_status['start_time'])
        if collection_status['end_time']:
            end_time = datetime.fromisoformat(collection_status['end_time'])
            collection_status['elapsed_time'] = str(end_time - start_time)
        else:
            collection_status['elapsed_time'] = str(datetime.now() - start_time)
    
    logger.info(f"진행률 업데이트: {phase} - {current_stock} ({progress}%)")

@executor.job
def collect_data_background(years: int = 3, max_pages: int = 10):
    """Flask-Executor를 사용한 백그라운드 데이터 수집"""
    global collection_status
    
    try:
        collection_status['is_running'] = True
        collection_status['start_time'] = datetime.now().isoformat()
        
        logger.info(f"백그라운드 데이터 수집 시작 ({years}년, 최대 {max_pages}페이지)")
        
        # 1. 초기화 단계
        update_progress('initializing', '주식 목록 초기화 중...', 0)
        
        # 주식 목록 초기화
        if not DataCollectorService.initialize_stock_list():
            update_progress('error', '', 0, 0, 0, '주식 목록 초기화 실패')
            return {'status': 'error', 'message': '주식 목록 초기화 실패'}
        
        # 2. 주식 목록 조회
        stocks = StockService.get_all_stocks()
        collection_status['total_stocks'] = len(stocks)
        
        if not stocks:
            update_progress('error', '', 0, 0, 0, '수집할 주식이 없습니다')
            return {'status': 'error', 'message': '수집할 주식이 없습니다'}
        
        logger.info(f"총 {len(stocks)}개 주식 데이터 수집 시작")
        
        # 3. 데이터 수집 단계
        update_progress('collecting', '', 0, 0, 0)
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        progress = 0  # 초기값 설정
        
        for i, stock in enumerate(stocks):
            if not collection_status['is_running']:  # 중단 요청 확인
                logger.info("데이터 수집이 사용자에 의해 중단되었습니다")
                break
            
            try:
                # 현재 진행률 계산
                progress = int((i / len(stocks)) * 100)
                update_progress('collecting', f"{stock.stock_code} {stock.stock_name}", 
                              progress, success_count, failed_count)
                
                # 수집 필요 여부 확인
                collection_check = DataCollectorService.should_collect_data(stock.stock_code, years)
                
                if not collection_check['should_collect']:
                    # 수집 불필요한 경우
                    skipped_count += 1
                    logger.info(f"수집 건너뛰기: {stock.stock_code} {stock.stock_name} - {collection_check['reason']}")
                    continue
                
                # 수집 필요한 경우
                success = DataCollectorService.collect_and_save_trading_data(
                    stock.stock_code, stock.stock_name, years, max_pages
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    update_progress('collecting', f"{stock.stock_code} {stock.stock_name}", 
                                  progress, success_count, failed_count, 
                                  failed_stock=f"{stock.stock_code} {stock.stock_name}")
                
                # 요청 간 대기
                time.sleep(DataCollectorService.REQUEST_DELAY)
                
            except Exception as e:
                failed_count += 1
                update_progress('collecting', f"{stock.stock_code} {stock.stock_name}", 
                              progress, success_count, failed_count, 
                              failed_stock=f"{stock.stock_code} {stock.stock_name}: {str(e)}")
                logger.error(f"주식 데이터 수집 중 오류: {stock.stock_code}, {e}")
                continue
        
        final_progress = 100 if collection_status['is_running'] else progress
        collection_status['end_time'] = datetime.now().isoformat()
        
        if collection_status['is_running']:  # 정상 완료
            update_progress('completed', '데이터 수집 완료', final_progress, 
                          success_count, failed_count)
            logger.info(f"데이터 수집 완료: 성공 {success_count}개, 실패 {failed_count}개, 건너뛴 {skipped_count}개")
            return {
                'status': 'completed', 
                'success_count': success_count, 
                'failed_count': failed_count,
                'skipped_count': skipped_count
            }
        else:  # 중단됨
            update_progress('cancelled', '데이터 수집 중단됨', progress, 
                          success_count, failed_count)
            logger.info("데이터 수집이 중단되었습니다")
            return {
                'status': 'cancelled', 
                'success_count': success_count, 
                'failed_count': failed_count,
                'skipped_count': skipped_count
            }
        
    except Exception as e:
        collection_status['end_time'] = datetime.now().isoformat()
        update_progress('error', '', 0, 0, 0, f'데이터 수집 중 오류: {str(e)}')
        logger.error(f"데이터 수집 중 치명적 오류: {e}")
        return {'status': 'error', 'message': str(e)}
    
    finally:
        collection_status['is_running'] = False
        collection_status['task_id'] = None

@collector_bp.route('/status', methods=['GET'])
@read_only_transaction
def get_collection_status():
    """
    데이터 수집 상태 조회
    """
    try:
        return jsonify(collection_status), 200
        
    except Exception as e:
        logger.error(f"상태 조회 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collector_bp.route('/start', methods=['POST'])
@safe_transaction
def start_collection():
    """
    데이터 수집 시작
    """
    global collection_status
    
    try:
        if collection_status['is_running']:
            return jsonify({
                'status': 'error',
                'error': '데이터 수집이 이미 진행 중입니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 요청 데이터 파싱
        data = request.get_json() or {}
        
        # 타입 변환 및 기본값 설정
        try:
            years = int(data.get('years', 3))
            max_pages = int(data.get('max_pages', 10))
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'error': '수집 기간과 페이지 수는 숫자여야 합니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 입력 검증
        if years < 1 or years > 10:
            return jsonify({
                'status': 'error',
                'error': f'수집 기간은 1-10년 사이여야 합니다 (입력값: {years}년)',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if max_pages < 1 or max_pages > 50:
            return jsonify({
                'status': 'error',
                'error': f'페이지 수는 1-50 사이여야 합니다 (입력값: {max_pages}페이지)',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 상태 초기화
        collection_status.update({
            'is_running': True,
            'current_phase': 'initializing',
            'current_stock': '',
            'progress': 0,
            'total_stocks': 0,
            'success_count': 0,
            'failed_count': 0,
            'failed_stocks': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'error_message': ''
        })
        
        # Flask-Executor로 백그라운드 작업 시작
        future = collect_data_background.submit(years, max_pages)
        collection_status['task_id'] = str(id(future))
        
        logger.info(f"데이터 수집 시작: {years}년, {max_pages}페이지, 작업 ID: {collection_status['task_id']}")
        
        return jsonify({
            'status': 'success',
            'message': f'{years}년간의 데이터 수집이 시작되었습니다 (최대 {max_pages}페이지)',
            'task_id': collection_status['task_id'],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"데이터 수집 시작 실패: {str(e)}")
        collection_status['is_running'] = False
        return jsonify({
            'status': 'error',
            'error': f'데이터 수집 시작 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@collector_bp.route('/stop', methods=['POST'])
@safe_transaction
def stop_collection():
    """
    데이터 수집 중단
    """
    try:
        if not collection_status['is_running']:
            return jsonify({
                'status': 'error',
                'error': '진행 중인 데이터 수집이 없습니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 수집 중단 플래그 설정
        collection_status['is_running'] = False
        
        logger.info("데이터 수집 중단 요청")
        
        return jsonify({
            'status': 'success',
            'message': '데이터 수집 중단이 요청되었습니다',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"데이터 수집 중단 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'데이터 수집 중단 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@collector_bp.route('/reset', methods=['POST'])
@safe_transaction
def reset_collection():
    """
    수집 상태 초기화
    """
    global collection_status
    
    try:
        # 진행 중인 작업이 있으면 중단
        if collection_status['is_running']:
            collection_status['is_running'] = False
        
        # 상태 완전 초기화
        collection_status = {
            'is_running': False,
            'current_phase': 'idle',
            'current_stock': '',
            'progress': 0,
            'total_stocks': 0,
            'success_count': 0,
            'failed_count': 0,
            'failed_stocks': [],
            'start_time': None,
            'end_time': None,
            'error_message': '',
            'task_id': None,
            'elapsed_time': None
        }
        
        logger.info("데이터 수집 상태 초기화")
        
        return jsonify({
            'status': 'success',
            'message': '수집 상태가 초기화되었습니다',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"상태 초기화 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'상태 초기화 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@collector_bp.route('/stocks', methods=['GET'])
@read_only_transaction
def get_available_stocks():
    """
    수집 가능한 주식 목록 조회
    """
    try:
        stocks = StockService.get_all_stocks()
        
        stock_list = []
        for stock in stocks:
            stock_list.append({
                'code': stock.stock_code,
                'name': stock.stock_name
            })
        
        # 주식이 없으면 빈 목록 반환 (DB 기반)
        if not stock_list:
            logger.warning("DB에 등록된 주식이 없습니다.")
        
        return jsonify({
            'stocks': stock_list,
            'total_count': len(stock_list)
        }), 200
        
    except Exception as e:
        logger.error(f"주식 목록 조회 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collector_bp.route('/calculate-accumulated', methods=['POST'])
@safe_transaction
def calculate_accumulated_data():
    """
    모든 주식의 누적 매수량 데이터를 계산
    
    Returns:
        JSON: 계산 결과
    """
    try:
        logger.info("누적 데이터 계산 요청")
        
        # 누적 데이터 계산
        results = DataCollectorService.calculate_all_accumulated_data()
        
        return jsonify({
            'status': 'success' if results.get('success_stocks', 0) > 0 else 'info',
            'message': f"누적 데이터 계산 완료: 성공 {results.get('success_stocks', 0)}개, 실패 {results.get('failed_stocks', 0)}개",
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200
            
    except Exception as e:
        logger.error(f"누적 데이터 계산 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@collector_bp.route('/clear-all-trading-data', methods=['DELETE'])
@safe_transaction
def clear_all_trading_data():
    """
    모든 거래 데이터를 삭제
    
    Returns:
        JSON: 삭제 결과
    """
    try:
        logger.info("전체 거래 데이터 초기화 요청")
        
        # 모든 거래 데이터 삭제
        results = DataCollectorService.clear_all_trading_data()
        
        if 'error' in results:
            return jsonify({
                'status': 'error',
                'error': results['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': results['message'],
            'deleted_count': results['deleted_count'],
            'timestamp': datetime.now().isoformat()
        }), 200
            
    except Exception as e:
        logger.error(f"전체 거래 데이터 초기화 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@collector_bp.route('/clear-trading-data/<stock_code>', methods=['DELETE'])
@safe_transaction
def clear_trading_data_by_stock(stock_code):
    """
    특정 종목의 거래 데이터를 삭제
    
    Args:
        stock_code (str): 주식 코드
        
    Returns:
        JSON: 삭제 결과
    """
    try:
        logger.info(f"종목별 거래 데이터 초기화 요청: {stock_code}")
        
        # 입력값 검증
        if not stock_code or not stock_code.strip():
            return jsonify({
                'status': 'error',
                'error': '주식 코드는 필수입니다.',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 해당 종목의 거래 데이터 삭제
        success = DataCollectorService.clear_trading_data_by_stock(stock_code.strip())
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'{stock_code} 종목의 거래 데이터가 삭제되었습니다.',
                'stock_code': stock_code,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': f'{stock_code} 종목의 거래 데이터 삭제에 실패했습니다.',
                'stock_code': stock_code,
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"종목별 거래 데이터 초기화 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'stock_code': stock_code,
            'timestamp': datetime.now().isoformat()
        }), 500


@collector_bp.route('/clear-trading-data-bulk', methods=['DELETE'])
@safe_transaction
def clear_trading_data_bulk():
    """
    여러 종목의 거래 데이터를 일괄 삭제
    
    Request Body:
        stock_codes (List[str]): 삭제할 주식 코드 목록
        
    Returns:
        JSON: 삭제 결과
    """
    try:
        logger.info("일괄 거래 데이터 초기화 요청")
        
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'error': 'Content-Type은 application/json이어야 합니다.',
                'timestamp': datetime.now().isoformat()
            }), 400
            
        data = request.get_json()
        
        if not data or 'stock_codes' not in data:
            return jsonify({
                'status': 'error',
                'error': 'stock_codes 필드는 필수입니다.',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        stock_codes = data['stock_codes']
        
        if not isinstance(stock_codes, list) or len(stock_codes) == 0:
            return jsonify({
                'status': 'error',
                'error': 'stock_codes는 비어있지 않은 배열이어야 합니다.',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 여러 종목의 거래 데이터 삭제
        results = DataCollectorService.clear_trading_data_by_stocks(stock_codes)
        
        return jsonify({
            'status': 'success' if results['success_stocks'] > 0 else 'error',
            'message': f"일괄 삭제 완료: 성공 {results['success_stocks']}개, 실패 {results['failed_stocks']}개",
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200
            
    except Exception as e:
        logger.error(f"일괄 거래 데이터 초기화 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@collector_bp.route('/calculate-accumulated/<stock_code>', methods=['POST'])
@safe_transaction
def calculate_accumulated_data_by_stock(stock_code):
    """
    특정 종목의 누적 매수량 데이터를 계산
    
    Args:
        stock_code (str): 주식 코드
        
    Returns:
        JSON: 계산 결과
    """
    try:
        logger.info(f"종목별 누적 데이터 계산 요청: {stock_code}")
        
        # 입력값 검증
        if not stock_code or not stock_code.strip():
            return jsonify({
                'status': 'error',
                'error': '주식 코드는 필수입니다.',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 해당 종목의 누적 데이터 계산
        success = DataCollectorService.calculate_accumulated_data(stock_code.strip())
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'{stock_code} 종목의 누적 데이터 계산이 완료되었습니다.',
                'stock_code': stock_code,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': f'{stock_code} 종목의 누적 데이터 계산에 실패했습니다.',
                'stock_code': stock_code,
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"종목별 누적 데이터 계산 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'stock_code': stock_code,
            'timestamp': datetime.now().isoformat()
        }), 500


@collector_bp.route('/test-url/<stock_code>', methods=['GET'])
@read_only_transaction
def test_url(stock_code):
    """
    특정 주식의 데이터를 가져오는 테스트 엔드포인트
    """
    try:
        # 실제 데이터 수집 로직을 호출하는 대신, 단순히 주어진 코드를 반환
        return jsonify({
            'status': 'success',
            'message': f'테스트 URL 호출: {stock_code}',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"테스트 URL 호출 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collector_bp.route('/monitor', methods=['GET'])
@read_only_transaction
def get_batch_monitoring():
    """
    배치 처리 모니터링 정보 조회
    
    Returns:
        JSON: 배치 처리 상태 및 시스템 정보
    """
    try:
        import psutil
        
        # 시스템 리소스 정보
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 현재 프로세스 정보
        process = psutil.Process()
        process_memory = process.memory_info()
        
        monitoring_info = {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2)
            },
            'process': {
                'memory_percent': process.memory_percent(),
                'memory_rss_mb': round(process_memory.rss / (1024**2), 2),
                'memory_vms_mb': round(process_memory.vms / (1024**2), 2),
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads()
            },
            'collection': collection_status,
            'batch_settings': {
                'batch_size': DataCollectorService.BATCH_SIZE,
                'batch_delay': DataCollectorService.BATCH_DELAY,
                'memory_check_interval': DataCollectorService.MEMORY_CHECK_INTERVAL,
                'max_memory_usage': DataCollectorService.MAX_MEMORY_USAGE,
                'session_refresh_interval': DataCollectorService.SESSION_REFRESH_INTERVAL
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(monitoring_info), 200
        
    except Exception as e:
        logger.error(f"모니터링 정보 조회 실패: {e}")
        return jsonify({
            'error': '모니터링 정보 조회 중 오류가 발생했습니다.',
            'message': str(e)
        }), 500


@collector_bp.route('/incremental', methods=['POST'])
@safe_transaction
def start_incremental_collection():
    """
    증분 크롤링 시작 (누락된 최신 데이터만 수집)
    
    Request Body:
        stock_code (str, optional): 특정 주식 코드 (없으면 전체)
        days_back (int, optional): 확인할 기간 (일 단위, 기본값: 30)
        max_pages (int, optional): 최대 페이지 수 (기본값: 5)
        force_collect (bool, optional): 강제 수집 여부 (기본값: False)
    
    Returns:
        JSON: 증분 수집 결과
    """
    try:
        # 요청 데이터 파싱
        data = request.get_json() or {}
        
        stock_code = data.get('stock_code')
        days_back = int(data.get('days_back', 30))
        max_pages = int(data.get('max_pages', 5))
        force_collect = bool(data.get('force_collect', False))
        
        # 입력값 검증
        if stock_code and not re.match(r'^\d{6}$', stock_code):
            return jsonify({
                'status': 'error',
                'error': '주식 코드는 6자리 숫자여야 합니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if days_back <= 0 or days_back > 365:
            return jsonify({
                'status': 'error',
                'error': '확인 기간은 1~365일 사이여야 합니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if max_pages <= 0 or max_pages > 20:
            return jsonify({
                'status': 'error',
                'error': '최대 페이지 수는 1~20 사이여야 합니다',
                'timestamp': datetime.now().isoformat()
            }), 400
                
        logger.info(f"증분 크롤링 시작 - 주식: {stock_code or '전체'}, 기간: {days_back}일")
        
        # 증분 수집 실행
        results = DataCollectorService.collect_incremental_data(
            stock_code=stock_code,
            days_back=days_back,
            max_pages=max_pages,
            force_collect=force_collect
        )
        
        # 에러가 있는 경우
        if 'error' in results:
            return jsonify({
                'status': 'error',
                'error': results['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # 성공 응답
        return jsonify({
            'status': 'success',
            'message': '증분 크롤링이 완료되었습니다',
            'results': results,
            'parameters': {
                'stock_code': stock_code,
                'days_back': days_back,
                'max_pages': max_pages,
                'force_collect': force_collect
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except ValueError as e:
        logger.warning(f"증분 크롤링 입력값 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'입력값 오류: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"증분 크롤링 중 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': '증분 크롤링 중 오류가 발생했습니다',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@collector_bp.route('/check-missing', methods=['GET'])
def check_missing_dates():
    """
    누락된 거래 날짜 확인 (수집 전 미리보기)
    
    Query Parameters:
        stock_code (str): 주식 코드 (필수)
        days_back (int, optional): 확인할 기간 (일 단위, 기본값: 30)
    
    Returns:
        JSON: 누락된 날짜 정보
    """
    try:
        stock_code = request.args.get('stock_code', '').strip()
        days_back = int(request.args.get('days_back', 30))
        
        if not stock_code:
            return jsonify({
                'status': 'error',
                'error': '주식 코드는 필수입니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        if not re.match(r'^\d{6}$', stock_code):
            return jsonify({
                'status': 'error',
                'error': '주식 코드는 6자리 숫자여야 합니다',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 주식 정보 확인
        from services.stock_service import StockService
        stock = StockService.get_stock_by_code(stock_code)
        if not stock:
            return jsonify({
                'status': 'error',
                'error': f'주식을 찾을 수 없습니다: {stock_code}',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # 누락된 날짜와 최신 데이터 조회
        from services.trading_service import TradingService
        
        missing_dates = TradingService.get_missing_trade_dates(stock_code, days_back)
        latest_date = TradingService.get_latest_trade_date(stock_code)
        
        return jsonify({
            'status': 'success',
            'stock_info': {
                'stock_code': stock.stock_code,
                'stock_name': stock.stock_name
            },
            'latest_trade_date': latest_date,
            'missing_dates': missing_dates,
            'missing_count': len(missing_dates),
            'check_period_days': days_back,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': f'입력값 오류: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"누락 날짜 확인 중 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': '누락 날짜 확인 중 오류가 발생했습니다',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# 에러 핸들러
@collector_bp.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        'error': '요청한 리소스를 찾을 수 없습니다.',
        'status_code': 404
    }), 404


@collector_bp.errorhandler(405)
def method_not_allowed(error):
    """405 에러 핸들러"""
    return jsonify({
        'error': '허용되지 않은 HTTP 메서드입니다.',
        'status_code': 405
    }), 405


@collector_bp.errorhandler(500)
def internal_server_error(error):
    """500 에러 핸들러"""
    logger.error(f"내부 서버 오류: {str(error)}")
    return jsonify({
        'error': '내부 서버 오류가 발생했습니다.',
        'status_code': 500
    }), 500 