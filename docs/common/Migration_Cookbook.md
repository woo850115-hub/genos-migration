# GenOS Migration Cookbook

**실전 마이그레이션 가이드**

---

## 빠른 시작

### 설치

```bash
cd /home/genos/workspace/genos-migration
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 분석 실행

```bash
genos analyze /path/to/your/mud
```

### 마이그레이션 실행

```bash
# YAML 형식 (기본)
genos migrate /path/to/your/mud -o ./output

# JSON 형식
genos migrate /path/to/your/mud -o ./output -f json

# 상세 로그
genos -v migrate /path/to/your/mud -o ./output
```

### 출력 구조

```
output/
├── uir.yaml              # UIR 중간 표현 (전체 게임 데이터)
├── sql/
│   ├── schema.sql        # PostgreSQL CREATE TABLE DDL
│   └── seed_data.sql     # INSERT 문 (모든 엔티티)
└── lua/
    ├── combat.lua         # 전투 시스템
    ├── classes.lua        # 캐릭터 클래스 정의
    └── triggers.lua       # 트리거 스크립트 → Lua 변환
```

---

## 게임별 가이드

소스 MUD 엔진별 상세 가이드는 아래를 참조하세요:

- [CircleMUD/tbaMUD](../circlemud/Migration_Cookbook_CircleMUD.md)
