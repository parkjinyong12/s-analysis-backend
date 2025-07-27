# 주식 분석 백엔드 (Stock Analysis Backend)

주식 데이터 수집, 분석 및 거래 정보를 관리하는 Flask 기반 REST API 서버입니다.

## 🚀 주요 기능

- **주식 데이터 관리**: 주식 정보 CRUD 작업
- **거래 데이터 수집**: 실시간 주식 거래 데이터 수집
- **사용자 관리**: 사용자 계정 및 권한 관리
- **데이터 분석**: 주식 데이터 분석 및 인덱스 계산
- **REST API**: 표준화된 RESTful API 제공
- **실시간 처리**: 비동기 데이터 처리 및 배치 작업

## 🏗️ 프로젝트 구조

```
s_analysis-backend/
├── api/                       # API 관련 모듈
│   ├── schemas.py             # API 스키마 정의
│   └── __init__.py
├── core/                      # 핵심 기능
│   ├── exceptions.py          # 커스텀 예외
│   ├── logger.py              # 로깅 시스템
│   ├── decorators.py          # 유틸리티 데코레이터
│   └── __init__.py
├── models/                    # 데이터 모델
│   ├── stock.py               # 주식 모델
│   ├── trading.py             # 거래 모델
│   ├── user.py                # 사용자 모델
│   └── ...
├── services/                  # 비즈니스 로직
│   ├── stock_service.py       # 주식 서비스
│   ├── trading_service.py     # 거래 서비스
│   └── ...
├── views/                     # API 뷰
│   ├── stock.py               # 주식 API
│   ├── trading.py             # 거래 API
│   └── ...
├── tests/                     # 테스트
│   ├── conftest.py            # pytest 설정
│   ├── test_stock_api.py      # 주식 API 테스트
│   └── ...
├── scripts/                   # 유틸리티 스크립트
│   ├── setup_dev.py           # 개발 환경 설정
│   ├── database/              # 데이터베이스 스크립트
│   │   ├── fix_system_log.py  # 시스템 로그 수정
│   │   └── apply_trading_indexes.py # 거래 인덱스 적용
│   └── deployment/            # 배포 스크립트
│       └── collect_data.py    # 데이터 수집
├── migrations/                # 데이터베이스 마이그레이션
│   ├── init_tables.sql        # 초기 테이블 생성
│   ├── postgresql_schema.sql  # PostgreSQL 스키마
│   └── trading_indexes.sql    # 거래 인덱스
├── database/                  # 데이터베이스 관련
│   └── transaction.py         # 트랜잭션 유틸리티
├── docs/                      # 문서
│   ├── README.md              # 문서 목록
│   └── api/                   # API 문서
│       └── TRADING_INDEXES.md # 거래 인덱스 API
├── app.py                     # Flask 애플리케이션
├── config.py                  # 설정 관리
├── extensions.py              # Flask 확장
├── requirements.txt           # Python 의존성
├── docker-compose.yml         # Docker Compose 설정
├── Dockerfile                 # Docker 이미지 설정
├── nginx.conf                 # Nginx 설정
├── .github/workflows/         # CI/CD 파이프라인
└── README.md                  # 프로젝트 문서
```

## 🛠️ 기술 스택

- **Backend**: Flask 3.1.1, Python 3.11
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7
- **Container**: Docker, Docker Compose
- **Testing**: pytest, pytest-cov
- **Code Quality**: black, flake8, mypy
- **CI/CD**: GitHub Actions
- **Documentation**: OpenAPI/Swagger

## 📋 요구사항

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (선택사항)

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd s_analysis-backend
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 실제 서버 정보 입력
# DATABASE_URL=postgresql://username:password@host:port/database_name
# TEST_DATABASE_URL=postgresql://username:password@host:port/test_database_name
```

### 3. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

### 4. 의존성 설치

```bash
pip install -r requirements.txt
```

### 5. 개발 환경 설정

```bash
python scripts/setup_dev.py
```

### 6. 애플리케이션 실행

```bash
python app.py
```

서버가 `http://127.0.0.1:5001`에서 실행됩니다.

## 🐳 Docker 사용

### 전체 스택 실행

```bash
docker-compose up -d
```

### 개별 서비스 실행

```bash
# 데이터베이스만 실행
docker-compose up postgres redis

# 애플리케이션만 실행
docker-compose up app
```

## 📚 API 문서

### 주요 엔드포인트

- `GET /health` - 헬스체크
- `GET /api/v1/stocks/` - 주식 목록 조회
- `GET /api/v1/stocks/{code}` - 주식 상세 조회
- `POST /api/v1/stocks/` - 주식 생성
- `PUT /api/v1/stocks/{code}` - 주식 수정
- `DELETE /api/v1/stocks/{code}` - 주식 삭제

### 예시 요청

```bash
# 주식 목록 조회
curl http://localhost:5001/api/v1/stocks/

# 주식 생성
curl -X POST http://localhost:5001/api/v1/stocks/ \
  -H "Content-Type: application/json" \
  -d '{"code": "005930", "name": "삼성전자", "market": "KOSPI"}'
```

## 🧪 테스트

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=. --cov-report=html

# 특정 테스트 파일 실행
pytest tests/test_stock_api.py -v
```

### 코드 품질 검사

```bash
# 코드 포맷팅
black .

# 린팅
flake8 .

# 타입 검사
mypy .
```

## 🔧 개발

### 코드 스타일

- **포맷터**: Black
- **린터**: flake8
- **타입 검사**: mypy
- **문서화**: docstring (Google 스타일)

### 브랜치 전략

- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치
- `hotfix/*`: 긴급 수정 브랜치

### 커밋 메시지 규칙

```
type(scope): description

feat: 새로운 기능
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드 프로세스 또는 보조 도구 변경
```

## 📊 모니터링

### 헬스체크

- `GET /health` - 애플리케이션 상태 확인
- `GET /ready` - 준비 상태 확인

### 로깅

- 구조화된 로깅 (JSON 형식)
- 요청/응답 로깅
- 에러 추적

## 🔒 보안

- 환경 변수를 통한 설정 관리
- CORS 설정
- 입력 데이터 검증
- SQL 인젝션 방지 (SQLAlchemy ORM 사용)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**개발자**: Stock Analysis Team  
**버전**: 1.0.0  
**최종 업데이트**: 2025년 1월 