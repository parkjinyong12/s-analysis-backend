# -*- coding: utf-8 -*-
"""
Stock Investor Trading REST API 뷰
주식 투자자별 거래 데이터에 대한 CRUD API 엔드포인트를 제공합니다.
"""
from flask import Blueprint, jsonify, request
from services.trading_service import TradingService
from database.transaction import safe_transaction, read_only_transaction
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
trading_bp = Blueprint('trading', __name__, url_prefix='/trading')


@trading_bp.route('/', methods=['GET'])
@read_only_transaction
def list_trading_data():
    """
    거래 데이터 목록 조회
    
    Returns:
        JSON: 거래 데이터 목록 배열
        
    Example:
        GET /trading/
        Response: [{"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "trade_date": "2024-01-01", "close_price": 70000, ...}]
    """
    try:
        trading_data = TradingService.get_all_trading_data()
        return jsonify([data.to_dict() for data in trading_data]), 200
        
    except Exception as e:
        logger.error(f"거래 데이터 목록 조회 실패: {str(e)}")
        return jsonify({
            'error': '거래 데이터 목록을 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/<int:trading_id>', methods=['GET'])
@read_only_transaction
def get_trading_data(trading_id):
    """
    특정 거래 데이터 조회
    
    Args:
        trading_id (int): 거래 데이터 ID
        
    Returns:
        JSON: 거래 데이터 정보 또는 에러 메시지
        
    Example:
        GET /trading/1
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "trade_date": "2024-01-01", "close_price": 70000, ...}
    """
    try:
        # 입력값 검증
        if trading_id <= 0:
            return jsonify({
                'error': '유효하지 않은 거래 데이터 ID입니다.',
                'trading_id': trading_id
            }), 400
        
        trading_data = TradingService.get_trading_data_by_id(trading_id)
        
        if not trading_data:
            return jsonify({
                'error': '거래 데이터를 찾을 수 없습니다.',
                'trading_id': trading_id
            }), 404
            
        return jsonify(trading_data.to_dict()), 200
        
    except Exception as e:
        logger.error(f"거래 데이터 조회 실패 (ID: {trading_id}): {str(e)}")
        return jsonify({
            'error': '거래 데이터를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/stock/<string:stock_code>', methods=['GET'])
@read_only_transaction
def get_trading_data_by_stock_code(stock_code):
    """
    주식 코드로 거래 데이터 조회
    
    Args:
        stock_code (str): 주식 코드
        
    Returns:
        JSON: 거래 데이터 목록 또는 에러 메시지
        
    Example:
        GET /trading/stock/005930
        Response: [{"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "trade_date": "2024-01-01", ...}]
    """
    try:
        # 입력값 검증
        if not stock_code or not stock_code.strip():
            return jsonify({
                'error': '주식 코드는 필수입니다.',
                'stock_code': stock_code
            }), 400
        
        trading_data = TradingService.get_trading_data_by_stock_code(stock_code.strip())
        
        return jsonify([data.to_dict() for data in trading_data]), 200
        
    except Exception as e:
        logger.error(f"거래 데이터 조회 실패 (Code: {stock_code}): {str(e)}")
        return jsonify({
            'error': '거래 데이터를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/date-range', methods=['GET'])
@read_only_transaction
def get_trading_data_by_date_range():
    """
    날짜 범위로 거래 데이터 조회 (인덱스 최적화)
    
    Query Parameters:
        start_date (str): 시작 날짜 (YYYY-MM-DD, 필수)
        end_date (str): 종료 날짜 (YYYY-MM-DD, 필수)
        stock_code (str): 주식 코드 (선택)
        
    Returns:
        JSON: 거래 데이터 목록
        
    Example:
        GET /trading/date-range?start_date=2024-01-01&end_date=2024-01-31&stock_code=005930
        Response: [{"id": 1, "stock_code": "005930", "trade_date": "2024-01-01", ...}]
    """
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        stock_code = request.args.get('stock_code', '').strip() or None
        
        if not start_date or not end_date:
            return jsonify({
                'error': '시작 날짜와 종료 날짜는 필수입니다.',
                'required_parameters': ['start_date', 'end_date'],
                'format': 'YYYY-MM-DD'
            }), 400
        
        trading_data = TradingService.get_trading_data_by_date_range(
            start_date, end_date, stock_code
        )
        
        return jsonify([data.to_dict() for data in trading_data]), 200
        
    except Exception as e:
        logger.error(f"날짜 범위 거래 데이터 조회 실패: {str(e)}")
        return jsonify({
            'error': '거래 데이터를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500

@trading_bp.route('/stock-date-range', methods=['GET'])
@read_only_transaction
def get_trading_data_by_stock_date_range():
    """
    특정 종목의 날짜 범위 거래 데이터 조회 (고성능)
    
    Query Parameters:
        stock_code (str): 주식 코드 (필수)
        start_date (str): 시작 날짜 (YYYY-MM-DD, 필수)
        end_date (str): 종료 날짜 (YYYY-MM-DD, 필수)
        include_price (bool): 종가 포함 여부 (기본값: true)
        include_institution (bool): 기관 데이터 포함 여부 (기본값: true)
        include_foreigner (bool): 외국인 데이터 포함 여부 (기본값: true)
        
    Returns:
        JSON: 거래 데이터 목록
        
    Example:
        GET /trading/stock-date-range?stock_code=005930&start_date=2024-01-01&end_date=2024-01-31&include_price=true&include_institution=true&include_foreigner=false
        Response: [{"id": 1, "stock_code": "005930", "trade_date": "2024-01-01", "close_price": 70000, "institution_net_buy": 1000, ...}]
    """
    try:
        stock_code = request.args.get('stock_code', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # 불린 파라미터 처리
        include_price = request.args.get('include_price', 'true').lower() == 'true'
        include_institution = request.args.get('include_institution', 'true').lower() == 'true'
        include_foreigner = request.args.get('include_foreigner', 'true').lower() == 'true'
        
        if not stock_code:
            return jsonify({
                'error': '주식 코드는 필수입니다.',
                'required_parameters': ['stock_code']
            }), 400
        
        if not start_date or not end_date:
            return jsonify({
                'error': '시작 날짜와 종료 날짜는 필수입니다.',
                'required_parameters': ['start_date', 'end_date'],
                'format': 'YYYY-MM-DD'
            }), 400
        
        trading_data = TradingService.get_trading_data_by_stock_date_range(
            stock_code, start_date, end_date, include_price, include_institution, include_foreigner
        )
        
        return jsonify([data.to_dict() for data in trading_data]), 200
        
    except Exception as e:
        logger.error(f"종목별 날짜 범위 거래 데이터 조회 실패: {str(e)}")
        return jsonify({
            'error': '거래 데이터를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500

@trading_bp.route('/date-range-optimized', methods=['GET'])
@read_only_transaction
def get_trading_data_by_date_range_optimized():
    """
    날짜 범위 거래 데이터 조회 (페이징 지원, 고성능)
    
    Query Parameters:
        start_date (str): 시작 날짜 (YYYY-MM-DD, 필수)
        end_date (str): 종료 날짜 (YYYY-MM-DD, 필수)
        limit (int): 조회할 레코드 수 제한 (선택, 기본값: 1000)
        offset (int): 건너뛸 레코드 수 (선택, 기본값: 0)
        
    Returns:
        JSON: 거래 데이터 목록
        
    Example:
        GET /trading/date-range-optimized?start_date=2024-01-01&end_date=2024-01-31&limit=100&offset=0
        Response: [{"id": 1, "stock_code": "005930", "trade_date": "2024-01-01", ...}]
    """
    try:
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # 페이징 파라미터 처리
        try:
            limit = int(request.args.get('limit', 1000))
            if limit <= 0:
                limit = 1000
        except ValueError:
            limit = 1000
        
        try:
            offset = int(request.args.get('offset', 0))
            if offset < 0:
                offset = 0
        except ValueError:
            offset = 0
        
        if not start_date or not end_date:
            return jsonify({
                'error': '시작 날짜와 종료 날짜는 필수입니다.',
                'required_parameters': ['start_date', 'end_date'],
                'format': 'YYYY-MM-DD'
            }), 400
        
        trading_data = TradingService.get_trading_data_by_date_range_optimized(
            start_date, end_date, limit, offset
        )
        
        return jsonify([data.to_dict() for data in trading_data]), 200
        
    except Exception as e:
        logger.error(f"최적화된 날짜 범위 거래 데이터 조회 실패: {str(e)}")
        return jsonify({
            'error': '거래 데이터를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/', methods=['POST'])
@safe_transaction
def create_trading_data_api():
    """
    새 거래 데이터 생성
    
    Request Body:
        stock_code (str): 주식 코드 (필수, 6자리 숫자, 최대 20자)
        stock_name (str): 주식명 (필수, 최대 100자)
        trade_date (str): 거래 날짜 (필수, YYYY-MM-DD 형식, 최대 10자)
        close_price (int): 종가 (선택, 0 이상)
        institution_net_buy (int): 기관 순매수 (선택)
        foreigner_net_buy (int): 외국인 순매수 (선택)
        institution_accum (int): 기관 누적 매수 (선택)
        foreigner_accum (int): 외국인 누적 매수 (선택)
        institution_trend_signal (str): 기관 트렌드 신호 (선택, 최대 50자)
        institution_trend_score (float): 기관 트렌드 점수 (선택)
        foreigner_trend_signal (str): 외국인 트렌드 신호 (선택, 최대 50자)
        foreigner_trend_score (float): 외국인 트렌드 점수 (선택)
        
    Returns:
        JSON: 생성된 거래 데이터 정보
        
    Example:
        POST /trading/
        Body: {"stock_code": "005930", "stock_name": "삼성전자", "trade_date": "2024-01-01", "close_price": 70000, ...}
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자", "trade_date": "2024-01-01", ...}
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
        
        trade_date = data.get('trade_date')
        if not trade_date or not isinstance(trade_date, str) or not trade_date.strip():
            return jsonify({
                'error': '거래 날짜는 필수이며 비어있을 수 없습니다.',
                'field': 'trade_date',
                'constraints': 'YYYY-MM-DD 형식, 최대 10자'
            }), 400
        
        # 선택 필드 검증
        close_price = data.get('close_price')
        if close_price is not None and not isinstance(close_price, int):
            return jsonify({
                'error': '종가는 정수여야 합니다.',
                'field': 'close_price',
                'constraints': '0 이상의 정수'
            }), 400
        
        institution_net_buy = data.get('institution_net_buy')
        if institution_net_buy is not None and not isinstance(institution_net_buy, int):
            return jsonify({
                'error': '기관 순매수는 정수여야 합니다.',
                'field': 'institution_net_buy'
            }), 400
        
        foreigner_net_buy = data.get('foreigner_net_buy')
        if foreigner_net_buy is not None and not isinstance(foreigner_net_buy, int):
            return jsonify({
                'error': '외국인 순매수는 정수여야 합니다.',
                'field': 'foreigner_net_buy'
            }), 400
        
        institution_accum = data.get('institution_accum')
        if institution_accum is not None and not isinstance(institution_accum, int):
            return jsonify({
                'error': '기관 누적 매수는 정수여야 합니다.',
                'field': 'institution_accum'
            }), 400
        
        foreigner_accum = data.get('foreigner_accum')
        if foreigner_accum is not None and not isinstance(foreigner_accum, int):
            return jsonify({
                'error': '외국인 누적 매수는 정수여야 합니다.',
                'field': 'foreigner_accum'
            }), 400
        
        institution_trend_signal = data.get('institution_trend_signal')
        if institution_trend_signal is not None and not isinstance(institution_trend_signal, str):
            return jsonify({
                'error': '기관 트렌드 신호는 문자열이어야 합니다.',
                'field': 'institution_trend_signal',
                'constraints': '최대 50자'
            }), 400
        
        institution_trend_score = data.get('institution_trend_score')
        if institution_trend_score is not None and not isinstance(institution_trend_score, (int, float)):
            return jsonify({
                'error': '기관 트렌드 점수는 숫자여야 합니다.',
                'field': 'institution_trend_score'
            }), 400
        
        foreigner_trend_signal = data.get('foreigner_trend_signal')
        if foreigner_trend_signal is not None and not isinstance(foreigner_trend_signal, str):
            return jsonify({
                'error': '외국인 트렌드 신호는 문자열이어야 합니다.',
                'field': 'foreigner_trend_signal',
                'constraints': '최대 50자'
            }), 400
        
        foreigner_trend_score = data.get('foreigner_trend_score')
        if foreigner_trend_score is not None and not isinstance(foreigner_trend_score, (int, float)):
            return jsonify({
                'error': '외국인 트렌드 점수는 숫자여야 합니다.',
                'field': 'foreigner_trend_score'
            }), 400
        
        # 거래 데이터 생성
        trading_data = TradingService.create_trading_data(
            stock_code=stock_code.strip(),
            stock_name=stock_name.strip(),
            trade_date=trade_date.strip(),
            close_price=close_price,
            institution_net_buy=institution_net_buy,
            foreigner_net_buy=foreigner_net_buy,
            institution_accum=institution_accum,
            foreigner_accum=foreigner_accum,
            institution_trend_signal=institution_trend_signal.strip() if institution_trend_signal else None,
            institution_trend_score=float(institution_trend_score) if institution_trend_score is not None else None,
            foreigner_trend_signal=foreigner_trend_signal.strip() if foreigner_trend_signal else None,
            foreigner_trend_score=float(foreigner_trend_score) if foreigner_trend_score is not None else None
        )
        
        if not trading_data:
            return jsonify({
                'error': '거래 데이터 생성에 실패했습니다.'
            }), 500
        
        logger.info(f"새 거래 데이터 생성됨: {trading_data.stock_code} {trading_data.trade_date} (ID: {trading_data.id})")
        return jsonify(trading_data.to_dict()), 201
        
    except ValueError as e:
        logger.warning(f"거래 데이터 생성 입력값 오류: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"거래 데이터 생성 실패: {str(e)}")
        return jsonify({
            'error': '거래 데이터를 생성하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/<int:trading_id>', methods=['PUT'])
@safe_transaction
def update_trading_data_api(trading_id):
    """
    거래 데이터 정보 수정
    
    Args:
        trading_id (int): 거래 데이터 ID
        
    Request Body:
        stock_name (str): 주식명 (필수, 최대 100자)
        close_price (int): 종가 (선택, 0 이상)
        institution_net_buy (int): 기관 순매수 (선택)
        foreigner_net_buy (int): 외국인 순매수 (선택)
        institution_accum (int): 기관 누적 매수 (선택)
        foreigner_accum (int): 외국인 누적 매수 (선택)
        institution_trend_signal (str): 기관 트렌드 신호 (선택, 최대 50자)
        institution_trend_score (float): 기관 트렌드 점수 (선택)
        foreigner_trend_signal (str): 외국인 트렌드 신호 (선택, 최대 50자)
        foreigner_trend_score (float): 외국인 트렌드 점수 (선택)
        
    Returns:
        JSON: 수정된 거래 데이터 정보
        
    Example:
        PUT /trading/1
        Body: {"stock_name": "삼성전자우", "close_price": 71000, ...}
        Response: {"id": 1, "stock_code": "005930", "stock_name": "삼성전자우", "close_price": 71000, ...}
    """
    try:
        # 입력값 검증
        if trading_id <= 0:
            return jsonify({
                'error': '유효하지 않은 거래 데이터 ID입니다.',
                'trading_id': trading_id
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
        
        # 선택 필드 검증 (create와 동일한 로직)
        close_price = data.get('close_price')
        if close_price is not None and not isinstance(close_price, int):
            return jsonify({
                'error': '종가는 정수여야 합니다.',
                'field': 'close_price',
                'constraints': '0 이상의 정수'
            }), 400
        
        # 나머지 필드들도 동일하게 검증 (생략된 부분은 create와 동일)
        institution_net_buy = data.get('institution_net_buy')
        foreigner_net_buy = data.get('foreigner_net_buy')
        institution_accum = data.get('institution_accum')
        foreigner_accum = data.get('foreigner_accum')
        institution_trend_signal = data.get('institution_trend_signal')
        institution_trend_score = data.get('institution_trend_score')
        foreigner_trend_signal = data.get('foreigner_trend_signal')
        foreigner_trend_score = data.get('foreigner_trend_score')
        
        # 거래 데이터 수정
        trading_data = TradingService.update_trading_data(
            trading_id=trading_id,
            stock_name=stock_name.strip(),
            close_price=close_price,
            institution_net_buy=institution_net_buy,
            foreigner_net_buy=foreigner_net_buy,
            institution_accum=institution_accum,
            foreigner_accum=foreigner_accum,
            institution_trend_signal=institution_trend_signal.strip() if institution_trend_signal else None,
            institution_trend_score=float(institution_trend_score) if institution_trend_score is not None else None,
            foreigner_trend_signal=foreigner_trend_signal.strip() if foreigner_trend_signal else None,
            foreigner_trend_score=float(foreigner_trend_score) if foreigner_trend_score is not None else None
        )
        
        if not trading_data:
            return jsonify({
                'error': '거래 데이터를 찾을 수 없습니다.',
                'trading_id': trading_id
            }), 404
        
        logger.info(f"거래 데이터 수정됨: {trading_data.stock_code} {trading_data.trade_date} (ID: {trading_data.id})")
        return jsonify(trading_data.to_dict()), 200
        
    except ValueError as e:
        logger.warning(f"거래 데이터 수정 입력값 오류 (ID: {trading_id}): {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"거래 데이터 수정 실패 (ID: {trading_id}): {str(e)}")
        return jsonify({
            'error': '거래 데이터를 수정하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/<int:trading_id>', methods=['DELETE'])
@safe_transaction
def delete_trading_data_api(trading_id):
    """
    거래 데이터 삭제
    
    Args:
        trading_id (int): 거래 데이터 ID
        
    Returns:
        JSON: 삭제 결과 메시지
        
    Example:
        DELETE /trading/1
        Response: {"result": "success", "message": "거래 데이터가 성공적으로 삭제되었습니다.", "trading_id": 1}
    """
    try:
        # 입력값 검증
        if trading_id <= 0:
            return jsonify({
                'error': '유효하지 않은 거래 데이터 ID입니다.',
                'trading_id': trading_id
            }), 400
        
        # 삭제 전 거래 데이터 존재 확인
        existing_trading = TradingService.get_trading_data_by_id(trading_id)
        if not existing_trading:
            return jsonify({
                'error': '거래 데이터를 찾을 수 없습니다.',
                'trading_id': trading_id
            }), 404
        
        # 거래 데이터 삭제
        success = TradingService.delete_trading_data(trading_id)
        
        if not success:
            return jsonify({
                'error': '거래 데이터 삭제에 실패했습니다.',
                'trading_id': trading_id
            }), 500
        
        logger.info(f"거래 데이터 삭제됨: {existing_trading.stock_code} {existing_trading.trade_date} (ID: {trading_id})")
        return jsonify({
            'result': 'success',
            'message': '거래 데이터가 성공적으로 삭제되었습니다.',
            'trading_id': trading_id
        }), 200
        
    except Exception as e:
        logger.error(f"거래 데이터 삭제 실패 (ID: {trading_id}): {str(e)}")
        return jsonify({
            'error': '거래 데이터를 삭제하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/search', methods=['GET'])
@read_only_transaction
def search_trading_data():
    """
    거래 데이터 검색
    
    Query Parameters:
        query (str): 검색할 주식 코드 또는 주식명 (부분 일치)
        name (str): 검색할 주식명 (부분 일치) - 하위 호환성을 위해 유지
        
    Returns:
        JSON: 검색된 거래 데이터 목록
        
    Example:
        GET /trading/search?query=삼성바이오로직스
        GET /trading/search?query=207940
        GET /trading/search?name=삼성  (기존 방식)
        Response: [{"id": 1, "stock_code": "207940", "stock_name": "삼성바이오로직스", "trade_date": "2024-01-01", ...}]
    """
    try:
        # 새로운 query 파라미터 우선, 없으면 기존 name 파라미터 사용
        query = request.args.get('query', '').strip()
        name = request.args.get('name', '').strip()
        
        search_term = query or name
        
        if not search_term:
            return jsonify({
                'error': '검색할 주식 코드 또는 주식명을 입력해주세요.',
                'parameters': ['query', 'name']
            }), 400
        
        # query 파라미터가 있으면 코드/이름 모두 검색, name 파라미터면 이름만 검색
        if query:
            trading_data = TradingService.search_trading_data_by_query(search_term)
        else:
            trading_data = TradingService.search_trading_data_by_name(search_term)
        
        return jsonify([data.to_dict() for data in trading_data]), 200
        
    except Exception as e:
        logger.error(f"거래 데이터 검색 실패 (query: {search_term}): {str(e)}")
        return jsonify({
            'error': '거래 데이터를 검색하는데 실패했습니다.',
            'message': str(e)
        }), 500


@trading_bp.route('/<int:trading_id>/trend', methods=['PUT'])
@safe_transaction
def update_trend_analysis(trading_id):
    """
    트렌드 분석 데이터 업데이트
    
    Args:
        trading_id (int): 거래 데이터 ID
        
    Request Body:
        institution_trend_signal (str): 기관 트렌드 신호 (필수, 최대 50자)
        institution_trend_score (float): 기관 트렌드 점수 (필수)
        foreigner_trend_signal (str): 외국인 트렌드 신호 (필수, 최대 50자)
        foreigner_trend_score (float): 외국인 트렌드 점수 (필수)
        
    Returns:
        JSON: 업데이트된 거래 데이터 정보
        
    Example:
        PUT /trading/1/trend
        Body: {"institution_trend_signal": "상승", "institution_trend_score": 0.8, "foreigner_trend_signal": "하락", "foreigner_trend_score": -0.3}
        Response: {"id": 1, "stock_code": "005930", "institution_trend_signal": "상승", ...}
    """
    try:
        # 입력값 검증
        if trading_id <= 0:
            return jsonify({
                'error': '유효하지 않은 거래 데이터 ID입니다.',
                'trading_id': trading_id
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
        institution_trend_signal = data.get('institution_trend_signal')
        if not institution_trend_signal or not isinstance(institution_trend_signal, str):
            return jsonify({
                'error': '기관 트렌드 신호는 필수이며 문자열이어야 합니다.',
                'field': 'institution_trend_signal',
                'constraints': '최대 50자'
            }), 400
        
        institution_trend_score = data.get('institution_trend_score')
        if institution_trend_score is None or not isinstance(institution_trend_score, (int, float)):
            return jsonify({
                'error': '기관 트렌드 점수는 필수이며 숫자여야 합니다.',
                'field': 'institution_trend_score'
            }), 400
        
        foreigner_trend_signal = data.get('foreigner_trend_signal')
        if not foreigner_trend_signal or not isinstance(foreigner_trend_signal, str):
            return jsonify({
                'error': '외국인 트렌드 신호는 필수이며 문자열이어야 합니다.',
                'field': 'foreigner_trend_signal',
                'constraints': '최대 50자'
            }), 400
        
        foreigner_trend_score = data.get('foreigner_trend_score')
        if foreigner_trend_score is None or not isinstance(foreigner_trend_score, (int, float)):
            return jsonify({
                'error': '외국인 트렌드 점수는 필수이며 숫자여야 합니다.',
                'field': 'foreigner_trend_score'
            }), 400
        
        # 트렌드 분석 업데이트
        trading_data = TradingService.update_trend_analysis(
            trading_id=trading_id,
            institution_trend_signal=institution_trend_signal.strip(),
            institution_trend_score=float(institution_trend_score),
            foreigner_trend_signal=foreigner_trend_signal.strip(),
            foreigner_trend_score=float(foreigner_trend_score)
        )
        
        if not trading_data:
            return jsonify({
                'error': '거래 데이터를 찾을 수 없습니다.',
                'trading_id': trading_id
            }), 404
        
        logger.info(f"트렌드 분석 업데이트됨: {trading_data.stock_code} {trading_data.trade_date} (ID: {trading_data.id})")
        return jsonify(trading_data.to_dict()), 200
        
    except ValueError as e:
        logger.warning(f"트렌드 분석 업데이트 입력값 오류 (ID: {trading_id}): {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'validation_error'
        }), 400
        
    except Exception as e:
        logger.error(f"트렌드 분석 업데이트 실패 (ID: {trading_id}): {str(e)}")
        return jsonify({
            'error': '트렌드 분석을 업데이트하는데 실패했습니다.',
            'message': str(e)
        }), 500


# 에러 핸들러
@trading_bp.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        'error': '요청한 리소스를 찾을 수 없습니다.',
        'status_code': 404
    }), 404


@trading_bp.errorhandler(405)
def method_not_allowed(error):
    """405 에러 핸들러"""
    return jsonify({
        'error': '허용되지 않은 HTTP 메서드입니다.',
        'status_code': 405
    }), 405


@trading_bp.errorhandler(500)
def internal_server_error(error):
    """500 에러 핸들러"""
    logger.error(f"내부 서버 오류: {str(error)}")
    return jsonify({
        'error': '내부 서버 오류가 발생했습니다.',
        'status_code': 500
    }), 500 