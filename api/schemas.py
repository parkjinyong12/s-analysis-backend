# -*- coding: utf-8 -*-
"""
API 스키마 정의
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

class StockSchema:
    """주식 데이터 스키마"""
    
    @staticmethod
    def stock_response(stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """주식 응답 스키마"""
        return {
            'id': stock_data.get('id'),
            'code': stock_data.get('code'),
            'name': stock_data.get('name'),
            'market': stock_data.get('market'),
            'sector': stock_data.get('sector'),
            'created_at': stock_data.get('created_at'),
            'updated_at': stock_data.get('updated_at')
        }
    
    @staticmethod
    def stock_list_response(stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """주식 목록 응답 스키마"""
        return {
            'stocks': [StockSchema.stock_response(stock) for stock in stocks],
            'total_count': len(stocks)
        }

class TradingSchema:
    """거래 데이터 스키마"""
    
    @staticmethod
    def trading_response(trading_data: Dict[str, Any]) -> Dict[str, Any]:
        """거래 응답 스키마"""
        return {
            'id': trading_data.get('id'),
            'stock_code': trading_data.get('stock_code'),
            'date': trading_data.get('date'),
            'open_price': trading_data.get('open_price'),
            'high_price': trading_data.get('high_price'),
            'low_price': trading_data.get('low_price'),
            'close_price': trading_data.get('close_price'),
            'volume': trading_data.get('volume'),
            'created_at': trading_data.get('created_at')
        }
    
    @staticmethod
    def trading_list_response(tradings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """거래 목록 응답 스키마"""
        return {
            'tradings': [TradingSchema.trading_response(trading) for trading in tradings],
            'total_count': len(tradings)
        }

class UserSchema:
    """사용자 데이터 스키마"""
    
    @staticmethod
    def user_response(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 응답 스키마"""
        return {
            'id': user_data.get('id'),
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            'created_at': user_data.get('created_at'),
            'updated_at': user_data.get('updated_at')
        }

class ErrorSchema:
    """에러 응답 스키마"""
    
    @staticmethod
    def error_response(message: str, code: str = None) -> Dict[str, Any]:
        """에러 응답 스키마"""
        return {
            'error': {
                'message': message,
                'code': code,
                'timestamp': datetime.utcnow().isoformat()
            }
        } 