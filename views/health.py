# -*- coding: utf-8 -*-
"""
헬스체크 API
"""
from flask import Blueprint, jsonify
from extensions import db
from core.logger import get_logger

health_bp = Blueprint('health', __name__)
logger = get_logger(__name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """애플리케이션 헬스체크"""
    try:
        # 데이터베이스 연결 확인
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        logger.error('Database health check failed', error=str(e))
        db_status = 'unhealthy'
    
    health_status = {
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'database': db_status,
        'timestamp': '2025-01-27T00:00:00Z'
    }
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """애플리케이션 준비 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        logger.error('Readiness check failed', error=str(e))
        return jsonify({'status': 'not ready'}), 503 