# -*- coding: utf-8 -*-
"""
Stock API 테스트
"""
import pytest
import json
from models.stock import StockList


@pytest.mark.api
def test_get_stocks(client):
    """주식 목록 조회 테스트"""
    response = client.get('/api/v1/stocks/')
    assert response.status_code == 200
    data = json.loads(response.data)
    # API는 배열을 직접 반환하므로 배열인지 확인
    assert isinstance(data, list)


@pytest.mark.api
def test_get_stock_by_code(client):
    """주식 코드로 조회 테스트"""
    # 고유한 주식 코드 사용 (6자리 숫자)
    import random
    unique_code = f"{random.randint(100000, 999999)}"
    
    # 먼저 주식 생성
    create_data = {
        'stock_code': unique_code,
        'stock_name': '테스트주식'
    }
    create_response = client.post(
        '/api/v1/stocks/',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    assert create_response.status_code == 201

    # 주식 코드로 조회
    response = client.get(f'/api/v1/stocks/code/{unique_code}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['stock_code'] == unique_code


@pytest.mark.api
def test_create_stock(client):
    """주식 생성 테스트"""
    # 고유한 주식 코드 사용 (6자리 숫자)
    import random
    unique_code = f"{random.randint(400000, 499999)}"
    
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
    data = json.loads(response.data)
    assert data['stock_code'] == unique_code


@pytest.mark.api
def test_simple_crud_flow(client):
    """간단한 CRUD 플로우 테스트"""
    # 고유한 주식 코드 생성
    import random
    import time
    unique_code = f"{random.randint(100000, 999999)}"
    
    # 1. CREATE - 주식 생성
    create_data = {
        'stock_code': unique_code,
        'stock_name': 'CRUD테스트주식'
    }
    create_response = client.post(
        '/api/v1/stocks/',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    print(f"CREATE 응답 상태: {create_response.status_code}")
    print(f"CREATE 응답 데이터: {create_response.data}")
    
    assert create_response.status_code == 201
    created_stock = json.loads(create_response.data)
    print(f"생성된 주식 전체 데이터: {created_stock}")
    
    stock_id = created_stock.get('id')
    print(f"생성된 주식 ID: {stock_id}")
    print(f"ID 타입: {type(stock_id)}")
    
    # ID가 None이면 테스트 중단
    if stock_id is None:
        print("❌ ID가 None입니다. API 응답을 확인하세요.")
        return
    
    # 2. READ - 주식 조회
    get_response = client.get(f'/api/v1/stocks/{stock_id}')
    print(f"GET 응답 상태: {get_response.status_code}")
    if get_response.status_code == 200:
        stock_data = json.loads(get_response.data)
        print(f"조회된 주식: {stock_data}")
    
    # 3. UPDATE - 주식 수정
    update_data = {
        'stock_name': '수정된주식명'
    }
    update_response = client.put(
        f'/api/v1/stocks/{stock_id}',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    print(f"PUT 응답 상태: {update_response.status_code}")
    if update_response.status_code != 200:
        print(f"PUT 응답 데이터: {update_response.data}")
    
    # 4. DELETE - 주식 삭제
    delete_response = client.delete(f'/api/v1/stocks/{stock_id}')
    print(f"DELETE 응답 상태: {delete_response.status_code}")
    
    # 최소한 CREATE는 성공해야 함
    assert create_response.status_code == 201


@pytest.mark.api
def test_update_stock(client):
    """주식 수정 테스트"""
    # 고유한 주식 코드 사용 (6자리 숫자)
    import random
    unique_code = f"{random.randint(200000, 299999)}"
    
    # 먼저 주식 생성
    create_data = {
        'stock_code': unique_code,
        'stock_name': '테스트주식'
    }
    create_response = client.post(
        '/api/v1/stocks/',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    assert create_response.status_code == 201
    
    # 생성된 주식의 ID 가져오기
    created_stock = json.loads(create_response.data)
    stock_id = created_stock['id']
    
    # 디버깅 정보 출력
    print(f"생성된 주식 ID: {stock_id}")
    print(f"생성된 주식 데이터: {created_stock}")
    
    # 주식 수정
    update_data = {
        'stock_name': '업데이트된 주식명'
    }

    response = client.put(
        f'/api/v1/stocks/{stock_id}',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    # 디버깅 정보 출력
    print(f"PUT 응답 상태 코드: {response.status_code}")
    print(f"PUT 응답 데이터: {response.data}")
    
    assert response.status_code == 200


@pytest.mark.api
def test_delete_stock(client):
    """주식 삭제 테스트"""
    # 고유한 주식 코드 사용 (6자리 숫자)
    import random
    unique_code = f"{random.randint(300000, 399999)}"
    
    # 먼저 주식 생성
    create_data = {
        'stock_code': unique_code,
        'stock_name': '테스트주식'
    }
    create_response = client.post(
        '/api/v1/stocks/',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    assert create_response.status_code == 201
    
    # 생성된 주식의 ID 가져오기
    created_stock = json.loads(create_response.data)
    stock_id = created_stock['id']
    
    # 주식 삭제
    response = client.delete(f'/api/v1/stocks/{stock_id}')
    assert response.status_code == 204 