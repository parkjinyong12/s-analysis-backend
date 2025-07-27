# -*- coding: utf-8 -*-
"""
Stock Investor Trading 모델 정의
주식 투자자별 거래 데이터를 관리하는 SQLAlchemy 모델
"""
from extensions import db
from typing import Dict, Any, Optional


class StockInvestorTrading(db.Model):
    """
    주식 투자자별 거래 데이터 모델
    
    Attributes:
        id (int): 거래 고유 ID (Primary Key, Auto Increment)
        stock_code (str): 주식 코드
        stock_name (str): 주식명
        trade_date (str): 거래 날짜 (YYYY-MM-DD)
        close_price (int): 종가
        institution_net_buy (int): 기관 순매수
        foreigner_net_buy (int): 외국인 순매수
        institution_accum (int): 기관 누적 매수
        foreigner_accum (int): 외국인 누적 매수
        institution_trend_signal (str): 기관 트렌드 신호
        institution_trend_score (float): 기관 트렌드 점수
        foreigner_trend_signal (str): 외국인 트렌드 신호
        foreigner_trend_score (float): 외국인 트렌드 점수
    """
    __tablename__ = 'stock_investor_trading'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='거래 고유 ID')
    
    # 주식 기본 정보
    stock_code = db.Column(
        db.String(20), 
        nullable=False, 
        comment='주식 코드'
    )
    stock_name = db.Column(
        db.String(100), 
        nullable=False, 
        comment='주식명'
    )
    trade_date = db.Column(
        db.String(10), 
        nullable=False, 
        comment='거래 날짜 (YYYY-MM-DD)'
    )
    
    # 가격 정보
    close_price = db.Column(
        db.Integer, 
        comment='종가'
    )
    
    # 순매수 정보
    institution_net_buy = db.Column(
        db.Integer, 
        comment='기관 순매수'
    )
    foreigner_net_buy = db.Column(
        db.Integer, 
        comment='외국인 순매수'
    )
    
    # 누적 매수 정보
    institution_accum = db.Column(
        db.Integer, 
        comment='기관 누적 매수'
    )
    foreigner_accum = db.Column(
        db.Integer, 
        comment='외국인 누적 매수'
    )
    
    # 트렌드 분석 정보
    institution_trend_signal = db.Column(
        db.String(50), 
        comment='기관 트렌드 신호'
    )
    institution_trend_score = db.Column(
        db.Float, 
        comment='기관 트렌드 점수'
    )
    foreigner_trend_signal = db.Column(
        db.String(50), 
        comment='외국인 트렌드 신호'
    )
    foreigner_trend_score = db.Column(
        db.Float, 
        comment='외국인 트렌드 점수'
    )

    def __repr__(self) -> str:
        """객체 문자열 표현"""
        return f'<StockInvestorTrading {self.stock_code} {self.trade_date}>'

    def to_dict(self) -> Dict[str, Any]:
        """
        StockInvestorTrading 객체를 딕셔너리로 변환 (API 응답용)
        
        Returns:
            Dict[str, Any]: 거래 정보 딕셔너리
        """
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'trade_date': self.trade_date,
            'close_price': self.close_price,
            'institution_net_buy': self.institution_net_buy,
            'foreigner_net_buy': self.foreigner_net_buy,
            'institution_accum': self.institution_accum,
            'foreigner_accum': self.foreigner_accum,
            'institution_trend_signal': self.institution_trend_signal,
            'institution_trend_score': self.institution_trend_score,
            'foreigner_trend_signal': self.foreigner_trend_signal,
            'foreigner_trend_score': self.foreigner_trend_score
        }
    
    @classmethod
    def create_trading_data(
        cls, 
        stock_code: str, 
        stock_name: str, 
        trade_date: str,
        close_price: Optional[int] = None,
        institution_net_buy: Optional[int] = None,
        foreigner_net_buy: Optional[int] = None,
        institution_accum: Optional[int] = None,
        foreigner_accum: Optional[int] = None,
        institution_trend_signal: Optional[str] = None,
        institution_trend_score: Optional[float] = None,
        foreigner_trend_signal: Optional[str] = None,
        foreigner_trend_score: Optional[float] = None
    ) -> 'StockInvestorTrading':
        """
        새 거래 데이터 생성 (팩토리 메서드)
        
        Args:
            stock_code (str): 주식 코드
            stock_name (str): 주식명
            trade_date (str): 거래 날짜
            close_price (Optional[int]): 종가
            institution_net_buy (Optional[int]): 기관 순매수
            foreigner_net_buy (Optional[int]): 외국인 순매수
            institution_accum (Optional[int]): 기관 누적 매수
            foreigner_accum (Optional[int]): 외국인 누적 매수
            institution_trend_signal (Optional[str]): 기관 트렌드 신호
            institution_trend_score (Optional[float]): 기관 트렌드 점수
            foreigner_trend_signal (Optional[str]): 외국인 트렌드 신호
            foreigner_trend_score (Optional[float]): 외국인 트렌드 점수
            
        Returns:
            StockInvestorTrading: 생성된 거래 데이터 객체
        """
        return cls(
            stock_code=stock_code,
            stock_name=stock_name,
            trade_date=trade_date,
            close_price=close_price,
            institution_net_buy=institution_net_buy,
            foreigner_net_buy=foreigner_net_buy,
            institution_accum=institution_accum,
            foreigner_accum=foreigner_accum,
            institution_trend_signal=institution_trend_signal,
            institution_trend_score=institution_trend_score,
            foreigner_trend_signal=foreigner_trend_signal,
            foreigner_trend_score=foreigner_trend_score
        )
    
    def update_info(
        self, 
        stock_name: str, 
        close_price: Optional[int] = None,
        institution_net_buy: Optional[int] = None,
        foreigner_net_buy: Optional[int] = None,
        institution_accum: Optional[int] = None,
        foreigner_accum: Optional[int] = None,
        institution_trend_signal: Optional[str] = None,
        institution_trend_score: Optional[float] = None,
        foreigner_trend_signal: Optional[str] = None,
        foreigner_trend_score: Optional[float] = None
    ) -> None:
        """
        거래 데이터 정보 업데이트
        
        Args:
            stock_name (str): 새로운 주식명
            close_price (Optional[int]): 새로운 종가
            institution_net_buy (Optional[int]): 새로운 기관 순매수
            foreigner_net_buy (Optional[int]): 새로운 외국인 순매수
            institution_accum (Optional[int]): 새로운 기관 누적 매수
            foreigner_accum (Optional[int]): 새로운 외국인 누적 매수
            institution_trend_signal (Optional[str]): 새로운 기관 트렌드 신호
            institution_trend_score (Optional[float]): 새로운 기관 트렌드 점수
            foreigner_trend_signal (Optional[str]): 새로운 외국인 트렌드 신호
            foreigner_trend_score (Optional[float]): 새로운 외국인 트렌드 점수
        """
        self.stock_name = stock_name
        if close_price is not None:
            self.close_price = close_price
        if institution_net_buy is not None:
            self.institution_net_buy = institution_net_buy
        if foreigner_net_buy is not None:
            self.foreigner_net_buy = foreigner_net_buy
        if institution_accum is not None:
            self.institution_accum = institution_accum
        if foreigner_accum is not None:
            self.foreigner_accum = foreigner_accum
        if institution_trend_signal is not None:
            self.institution_trend_signal = institution_trend_signal
        if institution_trend_score is not None:
            self.institution_trend_score = institution_trend_score
        if foreigner_trend_signal is not None:
            self.foreigner_trend_signal = foreigner_trend_signal
        if foreigner_trend_score is not None:
            self.foreigner_trend_score = foreigner_trend_score
            
    def update_trend_analysis(
        self, 
        institution_trend_signal: str, 
        institution_trend_score: float,
        foreigner_trend_signal: str, 
        foreigner_trend_score: float
    ) -> None:
        """
        트렌드 분석 데이터 업데이트
        
        Args:
            institution_trend_signal (str): 기관 트렌드 신호
            institution_trend_score (float): 기관 트렌드 점수
            foreigner_trend_signal (str): 외국인 트렌드 신호
            foreigner_trend_score (float): 외국인 트렌드 점수
        """
        self.institution_trend_signal = institution_trend_signal
        self.institution_trend_score = institution_trend_score
        self.foreigner_trend_signal = foreigner_trend_signal
        self.foreigner_trend_score = foreigner_trend_score 