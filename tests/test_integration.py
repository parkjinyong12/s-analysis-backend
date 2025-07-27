# -*- coding: utf-8 -*-
"""
통합 테스트
"""
import pytest
import json
import random
from datetime import datetime
from app import create_app
from models.stock import StockList
from models.trading import StockInvestorTrading


@pytest.mark.integration
class TestStockAPIIntegration:
    """주식 API 통합 테스트"""
    
    def test_stock_crud_flow(self, client, db_session):
        """주식 CRUD 전체 플로우 테스트"""
        # 고유한 주식 코드 사용
        unique_code = f"{random.randint(100000, 999999)}"
        
        # 1. 주식 생성
        stock_data = {
            'stock_code': unique_code,
            'stock_name': '테스트주식'
        }
        
        response = client.post(
            '/api/v1/stocks/',
            data=json.dumps(stock_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        created_stock = json.loads(response.data)
        assert created_stock['stock_code'] == unique_code
        
        stock_id = created_stock['id']
        
        # 2. 주식 조회
        response = client.get(f'/api/v1/stocks/{stock_id}')
        assert response.status_code == 200
        stock = json.loads(response.data)
        assert stock['stock_name'] == '테스트주식'
        
        # 3. 주식 수정
        update_data = {'stock_name': '업데이트된 주식명'}
        response = client.put(
            f'/api/v1/stocks/{stock_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        updated_stock = json.loads(response.data)
        assert updated_stock['stock_name'] == '업데이트된 주식명'
        
        # 4. 주식 삭제
        response = client.delete(f'/api/v1/stocks/{stock_id}')
        assert response.status_code == 204
        
        # 5. 삭제 확인
        response = client.get(f'/api/v1/stocks/{stock_id}')
        assert response.status_code == 404
    
    def test_stock_list_pagination(self, client, db_session):
        """주식 목록 페이지네이션 테스트"""
        # 테스트 데이터 생성
        stocks = [
            StockList(stock_code='005930', stock_name='삼성전자'),
            StockList(stock_code='000660', stock_name='SK하이닉스'),
            StockList(stock_code='035420', stock_name='NAVER'),
        ]
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()
        
        # 페이지네이션 테스트
        response = client.get('/api/v1/stocks/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 3


@pytest.mark.integration
class TestTradingAPIIntegration:
    """거래 API 통합 테스트"""
    
    def test_trading_data_flow(self, client, db_session):
        """거래 데이터 플로우 테스트"""
        # 고유한 주식 코드 사용
        unique_code = f"{random.randint(200000, 299999)}"
        
        # 주식 데이터 먼저 생성
        stock = StockList(stock_code=unique_code, stock_name='테스트주식')
        db_session.add(stock)
        db_session.commit()
        
        # 거래 데이터 생성
        trading_data = {
            'stock_code': unique_code,
            'trade_date': datetime.now().date().isoformat(),
            'open_price': 50000,
            'high_price': 51000,
            'low_price': 49000,
            'close_price': 50500,
            'volume': 1000000,
            'institution_net_buy': 500,
            'foreigner_net_buy': 300
        }
        
        response = client.post(
            '/api/v1/trading/',
            data=json.dumps(trading_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # 거래 데이터 조회
        response = client.get(f'/api/v1/trading/{unique_code}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0


@pytest.mark.integration
class TestHealthCheckIntegration:
    """헬스 체크 통합 테스트"""
    
    def test_health_check(self, client):
        """헬스 체크 테스트"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_readiness_check(self, client):
        """준비 상태 체크 테스트"""
        response = client.get('/ready')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ready'


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """에러 처리 통합 테스트"""
    
    def test_404_error(self, client):
        """404 에러 테스트"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """잘못된 JSON 테스트"""
        response = client.post(
            '/api/v1/stocks/',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client):
        """필수 필드 누락 테스트"""
        response = client.post(
            '/api/v1/stocks/',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400


@pytest.mark.performance
class TestPerformanceIntegration:
    """성능 통합 테스트"""
    
    def test_large_dataset_performance(self, client, db_session):
        """대용량 데이터셋 성능 테스트"""
        # 대용량 데이터 생성
        stocks = []
        for i in range(100):
            stock = StockList(
                stock_code=f'{i:06d}',
                stock_name=f'주식{i}'
            )
            stocks.append(stock)
        
        db_session.add_all(stocks)
        db_session.commit()
        
        # 성능 테스트
        import time
        start_time = time.time()
        
        response = client.get('/api/v1/stocks/')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert response.status_code == 200
        assert execution_time < 1.0  # 1초 이내 응답 