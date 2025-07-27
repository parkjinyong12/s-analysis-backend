# -*- coding: utf-8 -*-
"""
system_log 테이블 수정 스크립트
누락된 컬럼들을 추가하고 불필요한 컬럼들을 제거합니다.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from sqlalchemy import text

def fix_system_log_table():
    """system_log 테이블을 수정합니다."""
    app = create_app()
    
    with app.app_context():
        try:
            # 1. category 컬럼 추가
            db.session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'category'
                    ) THEN
                        ALTER TABLE system_log ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'SYSTEM';
                    END IF;
                END $$;
            """))
            
            # 2. details 컬럼 추가
            db.session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'details'
                    ) THEN
                        ALTER TABLE system_log ADD COLUMN details TEXT;
                    END IF;
                END $$;
            """))
            
            # 3. user_id 컬럼 추가
            db.session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'user_id'
                    ) THEN
                        ALTER TABLE system_log ADD COLUMN user_id INTEGER;
                    END IF;
                END $$;
            """))
            
            # 4. ip_address 컬럼 추가
            db.session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'ip_address'
                    ) THEN
                        ALTER TABLE system_log ADD COLUMN ip_address VARCHAR(45);
                    END IF;
                END $$;
            """))
            
            # 5. level 컬럼 길이 변경
            db.session.execute(text("ALTER TABLE system_log ALTER COLUMN level TYPE VARCHAR(20);"))
            
            # 6. 불필요한 컬럼들 제거
            db.session.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'module'
                    ) THEN
                        ALTER TABLE system_log DROP COLUMN module;
                    END IF;
                    
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'function_name'
                    ) THEN
                        ALTER TABLE system_log DROP COLUMN function_name;
                    END IF;
                    
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'system_log' AND column_name = 'line_number'
                    ) THEN
                        ALTER TABLE system_log DROP COLUMN line_number;
                    END IF;
                END $$;
            """))
            
            # 7. 인덱스 추가
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_system_log_category ON system_log(category);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_system_log_level ON system_log(level);"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_system_log_created_at ON system_log(created_at);"))
            
            # 8. 댓글 추가
            db.session.execute(text("COMMENT ON TABLE system_log IS '시스템 로그';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.level IS '로그 레벨 (INFO, WARNING, ERROR)';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.category IS '카테고리 (API, DATABASE, COLLECTOR, etc.)';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.message IS '로그 메시지';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.details IS '상세 정보 (JSON)';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.user_id IS '사용자 ID';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.ip_address IS 'IP 주소';"))
            db.session.execute(text("COMMENT ON COLUMN system_log.created_at IS '생성 시간';"))
            
            db.session.commit()
            print("✅ system_log 테이블 수정 완료")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ system_log 테이블 수정 실패: {e}")
            raise

if __name__ == "__main__":
    fix_system_log_table() 