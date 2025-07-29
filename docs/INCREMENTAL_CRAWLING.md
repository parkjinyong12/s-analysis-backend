# 증분 크롤링 (Incremental Crawling) 가이드

## 개요

증분 크롤링은 전체 데이터를 다시 수집하는 대신, **누락된 최신 데이터만** 효율적으로 수집하는 기능입니다.

## 주요 기능

### 1. 자동 누락 데이터 감지
- 최근 N일 동안의 거래 데이터에서 누락된 날짜를 자동으로 찾습니다
- 주말(토,일)은 자동으로 제외됩니다

### 2. 선택적 수집
- **특정 주식**만 대상으로 하거나 **전체 주식** 대상 가능
- 누락 데이터가 없으면 자동으로 건너뜁니다
- `--force` 옵션으로 강제 수집 가능

### 3. 효율적인 크롤링
- 최신 데이터 위주로 **적은 페이지**만 크롤링 (기본값: 5페이지)
- 기존 전체 크롤링 대비 **시간과 리소스 절약**

## 사용 방법

### 1. API 방식 (웹 인터페이스)

#### 누락 데이터 확인
```bash
GET /api/v1/collector/check-missing?stock_code=005930&days_back=30
```

#### 증분 크롤링 실행
```bash
POST /api/v1/collector/incremental
Content-Type: application/json

{
    "stock_code": "005930",     # 선택적: 특정 주식 (없으면 전체)
    "days_back": 30,            # 선택적: 확인 기간 (기본값: 30일)
    "max_pages": 5,             # 선택적: 최대 페이지 (기본값: 5)
    "force_collect": false      # 선택적: 강제 수집 (기본값: false)
}
```

### 2. 명령행 스크립트 방식 (외부 실행)

#### 기본 사용법
```bash
# 도움말 확인
python scripts/incremental_crawler.py --help

# 특정 주식의 누락 데이터 확인만
python scripts/incremental_crawler.py --check --stock-code 005930 --days-back 30

# 특정 주식의 증분 크롤링 (최근 7일)
python scripts/incremental_crawler.py --stock-code 005930 --days-back 7

# 전체 주식의 증분 크롤링 (최근 7일)
python scripts/incremental_crawler.py --all --days-back 7

# 강제 수집 (누락 데이터가 없어도 크롤링)
python scripts/incremental_crawler.py --all --days-back 7 --force

# 시뮬레이션 모드 (실제 크롤링 없이 확인만)
python scripts/incremental_crawler.py --all --days-back 30 --dry-run
```

#### 고급 옵션
```bash
# 최대 페이지 수 지정
python scripts/incremental_crawler.py --stock-code 005930 --days-back 7 --max-pages 10

# 강제 수집 + 많은 페이지
python scripts/incremental_crawler.py --all --days-back 14 --max-pages 8 --force
```

## 사용 시나리오

### 시나리오 1: 일일 정기 업데이트
```bash
# 매일 아침 실행하여 어제 누락된 데이터만 수집
python scripts/incremental_crawler.py --all --days-back 3
```

### 시나리오 2: 특정 주식 모니터링
```bash
# 관심 종목의 최신 데이터 확인 및 수집
python scripts/incremental_crawler.py --stock-code 005930 --days-back 7
```

### 시나리오 3: 주말 후 업데이트
```bash
# 주말 후 월요일에 지난주 누락 데이터 수집
python scripts/incremental_crawler.py --all --days-back 10 --max-pages 8
```

## 출력 예시

### 누락 데이터 확인 결과
```
=== 누락 데이터 확인 결과 ===
주식: 005930 - 삼성전자
최신 데이터 날짜: 2024-07-26
확인 기간: 최근 30일
누락된 날짜 수: 3개
누락된 날짜들: ['2024-07-25', '2024-07-24', '2024-07-23']
```

### 증분 크롤링 완료 결과
```
=== 증분 크롤링 완료 ===
대상 주식: 2847개
수집 완료: 45개
건너뛰기: 2795개
실패: 7개
총 누락 날짜: 87개
수집된 날짜: 78개
```

## 로그 파일

실행 로그는 다음 위치에 저장됩니다:
- `logs/incremental_crawler_YYYYMMDD.log`

## 주의 사항

1. **네트워크 부하**: 전체 주식 대상 시 요청 간 지연시간이 적용됩니다
2. **데이터 중복**: 기존 데이터가 있는 날짜는 자동으로 업데이트됩니다
3. **주말 제외**: 토요일, 일요일은 거래일이 아니므로 누락 데이터로 간주하지 않습니다
4. **페이지 제한**: `max_pages`를 너무 크게 설정하면 불필요한 중복 데이터를 수집할 수 있습니다

## 성능 비교

| 방식 | 대상 기간 | 평균 소요시간 | 네트워크 요청 |
|------|-----------|---------------|---------------|
| 전체 크롤링 | 3년 | 30-50분 | ~30,000회 |
| 증분 크롤링 | 최근 30일 | 5-10분 | ~1,500회 |

## 문제 해결

### 자주 발생하는 오류

1. **"주식을 찾을 수 없습니다"**
   - 주식 코드가 정확한지 확인
   - 데이터베이스에 해당 주식이 등록되어 있는지 확인

2. **"크롤링 데이터 없음"**  
   - 네트워크 연결 상태 확인
   - 해당 주식의 거래 정지 여부 확인

3. **"데이터 저장 실패"**
   - 데이터베이스 연결 상태 확인
   - 디스크 용량 확인 