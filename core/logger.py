# -*- coding: utf-8 -*-
"""
로깅 시스템 설정
"""
import logging
import structlog
from flask import request, g
from datetime import datetime

def setup_logging(app):
    """로깅 설정"""
    # 기본 로깅 설정
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format=app.config['LOG_FORMAT']
    )
    
    # structlog 설정
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name):
    """로거 인스턴스 반환"""
    return structlog.get_logger(name)

def log_request_info():
    """요청 정보 로깅"""
    logger = get_logger('request')
    logger.info(
        'Request received',
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

def log_response_info(response):
    """응답 정보 로깅"""
    logger = get_logger('response')
    logger.info(
        'Response sent',
        status_code=response.status_code,
        content_length=len(response.get_data()),
        path=request.path
    )
    return response 