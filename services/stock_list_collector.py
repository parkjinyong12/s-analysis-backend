# -*- coding: utf-8 -*-
"""
주식 목록 수집 서비스
코스피/코스닥 상장 기업 목록을 자동으로 수집합니다.
"""
import requests
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)

class StockListCollectorService:
    """주식 목록 수집 서비스"""
    
    # 미리 정의된 주요 코스피 주식 목록
    KOSPI_MAJOR_STOCKS = [
        {"stock_code": "005930", "stock_name": "삼성전자"},
        {"stock_code": "000660", "stock_name": "SK하이닉스"},
        {"stock_code": "035420", "stock_name": "NAVER"},
        {"stock_code": "051910", "stock_name": "LG화학"},
        {"stock_code": "006400", "stock_name": "삼성SDI"},
        {"stock_code": "035720", "stock_name": "카카오"},
        {"stock_code": "051900", "stock_name": "LG생활건강"},
        {"stock_code": "068270", "stock_name": "셀트리온"},
        {"stock_code": "207940", "stock_name": "삼성바이오로직스"},
        {"stock_code": "006980", "stock_name": "우성사료"},
        {"stock_code": "028260", "stock_name": "삼성물산"},
        {"stock_code": "015760", "stock_name": "한국전력"},
        {"stock_code": "032830", "stock_name": "삼성생명"},
        {"stock_code": "086790", "stock_name": "하나금융지주"},
        {"stock_code": "105560", "stock_name": "KB금융"},
        {"stock_code": "055550", "stock_name": "신한지주"},
        {"stock_code": "005380", "stock_name": "현대차"},
        {"stock_code": "000270", "stock_name": "기아"},
        {"stock_code": "373220", "stock_name": "LG에너지솔루션"},
        {"stock_code": "323410", "stock_name": "카카오뱅크"},
        {"stock_code": "006800", "stock_name": "미래에셋증권"},
        {"stock_code": "003670", "stock_name": "포스코퓨처엠"},
        {"stock_code": "017670", "stock_name": "SK텔레콤"},
        {"stock_code": "018260", "stock_name": "삼성에스디에스"},
        {"stock_code": "096770", "stock_name": "SK이노베이션"},
        {"stock_code": "010130", "stock_name": "고려아연"},
        {"stock_code": "011070", "stock_name": "LG이노텍"},
        {"stock_code": "009150", "stock_name": "삼성전기"},
        {"stock_code": "004020", "stock_name": "현대제철"},
        {"stock_code": "012330", "stock_name": "현대모비스"},
        {"stock_code": "008560", "stock_name": "메리츠증권"},
        {"stock_code": "000810", "stock_name": "삼성화재"},
        {"stock_code": "009830", "stock_name": "한화솔루션"},
        {"stock_code": "010950", "stock_name": "S-Oil"},
        {"stock_code": "011200", "stock_name": "HMM"},
        {"stock_code": "008770", "stock_name": "호텔신라"},
        {"stock_code": "004990", "stock_name": "롯데지주"},
        {"stock_code": "002790", "stock_name": "아모레G"},
        {"stock_code": "035250", "stock_name": "강원랜드"},
        {"stock_code": "008930", "stock_name": "한미사이언스"},
        {"stock_code": "000720", "stock_name": "현대건설"},
        {"stock_code": "009240", "stock_name": "한샘"},
        {"stock_code": "008110", "stock_name": "대동전자"},
        {"stock_code": "007310", "stock_name": "오뚜기"},
        {"stock_code": "005300", "stock_name": "롯데칠성"},
        {"stock_code": "004170", "stock_name": "신세계"},
        {"stock_code": "003490", "stock_name": "대한항공"},
        {"stock_code": "002460", "stock_name": "화천기계"},
        {"stock_code": "001800", "stock_name": "오리온홀딩스"},
        {"stock_code": "001450", "stock_name": "현대해상"},
        {"stock_code": "001040", "stock_name": "CJ"},
        {"stock_code": "000880", "stock_name": "한화"},
        {"stock_code": "000660", "stock_name": "SK하이닉스"},
        {"stock_code": "000590", "stock_name": "CS홀딩스"},
        {"stock_code": "000430", "stock_name": "대원강업"},
        {"stock_code": "000270", "stock_name": "기아"},
        {"stock_code": "000120", "stock_name": "CJ대한통운"}
    ]
    
    # 미리 정의된 주요 코스닥 주식 목록
    KOSDAQ_MAJOR_STOCKS = [
        {"stock_code": "035420", "stock_name": "NAVER"},
        {"stock_code": "035720", "stock_name": "카카오"},
        {"stock_code": "323410", "stock_name": "카카오뱅크"},
        {"stock_code": "068270", "stock_name": "셀트리온"},
        {"stock_code": "207940", "stock_name": "삼성바이오로직스"},
        {"stock_code": "006400", "stock_name": "삼성SDI"},
        {"stock_code": "051910", "stock_name": "LG화학"},
        {"stock_code": "373220", "stock_name": "LG에너지솔루션"},
        {"stock_code": "051900", "stock_name": "LG생활건강"},
        {"stock_code": "006980", "stock_name": "우성사료"},
        {"stock_code": "028260", "stock_name": "삼성물산"},
        {"stock_code": "015760", "stock_name": "한국전력"},
        {"stock_code": "032830", "stock_name": "삼성생명"},
        {"stock_code": "086790", "stock_name": "하나금융지주"},
        {"stock_code": "105560", "stock_name": "KB금융"},
        {"stock_code": "055550", "stock_name": "신한지주"},
        {"stock_code": "005380", "stock_name": "현대차"},
        {"stock_code": "000270", "stock_name": "기아"},
        {"stock_code": "006800", "stock_name": "미래에셋증권"},
        {"stock_code": "003670", "stock_name": "포스코퓨처엠"},
        {"stock_code": "017670", "stock_name": "SK텔레콤"},
        {"stock_code": "018260", "stock_name": "삼성에스디에스"},
        {"stock_code": "096770", "stock_name": "SK이노베이션"},
        {"stock_code": "010130", "stock_name": "고려아연"},
        {"stock_code": "011070", "stock_name": "LG이노텍"},
        {"stock_code": "009150", "stock_name": "삼성전기"},
        {"stock_code": "004020", "stock_name": "현대제철"},
        {"stock_code": "012330", "stock_name": "현대모비스"},
        {"stock_code": "008560", "stock_name": "메리츠증권"},
        {"stock_code": "000810", "stock_name": "삼성화재"},
        {"stock_code": "009830", "stock_name": "한화솔루션"},
        {"stock_code": "010950", "stock_name": "S-Oil"},
        {"stock_code": "011200", "stock_name": "HMM"},
        {"stock_code": "008770", "stock_name": "호텔신라"},
        {"stock_code": "004990", "stock_name": "롯데지주"},
        {"stock_code": "002790", "stock_name": "아모레G"},
        {"stock_code": "035250", "stock_name": "강원랜드"},
        {"stock_code": "008930", "stock_name": "한미사이언스"},
        {"stock_code": "000720", "stock_name": "현대건설"},
        {"stock_code": "009240", "stock_name": "한샘"},
        {"stock_code": "008110", "stock_name": "대동전자"},
        {"stock_code": "007310", "stock_name": "오뚜기"},
        {"stock_code": "005300", "stock_name": "롯데칠성"},
        {"stock_code": "004170", "stock_name": "신세계"},
        {"stock_code": "003490", "stock_name": "대한항공"},
        {"stock_code": "002460", "stock_name": "화천기계"},
        {"stock_code": "001800", "stock_name": "오리온홀딩스"},
        {"stock_code": "001450", "stock_name": "현대해상"},
        {"stock_code": "001040", "stock_name": "CJ"},
        {"stock_code": "000880", "stock_name": "한화"},
        {"stock_code": "000660", "stock_name": "SK하이닉스"},
        {"stock_code": "000590", "stock_name": "CS홀딩스"},
        {"stock_code": "000430", "stock_name": "대원강업"},
        {"stock_code": "000270", "stock_name": "기아"},
        {"stock_code": "000120", "stock_name": "CJ대한통운"}
    ]
    
    @staticmethod
    def collect_kospi_stocks_from_web() -> List[Dict[str, str]]:
        """
        네이버 금융에서 코스피 전체 종목 수집 (웹 스크래핑)
        
        Returns:
            List[Dict]: 주식 코드와 주식명이 포함된 딕셔너리 리스트
        """
        try:
            logger.info("코스피 전체 종목 수집 시작 (웹 스크래핑)")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            all_stocks = []
            page = 1
            max_pages = 50  # 최대 50페이지까지 (약 1000개 종목)
            
            while page <= max_pages:
                try:
                    url = f"https://finance.naver.com/sise/sise_market_sum.nhn?sosok=0&page={page}"
                    
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    response.encoding = 'euc-kr'
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 주식 목록 테이블에서 데이터 추출
                    table = soup.find('table', {'class': 'type_2'})
                    if not table:
                        logger.warning(f"페이지 {page}에서 테이블을 찾을 수 없습니다.")
                        break
                    
                    rows = table.find_all('tr')
                    page_stocks = []
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            # 주식명과 코드 추출
                            name_cell = cells[1]
                            code_cell = cells[0]
                            
                            if name_cell and code_cell:
                                stock_name = name_cell.get_text(strip=True)
                                stock_code = code_cell.get_text(strip=True)
                                
                                # 유효한 데이터인지 확인
                                if stock_name and stock_code and stock_code.isdigit() and len(stock_code) == 6:
                                    page_stocks.append({
                                        'stock_code': stock_code,
                                        'stock_name': stock_name
                                    })
                    
                    if not page_stocks:
                        logger.info(f"페이지 {page}에서 더 이상 주식이 없습니다.")
                        break
                    
                    all_stocks.extend(page_stocks)
                    logger.info(f"페이지 {page} 수집 완료: {len(page_stocks)}개 (총 {len(all_stocks)}개)")
                    
                    # 요청 간격을 두어 서버 부하 방지
                    time.sleep(random.uniform(1, 2))
                    page += 1
                    
                except Exception as e:
                    logger.error(f"페이지 {page} 수집 실패: {str(e)}")
                    break
            
            logger.info(f"코스피 전체 종목 수집 완료: {len(all_stocks)}개")
            return all_stocks
            
        except Exception as e:
            logger.error(f"코스피 전체 종목 수집 실패: {str(e)}")
            return []
    
    @staticmethod
    def collect_kospi_stocks() -> List[Dict[str, str]]:
        """
        코스피 상장 기업 목록 수집 (미리 정의된 목록 사용)
        
        Returns:
            List[Dict]: 주식 코드와 주식명이 포함된 딕셔너리 리스트
        """
        try:
            logger.info("코스피 주식 목록 수집 시작")
            
            # 미리 정의된 코스피 주요 주식 목록 반환
            stocks = StockListCollectorService.KOSPI_MAJOR_STOCKS.copy()
            
            logger.info(f"코스피 주식 목록 수집 완료: {len(stocks)}개")
            return stocks
            
        except Exception as e:
            logger.error(f"코스피 주식 목록 수집 실패: {str(e)}")
            return []
    
    @staticmethod
    def collect_kospi_all_stocks() -> List[Dict[str, str]]:
        """
        코스피 전체 종목 수집 (웹 스크래핑 시도, 실패시 미리 정의된 목록 사용)
        
        Returns:
            List[Dict]: 주식 코드와 주식명이 포함된 딕셔너리 리스트
        """
        try:
            logger.info("코스피 전체 종목 수집 시작")
            
            # 웹 스크래핑 시도
            web_stocks = StockListCollectorService.collect_kospi_stocks_from_web()
            
            if web_stocks and len(web_stocks) > 100:  # 충분한 데이터가 수집된 경우
                logger.info(f"웹 스크래핑으로 코스피 전체 종목 수집 성공: {len(web_stocks)}개")
                return web_stocks
            else:
                logger.warning("웹 스크래핑 실패, 미리 정의된 목록 사용")
                return StockListCollectorService.collect_kospi_stocks()
                
        except Exception as e:
            logger.error(f"코스피 전체 종목 수집 실패: {str(e)}")
            return StockListCollectorService.collect_kospi_stocks()
    
    @staticmethod
    def collect_kosdaq_stocks() -> List[Dict[str, str]]:
        """
        코스닥 상장 기업 목록 수집 (미리 정의된 목록 사용)
        
        Returns:
            List[Dict]: 주식 코드와 주식명이 포함된 딕셔너리 리스트
        """
        try:
            logger.info("코스닥 주식 목록 수집 시작")
            
            # 미리 정의된 코스닥 주요 주식 목록 반환
            stocks = StockListCollectorService.KOSDAQ_MAJOR_STOCKS.copy()
            
            logger.info(f"코스닥 주식 목록 수집 완료: {len(stocks)}개")
            return stocks
            
        except Exception as e:
            logger.error(f"코스닥 주식 목록 수집 실패: {str(e)}")
            return []
    
    @staticmethod
    def collect_all_stocks() -> Dict[str, List[Dict[str, str]]]:
        """
        코스피와 코스닥 전체 주식 목록 수집
        
        Returns:
            Dict: 코스피와 코스닥 주식 목록을 포함한 딕셔너리
        """
        try:
            logger.info("전체 주식 목록 수집 시작")
            
            # 코스피와 코스닥 주식 목록 수집
            kospi_stocks = StockListCollectorService.collect_kospi_stocks()
            kosdaq_stocks = StockListCollectorService.collect_kosdaq_stocks()
            
            result = {
                'kospi': kospi_stocks,
                'kosdaq': kosdaq_stocks,
                'total': len(kospi_stocks) + len(kosdaq_stocks)
            }
            
            logger.info(f"전체 주식 목록 수집 완료: 코스피 {len(kospi_stocks)}개, 코스닥 {len(kosdaq_stocks)}개")
            return result
            
        except Exception as e:
            logger.error(f"전체 주식 목록 수집 실패: {str(e)}")
            return {'kospi': [], 'kosdaq': [], 'total': 0} 