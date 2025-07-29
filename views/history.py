# -*- coding: utf-8 -*-
"""
히스토리 관리 REST API 뷰
데이터 변경 히스토리와 시스템 로그를 관리하는 API 엔드포인트를 제공합니다.
"""
from flask import Blueprint, jsonify, request
from services.history_service import HistoryService
from extensions import db
from models.history import DataHistory, SystemLog
from database.transaction import safe_transaction, read_only_transaction
from datetime import datetime, timedelta
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
history_bp = Blueprint('history', __name__)


@history_bp.route('/data', methods=['GET'])
@read_only_transaction
def get_data_history():
    """
    데이터 히스토리 조회
    
    Query Parameters:
        table_name (str, optional): 테이블명 필터
        record_id (int, optional): 레코드 ID 필터
        action (str, optional): 작업 유형 필터 (CREATE, READ, UPDATE, DELETE)
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD)
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD)
        limit (int, optional): 조회 개수 제한 (기본값: 100)
        offset (int, optional): 오프셋 (기본값: 0)
        
    Returns:
        JSON: 히스토리 목록
    """
    try:
        # 쿼리 파라미터 파싱
        table_name = request.args.get('table_name')
        record_id = request.args.get('record_id', type=int)
        action = request.args.get('action')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 날짜 파싱
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({
                    'error': '잘못된 시작 날짜 형식입니다. (YYYY-MM-DD 형식 사용)'
                }), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({
                    'error': '잘못된 종료 날짜 형식입니다. (YYYY-MM-DD 형식 사용)'
                }), 400
        
        # 히스토리 조회
        history_list = HistoryService.get_data_history(
            table_name=table_name,
            record_id=record_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return jsonify([history.to_dict() for history in history_list]), 200
        
    except Exception as e:
        logger.error(f"데이터 히스토리 조회 실패: {str(e)}")
        return jsonify({
            'error': '데이터 히스토리를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@history_bp.route('/system', methods=['GET'])
@read_only_transaction
def get_system_logs():
    """
    시스템 로그 조회
    
    Query Parameters:
        level (str, optional): 로그 레벨 필터 (INFO, WARNING, ERROR)
        category (str, optional): 카테고리 필터
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD)
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD)
        limit (int, optional): 조회 개수 제한 (기본값: 100)
        offset (int, optional): 오프셋 (기본값: 0)
        
    Returns:
        JSON: 시스템 로그 목록
    """
    try:
        # 쿼리 파라미터 파싱
        level = request.args.get('level')
        category = request.args.get('category')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 날짜 파싱
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({
                    'error': '잘못된 시작 날짜 형식입니다. (YYYY-MM-DD 형식 사용)'
                }), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({
                    'error': '잘못된 종료 날짜 형식입니다. (YYYY-MM-DD 형식 사용)'
                }), 400
        
        # 시스템 로그 조회
        logs = HistoryService.get_system_logs(
            level=level,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return jsonify([log.to_dict() for log in logs]), 200
        
    except Exception as e:
        logger.error(f"시스템 로그 조회 실패: {str(e)}")
        return jsonify({
            'error': '시스템 로그를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@history_bp.route('/latest', methods=['GET'])
@read_only_transaction
def get_latest_activity():
    """
    최근 활동 조회
    
    Query Parameters:
        table_name (str, optional): 테이블명 필터
        limit (int, optional): 조회 개수 제한 (기본값: 10)
        
    Returns:
        JSON: 최근 활동 목록
    """
    try:
        table_name = request.args.get('table_name')
        limit = request.args.get('limit', 10, type=int)
        
        # 최근 활동 조회
        activities = HistoryService.get_latest_activity(
            table_name=table_name,
            limit=limit
        )
        
        return jsonify([activity.to_dict() for activity in activities]), 200
        
    except Exception as e:
        logger.error(f"최근 활동 조회 실패: {str(e)}")
        return jsonify({
            'error': '최근 활동을 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@history_bp.route('/summary', methods=['GET'])
@read_only_transaction
def get_activity_summary():
    """
    활동 요약 조회
    
    Query Parameters:
        days (int, optional): 조회할 일수 (기본값: 7)
        
    Returns:
        JSON: 활동 요약 정보
    """
    try:
        days = request.args.get('days', 7, type=int)
        
        # 활동 요약 조회
        summary = HistoryService.get_activity_summary(days=days)
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"활동 요약 조회 실패: {str(e)}")
        return jsonify({
            'error': '활동 요약을 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@history_bp.route('/stats', methods=['GET'])
@read_only_transaction
def get_history_stats():
    """
    히스토리 통계 조회
    
    Returns:
        JSON: 히스토리 통계 정보
    """
    try:
        # 전체 통계
        total_data_history = DataHistory.query.count()
        total_system_logs = SystemLog.query.count()
        
        # 오늘 통계
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_data_history = DataHistory.query.filter(
            DataHistory.created_at >= today_start,
            DataHistory.created_at <= today_end
        ).count()
        
        today_system_logs = SystemLog.query.filter(
            SystemLog.created_at >= today_start,
            SystemLog.created_at <= today_end
        ).count()
        
        # 작업별 통계
        action_stats = db.session.query(
            DataHistory.action,
            db.func.count(DataHistory.id).label('count')
        ).group_by(DataHistory.action).all()
        
        # 로그 레벨별 통계
        level_stats = db.session.query(
            SystemLog.level,
            db.func.count(SystemLog.id).label('count')
        ).group_by(SystemLog.level).all()
        
        stats = {
            'total_data_history': total_data_history,
            'total_system_logs': total_system_logs,
            'today_data_history': today_data_history,
            'today_system_logs': today_system_logs,
            'action_stats': {action: count for action, count in action_stats},
            'level_stats': {level: count for level, count in level_stats}
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"히스토리 통계 조회 실패: {str(e)}")
        return jsonify({
            'error': '히스토리 통계를 조회하는데 실패했습니다.',
            'message': str(e)
        }), 500


@history_bp.route('/clear', methods=['DELETE'])
@safe_transaction
def clear_old_history():
    """
    오래된 히스토리 삭제
    
    Query Parameters:
        days (int, optional): 삭제할 일수 (기본값: 30)
        type (str, optional): 삭제할 타입 (data, system, all)
        
    Returns:
        JSON: 삭제 결과
    """
    try:
        days = request.args.get('days', 30, type=int)
        clear_type = request.args.get('type', 'all')
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = 0
        
        if clear_type in ['data', 'all']:
            # 오래된 데이터 히스토리 삭제
            data_deleted = DataHistory.query.filter(
                DataHistory.created_at < cutoff_date
            ).delete()
            deleted_count += data_deleted
        
        if clear_type in ['system', 'all']:
            # 오래된 시스템 로그 삭제
            system_deleted = SystemLog.query.filter(
                SystemLog.created_at < cutoff_date
            ).delete()
            deleted_count += system_deleted
        
        db.session.commit()
        
        return jsonify({
            'message': f'{days}일 이전의 히스토리가 삭제되었습니다.',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"히스토리 삭제 실패: {str(e)}")
        return jsonify({
            'error': '히스토리 삭제에 실패했습니다.',
            'message': str(e)
        }), 500


# 에러 핸들러
@history_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': '요청한 히스토리 리소스를 찾을 수 없습니다.'
    }), 404


@history_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': '허용되지 않는 HTTP 메서드입니다.'
    }), 405


@history_bp.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'error': '서버 내부 오류가 발생했습니다.'
    }), 500 