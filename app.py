# -*- coding: utf-8 -*-
import logging
from flask import Flask
from flask_cors import CORS
from extensions import db, cors, executor
from config import get_config
from core.logger import setup_logging

def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)
    
    # 설정 로드
    if config_name:
        app.config.from_object(f'config.{config_name}')
    else:
        app.config.from_object(get_config())
    
    # 로깅 설정
    setup_logging(app)
    
    # 확장 초기화
    initialize_extensions(app)
    
    # 블루프린트 등록
    register_blueprints(app)
    
    # 에러 핸들러 등록
    register_error_handlers(app)
    
    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    return app

def initialize_extensions(app):
    """확장 초기화"""
    db.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    executor.init_app(app)

def register_blueprints(app):
    """블루프린트 등록"""
    from views.user import user_bp
    from views.sample import sample_bp
    from views.stock import stock_bp
    from views.trading import trading_bp
    from views.data_collector import collector_bp
    from views.api_test import api_test_bp
    from views.history import history_bp
    from views.health import health_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(sample_bp, url_prefix='/api/v1/samples')
    app.register_blueprint(stock_bp, url_prefix='/api/v1/stocks')
    app.register_blueprint(trading_bp, url_prefix='/api/v1/trading')
    app.register_blueprint(collector_bp, url_prefix='/api/v1/collector')
    app.register_blueprint(api_test_bp, url_prefix='/api/v1/test')
    app.register_blueprint(history_bp, url_prefix='/api/v1/history')
    app.register_blueprint(health_bp)

def register_error_handlers(app):
    """에러 핸들러 등록"""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=True) 