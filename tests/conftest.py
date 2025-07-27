# -*- coding: utf-8 -*-
"""
pytest 설정 파일
"""
import pytest
import tempfile
import os
import json
from datetime import datetime
from flask import Flask
from app import create_app
from extensions import db
from tests.factories import (
    StockFactory, TradingFactory,
    create_test_stock_data, create_test_trading_data
)


@pytest.fixture(scope='session')
def app():
    """테스트용 Flask 애플리케이션"""
    # Flask 앱 생성 (설정 없이)
    app = Flask(__name__)
    
    # 직접 설정
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TEST_DATABASE_URL')
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("TEST_DATABASE_URL 환경변수가 설정되지 않았습니다.")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-key'
    app.config['CORS_ORIGINS'] = ['*']
    
    # 확장 초기화
    db.init_app(app)
    
    # 블루프린트 등록
    from views.stock import stock_bp
    from views.trading import trading_bp
    from views.data_collector import collector_bp
    from views.api_test import api_test_bp
    from views.history import history_bp
    from views.health import health_bp
    
    app.register_blueprint(stock_bp, url_prefix='/api/v1/stocks')
    app.register_blueprint(trading_bp, url_prefix='/api/v1/trading')
    app.register_blueprint(collector_bp, url_prefix='/api/v1/collector')
    app.register_blueprint(api_test_bp, url_prefix='/api/v1/test')
    app.register_blueprint(history_bp, url_prefix='/api/v1/history')
    app.register_blueprint(health_bp)
    
    with app.app_context():
        # 테이블은 이미 존재하므로 create_all()만 실행
        db.create_all()
        yield app
        # 테스트 세션 종료 시 데이터베이스 정리
        db.session.remove()
        # 테이블 삭제하지 않음


@pytest.fixture
def client(app):
    """테스트 클라이언트"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """테스트 CLI 러너"""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """데이터베이스 세션 - API와 공유"""
    with app.app_context():
        # 세션 초기화
        db.session.rollback()
        yield db.session
        # 테스트 종료 후 정리
        db.session.rollback()
        db.session.remove()


@pytest.fixture
def sample_stock(db_session):
    """샘플 주식 데이터"""
    stock = StockFactory(
        code='005930',
        name='삼성전자',
        market='KOSPI',
        sector='전기전자'
    )
    db_session.add(stock)
    db_session.commit()
    return stock


@pytest.fixture
def sample_trading(db_session, sample_stock):
    """샘플 거래 데이터"""
    trading = TradingFactory(
        stock_code=sample_stock.code,
        date=datetime.now().date(),
        open_price=50000,
        high_price=51000,
        low_price=49000,
        close_price=50500,
        volume=1000000
    )
    db_session.add(trading)
    db_session.commit()
    return trading


@pytest.fixture
def test_stocks(db_session):
    """테스트용 주식 데이터"""
    return create_test_stock_data(db_session)


@pytest.fixture
def test_trading_data(db_session, test_stocks):
    """테스트용 거래 데이터"""
    return create_test_trading_data(db_session, test_stocks)


@pytest.fixture
def stock_data():
    """주식 데이터 샘플"""
    return {
        'stock_code': '005930',
        'stock_name': '삼성전자',
        'init_date': '1983-01-01',
        'institution_accum_init': 1000,
        'foreigner_accum_init': 2000
    }


@pytest.fixture
def trading_data():
    """거래 데이터 샘플"""
    return {
        'stock_code': '005930',
        'stock_name': '삼성전자',
        'trade_date': datetime.now().date().isoformat(),
        'open_price': 50000,
        'high_price': 51000,
        'low_price': 49000,
        'close_price': 50500,
        'volume': 1000000,
        'institution_net_buy': 500,
        'foreigner_net_buy': 300
    }


@pytest.fixture
def mock_external_api():
    """외부 API 모킹"""
    from unittest.mock import Mock, patch
    
    mock_response = Mock()
    mock_response.json.return_value = {
        'data': [
            {
                'stock_code': '005930',
                'close_price': 50000,
                'volume': 1000000
            }
        ]
    }
    mock_response.status_code = 200
    
    with patch('requests.get', return_value=mock_response):
        yield mock_response


@pytest.fixture
def mock_database_connection():
    """데이터베이스 연결 모킹"""
    from unittest.mock import Mock, patch
    
    mock_connection = Mock()
    mock_connection.execute.return_value = Mock()
    
    with patch('sqlalchemy.create_engine', return_value=mock_connection):
        yield mock_connection


@pytest.fixture
def mock_redis():
    """Redis 모킹"""
    from unittest.mock import Mock, patch
    
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    with patch('redis.Redis', return_value=mock_redis):
        yield mock_redis


@pytest.fixture
def mock_logger():
    """로거 모킹"""
    from unittest.mock import Mock, patch
    
    mock_logger = Mock()
    
    with patch('core.logger.get_logger', return_value=mock_logger):
        yield mock_logger


# 성능 테스트용 fixture
@pytest.fixture
def large_dataset(db_session):
    """대용량 데이터셋"""
    # 1000개의 주식 데이터 생성
    stocks = []
    for i in range(1000):
        stock = StockFactory(
            code=f'{i:06d}',
            name=f'주식{i}',
            market='KOSPI' if i % 2 == 0 else 'KOSDAQ'
        )
        stocks.append(stock)
    
    db_session.add_all(stocks)
    db_session.commit()
    
    # 각 주식에 대한 거래 데이터 생성
    trading_data = []
    for stock in stocks[:100]:  # 처음 100개 주식만
        for day in range(30):  # 30일치 데이터
            trading = TradingFactory(
                stock_code=stock.code,
                date=datetime.now().date(),
                close_price=50000 + day * 100
            )
            trading_data.append(trading)
    
    db_session.add_all(trading_data)
    db_session.commit()
    
    return {'stocks': stocks, 'trading': trading_data}


# 병렬 테스트용 fixture
@pytest.fixture(scope='session')
def shared_app():
    """세션 전체에서 공유하는 앱"""
    # Flask 앱 생성 (설정 없이)
    app = Flask(__name__)
    
    # 직접 설정
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TEST_DATABASE_URL')
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("TEST_DATABASE_URL 환경변수가 설정되지 않았습니다.")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-key'
    app.config['CORS_ORIGINS'] = ['*']
    
    # 확장 초기화
    db.init_app(app)
    
    # 블루프린트 등록
    from views.stock import stock_bp
    from views.trading import trading_bp
    from views.data_collector import collector_bp
    from views.api_test import api_test_bp
    from views.history import history_bp
    from views.health import health_bp
    
    app.register_blueprint(stock_bp, url_prefix='/api/v1/stocks')
    app.register_blueprint(trading_bp, url_prefix='/api/v1/trading')
    app.register_blueprint(collector_bp, url_prefix='/api/v1/collector')
    app.register_blueprint(api_test_bp, url_prefix='/api/v1/test')
    app.register_blueprint(history_bp, url_prefix='/api/v1/history')
    app.register_blueprint(health_bp)
    
    with app.app_context():
        # 기존 데이터 정리
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def isolated_db_session(shared_app):
    """격리된 데이터베이스 세션"""
    with shared_app.app_context():
        yield db.session
        db.session.rollback()
        db.session.remove() 