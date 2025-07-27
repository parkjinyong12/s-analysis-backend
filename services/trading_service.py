# -*- coding: utf-8 -*-
"""
Stock Investor Trading 서비스 계층
주식 투자자별 거래 데이터 관련 비즈니스 로직을 처리하는 서비스
"""
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from models.trading import StockInvestorTrading
from extensions import db
from services.history_service import HistoryService
import re


class TradingService:
    """주식 투자자별 거래 데이터 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    # 데이터베이스 제약 조건 상수
    MAX_STOCK_CODE_LENGTH = 20
    MAX_STOCK_NAME_LENGTH = 100
    MAX_TRADE_DATE_LENGTH = 10
    MAX_TREND_SIGNAL_LENGTH = 50
    
    @staticmethod
    def validate_stock_code(stock_code: str) -> bool:
        """
        주식 코드 유효성 검증
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            bool: 유효성 여부
        """
        if len(stock_code) > TradingService.MAX_STOCK_CODE_LENGTH:
            return False
        return bool(re.match(r'^\d{6}$', stock_code))
    
    @staticmethod
    def validate_date_format(date_string: str) -> bool:
        """
        날짜 형식 검증 (YYYY-MM-DD)
        
        Args:
            date_string (str): 날짜 문자열
            
        Returns:
            bool: 유효성 여부
        """
        if len(date_string) > TradingService.MAX_TRADE_DATE_LENGTH:
            return False
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_string))
    
    @staticmethod
    def validate_stock_name(stock_name: str) -> bool:
        """
        주식명 유효성 검증
        
        Args:
            stock_name (str): 주식명
            
        Returns:
            bool: 유효성 여부
        """
        return 0 < len(stock_name.strip()) <= TradingService.MAX_STOCK_NAME_LENGTH
    
    @staticmethod
    def validate_trend_signal(trend_signal: str) -> bool:
        """
        트렌드 신호 유효성 검증
        
        Args:
            trend_signal (str): 트렌드 신호
            
        Returns:
            bool: 유효성 여부
        """
        return len(trend_signal.strip()) <= TradingService.MAX_TREND_SIGNAL_LENGTH
    
    @staticmethod
    def create_trading_data(
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
    ) -> Optional[StockInvestorTrading]:
        """
        새 거래 데이터 생성
        
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
            Optional[StockInvestorTrading]: 생성된 거래 데이터 객체 (실패 시 None)
            
        Raises:
            ValueError: 입력값이 잘못된 경우
        """
        try:
            # 필수 입력값 검증
            if not stock_code or not stock_code.strip():
                raise ValueError("주식 코드는 필수입니다.")
            
            if not TradingService.validate_stock_code(stock_code.strip()):
                raise ValueError(f"주식 코드는 6자리 숫자여야 하며 {TradingService.MAX_STOCK_CODE_LENGTH}자 이내여야 합니다.")
            
            if not stock_name or not stock_name.strip():
                raise ValueError("주식명은 필수입니다.")
            
            if not TradingService.validate_stock_name(stock_name):
                raise ValueError(f"주식명은 1자 이상 {TradingService.MAX_STOCK_NAME_LENGTH}자 이내여야 합니다.")
            
            if not trade_date or not trade_date.strip():
                raise ValueError("거래 날짜는 필수입니다.")
            
            if not TradingService.validate_date_format(trade_date.strip()):
                raise ValueError(f"거래 날짜는 YYYY-MM-DD 형식이어야 하며 {TradingService.MAX_TRADE_DATE_LENGTH}자 이내여야 합니다.")
            
            # 선택 입력값 검증
            if close_price is not None and close_price < 0:
                raise ValueError("종가는 0 이상이어야 합니다.")
            
            if institution_trend_signal and not TradingService.validate_trend_signal(institution_trend_signal):
                raise ValueError(f"기관 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            if foreigner_trend_signal and not TradingService.validate_trend_signal(foreigner_trend_signal):
                raise ValueError(f"외국인 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            # 중복 체크 (같은 주식 코드, 같은 날짜)
            existing_trading = StockInvestorTrading.query.filter_by(
                stock_code=stock_code.strip(),
                trade_date=trade_date.strip()
            ).first()
            if existing_trading:
                raise ValueError(f"주식 코드 '{stock_code}', 날짜 '{trade_date}'의 거래 데이터가 이미 존재합니다.")
            
            # 거래 데이터 생성
            trading_data = StockInvestorTrading.create_trading_data(
                stock_code=stock_code.strip(),
                stock_name=stock_name.strip(),
                trade_date=trade_date.strip(),
                close_price=close_price,
                institution_net_buy=institution_net_buy,
                foreigner_net_buy=foreigner_net_buy,
                institution_accum=institution_accum,
                foreigner_accum=foreigner_accum,
                institution_trend_signal=institution_trend_signal.strip() if institution_trend_signal else None,
                institution_trend_score=institution_trend_score,
                foreigner_trend_signal=foreigner_trend_signal.strip() if foreigner_trend_signal else None,
                foreigner_trend_score=foreigner_trend_score
            )
            
            db.session.add(trading_data)
            db.session.commit()
            
            # 히스토리 로깅
            try:
                HistoryService.log_data_change(
                    table_name='stock_investor_trading',
                    record_id=trading_data.id,
                    action='CREATE',
                    description=f'새 거래 데이터 생성: {stock_code} ({stock_name}) - {trade_date}'
                )
            except Exception as e:
                # 히스토리 로깅 실패는 무시 (주요 기능에 영향 없도록)
                pass
            
            return trading_data
            
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("데이터베이스 제약 조건 위반") from e
        except Exception as e:
            db.session.rollback()
            raise Exception(f"거래 데이터 생성 중 오류 발생: {str(e)}") from e

    @staticmethod
    def create_trading_data_batch(
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
    ) -> Optional[StockInvestorTrading]:
        """
        새 거래 데이터 생성 (배치 처리용 - 즉시 커밋하지 않음)
        
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
            Optional[StockInvestorTrading]: 생성된 거래 데이터 객체 (실패 시 None)
            
        Raises:
            ValueError: 입력값이 잘못된 경우
        """
        try:
            # 필수 입력값 검증
            if not stock_code or not stock_code.strip():
                raise ValueError("주식 코드는 필수입니다.")
            
            if not TradingService.validate_stock_code(stock_code.strip()):
                raise ValueError(f"주식 코드는 6자리 숫자여야 하며 {TradingService.MAX_STOCK_CODE_LENGTH}자 이내여야 합니다.")
            
            if not stock_name or not stock_name.strip():
                raise ValueError("주식명은 필수입니다.")
            
            if not TradingService.validate_stock_name(stock_name):
                raise ValueError(f"주식명은 1자 이상 {TradingService.MAX_STOCK_NAME_LENGTH}자 이내여야 합니다.")
            
            if not trade_date or not trade_date.strip():
                raise ValueError("거래 날짜는 필수입니다.")
            
            if not TradingService.validate_date_format(trade_date.strip()):
                raise ValueError(f"거래 날짜는 YYYY-MM-DD 형식이어야 하며 {TradingService.MAX_TRADE_DATE_LENGTH}자 이내여야 합니다.")
            
            # 선택 입력값 검증
            if close_price is not None and close_price < 0:
                raise ValueError("종가는 0 이상이어야 합니다.")
            
            if institution_trend_signal and not TradingService.validate_trend_signal(institution_trend_signal):
                raise ValueError(f"기관 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            if foreigner_trend_signal and not TradingService.validate_trend_signal(foreigner_trend_signal):
                raise ValueError(f"외국인 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            # 거래 데이터 생성 (DB에 저장하지 않고 객체만 생성)
            trading_data = StockInvestorTrading.create_trading_data(
                stock_code=stock_code.strip(),
                stock_name=stock_name.strip(),
                trade_date=trade_date.strip(),
                close_price=close_price,
                institution_net_buy=institution_net_buy,
                foreigner_net_buy=foreigner_net_buy,
                institution_accum=institution_accum,
                foreigner_accum=foreigner_accum,
                institution_trend_signal=institution_trend_signal.strip() if institution_trend_signal else None,
                institution_trend_score=institution_trend_score,
                foreigner_trend_signal=foreigner_trend_signal.strip() if foreigner_trend_signal else None,
                foreigner_trend_score=foreigner_trend_score
            )
            
            # 여기서는 커밋하지 않음 - 호출자가 배치로 처리
            return trading_data
            
        except Exception as e:
            raise Exception(f"거래 데이터 생성 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_all_trading_data() -> List[StockInvestorTrading]:
        """
        모든 거래 데이터 조회
        
        Returns:
            List[StockInvestorTrading]: 거래 데이터 목록 (날짜 기준 내림차순)
        """
        try:
            return StockInvestorTrading.query.order_by(StockInvestorTrading.trade_date.desc()).all()
        except Exception as e:
            raise Exception(f"거래 데이터 목록 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_trading_data_by_id(trading_id: int) -> Optional[StockInvestorTrading]:
        """
        ID로 거래 데이터 조회
        
        Args:
            trading_id (int): 거래 데이터 ID
            
        Returns:
            Optional[StockInvestorTrading]: 거래 데이터 객체 (없으면 None)
        """
        try:
            if trading_id <= 0:
                return None
            return StockInvestorTrading.query.get(trading_id)
        except Exception as e:
            raise Exception(f"거래 데이터 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_trading_data_by_stock_code(stock_code: str) -> List[StockInvestorTrading]:
        """
        주식 코드로 거래 데이터 조회
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            List[StockInvestorTrading]: 거래 데이터 목록 (날짜 기준 내림차순)
        """
        try:
            if not stock_code or not stock_code.strip():
                return []
            return StockInvestorTrading.query.filter_by(
                stock_code=stock_code.strip()
            ).order_by(StockInvestorTrading.trade_date.desc()).all()
        except Exception as e:
            raise Exception(f"거래 데이터 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_trading_data_by_date_range(
        start_date: str, 
        end_date: str, 
        stock_code: Optional[str] = None
    ) -> List[StockInvestorTrading]:
        """
        날짜 범위로 거래 데이터 조회 (인덱스 최적화)
        
        Args:
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD)
            stock_code (Optional[str]): 주식 코드 (선택)
            
        Returns:
            List[StockInvestorTrading]: 거래 데이터 목록
        """
        try:
            # 날짜 형식 검증
            if not TradingService.validate_date_format(start_date):
                raise ValueError("시작 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            if not TradingService.validate_date_format(end_date):
                raise ValueError("종료 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            
            # 주식 코드가 있는 경우: 복합 인덱스 활용
            if stock_code and stock_code.strip():
                if not TradingService.validate_stock_code(stock_code.strip()):
                    raise ValueError("주식 코드 형식이 올바르지 않습니다. (6자리 숫자)")
                
                query = StockInvestorTrading.query.filter(
                    StockInvestorTrading.stock_code == stock_code.strip(),
                    StockInvestorTrading.trade_date >= start_date,
                    StockInvestorTrading.trade_date <= end_date
                ).order_by(StockInvestorTrading.trade_date.desc())
            else:
                # 날짜만으로 조회: 날짜 인덱스 활용
                query = StockInvestorTrading.query.filter(
                    StockInvestorTrading.trade_date >= start_date,
                    StockInvestorTrading.trade_date <= end_date
                ).order_by(StockInvestorTrading.trade_date.desc())
            
            return query.all()
        except Exception as e:
            raise Exception(f"날짜 범위 거래 데이터 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_trading_data_by_stock_date_range(
        stock_code: str,
        start_date: str, 
        end_date: str,
        include_price: bool = True,
        include_institution: bool = True,
        include_foreigner: bool = True
    ) -> List[StockInvestorTrading]:
        """
        특정 종목의 날짜 범위 거래 데이터 조회 (고성능)
        
        Args:
            stock_code (str): 주식 코드
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD)
            include_price (bool): 종가 포함 여부
            include_institution (bool): 기관 데이터 포함 여부
            include_foreigner (bool): 외국인 데이터 포함 여부
            
        Returns:
            List[StockInvestorTrading]: 거래 데이터 목록
        """
        try:
            # 입력값 검증
            if not TradingService.validate_stock_code(stock_code):
                raise ValueError("주식 코드 형식이 올바르지 않습니다. (6자리 숫자)")
            if not TradingService.validate_date_format(start_date):
                raise ValueError("시작 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            if not TradingService.validate_date_format(end_date):
                raise ValueError("종료 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            
            # 기본 쿼리 (복합 인덱스 활용)
            query = StockInvestorTrading.query.filter(
                StockInvestorTrading.stock_code == stock_code,
                StockInvestorTrading.trade_date >= start_date,
                StockInvestorTrading.trade_date <= end_date
            )
            
            # 필요한 컬럼만 선택하여 성능 최적화
            if include_price and include_institution and include_foreigner:
                # 모든 데이터 포함
                pass
            elif include_price and include_institution:
                # 종가 + 기관 데이터만
                query = query.with_entities(
                    StockInvestorTrading.id,
                    StockInvestorTrading.stock_code,
                    StockInvestorTrading.stock_name,
                    StockInvestorTrading.trade_date,
                    StockInvestorTrading.close_price,
                    StockInvestorTrading.institution_net_buy,
                    StockInvestorTrading.institution_accum,
                    StockInvestorTrading.institution_trend_signal,
                    StockInvestorTrading.institution_trend_score
                )
            elif include_price and include_foreigner:
                # 종가 + 외국인 데이터만
                query = query.with_entities(
                    StockInvestorTrading.id,
                    StockInvestorTrading.stock_code,
                    StockInvestorTrading.stock_name,
                    StockInvestorTrading.trade_date,
                    StockInvestorTrading.close_price,
                    StockInvestorTrading.foreigner_net_buy,
                    StockInvestorTrading.foreigner_accum,
                    StockInvestorTrading.foreigner_trend_signal,
                    StockInvestorTrading.foreigner_trend_score
                )
            elif include_price:
                # 종가만
                query = query.with_entities(
                    StockInvestorTrading.id,
                    StockInvestorTrading.stock_code,
                    StockInvestorTrading.stock_name,
                    StockInvestorTrading.trade_date,
                    StockInvestorTrading.close_price
                )
            
            return query.order_by(StockInvestorTrading.trade_date.desc()).all()
        except Exception as e:
            raise Exception(f"종목별 날짜 범위 거래 데이터 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_trading_data_by_date_range_optimized(
        start_date: str, 
        end_date: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[StockInvestorTrading]:
        """
        날짜 범위 거래 데이터 조회 (페이징 지원, 고성능)
        
        Args:
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD)
            limit (Optional[int]): 조회할 레코드 수 제한
            offset (Optional[int]): 건너뛸 레코드 수
            
        Returns:
            List[StockInvestorTrading]: 거래 데이터 목록
        """
        try:
            # 날짜 형식 검증
            if not TradingService.validate_date_format(start_date):
                raise ValueError("시작 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            if not TradingService.validate_date_format(end_date):
                raise ValueError("종료 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            
            # 기본 쿼리 (날짜 인덱스 활용)
            query = StockInvestorTrading.query.filter(
                StockInvestorTrading.trade_date >= start_date,
                StockInvestorTrading.trade_date <= end_date
            ).order_by(StockInvestorTrading.trade_date.desc())
            
            # 페이징 적용
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            raise Exception(f"날짜 범위 거래 데이터 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def update_trading_data(
        trading_id: int, 
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
    ) -> Optional[StockInvestorTrading]:
        """
        거래 데이터 정보 업데이트
        
        Args:
            trading_id (int): 거래 데이터 ID
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
            
        Returns:
            Optional[StockInvestorTrading]: 업데이트된 거래 데이터 객체 (실패 시 None)
            
        Raises:
            ValueError: 입력값이 잘못된 경우
        """
        try:
            # 입력값 검증
            if not stock_name or not stock_name.strip():
                raise ValueError("주식명은 필수입니다.")
            
            if not TradingService.validate_stock_name(stock_name):
                raise ValueError(f"주식명은 1자 이상 {TradingService.MAX_STOCK_NAME_LENGTH}자 이내여야 합니다.")
            
            if close_price is not None and close_price < 0:
                raise ValueError("종가는 0 이상이어야 합니다.")
            
            if institution_trend_signal and not TradingService.validate_trend_signal(institution_trend_signal):
                raise ValueError(f"기관 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            if foreigner_trend_signal and not TradingService.validate_trend_signal(foreigner_trend_signal):
                raise ValueError(f"외국인 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            # 거래 데이터 조회
            trading_data = StockInvestorTrading.query.get(trading_id)
            if not trading_data:
                return None
            
            # 정보 업데이트
            trading_data.update_info(
                stock_name=stock_name.strip(),
                close_price=close_price,
                institution_net_buy=institution_net_buy,
                foreigner_net_buy=foreigner_net_buy,
                institution_accum=institution_accum,
                foreigner_accum=foreigner_accum,
                institution_trend_signal=institution_trend_signal.strip() if institution_trend_signal else None,
                institution_trend_score=institution_trend_score,
                foreigner_trend_signal=foreigner_trend_signal.strip() if foreigner_trend_signal else None,
                foreigner_trend_score=foreigner_trend_score
            )
            
            db.session.commit()
            
            # 히스토리 로깅
            try:
                HistoryService.log_data_change(
                    table_name='stock_investor_trading',
                    record_id=trading_data.id,
                    action='UPDATE',
                    description=f'거래 데이터 업데이트: {trading_data.stock_code} ({trading_data.stock_name}) - {trading_data.trade_date}'
                )
            except Exception as e:
                # 히스토리 로깅 실패는 무시 (주요 기능에 영향 없도록)
                pass
            
            return trading_data
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"거래 데이터 업데이트 중 오류 발생: {str(e)}") from e

    @staticmethod
    def delete_trading_data(trading_id: int) -> bool:
        """
        거래 데이터 삭제
        
        Args:
            trading_id (int): 거래 데이터 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            trading_data = StockInvestorTrading.query.get(trading_id)
            if not trading_data:
                return False
            
            # 삭제 전 정보 저장 (히스토리용)
            stock_info = f"{trading_data.stock_code} ({trading_data.stock_name}) - {trading_data.trade_date}"
            
            db.session.delete(trading_data)
            db.session.commit()
            
            # 히스토리 로깅
            try:
                HistoryService.log_data_change(
                    table_name='stock_investor_trading',
                    record_id=trading_id,
                    action='DELETE',
                    description=f'거래 데이터 삭제: {stock_info}'
                )
            except Exception as e:
                # 히스토리 로깅 실패는 무시 (주요 기능에 영향 없도록)
                pass
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"거래 데이터 삭제 중 오류 발생: {str(e)}") from e

    @staticmethod
    def search_trading_data_by_name(name: str) -> List[StockInvestorTrading]:
        """
        주식명으로 거래 데이터 검색
        
        Args:
            name (str): 검색할 주식명 (부분 일치)
            
        Returns:
            List[StockInvestorTrading]: 검색된 거래 데이터 목록
        """
        try:
            if not name or not name.strip():
                return []
            
            return StockInvestorTrading.query.filter(
                StockInvestorTrading.stock_name.like(f'%{name.strip()}%')
            ).order_by(StockInvestorTrading.trade_date.desc()).all()
            
        except Exception as e:
            raise Exception(f"거래 데이터 검색 중 오류 발생: {str(e)}") from e

    @staticmethod
    def search_trading_data_by_query(query: str) -> List[StockInvestorTrading]:
        """
        주식 코드 또는 주식명으로 거래 데이터 검색
        
        Args:
            query (str): 검색할 주식 코드 또는 주식명 (부분 일치)
            
        Returns:
            List[StockInvestorTrading]: 검색된 거래 데이터 목록
        """
        try:
            if not query or not query.strip():
                return []
            
            search_term = query.strip()
            
            # 주식 코드 또는 주식명에서 검색 (OR 조건)
            return StockInvestorTrading.query.filter(
                or_(
                    StockInvestorTrading.stock_code.like(f'%{search_term}%'),
                    StockInvestorTrading.stock_name.like(f'%{search_term}%')
                )
            ).order_by(StockInvestorTrading.trade_date.desc()).all()
            
        except Exception as e:
            raise Exception(f"거래 데이터 검색 중 오류 발생: {str(e)}") from e

    @staticmethod
    def update_trend_analysis(
        trading_id: int, 
        institution_trend_signal: str, 
        institution_trend_score: float,
        foreigner_trend_signal: str, 
        foreigner_trend_score: float
    ) -> Optional[StockInvestorTrading]:
        """
        트렌드 분석 데이터 업데이트
        
        Args:
            trading_id (int): 거래 데이터 ID
            institution_trend_signal (str): 기관 트렌드 신호
            institution_trend_score (float): 기관 트렌드 점수
            foreigner_trend_signal (str): 외국인 트렌드 신호
            foreigner_trend_score (float): 외국인 트렌드 점수
            
        Returns:
            Optional[StockInvestorTrading]: 업데이트된 거래 데이터 객체 (실패 시 None)
        """
        try:
            # 입력값 검증
            if not TradingService.validate_trend_signal(institution_trend_signal):
                raise ValueError(f"기관 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            if not TradingService.validate_trend_signal(foreigner_trend_signal):
                raise ValueError(f"외국인 트렌드 신호는 {TradingService.MAX_TREND_SIGNAL_LENGTH}자 이내여야 합니다.")
            
            trading_data = StockInvestorTrading.query.get(trading_id)
            if not trading_data:
                return None
            
            trading_data.update_trend_analysis(
                institution_trend_signal=institution_trend_signal.strip(),
                institution_trend_score=institution_trend_score,
                foreigner_trend_signal=foreigner_trend_signal.strip(),
                foreigner_trend_score=foreigner_trend_score
            )
            db.session.commit()
            
            return trading_data
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"트렌드 분석 업데이트 중 오류 발생: {str(e)}") from e


# 하위 호환성을 위한 함수들
def create_trading_data(
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
) -> StockInvestorTrading:
    """거래 데이터 생성 (하위 호환성)"""
    result = TradingService.create_trading_data(
        stock_code, stock_name, trade_date, close_price,
        institution_net_buy, foreigner_net_buy, institution_accum, foreigner_accum,
        institution_trend_signal, institution_trend_score, 
        foreigner_trend_signal, foreigner_trend_score
    )
    if result is None:
        raise Exception("거래 데이터 생성 실패")
    return result


def get_all_trading_data() -> List[StockInvestorTrading]:
    """모든 거래 데이터 조회 (하위 호환성)"""
    return TradingService.get_all_trading_data()


def get_trading_data_by_id(trading_id: int) -> Optional[StockInvestorTrading]:
    """ID로 거래 데이터 조회 (하위 호환성)"""
    return TradingService.get_trading_data_by_id(trading_id) 