# -*- coding: utf-8 -*-
"""
데이터베이스 히스토리 모델
CRUD 작업의 히스토리를 저장합니다.
"""
from extensions import db
from datetime import datetime
import json

class DataHistory(db.Model):
    """데이터 변경 히스토리 모델"""
    __tablename__ = 'data_history'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False, comment='테이블명')
    record_id = db.Column(db.Integer, nullable=True, comment='레코드 ID')
    action = db.Column(db.String(20), nullable=False, comment='작업 유형 (CREATE, READ, UPDATE, DELETE)')
    field_name = db.Column(db.String(100), nullable=True, comment='변경된 필드명')
    old_value = db.Column(db.Text, nullable=True, comment='이전 값')
    new_value = db.Column(db.Text, nullable=True, comment='새로운 값')
    description = db.Column(db.Text, nullable=True, comment='작업 설명')
    user_id = db.Column(db.Integer, nullable=True, comment='사용자 ID')
    ip_address = db.Column(db.String(45), nullable=True, comment='IP 주소')
    user_agent = db.Column(db.Text, nullable=True, comment='사용자 에이전트')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='생성 시간')
    
    def __repr__(self):
        return f'<DataHistory {self.id}: {self.action} on {self.table_name}>'
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'action': self.action,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'description': self.description,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SystemLog(db.Model):
    """시스템 로그 모델"""
    __tablename__ = 'system_log'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False, comment='로그 레벨 (INFO, WARNING, ERROR)')
    category = db.Column(db.String(50), nullable=False, comment='카테고리 (API, DATABASE, COLLECTOR, etc.)')
    message = db.Column(db.Text, nullable=False, comment='로그 메시지')
    details = db.Column(db.Text, nullable=True, comment='상세 정보 (JSON)')
    user_id = db.Column(db.Integer, nullable=True, comment='사용자 ID')
    ip_address = db.Column(db.String(45), nullable=True, comment='IP 주소')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='생성 시간')
    
    def __repr__(self):
        return f'<SystemLog {self.id}: {self.level} - {self.message}>'
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'level': self.level,
            'category': self.category,
            'message': self.message,
            'details': self.details,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 