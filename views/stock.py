# -*- coding: utf-8 -*-
"""
Stock REST API 뷰
주식 목록에 대한 CRUD API 엔드포인트를 제공합니다.
"""
from flask import Blueprint, jsonify, request
from services.stock_service import StockService
from services.stock_list_collector import StockListCollectorService
from database.transaction import safe_transaction, read_only_transaction
import logging
from datetime import datetime
from extensions import db
import pandas as pd
import io
import os
import re

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
stock_bp = Blueprint('stock', __name__, url_prefix='/stocks')


@stock_bp.route('/', methods=['GET'])
@read_only_transaction
def list_stocks():
    """
    주식 목록 조회
    
    Returns:
        JSON: 주식 목록 배열
        
    Example:
        GET /stocks/
        Response: [{"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 0, "foreigner_accum_init": 0}]
    """
    try:
        stocks = StockService.get_all_stocks()
        return jsonify([stock.to_dict() for stock in stocks]), 200
        
    except Exception as e:
        logger.error(f"주식 목록 조회 실패: {str(e)}")
        return jsonify({
            'error': '주식 목록을 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/<int:stock_id>', methods=['GET'])
@read_only_transaction
def get_stock(stock_id):
    """
    특정 주식 조회
    
    Args:
        stock_id (int): 주식 ID
        
    Returns:
        JSON: 주식 정보 또는 에러 메시지
        
    Example:
        GET /stocks/1
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 0, "foreigner_accum_init": 0}
    """
    try:
        # 입력값 검증
        if stock_id <= 0:
            return jsonify({
                'error': '유효하지 않은 주식 ID입니다.',
                'stock_id': stock_id
            }), 400
        
        stock = StockService.get_stock_by_id(stock_id)
        
        if not stock:
            return jsonify({
                'error': '주식을 찾을 수 없습니다.',
                'stock_id': stock_id
            }), 404
            
        return jsonify(stock.to_dict()), 200
        
    except Exception as e:
        logger.error(f"주식 조회 실패 (ID: {stock_id}): {str(e)}")
        return jsonify({
            'error': '주식을 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/code/<string:stock_code>', methods=['GET'])
@read_only_transaction
def get_stock_by_code(stock_code):
    """
    주식 코드로 주식 조회
    
    Args:
        stock_code (str): 주식 코드
        
    Returns:
        JSON: 주식 정보 또는 에러 메시지
        
    Example:
        GET /stocks/code/005930
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 0, "foreigner_accum_init": 0}
    """
    try:
        # 입력값 검증
        if not stock_code or not stock_code.strip():
            return jsonify({
                'error': '주식 코드는 필수입니다.',
                'stock_code': stock_code
            }), 400
        
        stock = StockService.get_stock_by_code(stock_code.strip())
        
        if not stock:
            return jsonify({
                'error': '주식을 찾을 수 없습니다.',
                'stock_code': stock_code
            }), 404
            
        return jsonify(stock.to_dict()), 200
        
    except Exception as e:
        logger.error(f"주식 조회 실패 (Code: {stock_code}): {str(e)}")
        return jsonify({
            'error': '주식을 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/', methods=['POST'])
@safe_transaction
def create_stock_api():
    """
    새 주식 생성
    
    Request Body:
        stock_code (str): 주식 코드 (필수, 6자리 숫자, 최대 20자)
        stock_name (str): 주식명 (필수, 최대 100자)
        init_date (str): 초기화 날짜 (선택, YYYY-MM-DD 형식, 최대 10자)
        institution_accum_init (int): 기관 누적 초기값 (선택, 기본값: 0, 0 이상)
        foreigner_accum_init (int): 외국인 누적 초기값 (선택, 기본값: 0, 0 이상)
        
    Returns:
        JSON: 생성된 주식 정보
        
    Example:
        POST /stocks/
        Body: {"stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 1000, "foreigner_accum_init": 2000}
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 1000, "foreigner_accum_init": 2000}
    """
    try:
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type은 application/json이어야 합니다.'
            }), 400
            
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': '요청 본문이 비어있습니다.'
            }), 400
        
        # 필수 필드 검증
        stock_code = data.get('stock_code')
        if not stock_code or not isinstance(stock_code, str) or not stock_code.strip():
            return jsonify({
                'error': '주식 코드는 필수이며 비어있을 수 없습니다.',
                'field': 'stock_code',
                'constraints': '6자리 숫자, 최대 20자'
            }), 400
        
        stock_name = data.get('stock_name')
        if not stock_name or not isinstance(stock_name, str) or not stock_name.strip():
            return jsonify({
                'error': '주식명은 필수이며 비어있을 수 없습니다.',
                'field': 'stock_name',
                'constraints': '최대 100자'
            }), 400
        
        # 선택 필드 검증
        init_date = data.get('init_date')
        if init_date is not None and not isinstance(init_date, str):
            return jsonify({
                'error': '초기화 날짜는 문자열이어야 합니다.',
                'field': 'init_date',
                'constraints': 'YYYY-MM-DD 형식, 최대 10자'
            }), 400
        
        institution_accum_init = data.get('institution_accum_init', 0)
        if not isinstance(institution_accum_init, int):
            return jsonify({
                'error': '기관 누적 초기값은 정수여야 합니다.',
                'field': 'institution_accum_init',
                'constraints': '0 이상의 정수'
            }), 400
        
        foreigner_accum_init = data.get('foreigner_accum_init', 0)
        if not isinstance(foreigner_accum_init, int):
            return jsonify({
                'error': '외국인 누적 초기값은 정수여야 합니다.',
                'field': 'foreigner_accum_init',
                'constraints': '0 이상의 정수'
            }), 400
        
        # 주식 생성
        stock = StockService.create_stock(
            stock_code=stock_code.strip(),
            stock_name=stock_name.strip(),
            init_date=init_date.strip() if init_date else None,
            institution_accum_init=institution_accum_init,
            foreigner_accum_init=foreigner_accum_init
        )
        
        if not stock:
            return jsonify({
                'error': '주식 생성에 실패했습니다.'
            }), 500
        
        # ID 할당을 위해 commit
        db.session.commit()
        
        logger.info(f"새 주식 생성됨: {stock.stock_code} - {stock.stock_name} (ID: {stock.id})")
        return jsonify(stock.to_dict()), 201
        
    except ValueError as e:
        logger.warning(f"주식 생성 입력값 오류: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"주식 생성 실패: {str(e)}")
        return jsonify({
            'error': '주식을 생성하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/<int:stock_id>', methods=['PUT'])
@safe_transaction
def update_stock_api(stock_id):
    """
    주식 정보 수정
    
    Args:
        stock_id (int): 주식 ID
        
    Request Body:
        stock_name (str): 주식명 (필수, 최대 100자)
        init_date (str): 초기화 날짜 (선택, YYYY-MM-DD 형식, 최대 10자)
        institution_accum_init (int): 기관 누적 초기값 (선택, 0 이상)
        foreigner_accum_init (int): 외국인 누적 초기값 (선택, 0 이상)
        
    Returns:
        JSON: 수정된 주식 정보
        
    Example:
        PUT /stocks/1
        Body: {"stock_name": "삼성전자우", "init_date": "2024-01-02", "institution_accum_init": 1500, "foreigner_accum_init": 2500}
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자우", "init_date": "2024-01-02", "institution_accum_init": 1500, "foreigner_accum_init": 2500}
    """
    try:
        # 입력값 검증
        if stock_id <= 0:
            return jsonify({
                'error': '유효하지 않은 주식 ID입니다.',
                'stock_id': stock_id
            }), 400
        
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type은 application/json이어야 합니다.'
            }), 400
            
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': '요청 본문이 비어있습니다.'
            }), 400
        
        # 필수 필드 검증
        stock_name = data.get('stock_name')
        if not stock_name or not isinstance(stock_name, str) or not stock_name.strip():
            return jsonify({
                'error': '주식명은 필수이며 비어있을 수 없습니다.',
                'field': 'stock_name',
                'constraints': '최대 100자'
            }), 400
        
        # 선택 필드 검증
        init_date = data.get('init_date')
        if init_date is not None and not isinstance(init_date, str):
            return jsonify({
                'error': '초기화 날짜는 문자열이어야 합니다.',
                'field': 'init_date',
                'constraints': 'YYYY-MM-DD 형식, 최대 10자'
            }), 400
        
        institution_accum_init = data.get('institution_accum_init')
        if institution_accum_init is not None and not isinstance(institution_accum_init, int):
            return jsonify({
                'error': '기관 누적 초기값은 정수여야 합니다.',
                'field': 'institution_accum_init',
                'constraints': '0 이상의 정수'
            }), 400
        
        foreigner_accum_init = data.get('foreigner_accum_init')
        if foreigner_accum_init is not None and not isinstance(foreigner_accum_init, int):
            return jsonify({
                'error': '외국인 누적 초기값은 정수여야 합니다.',
                'field': 'foreigner_accum_init',
                'constraints': '0 이상의 정수'
            }), 400
        
        # 주식 수정
        stock = StockService.update_stock(
            stock_id=stock_id,
            stock_name=stock_name.strip(),
            init_date=init_date.strip() if init_date else None,
            institution_accum_init=institution_accum_init,
            foreigner_accum_init=foreigner_accum_init
        )
        
        if not stock:
            return jsonify({
                'error': '주식을 찾을 수 없습니다.',
                'stock_id': stock_id
            }), 404
        
        logger.info(f"주식 수정됨: {stock.stock_code} - {stock.stock_name} (ID: {stock.id})")
        return jsonify(stock.to_dict()), 200
        
    except ValueError as e:
        logger.warning(f"주식 수정 입력값 오류 (ID: {stock_id}): {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"주식 수정 실패 (ID: {stock_id}): {str(e)}")
        return jsonify({
            'error': '주식을 수정하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/<int:stock_id>', methods=['DELETE'])
@safe_transaction
def delete_stock_api(stock_id):
    """
    주식 삭제
    
    Args:
        stock_id (int): 주식 ID
        
    Returns:
        JSON: 삭제 결과 메시지
        
    Example:
        DELETE /stocks/1
        Response: {"result": "success", "message": "주식이 성공적으로 삭제되었습니다.", "stock_id": 1}
    """
    try:
        # 입력값 검증
        if stock_id <= 0:
            return jsonify({
                'error': '유효하지 않은 주식 ID입니다.',
                'stock_id': stock_id
            }), 400
        
        # 삭제 전 주식 존재 확인
        existing_stock = StockService.get_stock_by_id(stock_id)
        if not existing_stock:
            return jsonify({
                'error': '주식을 찾을 수 없습니다.',
                'stock_id': stock_id
            }), 404
        
        # 주식 삭제
        success = StockService.delete_stock(stock_id)
        
        if not success:
            return jsonify({
                'error': '주식 삭제에 실패했습니다.',
                'stock_id': stock_id
            }), 500
        
        logger.info(f"주식 삭제됨: {existing_stock.stock_code} - {existing_stock.stock_name} (ID: {stock_id})")
        return '', 204
        
    except Exception as e:
        logger.error(f"주식 삭제 실패 (ID: {stock_id}): {str(e)}")
        return jsonify({
            'error': '주식을 삭제하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/search/', methods=['GET'])
@stock_bp.route('/search', methods=['GET'])
@read_only_transaction
def search_stocks():
    """
    주식 검색
    
    Query Parameters:
        name (str): 검색할 주식명 (부분 일치)
        code (str): 검색할 주식 코드 (부분 일치)
        
    Returns:
        JSON: 검색된 주식 목록
        
    Example:
        GET /stocks/search?name=삼성
        GET /stocks/search?code=005
        Response: [{"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 0, "foreigner_accum_init": 0}]
    """
    try:
        name = request.args.get('name', '').strip()
        code = request.args.get('code', '').strip()
        
        if not name and not code:
            return jsonify({
                'error': '검색할 주식명 또는 주식 코드를 입력해주세요.',
                'parameters': ['name', 'code']
            }), 400
        
        stocks = []
        if name:
            stocks.extend(StockService.search_stocks_by_name(name))
        if code:
            code_stocks = StockService.search_stocks_by_code(code)
            # 중복 제거
            existing_ids = {stock.id for stock in stocks}
            stocks.extend([stock for stock in code_stocks if stock.id not in existing_ids])
        
        return jsonify([stock.to_dict() for stock in stocks]), 200
        
    except Exception as e:
        logger.error(f"주식 검색 실패 (name: {name}, code: {code}): {str(e)}")
        return jsonify({
            'error': '주식을 검색하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/<int:stock_id>/accum', methods=['PUT'])
@safe_transaction
def update_accum_values(stock_id):
    """
    누적 초기값 업데이트
    
    Args:
        stock_id (int): 주식 ID
        
    Request Body:
        institution_accum_init (int): 기관 누적 초기값 (필수, 0 이상)
        foreigner_accum_init (int): 외국인 누적 초기값 (필수, 0 이상)
        
    Returns:
        JSON: 업데이트된 주식 정보
        
    Example:
        PUT /stocks/1/accum
        Body: {"institution_accum_init": 1500, "foreigner_accum_init": 2500}
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "init_date": "2024-01-01", "institution_accum_init": 1500, "foreigner_accum_init": 2500}
    """
    try:
        # 입력값 검증
        if stock_id <= 0:
            return jsonify({
                'error': '유효하지 않은 주식 ID입니다.',
                'stock_id': stock_id
            }), 400
        
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type은 application/json이어야 합니다.'
            }), 400
            
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': '요청 본문이 비어있습니다.'
            }), 400
        
        # 필수 필드 검증
        institution_accum_init = data.get('institution_accum_init')
        if institution_accum_init is None or not isinstance(institution_accum_init, int):
            return jsonify({
                'error': '기관 누적 초기값은 필수이며 정수여야 합니다.',
                'field': 'institution_accum_init',
                'constraints': '0 이상의 정수'
            }), 400
        
        foreigner_accum_init = data.get('foreigner_accum_init')
        if foreigner_accum_init is None or not isinstance(foreigner_accum_init, int):
            return jsonify({
                'error': '외국인 누적 초기값은 필수이며 정수여야 합니다.',
                'field': 'foreigner_accum_init',
                'constraints': '0 이상의 정수'
            }), 400
        
        # 누적값 업데이트
        stock = StockService.update_accum_values(
            stock_id=stock_id,
            institution_accum_init=institution_accum_init,
            foreigner_accum_init=foreigner_accum_init
        )
        
        if not stock:
            return jsonify({
                'error': '주식을 찾을 수 없습니다.',
                'stock_id': stock_id
            }), 404
        
        logger.info(f"누적값 업데이트됨: {stock.stock_code} - {stock.stock_name} (ID: {stock.id})")
        return jsonify(stock.to_dict()), 200
        
    except ValueError as e:
        logger.warning(f"누적값 업데이트 입력값 오류 (ID: {stock_id}): {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"누적값 업데이트 실패 (ID: {stock_id}): {str(e)}")
        return jsonify({
            'error': '누적값을 업데이트하는데 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/bulk-create', methods=['POST'])
@safe_transaction
def bulk_create_stocks():
    """
    주식 목록 일괄 생성
    
    Request Body:
        stocks (List[Dict]): 주식 정보 목록
            - stock_code (str): 주식 코드 (필수)
            - stock_name (str): 주식명 (필수)
            - init_date (str): 초기화 날짜 (선택)
            - institution_accum_init (int): 기관 누적 초기값 (선택, 기본값: 0)
            - foreigner_accum_init (int): 외국인 누적 초기값 (선택, 기본값: 0)
        
    Returns:
        JSON: 일괄 생성 결과
        
    Example:
        POST /stocks/bulk-create
        Body: {
            "stocks": [
                {"stock_code": "005930", "stock_name": "삼성전자"},
                {"stock_code": "000660", "stock_name": "SK하이닉스"}
            ]
        }
    """
    try:
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type은 application/json이어야 합니다.'
            }), 400
            
        data = request.get_json()
        
        if not data or 'stocks' not in data:
            return jsonify({
                'error': 'stocks 필드는 필수입니다.'
            }), 400
        
        stocks_data = data['stocks']
        
        if not isinstance(stocks_data, list) or len(stocks_data) == 0:
            return jsonify({
                'error': 'stocks는 비어있지 않은 배열이어야 합니다.'
            }), 400
        
        # 결과 통계
        results = {
            'total_requested': len(stocks_data),
            'success_count': 0,
            'failed_count': 0,
            'success_list': [],
            'failed_list': []
        }
        
        # 각 주식별로 생성 시도
        for stock_data in stocks_data:
            try:
                # 필수 필드 검증
                stock_code = stock_data.get('stock_code')
                stock_name = stock_data.get('stock_name')
                
                if not stock_code or not stock_name:
                    results['failed_count'] += 1
                    results['failed_list'].append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'error': '주식 코드와 주식명은 필수입니다.'
                    })
                    continue
                
                # 선택 필드
                init_date = stock_data.get('init_date')
                institution_accum_init = stock_data.get('institution_accum_init', 0)
                foreigner_accum_init = stock_data.get('foreigner_accum_init', 0)
                
                # 주식 생성
                stock = StockService.create_stock(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    init_date=init_date,
                    institution_accum_init=institution_accum_init,
                    foreigner_accum_init=foreigner_accum_init
                )
                
                if stock:
                    results['success_count'] += 1
                    results['success_list'].append({
                        'id': stock.id,
                        'stock_code': stock.stock_code,
                        'stock_name': stock.stock_name
                    })
                    logger.info(f"주식 일괄 생성 성공: {stock.stock_code} - {stock.stock_name}")
                else:
                    results['failed_count'] += 1
                    results['failed_list'].append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'error': '주식 생성에 실패했습니다.'
                    })
                
            except ValueError as e:
                results['failed_count'] += 1
                results['failed_list'].append({
                    'stock_code': stock_data.get('stock_code'),
                    'stock_name': stock_data.get('stock_name'),
                    'error': str(e)
                })
                logger.warning(f"주식 일괄 생성 입력값 오류: {e}")
                
            except Exception as e:
                results['failed_count'] += 1
                results['failed_list'].append({
                    'stock_code': stock_data.get('stock_code'),
                    'stock_name': stock_data.get('stock_name'),
                    'error': f'주식 생성 중 오류: {str(e)}'
                })
                logger.error(f"주식 일괄 생성 실패: {e}")
        
        # 트랜잭션 커밋
        db.session.commit()
        
        logger.info(f"주식 일괄 생성 완료: 성공 {results['success_count']}개, 실패 {results['failed_count']}개")
        
        return jsonify({
            'status': 'success',
            'message': f'주식 일괄 생성 완료: 성공 {results["success_count"]}개, 실패 {results["failed_count"]}개',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"주식 일괄 생성 중 오류: {str(e)}")
        return jsonify({
            'error': '주식 일괄 생성에 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/collect-list', methods=['POST'])
def collect_stock_list():
    """
    코스피/코스닥 주식 목록 수집
    
    Request Body:
        market (str): 수집할 시장 ("kospi", "kosdaq", "all")
        
    Returns:
        JSON: 수집된 주식 목록
        
    Example:
        POST /stocks/collect-list
        Body: {"market": "all"}
    """
    try:
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type은 application/json이어야 합니다.'
            }), 400
            
        data = request.get_json()
        market = data.get('market', 'all').lower()
        
        if market not in ['kospi', 'kosdaq', 'kospi_all', 'all']:
            return jsonify({
                'error': 'market은 "kospi", "kosdaq", "kospi_all", "all" 중 하나여야 합니다.'
            }), 400
        
        # 주식 목록 수집
        if market == 'kospi':
            stocks = StockListCollectorService.collect_kospi_stocks()
            result = {
                'kospi': stocks,
                'kosdaq': [],
                'total': len(stocks)
            }
        elif market == 'kospi_all':
            stocks = StockListCollectorService.collect_kospi_all_stocks()
            result = {
                'kospi': stocks,
                'kosdaq': [],
                'total': len(stocks)
            }
        elif market == 'kosdaq':
            stocks = StockListCollectorService.collect_kosdaq_stocks()
            result = {
                'kospi': [],
                'kosdaq': stocks,
                'total': len(stocks)
            }
        else:  # all
            result = StockListCollectorService.collect_all_stocks()
        
        logger.info(f"주식 목록 수집 완료: {market} - 총 {result['total']}개")
        
        return jsonify({
            'status': 'success',
            'message': f'주식 목록 수집 완료: {result["total"]}개',
            'market': market,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"주식 목록 수집 실패: {str(e)}")
        return jsonify({
            'error': '주식 목록 수집에 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/auto-add', methods=['POST'])
@safe_transaction
def auto_add_stocks():
    """
    수집된 주식 목록을 자동으로 데이터베이스에 추가
    
    Request Body:
        market (str): 추가할 시장 ("kospi", "kosdaq", "all")
        limit (int): 추가할 최대 개수 (선택, 기본값: 50)
        
    Returns:
        JSON: 자동 추가 결과
        
    Example:
        POST /stocks/auto-add
        Body: {"market": "all", "limit": 100}
    """
    try:
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type은 application/json이어야 합니다.'
            }), 400
            
        data = request.get_json()
        market = data.get('market', 'all').lower()
        limit = data.get('limit', 50)
        
        if market not in ['kospi', 'kosdaq', 'kospi_all', 'all']:
            return jsonify({
                'error': 'market은 "kospi", "kosdaq", "kospi_all", "all" 중 하나여야 합니다.'
            }), 400
        
        if not isinstance(limit, int) or limit <= 0:
            return jsonify({
                'error': 'limit은 양의 정수여야 합니다.'
            }), 400
        
        # 주식 목록 수집
        if market == 'kospi':
            stocks_data = StockListCollectorService.collect_kospi_stocks()
        elif market == 'kospi_all':
            stocks_data = StockListCollectorService.collect_kospi_all_stocks()
        elif market == 'kosdaq':
            stocks_data = StockListCollectorService.collect_kosdaq_stocks()
        else:  # all
            all_stocks = StockListCollectorService.collect_all_stocks()
            stocks_data = all_stocks['kospi'] + all_stocks['kosdaq']
        
        # 제한 개수만큼만 처리
        stocks_data = stocks_data[:limit]
        
        # 결과 통계
        results = {
            'total_collected': len(stocks_data),
            'success_count': 0,
            'failed_count': 0,
            'duplicate_count': 0,
            'success_list': [],
            'failed_list': []
        }
        
        # 각 주식별로 추가 시도
        for stock_data in stocks_data:
            try:
                stock_code = stock_data['stock_code']
                stock_name = stock_data['stock_name']
                
                # 이미 존재하는지 확인
                existing_stock = StockService.get_stock_by_code(stock_code)
                if existing_stock:
                    results['duplicate_count'] += 1
                    continue
                
                # 주식 생성
                stock = StockService.create_stock(
                    stock_code=stock_code,
                    stock_name=stock_name
                )
                
                if stock:
                    results['success_count'] += 1
                    results['success_list'].append({
                        'id': stock.id,
                        'stock_code': stock.stock_code,
                        'stock_name': stock.stock_name
                    })
                    logger.info(f"주식 자동 추가 성공: {stock.stock_code} - {stock.stock_name}")
                else:
                    results['failed_count'] += 1
                    results['failed_list'].append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'error': '주식 생성에 실패했습니다.'
                    })
                
            except Exception as e:
                results['failed_count'] += 1
                results['failed_list'].append({
                    'stock_code': stock_data.get('stock_code'),
                    'stock_name': stock_data.get('stock_name'),
                    'error': str(e)
                })
                logger.error(f"주식 자동 추가 실패: {e}")
        
        # 트랜잭션 커밋
        db.session.commit()
        
        logger.info(f"주식 자동 추가 완료: 성공 {results['success_count']}개, 실패 {results['failed_count']}개, 중복 {results['duplicate_count']}개")
        
        return jsonify({
            'status': 'success',
            'message': f'주식 자동 추가 완료: 성공 {results["success_count"]}개, 실패 {results["failed_count"]}개, 중복 {results["duplicate_count"]}개',
            'market': market,
            'limit': limit,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"주식 자동 추가 중 오류: {str(e)}")
        return jsonify({
            'error': '주식 자동 추가에 실패했습니다.',
            'message': str(e)
        }), 500


@stock_bp.route('/upload-excel', methods=['POST'])
@safe_transaction
def upload_excel_stocks():
    """
    엑셀 파일을 통한 주식 목록 업로드 및 업데이트
    
    Request:
        - Content-Type: multipart/form-data
        - file: 엑셀 파일 (.xlsx, .xls)
        
    Excel Format:
        - stock_code (str): 주식 코드 (필수)
        - stock_name (str): 주식명 (필수)
        - init_date (str): 초기화 날짜 (선택)
        - institution_accum_init (int): 기관 누적 초기값 (선택)
        - foreigner_accum_init (int): 외국인 누적 초기값 (선택)
        
    Returns:
        JSON: 업로드 및 업데이트 결과
        
    Example:
        POST /stocks/upload-excel
        Body: multipart/form-data with excel file
    """
    try:
        # 파일 업로드 확인
        if 'file' not in request.files:
            return jsonify({
                'error': '파일이 업로드되지 않았습니다.'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': '파일이 선택되지 않았습니다.'
            }), 400
        
        # 파일 확장자 확인
        allowed_extensions = {'xlsx', 'xls', 'csv'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({
                'error': '지원하지 않는 파일 형식입니다. (.xlsx, .xls, .csv 파일만 지원)'
            }), 400
        
        # 파일 읽기 (엑셀 또는 CSV)
        try:
            if file_extension == 'csv':
                # CSV 파일 읽기 (다양한 인코딩 시도)
                encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
                df = None
                
                for encoding in encodings:
                    try:
                        file.seek(0)  # 파일 포인터 리셋
                        df = pd.read_csv(file, encoding=encoding)
                        if not df.empty:
                            logger.info(f"CSV 파일을 {encoding} 인코딩으로 성공적으로 읽었습니다.")
                            break
                    except Exception as encoding_error:
                        logger.debug(f"{encoding} 인코딩으로 읽기 실패: {str(encoding_error)}")
                        continue
                
                if df is None or df.empty:
                    raise Exception("지원되는 인코딩으로 CSV 파일을 읽을 수 없습니다.")
                    
            elif file_extension == 'xlsx':
                df = pd.read_excel(file, engine='openpyxl')
            else:  # xls
                df = pd.read_excel(file, engine='xlrd')
        except Exception as e:
            logger.error(f"파일 읽기 실패: {str(e)}")
            return jsonify({
                'error': '파일을 읽을 수 없습니다.',
                'message': str(e)
            }), 400
        
        # 필수 컬럼 확인 (한국 주식 형식)
        required_columns = ['단축코드', '한글 종목약명']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'필수 컬럼이 누락되었습니다: {", ".join(missing_columns)}',
                'required_columns': required_columns,
                'available_columns': list(df.columns)
            }), 400
        
        # 결과 통계
        results = {
            'total_rows': len(df),
            'success_count': 0,
            'update_count': 0,
            'create_count': 0,
            'failed_count': 0,
            'success_list': [],
            'update_list': [],
            'failed_list': []
        }
        
        # 각 행별로 처리
        for index, row in df.iterrows():
            try:
                # 데이터 추출 (한국 주식 형식)
                stock_code = str(row['단축코드']).strip().zfill(6)  # 6자리로 패딩
                stock_name = str(row['한글 종목약명']).strip()
                # 선택적 필드
                init_date = row.get('상장일')
                if pd.isna(init_date):
                    init_date = None
                else:
                    # 날짜 형식 정규화 (다양한 형식 -> YYYY-MM-DD)
                    init_date = str(init_date).strip()
                    
                    # 이미 YYYY-MM-DD 형식인 경우
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', init_date):
                        pass  # 그대로 사용
                    
                    # YYYY.M.D 형식인 경우
                    elif '.' in init_date:
                        parts = init_date.split('.')
                        if len(parts) == 3:
                            year = parts[0].zfill(4)  # 연도 4자리
                            month = parts[1].zfill(2)  # 월 2자리
                            day = parts[2].zfill(2)    # 일 2자리
                            init_date = f"{year}-{month}-{day}"
                        else:
                            init_date = None  # 잘못된 형식이면 None으로 설정
                    
                    # YYYY/MM/DD 형식인 경우
                    elif '/' in init_date:
                        parts = init_date.split('/')
                        if len(parts) == 3:
                            year = parts[0].zfill(4)  # 연도 4자리
                            month = parts[1].zfill(2)  # 월 2자리
                            day = parts[2].zfill(2)    # 일 2자리
                            init_date = f"{year}-{month}-{day}"
                        else:
                            init_date = None
                    
                    # YYYYMMDD 형식인 경우
                    elif len(init_date) == 8 and init_date.isdigit():
                        year = init_date[:4]
                        month = init_date[4:6]
                        day = init_date[6:8]
                        init_date = f"{year}-{month}-{day}"
                    
                    # 기타 형식은 None으로 설정
                    else:
                        logger.warning(f"지원하지 않는 날짜 형식: {init_date}")
                        init_date = None
                
                # 추가 정보 (선택적)
                market_type = row.get('시장구분', '')
                par_value = row.get('액면가', 0)
                listed_shares = row.get('상장주식수', 0)
                
                # 기본값 설정
                institution_accum_init = 0
                foreigner_accum_init = 0
                
                # 데이터 검증
                if not stock_code or not stock_name:
                    results['failed_count'] += 1
                    results['failed_list'].append({
                        'row': index + 1,
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'error': '주식 코드와 주식명은 필수입니다.'
                    })
                    continue
                
                # 보통주, 우선주만 허용 (6자리 숫자)
                if not stock_code.isdigit() or len(stock_code) != 6:
                    # 전환사채, 신주인수권증서 등 특수종목은 조용히 건너뛰기
                    continue
                
                # 기존 주식 확인
                existing_stock = StockService.get_stock_by_code(stock_code)
                
                if existing_stock:
                    # 기존 주식 업데이트
                    try:
                        # 주식 정보 업데이트
                        existing_stock.stock_name = stock_name
                        if init_date:
                            existing_stock.init_date = init_date
                        existing_stock.institution_accum_init = institution_accum_init
                        existing_stock.foreigner_accum_init = foreigner_accum_init
                        
                        results['update_count'] += 1
                        results['update_list'].append({
                            'id': existing_stock.id,
                            'stock_code': existing_stock.stock_code,
                            'stock_name': existing_stock.stock_name,
                            'action': 'updated'
                        })
                        
                        logger.info(f"주식 업데이트 성공: {stock_code} - {stock_name}")
                        
                    except Exception as e:
                        results['failed_count'] += 1
                        results['failed_list'].append({
                            'row': index + 1,
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'error': f'주식 업데이트 실패: {str(e)}'
                        })
                        logger.error(f"주식 업데이트 실패: {stock_code} - {e}")
                
                else:
                    # 새로운 주식 생성
                    try:
                        stock = StockService.create_stock(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            init_date=init_date,
                            institution_accum_init=institution_accum_init,
                            foreigner_accum_init=foreigner_accum_init
                        )
                        
                        if stock:
                            results['create_count'] += 1
                            results['success_list'].append({
                                'id': stock.id,
                                'stock_code': stock.stock_code,
                                'stock_name': stock.stock_name,
                                'action': 'created'
                            })
                            
                            logger.info(f"주식 생성 성공: {stock_code} - {stock_name}")
                        else:
                            results['failed_count'] += 1
                            results['failed_list'].append({
                                'row': index + 1,
                                'stock_code': stock_code,
                                'stock_name': stock_name,
                                'error': '주식 생성에 실패했습니다.'
                            })
                    
                    except Exception as e:
                        results['failed_count'] += 1
                        results['failed_list'].append({
                            'row': index + 1,
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'error': f'주식 생성 실패: {str(e)}'
                        })
                        logger.error(f"주식 생성 실패: {stock_code} - {e}")
                
                results['success_count'] += 1
                
            except Exception as e:
                results['failed_count'] += 1
                results['failed_list'].append({
                    'row': index + 1,
                    'stock_code': str(row.get('stock_code', '')),
                    'stock_name': str(row.get('stock_name', '')),
                    'error': f'행 처리 중 오류: {str(e)}'
                })
                logger.error(f"엑셀 행 처리 실패 (행 {index + 1}): {e}")
        
        # 트랜잭션 커밋
        db.session.commit()
        
        logger.info(f"엑셀 파일 업로드 완료: 총 {results['total_rows']}행, 성공 {results['success_count']}개, 업데이트 {results['update_count']}개, 생성 {results['create_count']}개, 실패 {results['failed_count']}개")
        
        return jsonify({
            'status': 'success',
            'message': f'엑셀 파일 업로드 완료: 총 {results["total_rows"]}행, 성공 {results["success_count"]}개, 업데이트 {results["update_count"]}개, 생성 {results["create_count"]}개, 실패 {results["failed_count"]}개',
            'filename': file.filename,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"엑셀 파일 업로드 중 오류: {str(e)}")
        return jsonify({
            'error': '엑셀 파일 업로드에 실패했습니다.',
            'message': str(e)
        }), 500


# 에러 핸들러
@stock_bp.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        'error': '요청한 리소스를 찾을 수 없습니다.',
        'status_code': 404
    }), 404


@stock_bp.errorhandler(405)
def method_not_allowed(error):
    """405 에러 핸들러"""
    return jsonify({
        'error': '허용되지 않은 HTTP 메서드입니다.',
        'status_code': 405
    }), 405


@stock_bp.errorhandler(500)
def internal_server_error(error):
    """500 에러 핸들러"""
    logger.error(f"내부 서버 오류: {str(error)}")
    return jsonify({
        'error': '내부 서버 오류가 발생했습니다.',
        'status_code': 500
    }), 500 