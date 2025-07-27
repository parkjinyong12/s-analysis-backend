# -*- coding: utf-8 -*-
"""
Stock 모델 정의
주식 목록 정보를 관리하는 SQLAlchemy 모델
"""
from extensions import db
from typing import Dict, Any, Optional


class StockList(db.Model):
    """
    주식 목록 모델
    
    Attributes:
        id (int): 주식 고유 ID (Primary Key, Auto Increment)
        stock_code (str): 주식 코드 (중복 불가)
        stock_name (str): 주식명
        init_date (str): 상장일자
        institution_accum_init (int): 기관 누적 초기값 (기본값: 0)
        foreigner_accum_init (int): 외국인 누적 초기값 (기본값: 0)
    """
    __tablename__ = 'stock_list'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='주식 고유 ID')
    
    # 주식 기본 정보
    stock_code = db.Column(
        db.String(20), 
        unique=True, 
        nullable=False, 
        comment='주식 코드'
    )
    stock_name = db.Column(
        db.String(100), 
        nullable=False, 
        comment='주식명'
    )
    init_date = db.Column(
        db.String(10), 
        comment='상장일자 (YYYY-MM-DD)'
    )
    
    # 누적 초기값
    institution_accum_init = db.Column(
        db.Integer, 
        nullable=False, 
        default=0, 
        comment='기관 누적 초기값'
    )
    foreigner_accum_init = db.Column(
        db.Integer, 
        nullable=False, 
        default=0, 
        comment='외국인 누적 초기값'
    )

    def __repr__(self) -> str:
        """객체 문자열 표현"""
        return f'<StockList {self.stock_code}: {self.stock_name}>'

    def to_dict(self) -> Dict[str, Any]:
        """
        StockList 객체를 딕셔너리로 변환 (API 응답용)
        
        Returns:
            Dict[str, Any]: 주식 정보 딕셔너리
        """
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'init_date': self.init_date,
            'institution_accum_init': self.institution_accum_init,
            'foreigner_accum_init': self.foreigner_accum_init
        }
    
    @classmethod
    def create_stock(
        cls, 
        stock_code: str, 
        stock_name: str, 
        init_date: Optional[str] = None,
        institution_accum_init: int = 0,
        foreigner_accum_init: int = 0
    ) -> 'StockList':
        """
        새 주식 생성 (팩토리 메서드)
        
        Args:
            stock_code (str): 주식 코드
            stock_name (str): 주식명
            init_date (Optional[str]): 초기화 날짜
            institution_accum_init (int): 기관 누적 초기값
            foreigner_accum_init (int): 외국인 누적 초기값
            
        Returns:
            StockList: 생성된 주식 객체
        """
        return cls(
            stock_code=stock_code,
            stock_name=stock_name,
            init_date=init_date,
            institution_accum_init=institution_accum_init,
            foreigner_accum_init=foreigner_accum_init
        )
    
    def update_info(
        self, 
        stock_name: str, 
        init_date: Optional[str] = None,
        institution_accum_init: Optional[int] = None,
        foreigner_accum_init: Optional[int] = None
    ) -> None:
        """
        주식 정보 업데이트
        
        Args:
            stock_name (str): 새로운 주식명
            init_date (Optional[str]): 새로운 상장일자
            institution_accum_init (Optional[int]): 새로운 기관 누적 초기값
            foreigner_accum_init (Optional[int]): 새로운 외국인 누적 초기값
        """
        self.stock_name = stock_name
        if init_date is not None:
            self.init_date = init_date
        if institution_accum_init is not None:
            self.institution_accum_init = institution_accum_init
        if foreigner_accum_init is not None:
            self.foreigner_accum_init = foreigner_accum_init
            
    def update_accum_values(
        self, 
        institution_accum_init: int, 
        foreigner_accum_init: int
    ) -> None:
        """
        누적 초기값 업데이트
        
        Args:
            institution_accum_init (int): 기관 누적 초기값
            foreigner_accum_init (int): 외국인 누적 초기값
        """
        self.institution_accum_init = institution_accum_init
        self.foreigner_accum_init = foreigner_accum_init 