# -*- coding: utf-8 -*-
"""
모델 테스트
"""
import pytest
import random
from datetime import datetime
from models.stock import StockList
from models.trading import StockInvestorTrading
from models.history import DataHistory, SystemLog


@pytest.mark.unit
class TestStockModel:
    """주식 모델 테스트"""
    
    def test_stock_creation(self, db_session):
        """주식 생성 테스트"""
        # 고유한 주식 코드 사용
        unique_code = f"{random.randint(100000, 999999)}"
        
        stock = StockList(
            stock_code=unique_code,
            stock_name='테스트주식',
            init_date='2020-01-01',
            institution_accum_init=0,
            foreigner_accum_init=0
        )
        db_session.add(stock)
        db_session.commit()
        
        assert stock.id is not None
        assert stock.stock_code == unique_code
        assert stock.stock_name == '테스트주식'
        assert stock.init_date == '2020-01-01'
    
    def test_stock_repr(self, db_session):
        """주식 모델 문자열 표현 테스트"""
        stock = StockList(stock_code='005930', stock_name='삼성전자')
        assert str(stock) == '<StockList 005930: 삼성전자>'
    
    def test_stock_unique_code(self, db_session):
        """주식 코드 중복 방지 테스트"""
        # 고유한 주식 코드 사용
        unique_code = f"{random.randint(200000, 299999)}"
        
        stock1 = StockList(stock_code=unique_code, stock_name='테스트주식1')
        stock2 = StockList(stock_code=unique_code, stock_name='테스트주식2')
        
        db_session.add(stock1)
        db_session.commit()
        
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.add(stock2)
            db_session.commit()
    
    def test_stock_to_dict(self, db_session):
        """주식 모델 딕셔너리 변환 테스트"""
        stock = StockList(
            stock_code='005930',
            stock_name='삼성전자',
            init_date='1983-01-01',
            institution_accum_init=1000,
            foreigner_accum_init=2000
        )
        
        stock_dict = stock.to_dict()
        
        assert stock_dict['stock_code'] == '005930'
        assert stock_dict['stock_name'] == '삼성전자'
        assert stock_dict['init_date'] == '1983-01-01'
        assert stock_dict['institution_accum_init'] == 1000
        assert stock_dict['foreigner_accum_init'] == 2000


@pytest.mark.unit
class TestTradingModel:
    """거래 모델 테스트"""
    
    def test_trading_creation(self, db_session):
        """거래 데이터 생성 테스트"""
        # 고유한 주식 코드 사용
        unique_code = f"{random.randint(300000, 399999)}"
        
        trading = StockInvestorTrading(
            stock_code=unique_code,
            stock_name='테스트주식',
            trade_date=datetime.now().date().isoformat(),
            close_price=50500,
            institution_net_buy=100000,
            foreigner_net_buy=200000
        )
        db_session.add(trading)
        db_session.commit()
        
        assert trading.id is not None
        assert trading.stock_code == unique_code
        assert trading.stock_name == '테스트주식'
        assert trading.close_price == 50500
    
    def test_trading_price_validation(self, db_session):
        """거래 가격 유효성 검사 테스트"""
        # 음수 가격은 허용하지 않음
        with pytest.raises(ValueError):
            trading = StockInvestorTrading(
                stock_code='005930',
                stock_name='삼성전자',
                trade_date=datetime.now().date().isoformat(),
                close_price=-1000
            )


@pytest.mark.unit
class TestHistoryModel:
    """히스토리 모델 테스트"""
    
    def test_data_history_creation(self, db_session):
        """데이터 히스토리 생성 테스트"""
        history = DataHistory(
            action='CREATE',
            table_name='stock_list',
            record_id=1,
            field_name='stock_name',
            old_value=None,
            new_value='삼성전자',
            description='새 주식 생성'
        )
        db_session.add(history)
        db_session.commit()
        
        assert history.id is not None
        assert history.action == 'CREATE'
        assert history.table_name == 'stock_list'
        assert history.record_id == 1
        assert history.field_name == 'stock_name'
        assert history.old_value is None
        assert history.new_value == '삼성전자'
        assert history.description == '새 주식 생성'
    
    def test_system_log_creation(self, db_session):
        """시스템 로그 생성 테스트"""
        log = SystemLog(
            level='INFO',
            category='API',
            message='API 요청 처리 완료',
            details='{"endpoint": "/api/v1/stocks/", "method": "GET"}'
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.level == 'INFO'
        assert log.category == 'API'
        assert log.message == 'API 요청 처리 완료'
        assert log.details == '{"endpoint": "/api/v1/stocks/", "method": "GET"}' 