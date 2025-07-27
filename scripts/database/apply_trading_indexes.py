#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래 데이터 조회 성능 최적화를 위한 인덱스 적용 스크립트
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def get_database_connection():
    """데이터베이스 연결을 생성합니다."""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return None

def apply_basic_indexes(conn):
    """기본 인덱스를 적용합니다."""
    print("=== 기본 인덱스 적용 ===")
    
    basic_indexes = [
        # 날짜 범위 조회 최적화
        "CREATE INDEX IF NOT EXISTS idx_trading_date_range ON stock_investor_trading(trade_date);",
        "CREATE INDEX IF NOT EXISTS idx_trading_date_close_price ON stock_investor_trading(trade_date, close_price);",
        
        # 종목별 날짜 범위 조회 최적화
        "CREATE INDEX IF NOT EXISTS idx_trading_stock_date_range ON stock_investor_trading(stock_code, trade_date);",
        "CREATE INDEX IF NOT EXISTS idx_trading_stock_date_close ON stock_investor_trading(stock_code, trade_date, close_price);",
        
        # 기관/외국인 순매수 조회 최적화
        "CREATE INDEX IF NOT EXISTS idx_trading_stock_date_institution_net ON stock_investor_trading(stock_code, trade_date, institution_net_buy);",
        "CREATE INDEX IF NOT EXISTS idx_trading_stock_date_foreigner_net ON stock_investor_trading(stock_code, trade_date, foreigner_net_buy);"
    ]
    
    cursor = conn.cursor()
    success_count = 0
    
    for index_sql in basic_indexes:
        try:
            cursor.execute(index_sql)
            print(f"✅ 인덱스 생성 완료: {index_sql.split('IF NOT EXISTS ')[1].split(' ON')[0]}")
            success_count += 1
        except Exception as e:
            print(f"❌ 인덱스 생성 실패: {e}")
    
    cursor.close()
    print(f"기본 인덱스 적용 완료: {success_count}/{len(basic_indexes)}")
    return success_count == len(basic_indexes)

def apply_advanced_indexes(conn):
    """고급 인덱스를 적용합니다."""
    print("\n=== 고급 인덱스 적용 ===")
    
    advanced_indexes = [
        # 종목명으로도 조회할 수 있도록 인덱스 추가
        "CREATE INDEX IF NOT EXISTS idx_trading_stock_name_date ON stock_investor_trading(stock_name, trade_date);",
        
        # 트렌드 신호 조회를 위한 인덱스
        "CREATE INDEX IF NOT EXISTS idx_trading_institution_trend ON stock_investor_trading(stock_code, trade_date, institution_trend_signal);",
        "CREATE INDEX IF NOT EXISTS idx_trading_foreigner_trend ON stock_investor_trading(stock_code, trade_date, foreigner_trend_signal);",
        
        # 트렌드 점수 조회를 위한 인덱스
        "CREATE INDEX IF NOT EXISTS idx_trading_institution_score ON stock_investor_trading(stock_code, trade_date, institution_trend_score);",
        "CREATE INDEX IF NOT EXISTS idx_trading_foreigner_score ON stock_investor_trading(stock_code, trade_date, foreigner_trend_score);"
    ]
    
    cursor = conn.cursor()
    success_count = 0
    
    for index_sql in advanced_indexes:
        try:
            cursor.execute(index_sql)
            print(f"✅ 고급 인덱스 생성 완료: {index_sql.split('IF NOT EXISTS ')[1].split(' ON')[0]}")
            success_count += 1
        except Exception as e:
            print(f"❌ 고급 인덱스 생성 실패: {e}")
    
    cursor.close()
    print(f"고급 인덱스 적용 완료: {success_count}/{len(advanced_indexes)}")
    return success_count == len(advanced_indexes)

def apply_partial_indexes(conn):
    """부분 인덱스를 적용합니다."""
    print("\n=== 부분 인덱스 적용 ===")
    
    partial_indexes = [
        # 기관 순매수가 있는 데이터만 인덱싱
        "CREATE INDEX IF NOT EXISTS idx_trading_institution_net_not_null ON stock_investor_trading(stock_code, trade_date) WHERE institution_net_buy IS NOT NULL;",
        
        # 외국인 순매수가 있는 데이터만 인덱싱
        "CREATE INDEX IF NOT EXISTS idx_trading_foreigner_net_not_null ON stock_investor_trading(stock_code, trade_date) WHERE foreigner_net_buy IS NOT NULL;",
        
        # 종가가 있는 데이터만 인덱싱
        "CREATE INDEX IF NOT EXISTS idx_trading_close_price_not_null ON stock_investor_trading(stock_code, trade_date) WHERE close_price IS NOT NULL;"
    ]
    
    cursor = conn.cursor()
    success_count = 0
    
    for index_sql in partial_indexes:
        try:
            cursor.execute(index_sql)
            print(f"✅ 부분 인덱스 생성 완료: {index_sql.split('IF NOT EXISTS ')[1].split(' ON')[0]}")
            success_count += 1
        except Exception as e:
            print(f"❌ 부분 인덱스 생성 실패: {e}")
    
    cursor.close()
    print(f"부분 인덱스 적용 완료: {success_count}/{len(partial_indexes)}")
    return success_count == len(partial_indexes)

def check_existing_indexes(conn):
    """기존 인덱스를 확인합니다."""
    print("=== 기존 인덱스 확인 ===")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'stock_investor_trading'
        ORDER BY indexname;
    """)
    
    indexes = cursor.fetchall()
    cursor.close()
    
    if indexes:
        print(f"발견된 인덱스 수: {len(indexes)}")
        for index_name, index_def in indexes:
            print(f"  - {index_name}")
    else:
        print("발견된 인덱스가 없습니다.")
    
    return len(indexes)

def analyze_table_performance(conn):
    """테이블 성능을 분석합니다."""
    print("\n=== 테이블 성능 분석 ===")
    
    cursor = conn.cursor()
    
    # 테이블 크기 확인
    cursor.execute("""
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE tablename = 'stock_investor_trading'
        ORDER BY attname;
    """)
    
    stats = cursor.fetchall()
    cursor.close()
    
    if stats:
        print("컬럼 통계 정보:")
        for schema, table, column, distinct, correlation in stats:
            print(f"  - {column}: distinct={distinct}, correlation={correlation}")
    else:
        print("통계 정보를 찾을 수 없습니다.")

def main():
    """메인 함수"""
    print("=== 거래 데이터 인덱스 최적화 스크립트 ===")
    
    # 데이터베이스 연결
    conn = get_database_connection()
    if not conn:
        print("데이터베이스 연결에 실패했습니다.")
        sys.exit(1)
    
    try:
        # 기존 인덱스 확인
        existing_count = check_existing_indexes(conn)
        
        # 기본 인덱스 적용
        basic_success = apply_basic_indexes(conn)
        
        # 고급 인덱스 적용 (선택적)
        if len(sys.argv) > 1 and sys.argv[1] == '--advanced':
            advanced_success = apply_advanced_indexes(conn)
            partial_success = apply_partial_indexes(conn)
        else:
            print("\n고급 인덱스는 --advanced 옵션으로 적용할 수 있습니다.")
            advanced_success = True
            partial_success = True
        
        # 최종 인덱스 확인
        final_count = check_existing_indexes(conn)
        
        # 성능 분석
        analyze_table_performance(conn)
        
        # 결과 요약
        print(f"\n=== 인덱스 적용 결과 ===")
        print(f"기존 인덱스 수: {existing_count}")
        print(f"새로 추가된 인덱스 수: {final_count - existing_count}")
        print(f"총 인덱스 수: {final_count}")
        print(f"기본 인덱스 적용: {'성공' if basic_success else '실패'}")
        
        if len(sys.argv) > 1 and sys.argv[1] == '--advanced':
            print(f"고급 인덱스 적용: {'성공' if advanced_success else '실패'}")
            print(f"부분 인덱스 적용: {'성공' if partial_success else '실패'}")
        
        print("\n🎉 인덱스 최적화가 완료되었습니다!")
        
    except Exception as e:
        print(f"인덱스 적용 중 오류 발생: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main() 