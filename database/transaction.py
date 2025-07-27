# -*- coding: utf-8 -*-
"""
트랜잭션 관리 유틸리티
API 레벨에서 트랜잭션을 안전하게 관리하기 위한 데코레이터와 함수들을 제공합니다.
"""
import functools
import logging
import time
from typing import Callable, Any
from flask import jsonify
from extensions import db
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

logger = logging.getLogger(__name__)

def transactional(func: Callable) -> Callable:
    """
    트랜잭션을 관리하는 데코레이터
    
    함수 실행 중 예외가 발생하면 자동으로 rollback하고,
    성공적으로 완료되면 commit합니다.
    
    Args:
        func: 트랜잭션으로 관리할 함수
        
    Returns:
        데코레이터가 적용된 함수
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 성공 시 commit
            db.session.commit()
            logger.debug(f"트랜잭션 commit 성공: {func.__name__}")
            
            return result
            
        except Exception as e:
            # 실패 시 rollback
            db.session.rollback()
            logger.error(f"트랜잭션 rollback: {func.__name__} - {str(e)}")
            raise
    
    return wrapper

def safe_transaction(func: Callable) -> Callable:
    """
    안전한 트랜잭션 관리 데코레이터 (API 응답 포함)
    
    함수 실행 중 예외가 발생하면 rollback하고 적절한 HTTP 응답을 반환합니다.
    
    Args:
        func: 트랜잭션으로 관리할 함수
        
    Returns:
        데코레이터가 적용된 함수
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 연결 상태 확인
                try:
                    db.session.execute(text("SELECT 1"))
                except Exception as conn_error:
                    logger.warning(f"데이터베이스 연결 확인 실패, 세션 재생성: {conn_error}")
                    db.session.close()
                    db.session.remove()
                    time.sleep(1)
                
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 성공 시 commit
                db.session.commit()
                logger.debug(f"트랜잭션 commit 성공: {func.__name__}")
                
                return result
                
            except OperationalError as e:
                db.session.rollback()
                db.session.close()
                db.session.remove()
                
                if "server closed the connection" in str(e).lower() or "connection" in str(e).lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"데이터베이스 연결 끊김, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries}): {func.__name__}")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"데이터베이스 연결 오류 (최대 재시도 초과): {func.__name__} - {str(e)}")
                        return jsonify({
                            'error': '데이터베이스 연결 오류가 발생했습니다.',
                            'type': 'database_error'
                        }), 503
                else:
                    logger.error(f"데이터베이스 오류: {func.__name__} - {str(e)}")
                    return jsonify({
                        'error': '데이터베이스 오류가 발생했습니다.',
                        'type': 'database_error'
                    }), 503
                    
            except ValueError as e:
                # 검증 오류 시 rollback
                db.session.rollback()
                logger.warning(f"트랜잭션 rollback (검증 오류): {func.__name__} - {str(e)}")
                return jsonify({
                    'error': str(e),
                    'type': 'validation_error'
                }), 400
                
            except Exception as e:
                # 기타 오류 시 rollback
                db.session.rollback()
                logger.error(f"트랜잭션 rollback (시스템 오류): {func.__name__} - {str(e)}")
                return jsonify({
                    'error': '서버 내부 오류가 발생했습니다.',
                    'type': 'system_error'
                }), 500
    
    return wrapper

def read_only_transaction(func: Callable) -> Callable:
    """
    읽기 전용 트랜잭션 데코레이터
    
    읽기 작업에 사용하며, 예외 발생 시에도 rollback하지 않습니다.
    
    Args:
        func: 읽기 전용 함수
        
    Returns:
        데코레이터가 적용된 함수
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 연결 상태 확인
                try:
                    db.session.execute(text("SELECT 1"))
                except Exception as conn_error:
                    logger.warning(f"데이터베이스 연결 확인 실패, 세션 재생성: {conn_error}")
                    db.session.close()
                    db.session.remove()
                    time.sleep(1)
                
                result = func(*args, **kwargs)
                return result
                
            except OperationalError as e:
                db.session.close()
                db.session.remove()
                
                if "server closed the connection" in str(e).lower() or "connection" in str(e).lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"데이터베이스 연결 끊김, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries}): {func.__name__}")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"데이터베이스 연결 오류 (최대 재시도 초과): {func.__name__} - {str(e)}")
                        raise
                else:
                    logger.error(f"데이터베이스 오류: {func.__name__} - {str(e)}")
                    raise
                    
            except Exception as e:
                logger.error(f"읽기 작업 실패: {func.__name__} - {str(e)}")
                raise
    
    return wrapper

def bulk_transaction(operations: list) -> bool:
    """
    여러 작업을 하나의 트랜잭션으로 처리
    
    Args:
        operations: 실행할 작업들의 리스트 (각각은 함수)
        
    Returns:
        bool: 모든 작업이 성공하면 True, 실패하면 False
    """
    try:
        # 연결 상태 확인
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as conn_error:
            logger.warning(f"데이터베이스 연결 확인 실패, 세션 재생성: {conn_error}")
            db.session.close()
            db.session.remove()
            time.sleep(1)
        
        for operation in operations:
            operation()
        
        db.session.commit()
        logger.info(f"벌크 트랜잭션 성공: {len(operations)}개 작업")
        return True
        
    except OperationalError as e:
        db.session.rollback()
        db.session.close()
        db.session.remove()
        logger.error(f"벌크 트랜잭션 실패 (연결 오류): {str(e)}")
        return False
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"벌크 트랜잭션 실패: {str(e)}")
        return False

def check_database_connection() -> bool:
    """
    데이터베이스 연결 상태를 확인합니다.
    
    Returns:
        bool: 연결이 정상이면 True, 아니면 False
    """
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"데이터베이스 연결 확인 실패: {e}")
        return False

def reset_database_session():
    """
    데이터베이스 세션을 재설정합니다.
    연결 오류 발생 시 호출하여 세션을 초기화합니다.
    """
    try:
        db.session.close()
        db.session.remove()
        logger.info("데이터베이스 세션 재설정 완료")
    except Exception as e:
        logger.error(f"데이터베이스 세션 재설정 실패: {e}") 