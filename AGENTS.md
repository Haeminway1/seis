# SEIS — 에이전트 사용 지침

SEIS v1 은 영어 시험 문항을 적는 **데이터 규격**이다. 이 문서는 사람이 아니라
**자동화 도구가 읽고 판단하기 위한 것**이다. 개념 설명은 [README.md](README.md),
규격 전문은 [spec/GUIDE.md](spec/GUIDE.md) 에 있다.

## 이 저장소가 하는 일 / 하지 않는 일

| 한다 | 하지 않는다 |
|---|---|
| 문항·지문·마커·정답을 적는 형식을 정한다 | 문항을 만들거나 채점하지 않는다 |
| 문서가 규격에 맞는지 검사한다 | 종이로 조판하지 않는다 → [seis-templates](https://github.com/Haeminway1/seis-templates) |
| 한국 고등 영어 유형 어휘를 제공한다 | 진단·난이도·오답 분석을 정의하지 않는다 (규격 밖) |

**기출 지문·교재 원문은 이 저장소에 없고, 넣어서도 안 된다.**

## 반드시 지킬 순서

```bash
./tools/seis-validate exam.seis.json           # 사람이 읽는 결과
./tools/seis-validate exam.seis.json --json    # 기계용
./tools/seis-validate *.seis.json              # 여러 개
```

종료 코드: `0` 통과 / `1` 실패 / `2` 파일·JSON 문제.

**문서를 만들거나 고친 뒤에는 반드시 검사한다.** 스키마만 통과하고 의미가 깨진
문서는 조판 단계에서 조용히 잘못된 종이를 낸다.

## 문서 최소 골격

```json
{
  "schema_id": "seis/v1",
  "exam": { "id": "...", "domain": "english", "title": "..." },
  "sources": [ { "id": "src_problem", "role": "problem", "locator": "..." } ],
  "passages": [ {
    "id": "psg_a",
    "text": "...",
    "markers": [],
    "provenance": [ { "source_id": "src_problem", "page": 1 } ],
    "integrity": { "is_original": true }
  } ],
  "items": [ {
    "id": "itm_01", "number": "01", "prompt": "...",
    "passage_ids": ["psg_a"],
    "choices": [ { "label": "①", "text": "..." } ],
    "answer": { "form": "single", "value": "①" },
    "problem_type": "MNI_GST", "type_status": "registered",
    "provenance": [ { "source_id": "src_problem", "page": 1 } ],
    "answer_provenance": [ { "source_id": "src_answer", "page": 1 } ]
  } ]
}
```

## 규격을 다룰 때 자주 틀리는 것

### 1. 마커 좌표를 사람이 적으면 안 된다

`marker.offset` 은 지문 본문의 **코드포인트 구간**이고, `marker.label` 은 그 구간의
글자와 **정확히 일치**해야 한다. 손으로 세면 반드시 어긋난다. 계산해서 넣는다.

```python
start = text.find(needle)
marker = { "label": needle,
           "offset": {"start": start, "end": start + len(needle),
                      "unit": "unicode_code_point"} }
```

어긋난 마커는 검증기가 잡는다. 잡히기 전에 조판되면 밑줄·빈칸이 통째로 사라진다.

### 2. `answer.form` 에 따라 필드가 다르다

| form | 필드 | 값 |
|---|---|---|
| `single` | `value` | 문자열 `"③"` |
| `multiple` | `values` | 배열 `["①","④"]` |
| `text` | `values` | 배열 (서술형 모범답안) |

선지 라벨은 `①②③④⑤` 다. `1` `(1)` `A` 를 쓰지 않는다.

### 3. `label` 은 정답이 아니다

마커의 `label` 은 **"지문의 그 자리에 실제로 적힌 글자"**다. 원문 그대로인 지문에서는
정답과 같지만, 변형 지문에서는 **바꿔치기된 오답**이 들어 있다. 정답을 꺼내려면
`item.answer` 를 본다. 이 둘을 섞으면 교사용 사본에 오답이 정답처럼 찍힌다.

### 4. 지문은 문항 안에 복사하지 않는다

여러 문항이 한 지문을 쓰면 `passage_ids` 로 **참조**한다. 복사해 넣으면 검증기가
막는다. 지문을 고칠 때 한 군데만 고치면 되게 하려는 것이다.

### 5. 변형 지문은 표시한다

시험용으로 훼손한 지문은 `integrity.is_original: false` 와 `restoration_kind` 를 적는다.
원문인지 아닌지를 데이터가 알고 있어야 나중에 원문 복원이 가능하다.

## 절대 넣지 말 것

- **기출 지문 원문, 시판 교재 지문, 학교 내신 문항** — 저작권 문제이며 이 저장소의
  전제를 깬다. 예시 문서의 지문은 전부 이 저장소를 위해 직접 쓴 것이다
- **학교명·학원명·학생 정보** — `exam.id`, `locator`, `metadata` 어디에도 넣지 않는다
- **로컬 절대 경로** (`/home/...`, `C:\Users\...`)

새 예시를 추가할 때는 지문을 직접 쓰고, 커밋 전에 위 세 가지를 훑는다.

## 유형 코드를 늘릴 때

`problem_type` 은 프로파일이 정한다(`profiles/ko-highschool-english/v1/item-types.json`).

- 새 유형은 **먼저 프로파일에 등록**하고 `type_status: "registered"` 로 쓴다
- 등록 전이면 `type_status: "provisional"` 로 두고, 코어 스키마는 건드리지 않는다
- 접미사 문법은 `<BASE>[_NEG][_MULTI]` 다. 임의 접미사를 만들지 않는다
- 절차는 [CONTRIBUTING.md](CONTRIBUTING.md) 에 있다

**코어 스키마(`schema/seis-v1.schema.json`)는 마지막에 손대는 곳이다.** 대부분의
확장 요구는 프로파일에서 끝난다.

## 조판까지 이어 갈 때

이 저장소는 종이를 만들지 않는다. 검사를 통과한 문서를 조판기에 넘긴다.

```bash
./tools/seis-validate exam.seis.json
# → github.com/Haeminway1/seis-templates
./bin/seis-build exam.seis.json --kind exam --theme veradict -o out/
```

## 구조

```
schema/seis-v1.schema.json   유일한 권위. 불변량 12개를 x-seis-invariants 에 선언
tools/seis-validate          참조 검증기 (파이썬 표준 라이브러리만)
spec/GUIDE.md                규격 전문
profiles/                    유형·별칭·카테고리 어휘
examples/                    최소 예시와 변형 지문 예시
```

구조가 맞는지는 스키마가 보고, **말이 되는지는 검증기가 본다.** 둘 다 통과해야 한다.
