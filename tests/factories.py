# -*- coding: utf-8 -*-
"""
테스트 데이터 팩토리
"""
import factory
from datetime import datetime, timedelta
from models.stock import StockList
from models.trading import StockInvestorTrading
from models.history import DataHistory, SystemLog


class StockFactory(factory.alchemy.SQLAlchemyModelFactory):
    """주식 모델 팩토리"""
    class Meta:
        model = StockList
        sqlalchemy_session_persistence = "commit"
    
    stock_code = factory.Sequence(lambda n: f'{n:06d}')
    stock_name = factory.Faker('company')
    init_date = factory.Faker('date')
    institution_accum_init = factory.Faker('pyint', min_value=0, max_value=1000000)
    foreigner_accum_init = factory.Faker('pyint', min_value=0, max_value=1000000)


class TradingFactory(factory.alchemy.SQLAlchemyModelFactory):
    """거래 모델 팩토리"""
    class Meta:
        model = StockInvestorTrading
        sqlalchemy_session_persistence = "commit"
    
    stock_code = factory.Sequence(lambda n: f'{n:06d}')
    stock_name = factory.Faker('company')
    trade_date = factory.LazyFunction(lambda: datetime.now().date().isoformat())
    close_price = factory.Faker('pyint', min_value=1000, max_value=100000)
    institution_net_buy = factory.Faker('pyint', min_value=-1000000, max_value=1000000)
    foreigner_net_buy = factory.Faker('pyint', min_value=-1000000, max_value=1000000)
    institution_accum = factory.Faker('pyint', min_value=0, max_value=10000000)
    foreigner_accum = factory.Faker('pyint', min_value=0, max_value=10000000)


class DataHistoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    """데이터 히스토리 모델 팩토리"""
    class Meta:
        model = DataHistory
        sqlalchemy_session_persistence = "commit"
    
    action = factory.Iterator(['CREATE', 'UPDATE', 'DELETE'])
    table_name = factory.Iterator(['stock_list', 'stock_investor_trading'])
    record_id = factory.Faker('pyint', min_value=1, max_value=1000)
    field_name = factory.Faker('word')
    old_value = factory.Faker('sentence')
    new_value = factory.Faker('sentence')
    description = factory.Faker('sentence')


class SystemLogFactory(factory.alchemy.SQLAlchemyModelFactory):
    """시스템 로그 모델 팩토리"""
    class Meta:
        model = SystemLog
        sqlalchemy_session_persistence = "commit"
    
    level = factory.Iterator(['INFO', 'WARNING', 'ERROR'])
    category = factory.Iterator(['API', 'DATABASE', 'COLLECTOR'])
    message = factory.Faker('sentence')
    details = factory.Faker('json')


# 특정 시나리오를 위한 팩토리
class SamsungStockFactory(StockFactory):
    """삼성전자 주식 팩토리"""
    stock_code = '005930'
    stock_name = '삼성전자'
    init_date = '1983-01-01'
    institution_accum_init = 0
    foreigner_accum_init = 0


class SKHynixStockFactory(StockFactory):
    """SK하이닉스 주식 팩토리"""
    stock_code = '000660'
    stock_name = 'SK하이닉스'
    init_date = '1996-01-01'
    institution_accum_init = 0
    foreigner_accum_init = 0


class NAVERStockFactory(StockFactory):
    """NAVER 주식 팩토리"""
    stock_code = '035420'
    stock_name = 'NAVER'
    init_date = '2002-01-01'
    institution_accum_init = 0
    foreigner_accum_init = 0


class TradingDataFactory(TradingFactory):
    """거래 데이터 팩토리"""
    
    @factory.post_generation
    def with_stock(self, create, extracted, **kwargs):
        """주식과 연결된 거래 데이터 생성"""
        if not create:
            return
        
        if extracted:
            self.stock_code = extracted.stock_code
            self.stock_name = extracted.stock_name


class StockDatasetFactory:
    """주식 데이터셋 팩토리"""
    
    @staticmethod
    def create_kospi_stocks(count=10):
        """KOSPI 주식 데이터 생성"""
        stocks = []
        for i in range(count):
            stock = StockFactory(
                stock_code=f'{i+1:06d}',
                stock_name=f'KOSPI주식{i+1}',
                init_date='2020-01-01'
            )
            stocks.append(stock)
        return stocks
    
    @staticmethod
    def create_kosdaq_stocks(count=10):
        """KOSDAQ 주식 데이터 생성"""
        stocks = []
        for i in range(count):
            stock = StockFactory(
                stock_code=f'{i+100:06d}',
                stock_name=f'KOSDAQ주식{i+1}',
                init_date='2020-01-01'
            )
            stocks.append(stock)
        return stocks


class TradingDatasetFactory:
    """거래 데이터셋 팩토리"""
    
    @staticmethod
    def create_daily_trading_data(stock_code, days=30):
        """일별 거래 데이터 생성"""
        trading_data = []
        base_date = datetime.now().date() - timedelta(days=days)
        
        for i in range(days):
            trading = TradingFactory(
                stock_code=stock_code,
                trade_date=(base_date + timedelta(days=i)).isoformat(),
                close_price=50000 + i * 100
            )
            trading_data.append(trading)
        
        return trading_data
    
    @staticmethod
    def create_multiple_stocks_trading_data(stock_codes, days=30):
        """여러 주식의 거래 데이터 생성"""
        all_trading_data = []
        
        for stock_code in stock_codes:
            trading_data = TradingDatasetFactory.create_daily_trading_data(stock_code, days)
            all_trading_data.extend(trading_data)
        
        return all_trading_data


def create_test_stock_data(db_session):
    """테스트용 주식 데이터 생성"""
    stocks = [
        StockFactory(stock_code='005930', stock_name='삼성전자'),
        StockFactory(stock_code='000660', stock_name='SK하이닉스'),
        StockFactory(stock_code='035420', stock_name='NAVER')
    ]
    
    for stock in stocks:
        db_session.add(stock)
    db_session.commit()
    
    return stocks


def create_test_trading_data(db_session, stocks):
    """테스트용 거래 데이터 생성"""
    trading_data = []
    
    for stock in stocks:
        for day in range(5):  # 5일치 데이터
            trading = TradingFactory(
                stock_code=stock.stock_code,
                stock_name=stock.stock_name,
                trade_date=(datetime.now().date() - timedelta(days=day)).isoformat(),
                close_price=50000 + day * 100
            )
            trading_data.append(trading)
    
    for trading in trading_data:
        db_session.add(trading)
    db_session.commit()
    
    return trading_data 