# 주식 분석 백엔드 문서

## 📚 문서 목록

### API 문서
- [거래 인덱스 API](./api/TRADING_INDEXES.md) - 거래 인덱스 관련 API 문서

### 개발 가이드
- [개발 환경 설정](../README.md#-빠른-시작) - 개발 환경 설정 가이드
- [API 사용법](../README.md#-api-문서) - API 사용법 및 예제

### 배포 가이드
- [Docker 배포](../README.md#-docker-사용) - Docker를 이용한 배포
- [CI/CD 파이프라인](../.github/workflows/ci.yml) - GitHub Actions CI/CD

## 🔧 개발 도구

### 코드 품질
- **Black**: 코드 포맷팅
- **Flake8**: 코드 린팅
- **MyPy**: 타입 검사
- **Pytest**: 테스트 프레임워크

### 사용법
```bash
# 코드 포맷팅
make format

# 코드 품질 검사
make check

# 테스트 실행
make test
```

## 📊 모니터링

### 헬스체크
- `GET /health` - 애플리케이션 상태 확인
- `GET /ready` - 준비 상태 확인

### 로깅
- 구조화된 JSON 로깅
- 요청/응답 로깅
- 에러 추적

## 🗄️ 데이터베이스

### 마이그레이션
마이그레이션 파일들은 `migrations/` 디렉토리에 있습니다.

### 스키마
- `migrations/postgresql_schema.sql` - PostgreSQL 스키마
- `migrations/init_tables.sql` - 초기 테이블 생성
- `migrations/trading_indexes.sql` - 거래 인덱스 관련 테이블

## 🚀 배포

### 환경 변수
필요한 환경 변수는 `.env` 파일에 설정하세요:

```env
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

### Docker 배포
```bash
docker-compose up -d
```

### 수동 배포
```bash
make run
``` 