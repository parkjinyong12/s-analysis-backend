# -*- coding: utf-8 -*-
"""
유용한 데코레이터들
"""
import functools
import time
from flask import request, jsonify
from .logger import get_logger
from .exceptions import ValidationError

logger = get_logger(__name__)

def log_execution_time(func):
    """함수 실행 시간을 로깅하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(
            'Function execution time',
            function=func.__name__,
            execution_time=execution_time
        )
        return result
    return wrapper

def validate_json(*required_fields):
    """JSON 요청 데이터 검증 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                raise ValidationError("Content-Type must be application/json")
            
            data = request.get_json()
            if data is None:
                raise ValidationError("Invalid JSON data")
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def handle_exceptions(func):
    """예외 처리를 위한 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning('Validation error', error=str(e))
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error('Unexpected error', error=str(e), exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper

def cache_result(ttl=300):
    """결과 캐싱 데코레이터 (간단한 메모리 캐시)"""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 간단한 캐시 키 생성
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            current_time = time.time()
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl:
                    return result
            
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            return result
        return wrapper
    return decorator 