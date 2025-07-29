#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
증분 크롤링 실행 스크립트
누락된 최신 거래 데이터만 수집하는 독립 실행 스크립트

사용법:
    python scripts/incremental_crawler.py --help
    python scripts/incremental_crawler.py --stock-code 005930 --days-back 30
    python scripts/incremental_crawler.py --all --days-back 7 --force
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Flask 앱 및 서비스 import
from app import create_app
from services.data_collector import DataCollectorService
from services.trading_service import TradingService
from services.stock_service import StockService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/incremental_crawler_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)


def check_missing_dates(stock_code: str, days_back: int = 30):
    """
    특정 주식의 누락된 날짜 확인
    
    Args:
        stock_code (str): 주식 코드
        days_back (int): 확인할 기간 (일 단위)
    """
    try:
        # 주식 정보 확인
        stock = StockService.get_stock_by_code(stock_code)
        if not stock:
            logger.error(f"주식을 찾을 수 없습니다: {stock_code}")
            return False
        
        # 누락된 날짜와 최신 데이터 조회
        missing_dates = TradingService.get_missing_trade_dates(stock_code, days_back)
        latest_date = TradingService.get_latest_trade_date(stock_code)
        
        print(f"""
=== 누락 데이터 확인 결과 ===
주식: {stock.stock_code} - {stock.stock_name}
최신 데이터 날짜: {latest_date}
확인 기간: 최근 {days_back}일
누락된 날짜 수: {len(missing_dates)}개
누락된 날짜들: {missing_dates[:10]}{'...' if len(missing_dates) > 10 else ''}
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"누락 날짜 확인 중 오류: {e}")
        return False


def run_incremental_crawling(
    stock_code: str = None,
    days_back: int = 30,
    max_pages: int = 5,
    force_collect: bool = False,
    dry_run: bool = False
):
    """
    증분 크롤링 실행
    
    Args:
        stock_code (str, optional): 특정 주식 코드
        days_back (int): 확인할 기간
        max_pages (int): 최대 페이지 수
        force_collect (bool): 강제 수집 여부
        dry_run (bool): 실제 수집 없이 시뮬레이션만
    """
    try:
        logger.info(f"증분 크롤링 시작 - 주식: {stock_code or '전체'}, 기간: {days_back}일, 강제수집: {force_collect}")
        
        if dry_run:
            logger.info("DRY RUN 모드: 실제 크롤링 없이 시뮬레이션만 실행합니다")
            
            # 대상 주식 확인
            if stock_code:
                stock = StockService.get_stock_by_code(stock_code)
                if not stock:
                    logger.error(f"주식을 찾을 수 없습니다: {stock_code}")
                    return False
                target_stocks = [stock]
            else:
                target_stocks = StockService.get_all_stocks()
            
            total_missing = 0
            for stock in target_stocks[:10]:  # 처음 10개만 확인
                missing_dates = TradingService.get_missing_trade_dates(stock.stock_code, days_back)
                if missing_dates:
                    print(f"{stock.stock_code} {stock.stock_name}: {len(missing_dates)}개 누락")
                    total_missing += len(missing_dates)
            
            print(f"\n총 {len(target_stocks)}개 주식 중 처음 10개에서 {total_missing}개 날짜 누락")
            return True
        
        # 실제 증분 수집 실행
        results = DataCollectorService.collect_incremental_data(
            stock_code=stock_code,
            days_back=days_back,
            max_pages=max_pages,
            force_collect=force_collect
        )
        
        # 결과 출력
        if 'error' in results:
            logger.error(f"증분 크롤링 실패: {results['error']}")
            return False
        
        print(f"""
=== 증분 크롤링 완료 ===
대상 주식: {results['total_stocks']}개
수집 완료: {results['collected_stocks']}개
건너뛰기: {results['skipped_stocks']}개
실패: {results['failed_stocks']}개
총 누락 날짜: {results['total_missing_dates']}개
수집된 날짜: {results['collected_dates']}개
        """)
        
        # 실패한 주식들 상세 정보
        if results['failed_stocks'] > 0:
            print("\n=== 실패한 주식들 ===")
            for detail in results['details']:
                if detail['status'] == 'failed':
                    print(f"- {detail['stock_code']} {detail['stock_name']}: {detail.get('reason', '알 수 없는 오류')}")
        
        return True
        
    except Exception as e:
        logger.error(f"증분 크롤링 중 오류: {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='주식 거래 데이터 증분 크롤링 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 특정 주식의 누락 데이터 확인
  python scripts/incremental_crawler.py --check --stock-code 005930 --days-back 30
  
  # 특정 주식의 증분 크롤링
  python scripts/incremental_crawler.py --stock-code 005930 --days-back 7 --max-pages 3
  
  # 전체 주식의 증분 크롤링 (최근 7일)
  python scripts/incremental_crawler.py --all --days-back 7
  
  # 강제 수집 (누락 데이터가 없어도 크롤링)
  python scripts/incremental_crawler.py --all --days-back 7 --force
  
  # 시뮬레이션 모드 (실제 크롤링 없이 확인만)
  python scripts/incremental_crawler.py --all --days-back 30 --dry-run
        """
    )
    
    # 필수 인수 그룹 (stock-code 또는 all 중 하나 필수)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--stock-code', type=str, help='특정 주식 코드 (6자리 숫자)')
    group.add_argument('--all', action='store_true', help='모든 주식 대상')
    
    # 선택적 인수들
    parser.add_argument('--days-back', type=int, default=30, 
                       help='확인할 기간 (일 단위, 기본값: 30)')
    parser.add_argument('--max-pages', type=int, default=5,
                       help='최대 크롤링 페이지 수 (기본값: 5)')
    parser.add_argument('--force', action='store_true',
                       help='강제 수집 (누락 데이터가 없어도 크롤링)')
    parser.add_argument('--check', action='store_true',
                       help='누락 데이터 확인만 (크롤링 안함)')
    parser.add_argument('--dry-run', action='store_true',
                       help='시뮬레이션 모드 (실제 크롤링 없이 확인만)')
    
    args = parser.parse_args()
    
    # 입력값 검증
    if args.stock_code and not args.stock_code.isdigit() or len(args.stock_code) != 6:
        print("오류: 주식 코드는 6자리 숫자여야 합니다")
        return 1
    
    if args.days_back <= 0 or args.days_back > 365:
        print("오류: 확인 기간은 1~365일 사이여야 합니다")
        return 1
    
    if args.max_pages <= 0 or args.max_pages > 50:
        print("오류: 최대 페이지 수는 1~50 사이여야 합니다")
        return 1
    
    # Flask 앱 컨텍스트 생성
    app = create_app()
    
    with app.app_context():
        try:
            # 누락 데이터 확인만
            if args.check:
                if args.stock_code:
                    success = check_missing_dates(args.stock_code, args.days_back)
                else:
                    print("--check 옵션은 특정 주식 코드와 함께 사용해야 합니다")
                    return 1
            else:
                # 증분 크롤링 실행
                success = run_incremental_crawling(
                    stock_code=args.stock_code,
                    days_back=args.days_back,
                    max_pages=args.max_pages,
                    force_collect=args.force,
                    dry_run=args.dry_run
                )
            
            return 0 if success else 1
            
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단되었습니다")
            return 1
        except Exception as e:
            logger.error(f"실행 중 오류: {e}")
            return 1


if __name__ == '__main__':
    exit(main()) 