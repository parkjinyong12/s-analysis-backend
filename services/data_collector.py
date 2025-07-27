# -*- coding: utf-8 -*-
"""
주식 데이터 수집 서비스
네이버 금융에서 주식 거래 데이터를 크롤링하여 DB에 저장하는 서비스
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional
from extensions import db
from models.stock import StockList
from services.stock_service import StockService
from services.trading_service import TradingService
import re
import psutil
import gc
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# 로깅 설정
logger = logging.getLogger(__name__)
# 디버깅을 위한 로그 레벨 설정
logger.setLevel(logging.INFO)  # DEBUG에서 INFO로 변경
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)  # DEBUG에서 INFO로 변경
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class DataCollectorService:
    """
    주식 데이터 수집 서비스
    네이버 금융에서 주식 거래 데이터를 크롤링하여 데이터베이스에 저장
    """
    
    # 기본 설정
    BASE_URL = "https://finance.naver.com/item/frgn.naver"
    REQUEST_DELAY = 1.0  # 요청 간 대기 시간 (초)
    
    # 장시간 배치 처리를 위한 설정
    BATCH_SIZE = 50  # 한 번에 처리할 주식 수
    BATCH_DELAY = 30  # 배치 간 대기 시간 (초)
    MEMORY_CHECK_INTERVAL = 100  # 메모리 체크 간격 (주식 수)
    MAX_MEMORY_USAGE = 80  # 최대 메모리 사용률 (%)
    SESSION_REFRESH_INTERVAL = 500  # 세션 새로고침 간격 (주식 수)
    
    # 주식 목록은 DB의 stock_list 테이블에서 관리됩니다.
    
    @staticmethod
    def check_memory_usage() -> float:
        """
        현재 메모리 사용률을 확인합니다.
        
        Returns:
            float: 메모리 사용률 (%)
        """
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            logger.debug(f"현재 메모리 사용률: {memory_percent:.1f}%")
            return memory_percent
        except Exception as e:
            logger.warning(f"메모리 사용률 확인 실패: {e}")
            return 0.0
    
    @staticmethod
    def cleanup_memory():
        """
        메모리 정리를 수행합니다.
        """
        try:
            # 가비지 컬렉션 실행
            collected = gc.collect()
            logger.debug(f"가비지 컬렉션 완료: {collected}개 객체 정리")
            
            # 데이터베이스 세션 정리
            db.session.close()
            db.session.remove()
            
            # 메모리 사용률 재확인
            memory_percent = DataCollectorService.check_memory_usage()
            logger.info(f"메모리 정리 후 사용률: {memory_percent:.1f}%")
            
        except Exception as e:
            logger.warning(f"메모리 정리 실패: {e}")
    
    @staticmethod
    def test_url_access(stock_code: str) -> bool:
        """
        URL 접근 테스트
        """
        try:
            params = {'code': stock_code}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(DataCollectorService.BASE_URL, params=params, headers=headers, timeout=10)
            logger.info(f"URL 테스트 - 상태코드: {response.status_code}, URL: {response.url}")
            
            # HTML 길이 확인
            logger.info(f"HTML 길이: {len(response.content)} bytes")
            
            # HTML 샘플 출력
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"HTML 제목: {soup.title.string if soup.title else 'None'}")
            
            # 테이블 개수 확인
            tables = soup.find_all('table')
            logger.info(f"테이블 개수: {len(tables)}")
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"URL 접근 테스트 실패: {e}")
            return False
    
    @staticmethod
    def initialize_stock_list() -> bool:
        """
        주식 목록 초기화 (DB 기반)
        
        Returns:
            bool: 초기화 성공 여부 (DB에 주식이 있으면 True)
        """
        try:
            logger.info("주식 목록 초기화 시작 - DB 확인")
            
            # DB에서 주식 목록 조회
            stocks = StockService.get_all_stocks()
            
            if stocks:
                logger.info(f"DB에서 {len(stocks)}개의 주식 목록을 확인했습니다.")
                return True
            else:
                logger.warning("DB에 등록된 주식이 없습니다. 주식 목록 관리 화면에서 주식을 등록해 주세요.")
                return False
            
        except Exception as e:
            logger.error(f"주식 목록 초기화 실패: {e}")
            return False
    
    @staticmethod
    def fetch_stock_data(stock_code: str, years: int = 3, max_pages: int = 10) -> Optional[pd.DataFrame]:
        """
        특정 주식의 외국인/기관 거래 데이터를 크롤링 (페이지네이션 지원)
        
        Args:
            stock_code (str): 주식 코드
            years (int): 수집할 기간 (년 단위)
            max_pages (int): 최대 페이지 수
            
        Returns:
            Optional[pd.DataFrame]: 수집된 데이터 또는 None
        """
        logger.debug(f"데이터 수집 시작: {stock_code}")
        
        all_data_list = []
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        
        # 대용량 수집 시 경고
        if max_pages >= 30:
            logger.warning(f"대용량 수집 모드: {stock_code} - {max_pages}페이지, 예상 시간 {max_pages * 2}초")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for page in range(1, max_pages + 1):
            try:
                # 페이지별 URL 구성
                url = f"https://finance.naver.com/item/frgn.naver?code={stock_code}&page={page}"
                logger.debug(f"페이지 {page} 요청: {stock_code}")
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # HTML 파싱
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 모든 테이블 검사하여 데이터 테이블 찾기
                all_tables = soup.find_all('table')
                logger.debug(f"페이지 {page}: {len(all_tables)}개 테이블")
                
                data_table = None
                
                # 각 테이블을 검사하여 날짜 데이터가 있는 테이블 찾기
                for i, table in enumerate(all_tables):
                    rows = table.find_all('tr')
                    logger.debug(f"페이지 {page} 테이블 {i}: {len(rows)}행")
                    
                    # 충분한 행이 있는 테이블만 검사
                    if len(rows) < 5:
                        continue
                    
                    # 첫 번째 행에서 날짜 패턴 찾기
                    for row in rows[:10]:  # 처음 10개 행만 검사
                        cols = row.find_all(['td', 'th'])
                        if len(cols) > 0:
                            first_col_text = cols[0].get_text(strip=True)
                            # 날짜 패턴 확인 (YYYY.MM.DD 형식)
                            if re.match(r'\d{4}\.\d{2}\.\d{2}', first_col_text):
                                data_table = table
                                logger.debug(f"페이지 {page}: 데이터 테이블 발견")
                                break
                    
                    if data_table:
                        break
                
                if not data_table:
                    logger.debug(f"페이지 {page}: 데이터 테이블 없음, 가장 큰 테이블 사용")
                    # 가장 큰 테이블 사용
                    if all_tables:
                        data_table = max(all_tables, key=lambda t: len(t.find_all('tr')))
                    else:
                        logger.warning(f"페이지 {page}: 테이블을 찾을 수 없음")
                        continue
                
                # 데이터 추출
                rows = data_table.find_all('tr')
                logger.debug(f"페이지 {page}: {len(rows)}행 처리")
                
                page_data_list = []
                found_data_in_page = False
                
                # 모든 행을 검사하여 데이터 추출
                for i, row in enumerate(rows):
                    cols = row.find_all(['td', 'th'])
                    
                    if len(cols) == 0:
                        continue
                    
                    try:
                        # 첫 번째 컬럼에서 날짜 찾기
                        date_str = cols[0].get_text(strip=True)
                        
                        if not date_str or '날짜' in date_str or '구분' in date_str:
                            continue
                        
                        logger.debug(f"페이지 {page} 행 {i} 처리 중: '{date_str}' (컬럼 수: {len(cols)})")
                        
                        # 날짜 파싱 시도
                        trade_date = None
                        date_formats = ['%Y.%m.%d', '%Y-%m-%d', '%Y/%m/%d', '%m.%d', '%m/%d']
                        
                        for fmt in date_formats:
                            try:
                                if fmt in ['%m.%d', '%m/%d']:
                                    # 년도가 없는 경우 현재 년도 사용
                                    current_year = datetime.now().year
                                    if fmt == '%m.%d':
                                        trade_date = datetime.strptime(f"{current_year}.{date_str}", '%Y.%m.%d')
                                    else:
                                        trade_date = datetime.strptime(f"{current_year}/{date_str}", '%Y/%m/%d')
                                else:
                                    trade_date = datetime.strptime(date_str, fmt)
                                break
                            except:
                                continue
                        
                        if not trade_date:
                            logger.debug(f"페이지 {page}: 날짜 파싱 실패: {date_str}")
                            continue
                        
                        # 기간 체크
                        if trade_date < cutoff_date:
                            logger.info(f"페이지 {page}: 기간 초과 데이터 발견, 수집 중단: {trade_date.strftime('%Y-%m-%d')}")
                            # 기간을 초과한 데이터가 나오면 더 이상 페이지를 확인할 필요 없음
                            return pd.DataFrame(all_data_list) if all_data_list else None
                        
                        # 컬럼 수 체크 (최소 6개 이상이어야 함 - cols[5]까지 접근하므로)
                        if len(cols) < 6:
                            logger.debug(f"페이지 {page}: 컬럼 수 부족: {len(cols)}")
                            continue
                        
                        # 데이터 추출 (실제 네이버 금융 테이블 구조에 맞게 수정)
                        try:
                            # 종가 (보통 2번째 컬럼)
                            close_price_text = cols[1].get_text(strip=True).replace(',', '').replace('+', '').replace('--', '0')
                            close_price = int(close_price_text) if close_price_text and close_price_text.isdigit() else 0
                            
                            # 실제 네이버 금융 구조에 맞게 수정:
                            # cols[5]: 기관 순매수
                            # cols[6]: 외국인 순매수
                            # 누적 데이터는 크롤링에서 수집되지 않음 (나중에 계산으로 처리)
                            
                            # 기관 순매수 (6번째 컬럼)
                            institution_net_text = cols[5].get_text(strip=True).replace(',', '').replace('+', '').replace('--', '0')
                            institution_net = int(institution_net_text) if institution_net_text and institution_net_text.lstrip('-').isdigit() else 0

                            # 외국인 순매수 (7번째 컬럼)  
                            foreigner_net_text = cols[6].get_text(strip=True).replace(',', '').replace('+', '').replace('--', '0')
                            foreigner_net = int(foreigner_net_text) if foreigner_net_text and foreigner_net_text.lstrip('-').isdigit() else 0

                            # 누적 데이터는 크롤링에서 수집하지 않음 (기본값 0으로 설정)
                            # 나중에 별도 계산 로직으로 채워넣을 예정
                            institution_accum = 0
                            foreigner_accum = 0

                            data_row = {
                                'trade_date': trade_date.date(),
                                'close_price': close_price,
                                'institution_net_buy': institution_net,
                                'foreigner_net_buy': foreigner_net,
                                'institution_accum': institution_accum,  # 크롤링에서는 0으로 설정
                                'foreigner_accum': foreigner_accum        # 크롤링에서는 0으로 설정
                            }
                            
                            page_data_list.append(data_row)
                            found_data_in_page = True
                            logger.debug(f"페이지 {page}: 데이터 추출 성공 - {trade_date.strftime('%Y-%m-%d')}")
                            
                        except (ValueError, IndexError) as e:
                            logger.debug(f"페이지 {page}: 데이터 파싱 오류 - {e}")
                            continue
                            
                    except Exception as e:
                        logger.debug(f"페이지 {page} 행 {i} 처리 오류: {e}")
                        continue
                
                # 페이지에서 데이터를 찾았으면 전체 리스트에 추가
                if page_data_list:
                    all_data_list.extend(page_data_list)
                    logger.info(f"페이지 {page}: {len(page_data_list)}건의 데이터 추출 완료")
                else:
                    logger.info(f"페이지 {page}: 추출된 데이터가 없음")
                    # 연속으로 데이터가 없으면 더 이상 페이지를 확인하지 않음
                    if not found_data_in_page:
                        logger.info(f"페이지 {page}에서 데이터가 없으므로 수집 중단")
                        break
                
            except requests.RequestException as e:
                logger.error(f"페이지 {page} 요청 오류: {e}")
                continue
            except Exception as e:
                logger.error(f"페이지 {page} 처리 오류: {e}")
                continue
        
        if not all_data_list:
            logger.warning(f"전체 페이지에서 추출된 데이터가 없음: {stock_code}")
            return None
        
        # DataFrame 생성
        df = pd.DataFrame(all_data_list)
        
        # 중복 제거 (같은 날짜의 데이터가 있을 수 있음)
        df = df.drop_duplicates(subset=['trade_date'], keep='first')
        
        # 날짜순 정렬 (최신순)
        df = df.sort_values('trade_date', ascending=False)
        
        logger.info(f"데이터 수집 완료: {stock_code}, 총 {len(df)}건 (중복 제거 후)")
        
        return df
    
    @staticmethod
    def save_trading_data(stock_code: str, stock_name: str, df: pd.DataFrame) -> bool:
        """
        거래 데이터를 데이터베이스에 저장 (효율적인 배치 처리)
        
        Args:
            stock_code (str): 주식 코드
            stock_name (str): 주식 이름
            df (pd.DataFrame): 거래 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 1단계: 새로운 데이터만 미리 필터링
            new_data_list = []
            
            for _, row in df.iterrows():
                # trade_date를 문자열로 변환
                trade_date_str = row['trade_date'].strftime('%Y-%m-%d') if hasattr(row['trade_date'], 'strftime') else str(row['trade_date'])
                
                # 기존 데이터 확인
                from models.trading import StockInvestorTrading
                existing_data = StockInvestorTrading.query.filter_by(
                    stock_code=stock_code,
                    trade_date=trade_date_str
                ).first()

                if existing_data:
                    logger.debug(f"기존 데이터 건너뛰기: {stock_code} {trade_date_str}")
                    continue

                # 새로운 데이터 생성 (아직 DB에 저장하지 않음)
                try:
                    trading_data = TradingService.create_trading_data_batch(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        trade_date=trade_date_str,
                        close_price=row['close_price'],
                        institution_net_buy=row['institution_net_buy'],
                        foreigner_net_buy=row['foreigner_net_buy'],
                        institution_accum=row['institution_accum'],
                        foreigner_accum=row['foreigner_accum']
                    )
                    
                    if trading_data:
                        new_data_list.append(trading_data)
                        logger.debug(f"새 데이터 준비: {stock_code} {trade_date_str}")
                        
                except Exception as e:
                    logger.warning(f"데이터 생성 실패: {stock_code} {trade_date_str}, 오류: {e}")
                    continue

            # 2단계: 새로운 데이터가 없으면 종료
            if not new_data_list:
                logger.info(f"저장할 새 데이터가 없음: {stock_code}")
                return True  # 성공으로 처리 (이미 모든 데이터가 존재)

            # 3단계: 한 종목의 모든 데이터를 한 번에 저장
            max_retries = 3
            retry_delay = 1
            
            logger.debug(f"데이터 저장: {stock_code} ({len(new_data_list)}건)")
            
            # 재시도 로직
            for attempt in range(max_retries):
                try:
                    # 연결 상태 확인 및 재연결
                    try:
                        db.session.execute(text("SELECT 1"))
                    except Exception as conn_error:
                        logger.warning(f"데이터베이스 연결 확인 실패, 세션 재생성: {conn_error}")
                        db.session.close()
                        db.session.remove()
                    
                    # 모든 데이터를 세션에 추가
                    for trading_data in new_data_list:
                        db.session.add(trading_data)
                    
                    # 한 번에 커밋
                    db.session.commit()
                    
                    logger.debug(f"저장 완료: {stock_code} ({len(new_data_list)}건)")
                    break  # 성공하면 종료
                    
                except OperationalError as e:
                    db.session.rollback()
                    db.session.close()
                    db.session.remove()
                    
                    if "server closed the connection" in str(e).lower() or "connection" in str(e).lower():
                        logger.warning(f"데이터베이스 연결 끊김, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries}): {stock_code}")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(f"데이터베이스 오류: {stock_code}, 시도 횟수: {attempt + 1}, 오류: {e}")
                        return False
                        
                except Exception as e:
                    db.session.rollback()
                    
                    if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(f"데이터베이스 잠금, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries}): {stock_code}")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                        continue
                    else:
                        logger.error(f"한 종목 데이터 저장 실패: {stock_code}, 시도 횟수: {attempt + 1}, 오류: {e}")
                        return False
            
            total_saved = len(new_data_list)
            
            logger.debug(f"저장 완료: {stock_code} ({total_saved}건)")
            
            # 히스토리 로깅 (배치 처리 완료 후)
            if total_saved > 0:
                try:
                    from services.history_service import HistoryService
                    HistoryService.log_data_change(
                        table_name='stock_investor_trading',
                        record_id=None,  # 배치 처리이므로 특정 ID 없음
                        action='CREATE',
                        description=f'데이터 수집으로 {total_saved}건의 거래 데이터 생성: {stock_code} ({stock_name})'
                    )
                except Exception as e:
                    logger.warning(f"히스토리 로깅 실패: {e}")
            
            return total_saved > 0
            
        except Exception as e:
            logger.error(f"데이터 저장 중 예외 발생: {stock_code}, 오류: {e}")
            return False
    
    @staticmethod
    def get_existing_data_range(stock_code: str) -> Optional[Dict[str, any]]:
        """
        특정 주식의 기존 데이터 날짜 범위를 확인
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            Dict: 기존 데이터 정보 (최소/최대 날짜, 레코드 수) 또는 None
        """
        try:
            from models.trading import StockInvestorTrading
            
            # 기존 데이터 조회
            existing_data = db.session.query(StockInvestorTrading).filter(
                StockInvestorTrading.stock_code == stock_code
            ).order_by(StockInvestorTrading.trade_date).all()
            
            if not existing_data:
                return None
            
            min_date = min(data.trade_date for data in existing_data)
            max_date = max(data.trade_date for data in existing_data)
            record_count = len(existing_data)
            
            return {
                'min_date': min_date,
                'max_date': max_date,
                'record_count': record_count,
                'has_data': True
            }
            
        except Exception as e:
            logger.error(f"기존 데이터 범위 확인 실패: {stock_code}, {e}")
            return None
    
    @staticmethod
    def should_collect_data(stock_code: str, target_years: int = 3) -> Dict[str, any]:
        """
        데이터 수집이 필요한지 확인
        
        Args:
            stock_code (str): 주식 코드
            target_years (int): 목표 수집 기간 (년 단위)
            
        Returns:
            Dict: 수집 필요 여부와 상세 정보
        """
        try:
            # 기존 데이터 확인
            existing_info = DataCollectorService.get_existing_data_range(stock_code)
            
            if not existing_info:
                return {
                    'should_collect': True,
                    'reason': '기존 데이터 없음',
                    'existing_info': None,
                    'target_date': datetime.now() - timedelta(days=target_years * 365)
                }
            
            # 목표 날짜 계산 (현재 날짜에서 target_years년 전)
            target_date = datetime.now() - timedelta(days=target_years * 365)
            
            # 기존 데이터가 목표 날짜보다 최신인지 확인
            if existing_info['min_date'] <= target_date:
                return {
                    'should_collect': True,
                    'reason': f'기존 데이터가 {target_years}년 전까지 포함하지 않음',
                    'existing_info': existing_info,
                    'target_date': target_date,
                    'missing_period': f"{target_date.strftime('%Y-%m-%d')} ~ {existing_info['min_date'].strftime('%Y-%m-%d')}"
                }
            
            # 최신 데이터 확인 (최근 30일 이내 데이터가 있는지)
            recent_threshold = datetime.now() - timedelta(days=30)
            if existing_info['max_date'] < recent_threshold:
                return {
                    'should_collect': True,
                    'reason': f'최신 데이터 부족 (최신: {existing_info["max_date"].strftime("%Y-%m-%d")})',
                    'existing_info': existing_info,
                    'target_date': recent_threshold,
                    'missing_period': f"{existing_info['max_date'].strftime('%Y-%m-%d')} ~ 현재"
                }
            
            return {
                'should_collect': False,
                'reason': '충분한 데이터 보유',
                'existing_info': existing_info,
                'target_date': target_date
            }
            
        except Exception as e:
            logger.error(f"수집 필요 여부 확인 실패: {stock_code}, {e}")
            return {
                'should_collect': True,
                'reason': f'확인 실패: {str(e)}',
                'existing_info': None,
                'target_date': datetime.now() - timedelta(days=target_years * 365)
            }
    
    @staticmethod
    def collect_and_save_trading_data(stock_code: str, stock_name: str, years: int = 3, max_pages: int = 10) -> bool:
        """
        특정 주식의 거래 데이터를 수집하고 저장 (중복 수집 방지)
        
        Args:
            stock_code (str): 주식 코드
            stock_name (str): 주식 이름
            years (int): 수집할 기간 (년 단위)
            max_pages (int): 최대 페이지 수
            
        Returns:
            bool: 수집 및 저장 성공 여부
        """
        try:
            # 1. 수집 필요 여부 확인
            collection_check = DataCollectorService.should_collect_data(stock_code, years)
            
            if not collection_check['should_collect']:
                logger.info(f"수집 건너뛰기: {stock_code} - {collection_check['reason']}")
                return True  # 성공으로 처리 (수집 불필요)
            
            logger.info(f"데이터 수집 시작: {stock_code} - {collection_check['reason']}")
            
            # 2. 데이터 크롤링 (페이지네이션 지원)
            df = DataCollectorService.fetch_stock_data(stock_code, years, max_pages)
            if df is None or df.empty:
                logger.warning(f"수집할 데이터가 없음: {stock_code}")
                return False
            
            # 3. 데이터베이스 저장
            success = DataCollectorService.save_trading_data(stock_code, stock_name, df)
            
            # 트렌드 분석은 별도의 API에서 수행하므로 여기서는 제거
            logger.info(f"데이터 저장 완료: {stock_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"데이터 수집 및 저장 실패: {stock_code}, {e}")
            return False
    
    @staticmethod  
    def collect_all_stocks_data(years: int = 3, max_pages: int = 10) -> Dict[str, any]:
        """
        모든 주식의 거래 데이터를 수집 (배치 처리 방식)
        
        Args:
            years (int): 수집할 기간 (년 단위)
            max_pages (int): 최대 페이지 수
            
        Returns:
            Dict: 수집 결과 통계
        """
        logger.info(f"전체 주식 데이터 수집 시작 ({years}년, 최대 {max_pages}페이지)")
        
        results = {
            'total_stocks': 0,
            'success_stocks': 0,
            'failed_stocks': 0,
            'skipped_stocks': 0,
            'failed_list': [],
            'skipped_list': [],
            'batches_processed': 0,
            'memory_cleanups': 0
        }
        
        try:
            # 1. DB에서 주식 목록 조회
            stocks = StockService.get_all_stocks()
            results['total_stocks'] = len(stocks)
            
            # 주식이 없으면 경고
            if not stocks:
                logger.warning("DB에 등록된 주식이 없습니다. 데이터 수집을 위해 먼저 주식을 등록해 주세요.")
                results['error'] = "DB에 등록된 주식이 없습니다."
                return results
            
            # 2. 배치 단위로 처리
            total_batches = (len(stocks) + DataCollectorService.BATCH_SIZE - 1) // DataCollectorService.BATCH_SIZE
            logger.info(f"총 {total_batches}개 배치로 처리 예정 (배치 크기: {DataCollectorService.BATCH_SIZE})")
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * DataCollectorService.BATCH_SIZE
                end_idx = min(start_idx + DataCollectorService.BATCH_SIZE, len(stocks))
                batch_stocks = stocks[start_idx:end_idx]
                
                logger.info(f"배치 {batch_idx + 1}/{total_batches} 처리 시작 ({len(batch_stocks)}개 주식)")
                
                # 배치 내 각 주식 처리
                for stock_idx, stock in enumerate(batch_stocks):
                    current_stock_count = start_idx + stock_idx + 1
                    
                    try:
                        # 메모리 사용률 체크
                        if current_stock_count % DataCollectorService.MEMORY_CHECK_INTERVAL == 0:
                            memory_percent = DataCollectorService.check_memory_usage()
                            if memory_percent > DataCollectorService.MAX_MEMORY_USAGE:
                                logger.warning(f"메모리 사용률 높음 ({memory_percent:.1f}%), 정리 수행")
                                DataCollectorService.cleanup_memory()
                                results['memory_cleanups'] += 1
                        
                        # 세션 새로고침
                        if current_stock_count % DataCollectorService.SESSION_REFRESH_INTERVAL == 0:
                            logger.info(f"세션 새로고침 수행 (처리된 주식: {current_stock_count}개)")
                            db.session.close()
                            db.session.remove()
                            time.sleep(2)
                        
                        # 데이터베이스 연결 상태 확인
                        try:
                            db.session.execute(text("SELECT 1"))
                        except Exception as conn_error:
                            logger.warning(f"데이터베이스 연결 확인 실패, 세션 재생성: {conn_error}")
                            db.session.close()
                            db.session.remove()
                            time.sleep(2)
                        
                        # 수집 필요 여부 미리 확인
                        collection_check = DataCollectorService.should_collect_data(stock.stock_code, years)
                        
                        if not collection_check['should_collect']:
                            # 수집 불필요한 경우
                            results['skipped_stocks'] += 1
                            results['skipped_list'].append({
                                'stock_code': stock.stock_code,
                                'stock_name': stock.stock_name,
                                'reason': collection_check['reason'],
                                'existing_info': collection_check.get('existing_info')
                            })
                            logger.info(f"수집 건너뛰기: {stock.stock_code} {stock.stock_name} - {collection_check['reason']}")
                        else:
                            # 수집 필요한 경우
                            success = DataCollectorService.collect_and_save_trading_data(
                                stock.stock_code, stock.stock_name, years, max_pages
                            )
                            
                            if success:
                                results['success_stocks'] += 1
                            else:
                                results['failed_stocks'] += 1
                                results['failed_list'].append(f"{stock.stock_code} {stock.stock_name}")
                                logger.warning(f"수집 실패: {stock.stock_code} {stock.stock_name}")
                        
                        # 요청 간 대기
                        time.sleep(DataCollectorService.REQUEST_DELAY)
                        
                    except OperationalError as e:
                        results['failed_stocks'] += 1
                        results['failed_list'].append(f"{stock.stock_code} {stock.stock_name}: 연결 오류")
                        logger.error(f"데이터베이스 연결 오류: {stock.stock_code}, {e}")
                        
                        # 연결 재생성
                        try:
                            db.session.close()
                            db.session.remove()
                            time.sleep(3)
                        except:
                            pass
                        continue
                        
                    except Exception as e:
                        results['failed_stocks'] += 1
                        results['failed_list'].append(f"{stock.stock_code} {stock.stock_name}: {str(e)}")
                        logger.error(f"주식 데이터 수집 중 오류: {stock.stock_code}, {e}")
                        continue
                
                # 배치 완료 후 대기
                if batch_idx < total_batches - 1:  # 마지막 배치가 아니면
                    logger.info(f"배치 {batch_idx + 1} 완료, {DataCollectorService.BATCH_DELAY}초 대기")
                    time.sleep(DataCollectorService.BATCH_DELAY)
                
                results['batches_processed'] += 1
            
            logger.info(f"전체 데이터 수집 완료: 성공 {results['success_stocks']}개, 실패 {results['failed_stocks']}개, 건너뛴 {results['skipped_stocks']}개, 배치 {results['batches_processed']}개, 메모리 정리 {results['memory_cleanups']}회")
            return results
            
        except Exception as e:
            logger.error(f"전체 데이터 수집 중 오류: {e}")
            results['error'] = str(e)
            return results

    @staticmethod
    def calculate_accumulated_data(stock_code: str) -> bool:
        """
        특정 주식의 누적 매수량 데이터를 계산하여 업데이트
        (초기값 0, 기존 데이터 초기화 후 재계산)
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            bool: 계산 성공 여부
        """
        try:
            from models.trading import StockInvestorTrading
            
            logger.info(f"누적 데이터 계산 시작: {stock_code}")
            
            # 해당 주식의 모든 거래 데이터를 날짜순으로 조회 (오래된 것부터)
            trading_data_list = StockInvestorTrading.query.filter_by(
                stock_code=stock_code
            ).order_by(StockInvestorTrading.trade_date.asc()).all()
            
            if not trading_data_list:
                logger.info(f"거래 데이터가 없음: {stock_code}")
                return True
            
            # 1단계: 기존 누적값을 모두 0으로 초기화
            logger.info(f"기존 누적값 초기화: {stock_code}")
            for trading_data in trading_data_list:
                trading_data.institution_accum = 0
                trading_data.foreigner_accum = 0
            
            # 2단계: 초기값을 0으로 시작하여 누적 계산
            institution_accum = 0  # 초기값 0
            foreigner_accum = 0    # 초기값 0
            
            updated_count = 0
            
            # 각 거래 데이터의 누적값 계산 (과거부터 최신까지)
            for trading_data in trading_data_list:
                # 순매수량을 누적값에 더함
                institution_accum += trading_data.institution_net_buy or 0
                foreigner_accum += trading_data.foreigner_net_buy or 0
                
                # 누적값 업데이트 (그날의 누적값이 됨)
                trading_data.institution_accum = institution_accum
                trading_data.foreigner_accum = foreigner_accum
                
                updated_count += 1
                
                logger.debug(f"{trading_data.trade_date}: 기관순매수={trading_data.institution_net_buy}, 기관누적={institution_accum}, 외국인순매수={trading_data.foreigner_net_buy}, 외국인누적={foreigner_accum}")
            
            # 배치로 저장
            db.session.commit()
            
            logger.info(f"누적 데이터 계산 완료: {stock_code}, {updated_count}건 업데이트 (초기값 0부터 시작)")
            return True
            
        except Exception as e:
            logger.error(f"누적 데이터 계산 실패: {stock_code}, 오류: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def calculate_all_accumulated_data() -> Dict[str, any]:
        """
        모든 주식의 누적 매수량 데이터를 계산
        
        Returns:
            Dict: 계산 결과 통계
        """
        try:
            from services.stock_service import StockService
            
            logger.info("전체 주식 누적 데이터 계산 시작")
            
            results = {
                'total_stocks': 0,
                'success_stocks': 0,
                'failed_stocks': 0,
                'failed_list': []
            }
            
            # 모든 주식 조회
            stocks = StockService.get_all_stocks()
            results['total_stocks'] = len(stocks)
            
            if not stocks:
                logger.warning("DB에 등록된 주식이 없습니다.")
                results['error'] = "DB에 등록된 주식이 없습니다."
                return results
            
            # 각 주식별 누적 데이터 계산
            for stock in stocks:
                try:
                    success = DataCollectorService.calculate_accumulated_data(stock.stock_code)
                    
                    if success:
                        results['success_stocks'] += 1
                    else:
                        results['failed_stocks'] += 1
                        results['failed_list'].append(f"{stock.stock_code} {stock.stock_name}")
                        
                except Exception as e:
                    results['failed_stocks'] += 1
                    results['failed_list'].append(f"{stock.stock_code} {stock.stock_name}: {str(e)}")
                    logger.error(f"누적 데이터 계산 중 오류: {stock.stock_code}, {e}")
                    continue
            
            logger.info(f"전체 누적 데이터 계산 완료: 성공 {results['success_stocks']}개, 실패 {results['failed_stocks']}개")
            return results
            
        except Exception as e:
            logger.error(f"전체 누적 데이터 계산 중 오류: {e}")
            return {
                'total_stocks': 0,
                'success_stocks': 0,
                'failed_stocks': 0,
                'failed_list': [],
                'error': str(e)
            }
    
    @staticmethod
    def clear_trading_data_by_stock(stock_code: str) -> bool:
        """
        특정 주식의 거래 데이터를 모두 삭제
        
        Args:
            stock_code (str): 주식 코드
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            from models.trading import StockInvestorTrading
            
            logger.info(f"거래 데이터 초기화 시작: {stock_code}")
            
            # 해당 주식의 모든 거래 데이터 조회
            trading_data_count = StockInvestorTrading.query.filter_by(stock_code=stock_code).count()
            
            if trading_data_count == 0:
                logger.info(f"삭제할 거래 데이터가 없음: {stock_code}")
                return True
            
            # 해당 주식의 모든 거래 데이터 삭제
            deleted_count = StockInvestorTrading.query.filter_by(stock_code=stock_code).delete()
            db.session.commit()
            
            # 히스토리 로깅
            if deleted_count > 0:
                try:
                    from services.history_service import HistoryService
                    HistoryService.log_data_change(
                        table_name='stock_investor_trading',
                        record_id=None,  # 전체 삭제이므로 특정 ID 없음
                        action='DELETE',
                        description=f'종목별 데이터 삭제: {stock_code} ({deleted_count}건)'
                    )
                except Exception as e:
                    logger.warning(f"히스토리 로깅 실패: {e}")
            
            logger.info(f"거래 데이터 초기화 완료: {stock_code}, {deleted_count}건 삭제")
            return True
            
        except Exception as e:
            logger.error(f"거래 데이터 초기화 실패: {stock_code}, 오류: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def clear_all_trading_data() -> Dict[str, any]:
        """
        모든 거래 데이터를 삭제
        
        Returns:
            Dict: 삭제 결과 통계
        """
        try:
            from models.trading import StockInvestorTrading
            
            logger.info("전체 거래 데이터 초기화 시작")
            
            # 전체 거래 데이터 개수 확인
            total_count = StockInvestorTrading.query.count()
            
            if total_count == 0:
                logger.info("삭제할 거래 데이터가 없습니다.")
                return {
                    'deleted_count': 0,
                    'message': '삭제할 거래 데이터가 없습니다.'
                }
            
            # 모든 거래 데이터 삭제
            deleted_count = StockInvestorTrading.query.delete()
            db.session.commit()
            
            # 히스토리 로깅
            if deleted_count > 0:
                try:
                    from services.history_service import HistoryService
                    HistoryService.log_data_change(
                        table_name='stock_investor_trading',
                        record_id=None,  # 전체 삭제이므로 특정 ID 없음
                        action='DELETE',
                        description=f'전체 거래 데이터 삭제: {deleted_count}건'
                    )
                except Exception as e:
                    logger.warning(f"히스토리 로깅 실패: {e}")
            
            logger.info(f"전체 거래 데이터 초기화 완료: {deleted_count}건 삭제")
            
            return {
                'deleted_count': deleted_count,
                'message': f'총 {deleted_count}건의 거래 데이터가 삭제되었습니다.'
            }
            
        except Exception as e:
            logger.error(f"전체 거래 데이터 초기화 실패: {e}")
            db.session.rollback()
            return {
                'deleted_count': 0,
                'error': str(e)
            }
    
    @staticmethod
    def clear_trading_data_by_stocks(stock_codes: List[str]) -> Dict[str, any]:
        """
        여러 주식의 거래 데이터를 삭제
        
        Args:
            stock_codes (List[str]): 주식 코드 목록
            
        Returns:
            Dict: 삭제 결과 통계
        """
        try:
            logger.info(f"선택 종목 거래 데이터 초기화 시작: {len(stock_codes)}개 종목")
            
            results = {
                'total_stocks': len(stock_codes),
                'success_stocks': 0,
                'failed_stocks': 0,
                'failed_list': [],
                'total_deleted': 0
            }
            
            for stock_code in stock_codes:
                try:
                    success = DataCollectorService.clear_trading_data_by_stock(stock_code)
                    
                    if success:
                        results['success_stocks'] += 1
                    else:
                        results['failed_stocks'] += 1
                        results['failed_list'].append(stock_code)
                        
                except Exception as e:
                    results['failed_stocks'] += 1
                    results['failed_list'].append(f"{stock_code}: {str(e)}")
                    logger.error(f"종목별 거래 데이터 초기화 중 오류: {stock_code}, {e}")
                    continue
            
            logger.info(f"선택 종목 거래 데이터 초기화 완료: 성공 {results['success_stocks']}개, 실패 {results['failed_stocks']}개")
            return results
            
        except Exception as e:
            logger.error(f"선택 종목 거래 데이터 초기화 중 오류: {e}")
            return {
                'total_stocks': len(stock_codes),
                'success_stocks': 0,
                'failed_stocks': len(stock_codes),
                'failed_list': stock_codes,
                'total_deleted': 0,
                'error': str(e)
            }