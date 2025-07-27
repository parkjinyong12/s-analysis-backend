# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class BaseConfig:
    """기본 설정 클래스"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'devkey')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL 기본 설정
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'stock_analysis',
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }
    
    # 배치 처리 설정
    BATCH_PROCESSING = {
        'max_workers': 2,
        'task_timeout': 3600,
        'heartbeat_interval': 300,
        'max_memory_usage': 80,
        'auto_restart_on_failure': True,
    }
    
    # 로깅 설정
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # API 설정
    API_TITLE = 'Stock Analysis API'
    API_VERSION = 'v1'
    API_DESCRIPTION = '주식 분석 및 거래 데이터 관리 API'
    
    # CORS 설정
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

class DevelopmentConfig(BaseConfig):
    """개발 환경 설정"""
    DEBUG = True
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

class ProductionConfig(BaseConfig):
    """운영 환경 설정"""
    DEBUG = False
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    # 운영 환경에서는 더 보수적인 설정
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'stock_analysis_prod',
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }

class TestingConfig(BaseConfig):
    """테스트 환경 설정"""
    TESTING = True
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("TEST_DATABASE_URL 환경변수가 설정되지 않았습니다.")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    WTF_CSRF_ENABLED = False

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """환경에 따른 설정 반환"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 