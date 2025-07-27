# -*- coding: utf-8 -*-
"""
Stock 서비스 계층
주식 목록 관련 비즈니스 로직을 처리하는 서비스
"""
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from models.stock import StockList
from extensions import db
import re


class StockService:
    """주식 목록 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    # 데이터베이스 제약 조건 상수
    MAX_STOCK_CODE_LENGTH = 20
    MAX_STOCK_NAME_LENGTH = 100
    MAX_INIT_DATE_LENGTH = 10
    
    @staticmethod
    def validate_stock_code(stock_code: str) -> bool:
        """
        주식 코드 유효성 검증
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            bool: 유효성 여부
        """
        # 주식 코드는 숫자 6자리 형식이고 20자 이내
        if len(stock_code) > StockService.MAX_STOCK_CODE_LENGTH:
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
        if len(date_string) > StockService.MAX_INIT_DATE_LENGTH:
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
        return 0 < len(stock_name.strip()) <= StockService.MAX_STOCK_NAME_LENGTH
    
    @staticmethod
    def create_stock(
        stock_code: str, 
        stock_name: str, 
        init_date: Optional[str] = None,
        institution_accum_init: int = 0,
        foreigner_accum_init: int = 0
    ) -> Optional[StockList]:
        """
        새 주식 생성
        
        Args:
            stock_code (str): 주식 코드
            stock_name (str): 주식명
            init_date (Optional[str]): 상장일자
            institution_accum_init (int): 기관 누적 초기값
            foreigner_accum_init (int): 외국인 누적 초기값
            
        Returns:
            Optional[StockList]: 생성된 주식 객체 (실패 시 None)
            
        Raises:
            ValueError: 입력값이 잘못된 경우
        """
        try:
            # 입력값 검증
            if not stock_code or not stock_code.strip():
                raise ValueError("주식 코드는 필수입니다.")
            
            if not StockService.validate_stock_code(stock_code.strip()):
                raise ValueError(f"주식 코드는 6자리 숫자여야 하며 {StockService.MAX_STOCK_CODE_LENGTH}자 이내여야 합니다.")
            
            if not stock_name or not stock_name.strip():
                raise ValueError("주식명은 필수입니다.")
            
            if not StockService.validate_stock_name(stock_name):
                raise ValueError(f"주식명은 1자 이상 {StockService.MAX_STOCK_NAME_LENGTH}자 이내여야 합니다.")
            
            if init_date and not StockService.validate_date_format(init_date):
                raise ValueError(f"날짜는 YYYY-MM-DD 형식이어야 하며 {StockService.MAX_INIT_DATE_LENGTH}자 이내여야 합니다.")
            
            # 음수 값 검증
            if institution_accum_init < 0:
                raise ValueError("기관 누적 초기값은 0 이상이어야 합니다.")
            
            if foreigner_accum_init < 0:
                raise ValueError("외국인 누적 초기값은 0 이상이어야 합니다.")
            
            # 중복 체크
            existing_stock = StockList.query.filter_by(stock_code=stock_code.strip()).first()
            if existing_stock:
                raise ValueError(f"주식 코드 '{stock_code}'이 이미 존재합니다.")
            
            # 주식 생성
            stock = StockList.create_stock(
                stock_code=stock_code.strip(),
                stock_name=stock_name.strip(),
                init_date=init_date,
                institution_accum_init=institution_accum_init,
                foreigner_accum_init=foreigner_accum_init
            )
            
            db.session.add(stock)
            # 트랜잭션은 API 레벨에서 관리됨
            return stock
            
        except IntegrityError as e:
            raise ValueError("데이터베이스 제약 조건 위반") from e
        except Exception as e:
            raise Exception(f"주식 생성 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_all_stocks() -> List[StockList]:
        """
        모든 주식 조회
        
        Returns:
            List[StockList]: 주식 목록 (주식 코드 기준 오름차순)
        """
        try:
            return StockList.query.order_by(StockList.stock_code.asc()).all()
        except Exception as e:
            raise Exception(f"주식 목록 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_stock_by_id(stock_id: int) -> Optional[StockList]:
        """
        ID로 주식 조회
        
        Args:
            stock_id (int): 주식 ID
            
        Returns:
            Optional[StockList]: 주식 객체 (없으면 None)
        """
        try:
            if stock_id <= 0:
                return None
            return StockList.query.get(stock_id)
        except Exception as e:
            raise Exception(f"주식 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def get_stock_by_code(stock_code: str) -> Optional[StockList]:
        """
        주식 코드로 주식 조회
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            Optional[StockList]: 주식 객체 (없으면 None)
        """
        try:
            if not stock_code or not stock_code.strip():
                return None
            return StockList.query.filter_by(stock_code=stock_code.strip()).first()
        except Exception as e:
            raise Exception(f"주식 조회 중 오류 발생: {str(e)}") from e

    @staticmethod
    def update_stock(
        stock_id: int, 
        stock_name: str, 
        init_date: Optional[str] = None,
        institution_accum_init: Optional[int] = None,
        foreigner_accum_init: Optional[int] = None
    ) -> Optional[StockList]:
        """
        주식 정보 업데이트
        
        Args:
            stock_id (int): 주식 ID
            stock_name (str): 새로운 주식명
            init_date (Optional[str]): 새로운 초기화 날짜
            institution_accum_init (Optional[int]): 새로운 기관 누적 초기값
            foreigner_accum_init (Optional[int]): 새로운 외국인 누적 초기값
            
        Returns:
            Optional[StockList]: 업데이트된 주식 객체 (실패 시 None)
            
        Raises:
            ValueError: 입력값이 잘못된 경우
        """
        try:
            # 입력값 검증
            if not stock_name or not stock_name.strip():
                raise ValueError("주식명은 필수입니다.")
            
            if not StockService.validate_stock_name(stock_name):
                raise ValueError(f"주식명은 1자 이상 {StockService.MAX_STOCK_NAME_LENGTH}자 이내여야 합니다.")
            
            if init_date and not StockService.validate_date_format(init_date):
                raise ValueError(f"날짜는 YYYY-MM-DD 형식이어야 하며 {StockService.MAX_INIT_DATE_LENGTH}자 이내여야 합니다.")
            
            # 음수 값 검증
            if institution_accum_init is not None and institution_accum_init < 0:
                raise ValueError("기관 누적 초기값은 0 이상이어야 합니다.")
            
            if foreigner_accum_init is not None and foreigner_accum_init < 0:
                raise ValueError("외국인 누적 초기값은 0 이상이어야 합니다.")
            
            # 주식 조회
            stock = StockList.query.get(stock_id)
            if not stock:
                return None
            
            # 정보 업데이트
            stock.update_info(
                stock_name=stock_name.strip(),
                init_date=init_date,
                institution_accum_init=institution_accum_init,
                foreigner_accum_init=foreigner_accum_init
            )
            
            db.session.commit()
            return stock
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"주식 업데이트 중 오류 발생: {str(e)}") from e

    @staticmethod
    def delete_stock(stock_id: int) -> bool:
        """
        주식 삭제
        
        Args:
            stock_id (int): 주식 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            stock = StockList.query.get(stock_id)
            if not stock:
                return False
            
            db.session.delete(stock)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"주식 삭제 중 오류 발생: {str(e)}") from e

    @staticmethod
    def search_stocks_by_name(name: str) -> List[StockList]:
        """
        주식명으로 주식 검색
        
        Args:
            name (str): 검색할 주식명 (부분 일치)
            
        Returns:
            List[StockList]: 검색된 주식 목록
        """
        try:
            if not name or not name.strip():
                return []
            
            return StockList.query.filter(
                StockList.stock_name.like(f'%{name.strip()}%')
            ).order_by(StockList.stock_code.asc()).all()
            
        except Exception as e:
            raise Exception(f"주식 검색 중 오류 발생: {str(e)}") from e

    @staticmethod
    def search_stocks_by_code(code: str) -> List[StockList]:
        """
        주식 코드로 주식 검색
        
        Args:
            code (str): 검색할 주식 코드 (부분 일치)
            
        Returns:
            List[StockList]: 검색된 주식 목록
        """
        try:
            if not code or not code.strip():
                return []
            
            return StockList.query.filter(
                StockList.stock_code.like(f'%{code.strip()}%')
            ).order_by(StockList.stock_code.asc()).all()
            
        except Exception as e:
            raise Exception(f"주식 코드 검색 중 오류 발생: {str(e)}") from e

    @staticmethod
    def update_accum_values(
        stock_id: int, 
        institution_accum_init: int, 
        foreigner_accum_init: int
    ) -> Optional[StockList]:
        """
        누적 초기값 업데이트
        
        Args:
            stock_id (int): 주식 ID
            institution_accum_init (int): 기관 누적 초기값
            foreigner_accum_init (int): 외국인 누적 초기값
            
        Returns:
            Optional[StockList]: 업데이트된 주식 객체 (실패 시 None)
        """
        try:
            # 음수 값 검증
            if institution_accum_init < 0:
                raise ValueError("기관 누적 초기값은 0 이상이어야 합니다.")
            
            if foreigner_accum_init < 0:
                raise ValueError("외국인 누적 초기값은 0 이상이어야 합니다.")
            
            stock = StockList.query.get(stock_id)
            if not stock:
                return None
            
            stock.update_accum_values(institution_accum_init, foreigner_accum_init)
            db.session.commit()
            
            return stock
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"누적값 업데이트 중 오류 발생: {str(e)}") from e


# 하위 호환성을 위한 함수들
def create_stock(
    stock_code: str, 
    stock_name: str, 
    init_date: Optional[str] = None,
    institution_accum_init: int = 0,
    foreigner_accum_init: int = 0
) -> StockList:
    """주식 생성 (하위 호환성)"""
    result = StockService.create_stock(
        stock_code, stock_name, init_date, 
        institution_accum_init, foreigner_accum_init
    )
    if result is None:
        raise Exception("주식 생성 실패")
    return result


def get_all_stocks() -> List[StockList]:
    """모든 주식 조회 (하위 호환성)"""
    return StockService.get_all_stocks()


def get_stock_by_id(stock_id: int) -> Optional[StockList]:
    """ID로 주식 조회 (하위 호환성)"""
    return StockService.get_stock_by_id(stock_id)


def update_stock(
    stock_id: int, 
    stock_name: str, 
    init_date: Optional[str] = None,
    institution_accum_init: Optional[int] = None,
    foreigner_accum_init: Optional[int] = None
) -> Optional[StockList]:
    """주식 업데이트 (하위 호환성)"""
    return StockService.update_stock(
        stock_id, stock_name, init_date, 
        institution_accum_init, foreigner_accum_init
    )


def delete_stock(stock_id: int) -> Optional[StockList]:
    """주식 삭제 (하위 호환성)"""
    stock = StockService.get_stock_by_id(stock_id)
    if stock and StockService.delete_stock(stock_id):
        return stock
    return None 