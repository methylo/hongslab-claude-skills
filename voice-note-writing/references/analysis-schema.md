# 음성 전사문 분석 스키마

이 문서는 비정형 음성 전사문을 Source Brief로 바꾸는 내부 분석 기준이다. 사용자가 분석 과정을 요청하지 않으면 이 분류표를 그대로 노출하지 않는다.

## 1. 의미 단위 분할

문장부호보다 의미가 바뀌는 지점에서 나눈다. 한 문장 안에 다음 요소가 섞이면 별도 단위로 분리한다.

| 코드 | 분류 | 판단 질문 | 처리 |
|---|---|---|---|
| E | 경험 | 실제로 무엇을 했거나 겪었는가 | 사용자 소유 경험으로 보존 |
| O | 관찰 | 사람·상황·도구에서 무엇을 보았는가 | 문제 상황이나 도입 재료 |
| J | 판단 | 지금 무엇이 필요하거나 맞다고 보는가 | 중심 판단 후보 |
| C | 사례 | 어떤 장면이 판단을 보여주는가 | 근거로 사용 |
| I | 작업 지시 | AI가 글을 어떻게 써야 하는가 | 본문과 분리해 편집 조건으로 전달 |
| U | 전사 불확실성 | 오인식 가능성이 있는가 | 교정 근거 확인 또는 질문 |
| F | 후속 글감 | 중심 판단과 다른 독립 주제인가 | 별도 글 후보로 이동 |
| X | 군더더기 | 삭제해도 의미·온도·강조가 유지되는가 | 작업본에서만 제거 |

### 분할 예시

전사문:

> 스킬을 어렵게만 느끼지 않게 하고 사례도 좀 넣어 주고 결국은 나에게 맞게 쓰는 방법이 필요한 것 같아.

분해:

- O: 많은 사람이 스킬을 어렵게 느낀다.
- I: 사례를 넣어 설명한다.
- J: 스킬을 자기 작업에 맞게 고쳐 쓰는 방법이 필요하다.

`사례를 넣어 설명한다`는 작업 지시이므로 글의 주장으로 쓰지 않는다.

## 2. 반복 묶음 만들기

반복은 단어가 같을 때만 묶지 않는다. 의미가 같으면 한 묶음으로 본다.

```text
반복 묶음 ID:
원문 표현:
- 표현 1
- 표현 2
- 표현 3
공통 생각:
후반 정정 또는 강화:
보존할 사용자 표현:
삭제 가능한 반복:
```

### 반복의 가중치

다음 신호가 겹칠수록 중심 판단 후보로 본다.

1. 같은 뜻을 세 번 이상 다른 말로 표현함
2. 발화 후반에 다시 돌아와 정리함
3. `결국`, `내가 말하려는 것은`, `필요한 것은` 뒤에 등장함
4. 사례나 문제 상황이 함께 제시됨
5. 사용자가 작업 결과에서 반드시 넣어 달라고 요청함

반복 횟수만으로 중심을 정하지 않는다. 단순 말버릇과 실제 강조를 구분한다.

## 3. 판단 후보·중심 의도·명확도 잠금

반복 묶음과 후반 정정에서 가능한 중심 판단을 최대 3개까지 적는다. 후보 수를 채우기 위해 같은 뜻을 나누지 않는다.

```text
판단 후보 1:
판단 후보 2:
판단 후보 3:
```

각 후보에 대해 다음을 확인한다.

- 원문에 실제 문제·관찰·경험이 있는가
- 다른 제목과 결론을 요구하는가
- 글 전체를 지탱할 재료가 있는가
- 작업 지시를 판단으로 잘못 읽지 않았는가

그다음 현재 가장 강한 후보로 다음 두 문장을 내부적으로 완성한다.

```text
이 글은 [실제 문제·관찰]을 통해 [글쓴이의 현재 판단]을 말한다.

[예상 독자]가 [기존에 어렵게 보던 것]을 [새 판단 기준]으로 다시 보게 하는 글이다.
```

검사 질문:

- 제목이 이 판단을 직접 받는가
- 도입이 실제 문제나 관찰에서 시작하는가
- 사례가 판단을 증명하는가
- 후반부가 기능 목록으로 흩어지지 않는가
- 마지막이 요약이 아니라 현재 판단·달라진 행동·현재 상태에서 멈추는가

### 판단 명확도

| 상태 | 기준 | 기본 동작 |
|---|---|---|
| `high` | 한 판단이 반복·후반 정정·장면으로 뚜렷하게 지지됨 | 직접 완성 가능 |
| `medium` | 우세한 판단은 있으나 다른 방향도 별도 제목과 결론을 가짐 | 긴 글·대표 글이면 판단 파일럿 |
| `low` | 후보 우열이 없거나 선택에 따라 경험 의미가 달라짐 | 최대 3개 파일럿 또는 한 번의 질문 |

명확도는 글의 완성도 점수가 아니라 방향 선택의 확신이다. 사용자가 직접 중심 판단을 지정하면 원문과 충돌하지 않는 범위에서 `judgment.selected`로 잠근다.

## 4. 주제 수 판정

### 한 글로 묶는 경우

- 여러 판단이 하나의 원인과 결론으로 이어짐
- 사례가 달라도 같은 중심 판단을 증명함
- 독자와 글의 목적이 같음

### 별도 글로 나누는 경우

- 각 판단이 서로 다른 제목과 결론을 요구함
- 독자나 채널이 달라짐
- 한 주제를 빼도 다른 글이 독립적으로 완성됨
- 기능 설명, 사용법, 개인화 방법이 각각 충분한 분량을 가짐

주제가 여러 개면 다음으로 분리한다.

```text
가장 강한 주제:
별도 글 후보:
메모로만 남길 내용:
```

## 5. Source Brief 템플릿

```yaml
source_type: unstructured_voice_or_spoken_message
requested_output: general_column

judgment:
  candidates: []
  selected: ""
  confidence: high | medium | low
  selected_pilot_id: ""
  approved_opening_direction: ""
  approved_ending_direction: ""
  rejected_directions: []
  merge_constraints: []

length_profile:
  mode: short_voice_column | standard_column | channel_defined
  target: 1300-1500_chars_excluding_title

extracted_topic: ""
problem_or_observation: ""
reader: ""
article_role: ""

owned_material:
  experiences: []
  observations: []
  examples: []
  exact_phrases_to_preserve: []

editorial_constraints:
  requested_tone: []
  requested_structure: []
  requested_case_density: ""
  exclusions: []

transcription:
  corrected_with_context: []
  needs_confirmation: []

research:
  needed: false
  claims_to_verify: []
  verified_claims: []
  limitations: []
  source_links: []
  checked_at: ""


review:
  level: basic | publish   # basic=역점검만, publish=문체 3층 재통과

routing:
  execution: voice-note-writing
  handoff: none
  mode: direct-completion | judgment-pilot | evidence-assisted
  final_writer: voice-note-writing
  canonical_sources:
    - "{hong-voice-reference BASE}/references/01-voice.md"
    - "{hong-voice-reference BASE}/references/02-glossary.md"
    - "{hong-voice-reference BASE}/references/03-anti-traces.md"

followup_topics: []
excluded_as_filler: []
```

빈 슬롯을 채우기 위해 경험·사례·독자를 만들지 않는다. 자료가 없으면 빈 배열로 남기거나 문제 상황 중심의 개념형 글로 전환한다. `research.needed: false`는 의도적 생략이므로 미완료로 보지 않는다.

채널이 명시된 경우에만 `handoff`와 `final_writer`를 해당 채널 스킬로 바꾼다. 채널 미지정·범용 칼럼·일반 글은 `execution: voice-note-writing`, `handoff: none`, `final_writer: voice-note-writing`을 유지한다. 판단 파일럿이 열렸으면 선택 전 `final_writer`가 있더라도 전체 원고를 생성하지 않는다.

## 6. 사용자 공개용 압축 형식

분석 공개 요청이 있을 때만 다음 형식으로 줄여 보여준다.

```text
추출한 주제: …
판단 후보: … (선택이 필요할 때만)
선택된 중심 판단: …
실행 모드·길이: …
보존한 경험·표현: …
분리한 작업 지시: …
확인할 주장: … (있을 때만)
후속 글감: … (있을 때만)
확인이 필요한 표현: … (있을 때만)
```

내부 코드, 가중치, YAML 전체는 사용자가 요구하지 않으면 노출하지 않는다.
