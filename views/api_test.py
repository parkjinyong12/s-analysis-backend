# -*- coding: utf-8 -*-
"""
API 테스트 관련 Blueprint
서버 기동 시 REST API의 상태를 테스트하는 기능을 제공합니다.
"""
from flask import Blueprint, jsonify
import requests
import logging
from datetime import datetime
import copy

# Blueprint 생성
api_test_bp = Blueprint('api_test', __name__, url_prefix='/api-test')

# 로거 설정
logger = logging.getLogger(__name__)

# 테스트 세션 상태 저장
test_session_state = {
    'backup_data': {},
    'is_test_mode': False,
    'test_start_time': None
}

def get_base_url():
    """기본 URL 반환"""
    return "http://127.0.0.1:5001"

def create_backup():
    """현재 데이터베이스 상태 백업"""
    try:
        from models.stock import StockList
        from models.trading import StockInvestorTrading
        
        backup = {
            'stocks': [{'id': s.id, 'stock_code': s.stock_code, 'stock_name': s.stock_name, 
                       'init_date': s.init_date, 'institution_accum_init': s.institution_accum_init, 
                       'foreigner_accum_init': s.foreigner_accum_init} for s in StockList.query.all()],
            'trading_data': [{'id': t.id, 'stock_code': t.stock_code, 'stock_name': t.stock_name,
                             'trade_date': t.trade_date, 'close_price': t.close_price,
                             'institution_net_buy': t.institution_net_buy, 'foreigner_net_buy': t.foreigner_net_buy,
                             'institution_accum': t.institution_accum, 'foreigner_accum': t.foreigner_accum,
                             'institution_trend_signal': t.institution_trend_signal, 'institution_trend_score': t.institution_trend_score,
                             'foreigner_trend_signal': t.foreigner_trend_signal, 'foreigner_trend_score': t.foreigner_trend_score} 
                            for t in StockInvestorTrading.query.all()]
        }
        
        test_session_state['backup_data'] = backup
        test_session_state['is_test_mode'] = True
        test_session_state['test_start_time'] = datetime.now().isoformat()
        
        logger.info(f"테스트 모드 백업 생성 완료: 주식 {len(backup['stocks'])}개, 거래데이터 {len(backup['trading_data'])}개")
        return True
    except Exception as e:
        logger.error(f"백업 생성 실패: {str(e)}")
        return False

def restore_backup():
    """백업된 데이터로 복원"""
    try:
        from extensions import db
        from models.stock import StockList
        from models.trading import StockInvestorTrading
        
        if not test_session_state['backup_data']:
            logger.warning("복원할 백업 데이터가 없습니다.")
            return False
        
        backup = test_session_state['backup_data']
        
        # 현재 데이터 삭제
        StockInvestorTrading.query.delete()
        StockList.query.delete()
        
        # 백업 데이터 복원
        for stock_data in backup['stocks']:
            stock = StockList(**stock_data)
            db.session.add(stock)
        
        for trading_data in backup['trading_data']:
            trading = StockInvestorTrading(**trading_data)
            db.session.add(trading)
        
        db.session.commit()
        
        # 테스트 모드 해제
        test_session_state['is_test_mode'] = False
        test_session_state['backup_data'] = {}
        
        logger.info(f"백업 복원 완료: 주식 {len(backup['stocks'])}개, 거래데이터 {len(backup['trading_data'])}개")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"백업 복원 실패: {str(e)}")
        return False

@api_test_bp.route('/health', methods=['GET'])
def health_check():
    """
    서버 상태 확인
    """
    try:
        return jsonify({
            'status': 'healthy',
            'message': 'API 서버가 정상적으로 작동 중입니다.',
            'timestamp': datetime.now().isoformat(),
            'server': 'Flask Development Server',
            'test_mode': test_session_state['is_test_mode']
        }), 200
    except Exception as e:
        logger.error(f"Health check 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'서버 상태 확인 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/test-mode/start', methods=['POST'])
def start_test_mode():
    """
    테스트 모드 시작 (데이터 백업)
    """
    try:
        if test_session_state['is_test_mode']:
            return jsonify({
                'status': 'warning',
                'message': '이미 테스트 모드가 활성화되어 있습니다.',
                'test_start_time': test_session_state['test_start_time'],
                'timestamp': datetime.now().isoformat()
            }), 200
        
        if create_backup():
            return jsonify({
                'status': 'success',
                'message': '테스트 모드가 시작되었습니다. 데이터가 백업되었습니다.',
                'test_start_time': test_session_state['test_start_time'],
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '테스트 모드 시작에 실패했습니다.',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"테스트 모드 시작 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'테스트 모드 시작 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/test-mode/end', methods=['POST'])
def end_test_mode():
    """
    테스트 모드 종료 (데이터 복원)
    """
    try:
        if not test_session_state['is_test_mode']:
            return jsonify({
                'status': 'warning',
                'message': '테스트 모드가 활성화되어 있지 않습니다.',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        if restore_backup():
            return jsonify({
                'status': 'success',
                'message': '테스트 모드가 종료되었습니다. 데이터가 복원되었습니다.',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '테스트 모드 종료에 실패했습니다.',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"테스트 모드 종료 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'테스트 모드 종료 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/test-mode/status', methods=['GET'])
def test_mode_status():
    """
    테스트 모드 상태 확인
    """
    try:
        backup = test_session_state['backup_data']
        return jsonify({
            'is_test_mode': test_session_state['is_test_mode'],
            'test_start_time': test_session_state['test_start_time'],
            'backup_summary': {
                'stocks_count': len(backup.get('stocks', [])),
                'trading_data_count': len(backup.get('trading_data', []))
            },
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"테스트 모드 상태 확인 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'테스트 모드 상태 확인 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/endpoints', methods=['GET'])
def test_all_endpoints():
    """
    모든 주요 API 엔드포인트 테스트 (읽기 전용)
    """
    base_url = get_base_url()
    test_results = []
    
    # 테스트할 엔드포인트 목록 (읽기 전용만)
    endpoints = [
        # Stock API (읽기 전용)
        {'name': 'Stock 목록 조회', 'method': 'GET', 'url': f'{base_url}/api/v1/stocks/', 'expected_status': 200},
        {'name': 'Stock 검색', 'method': 'GET', 'url': f'{base_url}/api/v1/stocks/search?name=삼성', 'expected_status': 200},
        {'name': 'Stock 코드별 조회', 'method': 'GET', 'url': f'{base_url}/api/v1/stocks/code/005930', 'expected_status': 200},
        
        # Trading API (읽기 전용)
        {'name': 'Trading 목록 조회', 'method': 'GET', 'url': f'{base_url}/api/v1/trading/', 'expected_status': 200},
        {'name': 'Trading 검색', 'method': 'GET', 'url': f'{base_url}/api/v1/trading/search?query=삼천당제약', 'expected_status': 200},
        {'name': 'Trading 날짜 범위 조회', 'method': 'GET', 'url': f'{base_url}/api/v1/trading/date-range?start_date=2024-01-01&end_date=2024-12-31', 'expected_status': 200},
        {'name': 'Trading 주식별 조회', 'method': 'GET', 'url': f'{base_url}/api/v1/trading/stock/005930', 'expected_status': 200},
        
        # Collector API (상태 조회만)
        {'name': 'Collector 상태 조회', 'method': 'GET', 'url': f'{base_url}/api/v1/collector/status', 'expected_status': 200},
        {'name': 'Collector 사용 가능한 주식 목록', 'method': 'GET', 'url': f'{base_url}/api/v1/collector/stocks', 'expected_status': 200},
        
        # API Test
        {'name': 'Health Check', 'method': 'GET', 'url': f'{base_url}/api/v1/test/health', 'expected_status': 200},
        {'name': 'Database 테스트', 'method': 'GET', 'url': f'{base_url}/api/v1/test/database', 'expected_status': 200},
        {'name': '테스트 모드 상태', 'method': 'GET', 'url': f'{base_url}/api/v1/test/test-mode/status', 'expected_status': 200},
        
        # History API (읽기 전용)
        {'name': 'History 통계', 'method': 'GET', 'url': f'{base_url}/api/v1/history/stats', 'expected_status': 200},
        {'name': 'History 최근 활동', 'method': 'GET', 'url': f'{base_url}/api/v1/history/latest', 'expected_status': 200},
        {'name': 'History 활동 요약', 'method': 'GET', 'url': f'{base_url}/api/v1/history/summary', 'expected_status': 200},
        {'name': 'History 데이터 히스토리', 'method': 'GET', 'url': f'{base_url}/api/v1/history/data', 'expected_status': 200},
        {'name': 'History 시스템 로그', 'method': 'GET', 'url': f'{base_url}/api/v1/history/system', 'expected_status': 200},
    ]
    
    for endpoint in endpoints:
        try:
            # HTTP 요청 실행
            headers = {'Content-Type': 'application/json'}
            
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], timeout=5)
            elif endpoint['method'] == 'POST':
                data = endpoint.get('data', {})
                response = requests.post(endpoint['url'], json=data, headers=headers, timeout=5)
            elif endpoint['method'] == 'PUT':
                data = endpoint.get('data', {})
                response = requests.put(endpoint['url'], json=data, headers=headers, timeout=5)
            elif endpoint['method'] == 'DELETE':
                response = requests.delete(endpoint['url'], timeout=5)
            else:
                continue
            
            # 결과 분석
            is_success = response.status_code == endpoint['expected_status']
            
            test_result = {
                'name': endpoint['name'],
                'method': endpoint['method'],
                'url': endpoint['url'],
                'status_code': response.status_code,
                'expected_status': endpoint['expected_status'],
                'success': is_success,
                'response_time': response.elapsed.total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            # 응답 내용이 있는 경우 추가
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    test_result['response_data'] = response.json()
            except:
                pass
            
            test_results.append(test_result)
            
        except requests.exceptions.Timeout:
            test_results.append({
                'name': endpoint['name'],
                'method': endpoint['method'],
                'url': endpoint['url'],
                'status_code': None,
                'expected_status': endpoint['expected_status'],
                'success': False,
                'error': 'Timeout',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            test_results.append({
                'name': endpoint['name'],
                'method': endpoint['method'],
                'url': endpoint['url'],
                'status_code': None,
                'expected_status': endpoint['expected_status'],
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    # 전체 결과 요약
    total_tests = len(test_results)
    successful_tests = len([r for r in test_results if r.get('success', False)])
    failed_tests = total_tests - successful_tests
    
    test_summary = {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'failed_tests': failed_tests,
        'success_rate': round((successful_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
        'test_mode': test_session_state['is_test_mode']
    }
    
    return jsonify({
        'test_summary': test_summary,
        'test_results': test_results,
        'timestamp': datetime.now().isoformat()
    }), 200

@api_test_bp.route('/endpoint/<path:endpoint_path>', methods=['GET'])
def test_single_endpoint(endpoint_path):
    """
    특정 엔드포인트 단일 테스트
    """
    from flask import request
    
    logger.info(f"API 테스트 - endpoint_path: {endpoint_path}")
    logger.info(f"API 테스트 - request.args: {dict(request.args)}")
    
    base_url = get_base_url()
    
    # 쿼리 파라미터 분리
    if '?' in endpoint_path:
        path_part, query_part = endpoint_path.split('?', 1)
        full_url = f"{base_url}/{path_part}"
        # requests.get에 params 파라미터로 전달
        params = {}
        for param in query_part.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value
        logger.info(f"API 테스트 - URL: {full_url}, Params: {params}")
        response = requests.get(full_url, params=params, timeout=5)
    else:
        full_url = f"{base_url}/{endpoint_path}"
        logger.info(f"API 테스트 - URL: {full_url}")
        response = requests.get(full_url, timeout=5)
    
    try:
        result = {
            'url': response.url,  # 실제 요청된 URL 사용
            'status_code': response.status_code,
            'success': 200 <= response.status_code < 300,
            'response_time_ms': response.elapsed.total_seconds() * 1000,
            'headers': dict(response.headers),
            'timestamp': datetime.now().isoformat()
        }
        
        # 응답 데이터 추가
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                result['response_data'] = response.json()
            else:
                result['response_data'] = response.text
        except Exception as e:
            result['response_data'] = f'응답 파싱 실패: {str(e)}'
        
        return jsonify(result), 200
        
    except requests.exceptions.Timeout:
        return jsonify({
            'url': full_url,
            'success': False,
            'error': '요청 타임아웃 (5초)',
            'timestamp': datetime.now().isoformat()
        }), 408
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            'url': full_url,
            'success': False,
            'error': '연결 실패',
            'timestamp': datetime.now().isoformat()
        }), 503
        
    except Exception as e:
        return jsonify({
            'url': full_url,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/database', methods=['GET'])
def test_database_connection():
    """
    데이터베이스 연결 상태 테스트
    """
    try:
        from extensions import db
        from models.stock import StockList
        from models.trading import StockInvestorTrading
        
        tables_status = {}
        
        # 각 테이블의 레코드 수 확인
        try:
            stock_count = StockList.query.count()
            tables_status['stock_list'] = {
                'status': 'accessible', 
                'record_count': stock_count
            }
        except Exception as e:
            tables_status['stock_list'] = {
                'status': 'error',
                'error': str(e),
                'record_count': 0
            }
        
        try:
            trading_count = StockInvestorTrading.query.count()
            tables_status['stock_investor_trading'] = {
                'status': 'accessible',
                'record_count': trading_count
            }
        except Exception as e:
            tables_status['stock_investor_trading'] = {
                'status': 'error',
                'error': str(e),
                'record_count': 0
            }
        
        # 전체 상태 결정
        has_errors = any(table.get('status') == 'error' for table in tables_status.values())
        
        return jsonify({
            'database_status': 'connected_with_errors' if has_errors else 'connected',
            'tables': tables_status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"데이터베이스 테스트 실패: {str(e)}")
        return jsonify({
            'database_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/database/init', methods=['POST'])
def initialize_database():
    """
    데이터베이스 테이블 초기화 (기존 데이터 보존)
    """
    try:
        from extensions import db
        from models.stock import StockList
        from models.trading import StockInvestorTrading
        
        # 테이블 생성
        db.create_all()
        
        # 테이블 개수 확인
        total_tables = 2  # stock_list, stock_investor_trading
        
        return jsonify({
            'status': 'success',
            'message': f'데이터베이스 테이블이 생성되었습니다. ({total_tables}개 테이블)',
            'total_tables': total_tables,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'데이터베이스 초기화 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_test_bp.route('/database/reset', methods=['POST'])
def reset_database():
    """
    테스트 데이터 초기화 (모든 데이터 삭제)
    """
    try:
        from extensions import db
        from models.stock import StockList
        from models.trading import StockInvestorTrading
        
        # 삭제 전 거래 데이터 개수 확인
        trading_count = StockInvestorTrading.query.count()
        
        # 모든 데이터 삭제
        StockInvestorTrading.query.delete()
        StockList.query.delete()
        
        db.session.commit()
        
        # 히스토리 로깅 (거래 데이터가 있었던 경우에만)
        if trading_count > 0:
            try:
                from services.history_service import HistoryService
                HistoryService.log_data_change(
                    table_name='stock_investor_trading',
                    record_id=None,  # 전체 삭제이므로 특정 ID 없음
                    action='DELETE',
                    description=f'API 테스트 데이터 초기화로 거래 데이터 삭제: {trading_count}건'
                )
            except Exception as e:
                logger.warning(f"히스토리 로깅 실패: {e}")
        
        return jsonify({
            'status': 'success',
            'message': '모든 테스트 데이터가 초기화되었습니다.',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'데이터베이스 초기화 실패: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500 