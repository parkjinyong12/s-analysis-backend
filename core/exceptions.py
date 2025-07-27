# -*- coding: utf-8 -*-
"""
커스텀 예외 클래스들
"""

class StockAnalysisError(Exception):
    """기본 예외 클래스"""
    pass

class DataCollectionError(StockAnalysisError):
    """데이터 수집 관련 예외"""
    pass

class DatabaseError(StockAnalysisError):
    """데이터베이스 관련 예외"""
    pass

class ValidationError(StockAnalysisError):
    """데이터 검증 관련 예외"""
    pass

class TradingError(StockAnalysisError):
    """거래 관련 예외"""
    pass

class UserError(StockAnalysisError):
    """사용자 관련 예외"""
    pass 