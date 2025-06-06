# CEDGE (Cyperus Embedded Dataflow Governance Environment)

CEDGE는 **대규모 AI 학습용 데이터셋**을 Git처럼 추적하고, 대용량 파일을 **병렬 분산 방식**으로 관리하기 위해 설계된 **분산형 데이터셋 협업 시스템**입니다.
LLM을 사용한 데이터셋 생성 자동화 시스템(Cyperus)을 보조하기 위하여 고안되었습니다.

---

## cedge의 구조도
                       ┌────────────────────────────┐
                       │            HOST            │
                       │  중앙 메타데이터 관리 서버 │
                       └──────────┬─────────────────┘
                                  │
               ┌─────────────────┴──────────────────┐
               │                                    │
     ┌─────────▼─────────┐              ┌───────────▼───────────┐
     │      HARBOR 1     │              │       HARBOR 2        │
     │  중간 관리자 노드 │              │   중간 관리자 노드    │
     └────────┬──────────┘              └──────────┬────────────┘
              │                                     │
    ┌─────────▼────────┐                 ┌──────────▼─────────┐
    │    파일 저장소    │                 │     파일 저장소     │
    └────────┬─────────┘                 └──────────┬──────────┘
              └────┬──────────────┬──────────────┬──┘
                   │              │              │
            ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐
            │  사용자 A  │ │  사용자 B  │ │  사용자 C  │
            └────────────┘ └────────────┘ └────────────┘

사용자 한 명이 여러 Harbor로부터 병렬로 파일을 받는 구조 지원



---

## 핵심 기능 요약

| 기능 명령어                   | 설명                                                                 |
|------------------------------|----------------------------------------------------------------------|
| `cedge new <proj>`           | 프로젝트 생성 (host에서만 실행 가능)                                |
| `cedge init --name <name>`   | harbor 초기화 및 host에 등록 요청                                   |
| `cedge register <파일>`      | 사용자 → 자신의 프로젝트 폴더를 cedge에 등록 (.cedge 폴더 생성)      |
| `cedge add <파일>`           | 사용자 → 자신의 프로젝트 폴더에서 변경 사항을 업데이트               |
| `cedge show diff <파일>`     | 현재 로컬 디렉토리와 등록된 파일 상태 비교                         |
| `cedge push (TODO)`          | harbor → host: 파일 UUID 전달 및 등록                               |
| `cedge clone <proj> (TODO)`  | 사용자 ← 여러 harbor: 병렬 전송 기반으로 전체 파일 클론             |
| `cedge log (TODO)`           | 프로젝트 파일의 등록/수정 기록 확인                                 |

---

## 🛠️ 구성 요소

- **Host**: 프로젝트와 UUID를 관리하는 중앙 서버
- **Harbor**: 실제 데이터를 저장하고 사용자 요청을 처리하는 중간 관리자 노드
- **User**: 파일을 등록하거나 받아가는 협업 참여자

---

## 🚀 주요 특징

- ✅ Git과 유사한 CLI 방식
- ✅ 대용량 파일에 적합한 병렬 전송 구조
- ✅ 분산 저장 및 UUID 기반의 신뢰 추적
- ✅ 사용자가 직접 host가 되어서 harbor들을 관리하는 cedge 프로젝트 생성 가능

---

## 📁 저장 구조 예시 (User용)

```
project/
├── .cedge/
│ └── tracked.json # 등록된 파일들의 UUID 기록
├── data/
│ ├── sample1.txt
│ ├── sample2.txt
```

---

## host의 명령어

```bash
# host 서버 시작
python server/main.py

# host에서 프로젝트 생성
curl -X POST http://localhost:8000/api/create_project \
     -H "Content-Type: application/json" \
     -d '{"name": "project_alpha"}'

# 생성된 프로젝트 조회
curl http://localhost:8000/api/project/project_alpha

# UUID 상세 정보 조회
curl http://localhost:8000/api/uuid/file-uuid-1234

# 전체 통계 확인
curl http://localhost:8000/api/stats
 
```

## harbor의 명령어

```bash
# harbor 초기화
python ../../server/harbor_main.py init --name h1(harbor의 이름) --project project_alpha(프로젝트의 이름, 기존에 host에서 생성한 것만 가능)

EX result : Harbor 'h1' registered for project 'my_pj'


# 파일 등록
python ../../server/harbor/harbor_main.py harbor --name h1 register-file .

EX result : File 's1.txt' registered with UUID: <자동 생성된 UUID>



### .cedge/harbor/harbor_db.json ###
{
  "harbor_name": "h1",
  "project": "my_pj",
  "files": {
    "s1.txt": {
      "uuid": "d39a...a112",
      "version": 1
    },
    "s2.txt": {
      "uuid": "aa53...c999",
      "version": 1
    }
  }
}
```
