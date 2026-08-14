# 프로파일 — 한국 고등 영어 (내신·수능)

SEIS 코어는 과목을 모른다. 유형 어휘는 여기 산다.

| 파일 | 내용 |
|---|---|
| `item-types.json` | 유형 계약. "이 문항이 이 유형인가"를 판정하는 규칙 |
| `aliases.json` | 표기 변형 → 정식 코드 매핑 |
| `categories.json` | 상위 카테고리 (MNI 대의파악 · LST 듣기 · LPS 장문세트 · VOC 어휘 · OEQ 서답형) |
| `distractor-mechanisms.json` | 오독 메커니즘 8종 — 오답을 "어떻게 틀렸는지"로 분류 |
| `status.json` | registered / candidate 구분 |

## registered 와 candidate

- **registered** — 유형 계약이 있어 판정 근거를 문서로 댈 수 있다
- **candidate** — 실데이터에는 있으나 계약이 아직 없다. **집계·생성에 쓰기 전에 계약을 먼저 채운다**

candidate 코드로 태깅된 문항을 통계에 넣으면 안 된다. 같은 코드가 사람마다 다른
것을 뜻하고 있을 수 있기 때문이다.

## aliases 가 필요한 이유

같은 개념이 현장에서 수십 가지로 적힌다. "제목" 하나에도 `title`, `TITLE`,
`글의 제목`, `제목 추론`, `title_inference`, `장문 제목` … 이 실제로 나온다.

`aliases.json` 은 그 표기들을 정식 코드로 수렴시킨다. 각 매핑에는 근거(`basis`)와
확신도(`confidence`)가 붙어 있어, 자동 매핑과 사람 확인을 구분할 수 있다.

**표기가 갈리는 것을 막을 수는 없다. 흡수할 수 있을 뿐이다.** 그래서 표준은
별칭표를 함께 배포한다.

## 이름 규칙

```
<BASE> [_NEG] [_MULTI]
```

`_NEG` 는 부정형("~하지 않는 것"), `_MULTI` 는 복수정답이다. 지문 개수는 코드에
넣지 않는다 — `passage_ids` 로 이미 알 수 있다.

우산 코드는 아직 하위를 정하지 않은 상태를 뜻한다.

```
BLK → BLK_WRD (빈칸 단어) | BLK_PHR (빈칸 구·절)
MNI → MNI_TIT | MNI_TPC | MNI_CLM | MNI_GST
CON → CON | CON_NEG | CON_CNT
```

## 다른 과목·시험을 위한 프로파일

이 폴더를 본떠 `profiles/<이름>/v1/` 을 만들면 된다. **코어는 건드리지 않는다.**
토익이든 중등이든 국어든, 코어 스키마와 검증기는 그대로 쓴다.
