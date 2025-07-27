#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 자동화 실행 스크립트
"""
import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path


class TestRunner:
    """테스트 실행기"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_command(self, command, description=""):
        """명령어 실행"""
        print(f"\n{'='*60}")
        print(f"🚀 {description}")
        print(f"{'='*60}")
        print(f"실행 명령어: {command}")
        print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        start_time = time.time()
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"실행 시간: {end_time - start_time:.2f}초")
        print(f"종료 코드: {result.returncode}")
        
        if result.stdout:
            print("\n📤 표준 출력:")
            print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  표준 에러:")
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_unit_tests(self):
        """단위 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -m 'unit' -v --tb=short",
            "단위 테스트 실행"
        )
    
    def run_integration_tests(self):
        """통합 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -m 'integration' -v --tb=short",
            "통합 테스트 실행"
        )
    
    def run_api_tests(self):
        """API 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -m 'api' -v --tb=short",
            "API 테스트 실행"
        )
    
    def run_database_tests(self):
        """데이터베이스 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -m 'database' -v --tb=short",
            "데이터베이스 테스트 실행"
        )
    
    def run_performance_tests(self):
        """성능 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -m 'performance' -v --tb=short",
            "성능 테스트 실행"
        )
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -v --tb=short",
            "모든 테스트 실행"
        )
    
    def run_tests_with_coverage(self):
        """커버리지와 함께 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80",
            "커버리지 테스트 실행"
        )
    
    def run_fast_tests(self):
        """빠른 테스트 실행 (느린 테스트 제외)"""
        return self.run_command(
            "python -m pytest tests/ -m 'not slow' -v --tb=short",
            "빠른 테스트 실행"
        )
    
    def run_parallel_tests(self):
        """병렬 테스트 실행"""
        return self.run_command(
            "python -m pytest tests/ -n auto -v --tb=short",
            "병렬 테스트 실행"
        )
    
    def generate_test_report(self):
        """테스트 리포트 생성"""
        return self.run_command(
            "python -m pytest tests/ --html=reports/test_report.html --self-contained-html --cov=. --cov-report=html:reports/coverage",
            "테스트 리포트 생성"
        )
    
    def run_linting(self):
        """코드 린팅 실행"""
        return self.run_command(
            "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics",
            "코드 린팅 실행"
        )
    
    def run_format_check(self):
        """코드 포맷 검사"""
        return self.run_command(
            "black --check .",
            "코드 포맷 검사"
        )
    
    def run_type_check(self):
        """타입 검사"""
        return self.run_command(
            "mypy .",
            "타입 검사"
        )
    
    def run_code_quality_checks(self):
        """코드 품질 검사"""
        print(f"\n{'='*60}")
        print("🔍 코드 품질 검사 시작")
        print(f"{'='*60}")
        
        checks = [
            (self.run_linting, "린팅"),
            (self.run_format_check, "포맷 검사"),
            (self.run_type_check, "타입 검사")
        ]
        
        results = []
        for check_func, name in checks:
            success = check_func()
            results.append((name, success))
            if not success:
                print(f"❌ {name} 실패")
            else:
                print(f"✅ {name} 성공")
        
        return all(success for _, success in results)
    
    def run_full_test_suite(self):
        """전체 테스트 스위트 실행"""
        print(f"\n{'='*60}")
        print("🎯 전체 테스트 스위트 실행")
        print(f"{'='*60}")
        
        # 코드 품질 검사
        quality_ok = self.run_code_quality_checks()
        if not quality_ok:
            print("❌ 코드 품질 검사 실패")
            return False
        
        # 테스트 실행
        test_results = [
            (self.run_unit_tests, "단위 테스트"),
            (self.run_integration_tests, "통합 테스트"),
            (self.run_api_tests, "API 테스트"),
            (self.run_database_tests, "데이터베이스 테스트"),
            (self.run_performance_tests, "성능 테스트")
        ]
        
        all_passed = True
        for test_func, name in test_results:
            success = test_func()
            if not success:
                print(f"❌ {name} 실패")
                all_passed = False
            else:
                print(f"✅ {name} 성공")
        
        # 커버리지 리포트 생성
        if all_passed:
            self.generate_test_report()
        
        return all_passed
    
    def clean_test_artifacts(self):
        """테스트 아티팩트 정리"""
        return self.run_command(
            "find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && "
            "find . -type f -name '*.pyc' -delete && "
            "rm -rf .pytest_cache htmlcov reports .coverage coverage.xml",
            "테스트 아티팩트 정리"
        )


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="테스트 자동화 실행기")
    parser.add_argument(
        "--type", "-t",
        choices=["unit", "integration", "api", "database", "performance", "all", "fast", "parallel", "coverage", "full"],
        default="all",
        help="실행할 테스트 타입"
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="테스트 아티팩트 정리"
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="테스트 리포트 생성"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.clean:
        runner.clean_test_artifacts()
        return
    
    if args.report:
        runner.generate_test_report()
        return
    
    # 테스트 타입에 따른 실행
    test_functions = {
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "api": runner.run_api_tests,
        "database": runner.run_database_tests,
        "performance": runner.run_performance_tests,
        "all": runner.run_all_tests,
        "fast": runner.run_fast_tests,
        "parallel": runner.run_parallel_tests,
        "coverage": runner.run_tests_with_coverage,
        "full": runner.run_full_test_suite
    }
    
    test_func = test_functions.get(args.type)
    if test_func:
        success = test_func()
        if success:
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
            sys.exit(0)
        else:
            print("\n❌ 일부 테스트가 실패했습니다.")
            sys.exit(1)
    else:
        print(f"❌ 알 수 없는 테스트 타입: {args.type}")
        sys.exit(1)


if __name__ == "__main__":
    main() 