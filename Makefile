.PHONY: help install test lint format clean docker-build docker-run docker-stop setup-dev

# 기본값 설정
PYTHON := python3
PIP := pip3
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
MYPY := mypy

help: ## 도움말 표시
	@echo "사용 가능한 명령어:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 의존성 설치
	$(PIP) install -r requirements.txt

install-dev: ## 개발 의존성 설치
	$(PIP) install -r requirements.txt
	$(PIP) install -e .[dev]

test: ## 테스트 실행
	$(PYTEST) tests/ -v

test-cov: ## 테스트 실행 (커버리지 포함)
	$(PYTEST) tests/ -v --cov=. --cov-report=html --cov-report=term

test-unit: ## 단위 테스트만 실행
	$(PYTEST) tests/ -m "unit" -v

test-integration: ## 통합 테스트만 실행
	$(PYTEST) tests/ -m "integration" -v

test-api: ## API 테스트만 실행
	$(PYTEST) tests/ -m "api" -v

test-database: ## 데이터베이스 테스트만 실행
	$(PYTEST) tests/ -m "database" -v

test-performance: ## 성능 테스트만 실행
	$(PYTEST) tests/ -m "performance" -v

test-fast: ## 빠른 테스트 실행 (느린 테스트 제외)
	$(PYTEST) tests/ -m "not slow" -v

test-watch: ## 테스트 파일 변경 감지 및 자동 실행
	$(PYTEST) tests/ --watch -v

test-parallel: ## 병렬 테스트 실행
	$(PYTEST) tests/ -n auto -v

test-report: ## 테스트 리포트 생성
	mkdir -p reports
	$(PYTEST) tests/ --html=reports/test_report.html --self-contained-html --cov=. --cov-report=html:reports/coverage

test-clean: ## 테스트 캐시 및 리포트 정리
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf reports
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

lint: ## 코드 린팅
	$(FLAKE8) .

format: ## 코드 포맷팅
	$(BLACK) .

type-check: ## 타입 검사
	$(MYPY) .

check: format lint type-check ## 모든 코드 품질 검사

clean: ## 임시 파일 정리
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

docker-build: ## Docker 이미지 빌드
	docker build -t stock-analysis-backend .

docker-run: ## Docker 컨테이너 실행
	docker-compose up -d

docker-stop: ## Docker 컨테이너 중지
	docker-compose down

docker-logs: ## Docker 로그 확인
	docker-compose logs -f

setup-dev: ## 개발 환경 설정
	$(PYTHON) scripts/setup_dev.py

run: ## 애플리케이션 실행
	$(PYTHON) app.py

run-dev: ## 개발 모드로 애플리케이션 실행
	FLASK_ENV=development $(PYTHON) app.py

migrate: ## 데이터베이스 마이그레이션
	$(PYTHON) -c "from app import create_app; from extensions import db; app = create_app(); app.app_context().push(); db.create_all()"

seed: ## 초기 데이터 삽입
	$(PYTHON) scripts/collect_data.py

# 데이터베이스 관련 명령어
db-create: ## 데이터베이스 생성
	createdb stock_analysis

db-drop: ## 데이터베이스 삭제
	dropdb stock_analysis

db-reset: db-drop db-create migrate ## 데이터베이스 초기화

# 배포 관련 명령어
deploy-staging: ## 스테이징 환경 배포
	@echo "스테이징 환경에 배포 중..."

deploy-production: ## 프로덕션 환경 배포
	@echo "프로덕션 환경에 배포 중..."

# 모니터링 관련 명령어
health-check: ## 헬스체크
	curl -f http://localhost:5001/health || exit 1

logs: ## 애플리케이션 로그 확인
	tail -f logs/app.log

# 개발 도구
shell: ## Python 쉘 실행
	$(PYTHON) -c "from app import create_app; app = create_app(); import code; code.interact(local=locals())"

profile: ## 성능 프로파일링
	$(PYTHON) -m cProfile -o profile.stats app.py

analyze-profile: ## 프로파일 결과 분석
	$(PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)" 