# SEIS — Standard English Item Schema

시험지 한 장을 **컴퓨터가 읽을 수 있는 형태로 적어두는 양식**이다.

한글 파일로 만든 시험지는 그 한글 파일 안에서만 산다. 다른 도구로 넘길 수 없고,
3년 뒤 같은 지문을 다시 쓰려 해도 찾을 방법이 없다. **양식이 없으면 데이터가 아니라
그냥 종이다.**

```
$ ./tools/seis-validate examples/minimal.seis.json
✓ PASS  examples/minimal.seis.json
       items 2  passages 1  markers 1  sources 2
```

## 왜 필요한가

문항을 열심히 만들어도 **한 번 쓰고 버려진다.** 다음 시험을 만들 때는 처음부터
다시 만든다. 만들어진 문항이 *찾을 수 있고 재조합할 수 있는 형태*로 남지 않기
때문이다.

SEIS는 세 가지로 그걸 해결한다.

| | 어떻게 |
|---|---|
| **지문 재사용** | 지문을 문항과 분리해 한 번만 저장한다. 같은 지문에 새 문항만 붙일 수 있다 |
| **위치 보존** | 빈칸·밑줄을 좌표로 적는다. 지문 원문에 `[BLANK]` 같은 걸 박아 넣지 않는다 |
| **출처 추적** | 문항과 정답이 각각 어디서 왔는지 따로 기록한다 |

## 구조 — 코어와 프로파일

```
schema/     seis-v1.schema.json     ← 코어. 과목·언어 무관
spec/       GUIDE.md                ← 규격 설명
tools/      seis-validate           ← 참조 검증기 (의존성 0)
profiles/   ko-highschool-english/  ← 유형 어휘. 과목별로 갈린다
examples/
```

코어에는 **영어에만 해당하는 게 하나도 없다.** 지문·문항·선지·정답·마커는 국어도
수학도 같다. 과목마다 다른 건 *유형 어휘*뿐이라 프로파일로 분리했다.

덕분에 새 과목을 추가해도 **코어는 바뀌지 않고, 기존 도구는 그대로 돈다.**

## 진단은 표준 밖이다

개념 분류·약점 계산·학생 진단은 SEIS가 정하지 않는다. 개념 체계는 가르치는 사람마다
다르고, 시험지를 정리하고 싶을 뿐인 사람에게 그걸 강제하면 아무도 쓰지 않는다.

대신 **확장 슬롯**이 열려 있다.

```json
"extensions": {
  "haeminway.diagnosis": {
    "concept_weights": { "vocabulary": 0.2, "syntax": 0.2, "inference": 0.6 }
  }
}
```

읽는 쪽은 **모르는 확장을 무시해야 한다.** 확장이 없다고 실패하면 안 된다.

## 시험지 지문은 원문이 아니다

이 규격의 특이한 필드 하나. 시험지는 원문을 **일부러 훼손한다** — 어휘 문제를 붙이려면
단어 하나를 틀린 것으로 바꾸고, 순서 문제를 붙이려면 문단을 섞는다.

그 지문을 그대로 재사용하면 **틀린 단어가 정답 지문으로 실린다.** 문서 자체가
"나는 변형본이다"라고 말해주지 않기 때문이다.

```json
"integrity": {
  "is_original": false,
  "restoration_kind": "vocabulary_correction",
  "restored_ref": "SRC_..."
}
```

선택 필드다. 없으면 "모름"이고 기존 문서는 그대로 유효하다. `restored_ref`는
**가리키기만 한다** — 복원된 원문 텍스트는 이 규격이 절대 담지 않는다.

## 저작권 — 이 저장소에 기출 지문은 없다

SEIS의 가치는 지문 텍스트가 아니라 **구조**에 있다. 그래서 이 저장소는 어떤 기출
지문도 배포하지 않는다.

시험문제는 저작물이고, 특히 수능 영어 지문은 대부분 해외 저작물에서 발췌된 것이라
출제 기관의 허락과 별개로 **원저작자의 권리가 살아있다.**

`examples/`의 영어 지문은 **이 저장소를 위해 새로 쓴 것**이다. 실제 기출은 각자
자기 파일을 자기 컴퓨터에서 넣으면 된다 — 원문이 이동하지 않으므로 위험이 애초에
발생하지 않는다.

## 시작하기

의존성이 없다. Python 3.9+ 만 있으면 된다.

```bash
./tools/seis-validate examples/minimal.seis.json
./tools/seis-validate examples/modified-passage.seis.json   # integrity 사용 예
./tools/seis-validate my-exam.json --json                   # 기계용 출력
```

검증기는 JSON Schema가 못 잡는 것을 본다. **불변량 12개**가 `schema.json`의
`x-seis-invariants`에 선언돼 있다.

- `passage.text[start:end]` 가 마커 `label` 과 **정확히 일치**하는가
- `passage_ids` · `owner_item` · `source_id` 가 실제 존재하는 것을 가리키는가
- 정답 라벨이 선지에 실제로 있는가
- 문항 안에 공유 지문을 복사해 넣지 않았는가

구조가 맞는지는 스키마가 보고, **말이 되는지는 검증기가 본다.**

## 인쇄물로 뽑기 — seis-templates

검증기는 "맞다"는 것만 알려 주고 손에 쥘 종이를 주지 않는다. SEIS 를 쓰는 일이
*인쇄 능력을 잃는 일*이 되지 않도록, 조판 참조 구현을 따로 둔다.

**[Haeminway1/seis-templates](https://github.com/Haeminway1/seis-templates)** — 같은
JSON 하나에서 시험지·연습문제·숙제·교재·클리닉지가 나온다. 의존성 없고, 브라우저에서
`Ctrl+P` 하면 A4 인쇄물이 된다.

```bash
./bin/seis-build exam.seis.json --kind exam --theme academy-navy -o out/
```

마커 조판(빈칸·밑줄·삽입 자리), A4 면 나누기, 정답표·해설면이 들어 있다.

## 문서

| | |
|---|---|
| [`spec/GUIDE.md`](spec/GUIDE.md) | 규격 전체 설명 |
| [`schema/seis-v1.schema.json`](schema/seis-v1.schema.json) | 유일한 권위. 불변량 12개 포함 |
| [`profiles/ko-highschool-english/v1/`](profiles/ko-highschool-english/v1/) | 한국 고등 영어 유형 어휘 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 유형 추가·스펙 변경 절차 |
| [`AGENTS.md`](AGENTS.md) | 자동화 도구·에이전트용 사용 지침 |

## 라이선스

- **코드** (`tools/`, `schema/`) — [MIT](LICENSE)
- **문서·프로파일** (`spec/`, `profiles/`, `README.md`) — [CC BY 4.0](LICENSE-DOCS)

가져다 쓰고 고쳐 쓰라는 쪽이다. 표준은 퍼져야 표준이다.

## 상태

`seis/v1` — 실사용 중인 형태를 명세로 옮긴 것이다. 여기 있는 규격과 검증기는
실제 시험지 데이터에 매일 돌고 있다.
