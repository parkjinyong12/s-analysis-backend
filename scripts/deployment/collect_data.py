#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
주식 데이터 수집 실행 스크립트
네이버 금융에서 주식 거래 데이터를 크롤링하여 DB에 저장
"""
import sys
import os
import logging
from datetime import datetime

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from services.data_collector import DataCollectorService


def setup_logging():
    """로깅 설정"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'data_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def main():
    """메인 실행 함수"""
    print("="*60)
    print("주식 데이터 수집 시작")
    print("="*60)
    
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Flask 앱 컨텍스트 설정
        app = create_app()
        
        with app.app_context():
            # 데이터베이스 테이블 생성
            db.create_all()
            logger.info("데이터베이스 테이블 초기화 완료")
            
            # 데이터 수집 실행
            logger.info("데이터 수집 시작...")
            results = DataCollectorService.collect_all_stocks_data(years=3)
            
            # 결과 출력
            print("\n" + "="*60)
            print("데이터 수집 결과")
            print("="*60)
            print(f"전체 주식 수: {results.get('total_stocks', 0)}")
            print(f"성공: {results.get('success_stocks', 0)}")
            print(f"실패: {results.get('failed_stocks', 0)}")
            
            if results.get('failed_list'):
                print(f"\n실패 목록 ({len(results['failed_list'])}개):")
                for i, failed in enumerate(results['failed_list'], 1):
                    print(f"  {i:2d}. {failed}")
            
            if 'error' in results:
                print(f"\n오류: {results['error']}")
                logger.error(f"수집 중 오류 발생: {results['error']}")
            
            print("="*60)
            
            # 성공률 계산
            if results.get('total_stocks', 0) > 0:
                success_rate = (results.get('success_stocks', 0) / results['total_stocks']) * 100
                print(f"성공률: {success_rate:.1f}%")
                
                if success_rate >= 90:
                    print("✅ 데이터 수집이 성공적으로 완료되었습니다!")
                elif success_rate >= 70:
                    print("⚠️  일부 주식의 데이터 수집에 실패했습니다.")
                else:
                    print("❌ 많은 주식의 데이터 수집에 실패했습니다.")
            
            logger.info("데이터 수집 프로세스 완료")
            
    except Exception as e:
        logger.error(f"데이터 수집 중 치명적 오류: {e}")
        print(f"\n❌ 치명적 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 