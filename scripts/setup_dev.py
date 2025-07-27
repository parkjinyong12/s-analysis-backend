#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개발 환경 설정 스크립트
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """명령어 실행"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실패: {e}")
        print(f"에러 출력: {e.stderr}")
        return False

def create_env_file():
    """환경 변수 파일 생성"""
    env_content = """# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_analysis
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/test_stock_analysis

# 애플리케이션 설정
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
LOG_LEVEL=INFO

# Redis 설정
REDIS_URL=redis://localhost:6379/0

# CORS 설정
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ .env 파일 생성 완료")
    else:
        print("ℹ️ .env 파일이 이미 존재합니다")

def main():
    """메인 함수"""
    print("🚀 주식 분석 백엔드 개발 환경 설정을 시작합니다...")
    
    # 현재 디렉토리 확인
    if not Path('app.py').exists():
        print("❌ app.py 파일을 찾을 수 없습니다. 올바른 디렉토리에서 실행해주세요.")
        sys.exit(1)
    
    # Python 가상환경 확인
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️ 가상환경이 활성화되지 않았습니다. 가상환경을 활성화하고 다시 실행해주세요.")
        sys.exit(1)
    
    # 환경 변수 파일 생성
    create_env_file()
    
    # Python 패키지 설치
    if not run_command("pip install -r requirements.txt", "Python 패키지 설치"):
        sys.exit(1)
    
    # 코드 포맷팅
    run_command("black .", "코드 포맷팅")
    
    # 린팅
    run_command("flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics", "코드 린팅")
    
    # 테스트 실행
    run_command("python -m pytest tests/ -v", "테스트 실행")
    
    print("\n🎉 개발 환경 설정이 완료되었습니다!")
    print("\n다음 단계:")
    print("1. PostgreSQL 데이터베이스를 설정하세요")
    print("2. .env 파일의 설정을 확인하세요")
    print("3. 'python backend/app.py'로 애플리케이션을 실행하세요")
    print("4. 또는 'docker-compose up'으로 Docker 환경을 사용하세요")

if __name__ == '__main__':
    main() 