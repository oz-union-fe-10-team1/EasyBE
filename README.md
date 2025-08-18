# Hanjan - BE 🍶

AI 기반 맛 프로파일링을 통한 개인화된 전통주 추천 서비스
(https://hanjantest.store)

---

## 목차

1. [주요 기능](#주요-기능)
2. [팀원](#팀원)
3. [기술 스택](#기술-스택)
4. [시스템 아키텍처](#시스템-아키텍처)
5. [프로젝트 구조](#프로젝트-구조)
6. [API 문서](#api-문서)
7. [배포](#배포)

---

## 주요 기능

### 핵심 컨셉
전통주 추천 플랫폼의 백엔드 부분입니다.</br>**'입맛 테스트'**로 첫 추천을, **'시음 피드백'**을 통한 **'맛 보정'**으로 정교한 재추천을 제공합니다.

### 사용자 여정
1. **신규 사용자 (On-boarding)**
   - 입맛 테스트 수행 → 취향 유형 발견 → 첫 시음 패키지 추천

2. **기존 사용자 (Re-targeting)**
   - 시음 피드백 제공 → 맛 보정 시스템 작동 → 정밀한 재추천

### 1. 사용자 인증
- **OAuth 2.0 소셜 로그인**: 카카오/구글/네이버
- **JWT 기반 인증 시스템**

### 2. 입맛 테스트 (온보딩)
- 개인화된 테스트 질문 시스템
- 답변 기반 취향 유형 도출 로직
- 초기 추천 제품 제공

### 3. 제품 관리
- 전통주 목록/상세 조회 API
- **다중 필터링**: 맛 태그/주종/도수별
- 통합 검색 기능

### 4. ⭐ 맛 보정 및 추천 알고리즘 (핵심 특허 기술)
```python
# 핵심 알고리즘 개념
개별 맛 보정 계수 = f(피드백 점수, 신뢰도)
통합 맛 보정 계수 = 이동평균(기존 계수, 새로운 계수)  
개인화 추천 = g(사용자 프로필, 제품 맛 지수, 보정 계수)
```

- **피드백 저장 API**: 개별 맛 보정 계수, 신뢰도 적용 보정 계수 계산
- **프로필 업데이트**: 이동 평균 방식으로 통합 맛 보정 계수 업데이트
- **추천 제공 API**: 업데이트된 프로필 기반 개인화 추천

### 5. 시음 후기 및 피드백
- **시음 후기 작성**: 사용자가 전통주 시음 후 후기 및 평점 등록
- **피드백 기반 추천**: 사용자의 후기와 피드백을 바탕으로 맞춤형 추천 제공
- **후기 관리**: 작성된 후기 조회 및 수정 기능

### 6. 패키지 제작
- 맞춤형 패키지 구성 시스템
- 장바구니 기능 API
- 결제 모듈 연동 (추후 구현 예정)

### 7. 마이페이지
- **주문/배송 내역** 관리
- **입맛 프로필 시각화** (테스트 결과, 보정 계수)
- **시음 피드백** 관리
- **회원정보** 수정

### 8. 관리자 시스템
- **전통주 관리**: 제품 CRUD, 표준 맛 지수 및 맛 태그 관리
- **고객/후기 관리**: 사용자 관리 및 후기 승인/삭제
- **입맛 테스트 관리**: 테스트 문항과 결과 유형 수정

---

## 팀원

| <a href="https://github.com/leejiyun1"><img src="https://avatars.githubusercontent.com/u/201066873?v=4" width=100px/><br/><sub><b>@leejiyun1</b></sub></a> | <a href="https://github.com/choismjames23"><img src="https://avatars.githubusercontent.com/u/200033221?v=4" width=100px/><br/><sub><b>@choismjames23</b></sub></a> | <a href="https://github.com/yangjiun00"><img src="https://avatars.githubusercontent.com/u/144764519?v=4" width=100px/><br/><sub><b>@yangjiun00</b></sub></a> |
|:-------------------------------------------------------------:|:-------------------------------------------------------------:|:-------------------------------------------------------------:|
| 이지윤 | 최승민 | 양지운 |
| 팀장 | 팀원 | 팀원 |
| 상품, 테스트 API 담당 | 유저 API, 인프라 구축 및 배포 담당 | 주문 API 담당 |

---

## 기술 스택

| 분류 | 기술 스택                                     |
|------|-------------------------------------------|
| **Language & Framework** | Python , Django, Django REST Framework    |
| **Database & Cache** | NCP PostgreSQL, Redis                     |
| **Authentication** | OAuth 2.0 (카카오/네이버/구글), JWT               |
| **Infrastructure** | Docker, Nginx, Gunicorn                   |
| **Cloud & Storage** | NCP Server, Load Balancer, Object Storage |
| **CI/CD** | GitHub Actions, Docker Hub                |
| **Documentation** | drf-spectacular (Swagger/OpenAPI)         |

---

## 시스템 아키텍처

> 전체 아키텍처는 아래 다이어그램을 참고하세요.

![hanjan system](hanjan%20system%20.jpeg)

### 아키텍처 구성 설명

전체적인 시스템은 **네이버 클라우드 플랫폼**을 이용하여 구성되어 있습니다.

#### 인프라 구성 요소
- **Load Balancer**: HTTPS 인증서 처리
- **NCS Server**: Docker Container 환경에서 Nginx + Django 구성
- **Gunicorn**: Django WSGI 서버로 실제 애플리케이션 실행
- **PostgreSQL**: RDBMS로 사용하여 주요 데이터 저장
- **Redis**: Cache Memory로 API 응답 캐싱
- **Object Storage**: 상품 이미지 등 정적 파일 저장

#### 데이터 흐름
1. **사용자 요청** → Load Balancer → Nginx → Gunicorn → Django 애플리케이션
2. **Django**에서 PostgreSQL (데이터 저장), Redis (캐싱), Object Storage (이미지) 연동
3. **OAuth 2.0**을 이용하여 카카오/네이버/구글 소셜 로그인 구현

#### CI/CD 파이프라인
- **GitHub Actions** → Docker 이미지 빌드 → Docker Hub → 자동 배포
- 코드 푸시 시 자동으로 Docker 컨테이너 빌드 및 운영 서버 배포

---

## 프로젝트 구조

```
hanjan-backend/
├── config/                     # Django 설정
│   ├── settings/
│   │   ├── base.py            # 공통 설정
│   │   ├── local.py           # 로컬 개발 환경
│   │   ├── dev.py             # 개발 환경
│   │   └── prod.py            # 운영 환경
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/                 # 사용자 인증 및 관리
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── social_login/      # 소셜 로그인 (카카오/구글/네이버)
│   │   ├── utils/             # JWT, 인증 유틸리티
│   │   └── views/             # 로그인, 프로필 관련 뷰
│   ├── taste_test/            # 입맛 테스트 (핵심)
│   │   ├── models.py
│   │   ├── serializers/       # 요청/응답 시리얼라이저
│   │   ├── services/          # 테스트 분석 및 프로필 처리 로직
│   │   ├── constants/         # 취향 유형, 테스트 데이터
│   │   └── views/             # 테스트 진행, 프로필 관리
│   ├── products/              # 제품 관리
│   │   ├── models.py
│   │   ├── serializers/       # 제품별 시리얼라이저
│   │   ├── services/          # 검색, 좋아요 서비스
│   │   └── views/             # 제품 CRUD, 검색, 필터링
│   ├── feedback/              # 시음 피드백 (맛 보정 핵심)
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   ├── cart/                  # 장바구니
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   ├── orders/                # 주문/결제
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   ├── stores/                # 매장 관리
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   ├── adminpanel/            # 관리자 시스템
│   │   └── views.py
│   └── common/                # 공통 유틸리티
│       └── middleware.py
├── core/
│   └── utils/
│       └── ncloud_manager.py  # 네이버 클라우드 연동
├── static/
│   └── types/                 # 취향 유형 이미지
├── resources/
│   ├── nginx/                 # Nginx 설정
│   └── scripts/               # 배포 스크립트
├── docker-compose.local.yml
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```

---

## API 문서

### Swagger/OpenAPI 자동 문서화
개발 단계에서 **drf-spectacular**를 이용하여 모든 API를 자동으로 문서화했습니다.

- **개발 환경**: `http://localhost:8000/api/schema/swagger-ui/`
- **API 스키마**: `http://localhost:8000/api/schema/`

Swagger UI를 통해 실시간으로 API 테스트가 가능하며, 모든 엔드포인트의 요청/응답 형식을 확인할 수 있습니다.

---

## 배포

### 네이버 클라우드 플랫폼 + Docker Hub CI/CD

#### 인프라 구성
- **Server**: Naver Cloud Platform (Linux)
- **Database**: Cloud DB for PostgreSQL  
- **Storage**: Object Storage (정적 파일, 이미지)
- **Load Balancer**: Application Load Balancer
- **Container Registry**: Docker Hub

#### 배포 프로세스
1. **코드 푸시** → `main` 브랜치에 푸시 시 GitHub Actions 자동 트리거
2. **Docker 빌드** → Django 애플리케이션 Docker 이미지 빌드
3. **Docker Hub 업로드** → 빌드된 이미지를 Docker Hub에 푸시
4. **서버 배포** → NCP 서버에서 Docker Hub로부터 이미지 Pull 후 컨테이너 재시작

---