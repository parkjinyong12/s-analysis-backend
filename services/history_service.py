# -*- coding: utf-8 -*-
"""
히스토리 관리 서비스
CRUD 작업의 히스토리를 관리합니다.
"""
from models.history import DataHistory, SystemLog
from extensions import db
from datetime import datetime
import json
from flask import request

class HistoryService:
    """히스토리 관리 서비스 클래스"""
    
    @staticmethod
    def log_data_change(table_name, record_id, action, field_name=None, 
                       old_value=None, new_value=None, description=None, user_id=None):
        """
        데이터 변경 히스토리 로그
        
        Args:
            table_name (str): 테이블명
            record_id (int): 레코드 ID
            action (str): 작업 유형 (CREATE, READ, UPDATE, DELETE)
            field_name (str, optional): 변경된 필드명
            old_value (str, optional): 이전 값
            new_value (str, optional): 새로운 값
            description (str, optional): 작업 설명
            user_id (int, optional): 사용자 ID
        """
        try:
            # IP 주소와 User Agent 가져오기
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None
            
            # 값들을 문자열로 변환
            if old_value is not None and not isinstance(old_value, str):
                old_value = json.dumps(old_value, ensure_ascii=False)
            if new_value is not None and not isinstance(new_value, str):
                new_value = json.dumps(new_value, ensure_ascii=False)
            
            # 히스토리 레코드 생성
            history = DataHistory(
                table_name=table_name,
                record_id=record_id,
                action=action,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                description=description,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(history)
            db.session.commit()
            
            return history
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def log_system_event(level, category, message, details=None, user_id=None):
        """
        시스템 이벤트 로그
        
        Args:
            level (str): 로그 레벨 (INFO, WARNING, ERROR)
            category (str): 카테고리 (API, DATABASE, COLLECTOR, etc.)
            message (str): 로그 메시지
            details (dict, optional): 상세 정보
            user_id (int, optional): 사용자 ID
        """
        try:
            # IP 주소 가져오기
            ip_address = request.remote_addr if request else None
            
            # 상세 정보를 JSON으로 변환
            details_json = json.dumps(details, ensure_ascii=False) if details else None
            
            # 시스템 로그 레코드 생성
            log = SystemLog(
                level=level,
                category=category,
                message=message,
                details=details_json,
                user_id=user_id,
                ip_address=ip_address
            )
            
            db.session.add(log)
            db.session.commit()
            
            return log
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_data_history(table_name=None, record_id=None, action=None, 
                        start_date=None, end_date=None, limit=100, offset=0):
        """
        데이터 히스토리 조회
        
        Args:
            table_name (str, optional): 테이블명 필터
            record_id (int, optional): 레코드 ID 필터
            action (str, optional): 작업 유형 필터
            start_date (datetime, optional): 시작 날짜
            end_date (datetime, optional): 종료 날짜
            limit (int): 조회 개수 제한
            offset (int): 오프셋
            
        Returns:
            list: 히스토리 목록
        """
        query = DataHistory.query
        
        if table_name:
            query = query.filter(DataHistory.table_name == table_name)
        if record_id:
            query = query.filter(DataHistory.record_id == record_id)
        if action:
            query = query.filter(DataHistory.action == action)
        if start_date:
            query = query.filter(DataHistory.created_at >= start_date)
        if end_date:
            query = query.filter(DataHistory.created_at <= end_date)
        
        return query.order_by(DataHistory.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_system_logs(level=None, category=None, start_date=None, end_date=None, 
                       limit=100, offset=0):
        """
        시스템 로그 조회
        
        Args:
            level (str, optional): 로그 레벨 필터
            category (str, optional): 카테고리 필터
            start_date (datetime, optional): 시작 날짜
            end_date (datetime, optional): 종료 날짜
            limit (int): 조회 개수 제한
            offset (int): 오프셋
            
        Returns:
            list: 시스템 로그 목록
        """
        query = SystemLog.query
        
        if level:
            query = query.filter(SystemLog.level == level)
        if category:
            query = query.filter(SystemLog.category == category)
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        return query.order_by(SystemLog.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_latest_activity(table_name=None, limit=10):
        """
        최근 활동 조회
        
        Args:
            table_name (str, optional): 테이블명 필터
            limit (int): 조회 개수 제한
            
        Returns:
            list: 최근 활동 목록
        """
        query = DataHistory.query
        
        if table_name:
            query = query.filter(DataHistory.table_name == table_name)
        
        return query.order_by(DataHistory.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_activity_summary(days=7):
        """
        활동 요약 조회
        
        Args:
            days (int): 조회할 일수
            
        Returns:
            dict: 활동 요약 정보
        """
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 전체 활동 수
        total_activities = DataHistory.query.filter(
            DataHistory.created_at >= start_date
        ).count()
        
        # 작업별 통계
        action_stats = db.session.query(
            DataHistory.action,
            db.func.count(DataHistory.id).label('count')
        ).filter(
            DataHistory.created_at >= start_date
        ).group_by(DataHistory.action).all()
        
        # 테이블별 통계
        table_stats = db.session.query(
            DataHistory.table_name,
            db.func.count(DataHistory.id).label('count')
        ).filter(
            DataHistory.created_at >= start_date
        ).group_by(DataHistory.table_name).all()
        
        return {
            'total_activities': total_activities,
            'action_stats': {action: count for action, count in action_stats},
            'table_stats': {table: count for table, count in table_stats},
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        } 