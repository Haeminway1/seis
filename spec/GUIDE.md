# SEIS v1 가이드

**SEIS**는 *Standard English Item Schema*, 즉 **표준 영어 문항 규격**입니다. 규격 ID는 `seis/v1`입니다.

> 규격의 유일한 권위는 [`schema.json`](../schema/seis-v1.schema.json)입니다. 구조 규칙은 표준 JSON Schema 키로, 문서 간 참조·마커 위치·정답 연결 규칙은 `x-seis-invariants`로 선언됩니다. [`seis_validate.py`](../tools/seis_validate.py)는 그 불변량을 실행하는 공식 참조 검증기입니다. 이 문서와 구현이 다르면 `schema.json`이 맞습니다.

## 1. 한 문서가 담는 범위

SEIS 문서 하나는 **시험지 한 장 전체**를 담습니다.

- `exam`: 시험지의 ID·영역·제목
- `sources`: 문제지·정답지·대본·음원 출처
- `passages`: 지문. 공유 지문도 한 번만 저장
- `items`: 문항. 지문은 복사하지 않고 `passage_ids`로 참조

문항 하나나 세트 하나를 별도 SEIS 문서로 만들지 않습니다.

## 2. 빈칸은 어떻게 표기하나

빈칸을 `[BLANK]`나 `**(빈칸)**`으로 바꾸지 않습니다. **원본에 보이는 문자열을 그대로 보존**합니다.

원본이 다음과 같다면:

```text
The result depends on ______.
```

`passage.text`에도 `______`를 그대로 두고, 그 위치를 구조화된 마커로 기록합니다.

```json
{
  "id": "marker-blank-1",
  "label": "______",
  "kind": "blank",
  "owner_item": "item-1",
  "offset": {
    "start": 22,
    "end": 28,
    "unit": "unicode_code_point"
  }
}
```

핵심 규칙:

1. `label`은 원문에서 보이는 문자열과 정확히 같습니다.
2. `start`는 첫 글자의 위치이고 `end`는 마지막 글자 다음 위치입니다.
3. 위치 단위는 바이트나 UTF-16 코드 유닛이 아니라 **정규화하지 않은 Python 문자열의 유니코드 코드 포인트 인덱스**입니다. 결합문자도 실제 코드 포인트 수대로 셉니다.
4. `passage.text[start:end] == label`이어야 합니다.
5. 코드가 밑줄 개수나 `[BLANK]` 같은 문자열 패턴을 검색해 빈칸을 발견하지 않습니다. AI가 구조를 읽어 마커를 제출하고 검증기가 위치·소속·형태를 검사합니다.

따라서 원본에 `[BLANK]`가 실제로 인쇄되어 있다면 그 문자열 자체는 보존할 수 있지만, v3 변환기가 임의로 `[BLANK]`를 만들어 넣어서는 안 됩니다.

PDF의 시각적 빈칸처럼 지문 문자열에 대응되는 글자가 없으면 원문을 꾸며내지 않습니다. 글자 사이 위치는 `unicode_code_point_anchor`, 페이지의 시각 영역만 확인되는 경우는 `source_region` offset을 사용합니다. `source_region`은 페이지 왼쪽 위를 원점으로 하고 페이지 너비·높이를 각각 1로 정규화한 `normalized_page` 좌표이며, 해당 passage의 provenance와 같은 source/page만 참조할 수 있습니다. 이때 `label`은 빈 문자열일 수 있습니다.

## 3. 모든 마커의 공통 구조

모든 마커에는 다음 다섯 값이 필수입니다.

| 필드 | 뜻 |
|---|---|
| `id` | 문서 내부에서 유일한 마커 ID |
| `label` | 지문에 실제로 보이는 문자열 |
| `kind` | 마커의 용도 |
| `owner_item` | 이 마커를 사용하는 문항 ID |
| `offset` | 지문 안의 정확한 위치 |

허용되는 `kind`:

| kind | 용도 |
|---|---|
| `blank` | 빈칸 |
| `underline` | 밑줄 친 어휘·구절 |
| `paragraph` | `(A)`, `(B)` 같은 문단 라벨 |
| `reference` | `(a)`, `(b)` 같은 지칭·참조 대상 |
| `ordering_slot` | 순서 배열 위치 |
| `insert_slot` | 문장 삽입 위치 |
| `custom` | 위 항목에 속하지 않는 원문 마커 |

같은 `(a)`라도 `kind`와 `owner_item`이 다르면 다른 마커입니다. 문자열 모양만 보고 용도를 추측하지 않습니다.

## 4. 밑줄·문단·삽입 위치

- **밑줄:** `label`에는 밑줄 안의 실제 텍스트를 넣고 `kind`는 `underline`입니다. HTML `<u>`를 새로 만들어 원문에 삽입하지 않습니다.
- **문단 라벨:** 원문의 `(A)`를 그대로 보존하고 `kind`는 `paragraph`입니다.
- **지칭 대상:** 원문의 `(a)`를 그대로 보존하고 `kind`는 `reference`입니다.
- **순서·삽입 위치:** 원문에 표시된 기호를 그대로 보존하고 각각 `ordering_slot`, `insert_slot`을 사용합니다.

텍스트 마커는 지문 조각과 일치해야 합니다. 원문에 글자가 없는 시각적 마커는 `unicode_code_point_anchor` 또는 `source_region`으로 기록하며 가짜 밑줄·기호를 삽입하지 않습니다.

## 5. 보기와 정답

보기는 0개부터 여러 개까지 가능합니다. 라벨 형식은 제한하지 않습니다.

```json
"choices": [
  { "label": "ㄱ", "text": "첫 번째 보기" },
  { "label": "a", "text": "두 번째 보기" },
  { "label": "10", "text": "세 번째 보기" }
]
```

정답 형식:

- 단일 정답: `{ "form": "single", "value": "①" }`
- 복수 정답: `{ "form": "multiple", "values": ["ㄱ", "10"] }`
- 서술형: `{ "form": "free_text", "text": "정답 문장" }`

보기 라벨은 문항 안에서 중복될 수 없고, 단일·복수 정답은 실제 보기 라벨만 가리켜야 합니다. 서술형은 `choices: []`인 문항에 사용합니다. 각 문항의 `answer_provenance`는 정답을 확인한 answer source를 기록합니다.

## 6. 공유 지문과 세트 문항

공유 지문은 `passages[]`에 한 번만 저장합니다. 세트 문항은 같은 passage ID를 참조합니다.

```json
{
  "id": "item-43",
  "passage_ids": ["passage-43-45"]
}
```

문항 안에 지문 전문을 다시 넣는 필드는 없습니다. 이 규칙은 41–42번 지문의 `(a)`~`(e)`가 43–45번 문항으로 새어 들어간 v3 오류를 구조적으로 차단합니다.

## 7. 문제 유형과 TypeExpansion

SEIS의 유형 판정은 코드 이름만으로 하지 않습니다. 다음 세 권위를 함께 사용합니다.

1. `schema.json`: 문항·지문·마커·보기·정답의 공통 구조
2. [`profiles/ko-highschool-english/v1/status.json`](../profiles/ko-highschool-english/v1/status.json)과 [`aliases.json`](../profiles/ko-highschool-english/v1/aliases.json): 유형 코드의 등록 상태와 표기 변형
3. [`profiles/ko-highschool-english/v1/item-types.json`](../profiles/ko-highschool-english/v1/item-types.json): 유형별 판정·생성·표시·제외 계약

- 등록 유형: `"type_status": "registered"`
- 검토 중 확장 유형: `"type_status": "candidate"`

어떤 문항이 유형에 해당하려면 유형 계약의 평가 의도, 지문 구조, marker 개수와 단위, 선지 대응, 정답 개수, 표시 규칙을 모두 만족해야 합니다. 이름이나 발문에 특정 단어가 있다는 이유만으로 분류하지 않습니다. 예를 들어 `VOC`는 밑줄 단어가 있다는 사실만으로 성립하지 않으며, 서로 다른 문장에 한 단어씩 놓인 다섯 표적, 읽기 순서의 ①~⑤ 대응, 본문 표적과 동일한 다섯 선지, 문맥상 부적절한 단일 정답 계약을 모두 만족해야 합니다.

계약을 만족하지 않는 문항을 기존 유형에 억지로 넣지 않습니다. 기존 계약과 구별되는 재현 가능한 구조가 확인되면 `candidate` 유형을 만들고, 실제 문항 provenance·상세 계약·사람 승인을 거쳐 등록합니다. 따라서 `problem_type`만 복사해서는 새 문제를 생성할 수 없고, 반드시 해당 버전의 유형 계약을 함께 해석해야 합니다.
## 8. 추출 정규화와 렌더링

원문 보존은 지문·보기·마커 대상 문자열에 적용합니다. 시험 편집용 표지는 의미 필드와 분리합니다.

- 문항 번호는 `items[].number`에만 저장하고 `prompt` 앞의 `31.` 같은 번호는 제거합니다.
- `[31~34]`, `[36~37]` 같은 범위 표시는 `prompt`와 지문에 반복하지 않습니다. 공통 지시문이 필요하면 범위 숫자를 제거한 별도 instruction passage로 한 번만 저장합니다.
- `[3점]`은 `prompt`나 `passage.text`에 넣지 않고 `items[].auxiliary.points: 3`으로 저장합니다.
- `* tumultuous: 떠들썩한 ** buoyant: 부력이 있는` 같은 편집자 어휘 주석은 본문에 합치지 않습니다. 별도 `vocab-*` passage로 저장하고 해당 문항만 참조합니다.
- 주어진 문장·주어진 단어, 본문, 요약문은 서로 다른 passage로 저장합니다. 렌더러는 이를 각각 구분해서 보여야 합니다.
- 원문에 실제 밑줄 글자가 없는 시각적 빈칸은 JSON에서 가짜 밑줄을 만들지 않고 빈 label의 `unicode_code_point_anchor` 또는 `source_region`을 유지합니다. 렌더러만 해당 위치에 `______` 같은 가시적 대체물을 표시합니다.

이 정규화는 문항 번호·배점·범위 표지·어휘 주석이 평가 대상 본문에 섞이는 오염을 막기 위한 것입니다. 본문과 보기의 철자·문장부호·마커 대상 글자는 정규화하지 않습니다.
## 9. 출처

모든 지문과 문항에는 `provenance`가 필요합니다. `source_id`는 `sources[]`의 항목을 참조하며 필요하면 페이지와 영역을 기록합니다.

## 10. 거부되는 데이터

다음은 거부됩니다.

- 마커에서 `owner_item` 또는 위치 정보 누락
- 존재하지 않는 문항·지문·출처 ID 참조
- `label`과 실제 지문 조각 불일치
- 문항 안에 공유 지문을 복사해 넣기
- 스키마에 없는 임의 필드나 파생 필드 삽입
- `[BLANK]` 같은 통일 문자열로 원문을 임의 변경
- 코드펜스나 설명문이 섞인 JSON 아닌 출력

## 11. 예시

- 기본 예시: [`examples/minimal.seis.json`](../examples/minimal.seis.json)
- 시험용으로 변형된 지문(`integrity`): [`examples/modified-passage.seis.json`](../examples/modified-passage.seis.json)
