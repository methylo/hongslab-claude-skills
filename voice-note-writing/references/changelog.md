# 변경 이력

> `voice-note-writing` 버전 기록. **실행 중에는 읽지 않는다.**
> 스킬을 고칠 때 이전 결정을 확인하려는 목적으로만 연다.
> 최신 항목이 위에 온다.

---

- v3.5.1 변경(2026-09-23): 공개 배포 준비. 라이선스를 `CC-BY-NC-4.0`에서 `MIT`로 변경(`hongslab-claude-skills` 저장소 기준에 맞춤). `modes-optional.md`의 교정 경로가 v3.0.0 외부화 이전의 볼트 절대 경로(`04 공용 자료/...`)를 가리키던 것을 `hong-voice-reference` 수정 제안으로 교체. 의존 스킬 v1.6.0 기준으로 교차 참조(§11 지수·§5-1 판정·§3-1 규격화 금지)와 승인 원문 실측(18개 문단, 중앙값 174자)을 재확인했다

- v3.5.0 변경(2026-09-22): 합성 전사문으로 Step 1~10을 순차 실행해 점검하고 개선. 1차 초안이 688자로 나와 목표 1,400자의 49%에 그쳤다. v2.1.0 이후 changelog에 기록만 되고 원인이 특정되지 않던 회귀가 재현됐다. 원인은 둘이었다. (1) 초안 도중과 직후에 분량 신호가 없어 Step 10 역점검에서야 미달을 안다. (2) `count.py`의 `gap`이 하한까지의 거리여서 그만큼 채우면 매번 하한에 착지하고 `near_floor`가 다시 켜진다. 실측에서 688 → 1,193 → 1,265자로 세 번 돌고도 미달이었다. `count.py`에 문단 진단(`paragraphs.count`·`median`·`sizes`·`thin`·`thin_run`)과 `to_target`을 추가하고, 승인 원문 18개 문단 실측(중앙값 174자, 사분범위 87~244자)을 기준값으로 문서화했다. Step 8은 1차 초안 직후 측정을 의무화하고 보강량 기준을 `gap`에서 `to_target`으로 바꿨다. 100자 미만 문단이 3개 연속이면 전개 누락으로 판정한다. 함께 고친 것: Step 1의 작업본을 파일이 아닌 실행 맥락으로 명시해 저장 금지 계약과의 충돌 해소, Step 2 분류표에 `군더더기`를 추가해 `analysis-schema.md` 8종과 일치시킴, Step 4.5의 `중앙값 1,400 겨냥` 용어 잔재 제거와 `바로 완성` 요청 시 대기하지 않는다는 규칙 명시, Step 7에서 `direct-completion`은 48줄 YAML을 전량 채우지 않고 필수 슬롯만 채우도록 제한

- v3.4.0 변경(2026-09-22): 실행 시간 축소. 측정된 원인은 필수 입력 62,174자(산출물 1,400자 대비 44배), 최소 12회의 직렬 왕복, 원고 3회 이상 전면 재작성이었다. 문체 1·2·3층을 Step 9 진입 시 한 번에 읽도록 바꿔 읽기 왕복 3회를 1회로 축소(층 순서는 적용 순서이지 읽기 순서가 아님을 명시). AI 흔적 지수를 정본 `03-anti-traces.md` §11의 신규 생성 규칙에 맞춰 `현재 N.N (등급)` 1회 계량으로 교체 — 기존 2회 계량 형식은 전수 스캔을 두 번 돌리면서 정본과도 어긋났다. `worked-examples.md`를 읽기 규칙 표에서 조건부로 되돌려 본문 서술과 일치시킴. Step 10 분량 측정의 파일 쓰기·실행·삭제 3회 왕복을 한 명령으로 통합. `validate.py`에 회귀 가드 4종 추가(2회 계량 형식, 순차 읽기 문구, 일괄 읽기 지시 존재, 1회 계량 형식 존재). `02-glossary.md`(11,275자) 전량 로드는 유지했다. 정본 `00-caller-blocks.md` §A가 단어 선택 단계 필수로 규정하고 있어 이 스킬 단독으로 낮추면 계약 위반이며, 줄이려면 `hong-voice-reference`를 함께 고쳐야 한다

- v3.3.0 변경(2026-09-22): 분량 계약의 단일 기준을 `count.py`로 모음. `count.py`가 본문 뒤 메타 줄(`문체 기준:`·`AI 흔적 지수:`·`확인 메모` 블록)을 제외하도록 고쳐 최대 60여 자가 본문으로 계산되던 오류 제거, 프로필에 `target`(short 1,400 / standard 2,400)을 상수로 넣어 SKILL.md의 2,400과 스크립트 산술 중앙값 2,500의 불일치 해소, 출력 키 `midpoint`를 `target`으로 교체하고 `meta_lines_excluded` 추가. 발동 불가였던 `목표 중앙값의 80%` 규칙을 `verdict`·`near_floor` 기준으로 교체(1,400×0.8=1,120은 하한 1,300보다 낮아 항상 거짓이었다). `near_floor`를 계약 위반이 아닌 보강 신호로 재정의해 체크리스트가 1,300~1,500 계약을 1,350~1,500으로 좁히던 문제 수정. 문체 기준 한 줄의 이름을 `실행 모드 표기`에서 `문체 기준 표기`로 바꿔 `direct-completion` 계열 모드명과의 충돌 해소. 기본 경로에서 읽히지 않던 저장 3선택지 규칙을 `modes-optional.md`에서 `SKILL.md` 기본 출력 절로 이동. Source Brief 필드명을 `judgment.*`로 통일하고 `approved_opening_direction`·`approved_ending_direction`을 템플릿에 추가. Step 7.5-A의 4개 조건 중복을 Step 4.5 참조로 교체. 미설치 스킬 `write-brunch`를 인계 표에서 제외하고 인계 전 설치 확인 규칙 추가. `count.py` 호출을 `{SKILL_BASE}` 절대 경로로 교체. Linked References의 `실패 8종`을 18종으로 정정. 체크리스트에 AI 흔적 지수 한 줄과 저장 선택지 항목 추가. `validate.py`에 버전 정합성(frontmatter ↔ changelog), 분량 숫자 정합성(`count.py` ↔ 문서), 용어 충돌 검사를 추가하고 의존 스킬 미설치를 오류에서 경고로 분리

- v3.2.0 변경(2026-08-01): 실행당 컨텍스트 부하 축소. SKILL.md 49,464B → 33,315B(33% 감소). 원본 이력을 `changelog.md`로, 조건부 절 6개(부분 개선·채널 인계·저장 규칙·선택지 질문·Personalization Loop·Change Verification)를 `modes-optional.md`로, 판단 파일럿·분석 공개·주제 선택 출력 형식을 `output-modes.md`로, Common Pitfalls를 `common-pitfalls.md`로 분리. 공개 소개 글 모드는 진입 조건 한 줄만 남김. `읽기 규칙` 절 신설(조건 없이 미리 읽지 않는다). **Step 4.5 통합 관문 신설** — direct-completion 조건 충족 시 Step 5·7.5를 확인 1회로 묶어 왕복 3회를 1회로 축소. Workflow 상세(Step 1~10)와 골격(계약·우선순위·폴백·체크리스트)은 분리하지 않았다. 지시가 references로 빠지면 단계를 건너뛸 위험이 있어 품질 우선으로 남겼다

- v3.1.0 변경(2026-08-01): 전환 미완 4건 수정. `general-column-composition.md` §5가 삭제된 절·파일을 가리키던 것을 정본 호출 절차로 재작성(Step 8이 반드시 읽는 파일이라 초안 단계가 없는 경로로 유도되고 있었다), Common Pitfalls 8항·`verification-protocol.md` 3곳·`analysis-schema.md` canonical_sources 경로 갱신. 분량 예산의 문단 단위 하한 강제를 총량 기준으로 바꿔 `01-voice` §3-1과의 자기모순 해소. `03-anti-traces` §11 지수 한 줄을 출력 금지 예외로 명시. 폴백 카드에 볼드 조항 추가. 채널 인계 시 문체 3층 책임이 이 스킬에 있음을 명시(인계 대상 5개 스킬은 정본을 모른다). 판단 파일럿 후보에 1층 선적용 규칙 신설. `validate.py`를 토큰 존재 검사에서 구조 검사로 교체 — 필수 절 헤딩 존재, `문체 기준 로드`·Step 9 절 내부의 호출 지시, references 전체 옛 경로 스캔, 의존 스킬 설치 여부를 본다. 파손 시나리오 3종(Step 9 삭제·폴백 카드 삭제·옛 경로 주입)으로 탐지를 확인했다

- v3.0.0 변경(2026-08-01): 문체 기준 사본 4종(`hong-voice.md`·`hong-expression-glossary.md`·`anti-ai-traces.md`·`hong-positive-examples.md`, 합계 64.7KB)을 삭제하고 `hong-voice-reference` 스킬 호출로 전환. `문체 기준 3종 (내장)` 절을 `문체 기준 로드 (외부 정본 호출)`로 교체, 실행 모드 한 줄 표기 필수화, 폴백 최소 카드 신설. `analysis-schema.md` canonical_sources, `speech-correction-dictionary.md`, `verification-protocol.md` 참조 경로 갱신. `validate.py`의 사본 존재 검사를 정본 호출 문구 검사(`STYLE_CALL_TERMS`)와 옛 경로 잔존 검사(`STYLE_FORBIDDEN`)로 교체

## 원본 이력

- 원본: `voice-note-writing` v1.3.1 (Hermes Agent 환경). 스킬명을 그대로 승계한다.

- v2.4.0 변경(2026-07-31): 스킬명을 `write-voice`에서 원본 이름 `voice-note-writing`으로 되돌림. 사용자 호출명 `음성 글쓰기`와 워크플로우는 변경 없음

- v2.3.0 변경(2026-07-31): 저장 위치를 스킬에서 제거하고 사용자 지정 경로로만 저장하도록 변경, 볼트를 읽어야 성립하던 기존 글 중복 관문 삭제(사용자가 글을 직접 붙여 준 경우만 처리), `research-and-overlap-gate.md`를 `research-gate.md`로 축소, `선택지를 묻는 방법` 절 신설(`AskUserQuestion` 미지원 환경 대체 규칙)

- v2.2.1 변경(2026-07-31): 정리 후 스모크 테스트에서 드러난 5건 수정. 문체 3종이 근거로 참조하던 `홍작가_긍정원문사례`를 내장(`hong-positive-examples.md`)하고 위키링크를 내장 경로로 치환, `general-column-composition.md`의 옛 절 이름 참조 수정, Step 7의 검토 수준 값을 본문에 정의, 분량 예산을 나눗셈 공식으로 교체(문단 수 × 문단당 글자 수가 프로필 범위를 벗어나던 오류), 충족 불가능한 작업 지시 처리 절차 추가

- v2.2.0 변경(2026-07-31): 실행에서 한 번도 작동하지 않은 사본 드리프트 검사(`style_drift.py`·`style-sources.json`) 삭제, description과 중복되던 `사용하지 않는 경우` 표를 진입 후 되돌리는 2건으로 축소, 정의 없이 쓰이던 검토 수준 L0~L3를 `basic`·`publish`로 교체, 스킬이 자기 파일을 고칠 수 있다고 적힌 Personalization Loop 수정, 연결되지 않던 `worked-examples.md`를 Step 2에서 읽도록 연결, Verification Checklist 17항을 9항으로 압축

- v2.1.0 변경(2026-07-31): 회귀 검증 4갈래 실행 후 개정. 자동 판정 신호를 description에 명시, 분량 예산(문단 수·문단당 글자 수·허용 확장 4종) 신설, `count.py` 추가, `evidence-assisted` 확인 메모 형식 고정, 저장 위치를 오늘 글쓰기와 루틴 루트로 분리

- v2.0.0 변경: 스킬명 `write-voice`, Hermes 전용 frontmatter 제거, 볼트 절대 경로 3개를 내장 사본으로 치환, `clarify`·`delegate_task`를 `AskUserQuestion`·Skill 호출로 치환, 예약 글감 추천 모드와 과거 결과물 이관 모드 제외(세션 기록 의존), Step 4·7 중복 서술을 참조 파일로 이관

### 검증 이력 (2026-07-31)

| 갈래 | 결과 | 확인 내용 |
|---|---|---|
| 기본 작업만 | 통과 | 칼럼 미작성, 작업 지시 2건 분리, 전사 불확실성 질의 |
| 직접 완성 | 통과 | `direct-completion`, 1,375자, 확인 질문 0건, 파일 생성 0건 |
| 판단 파일럿 | 통과 | 후보 3개, 선택 전 정지, 평가표 미부착 |
| 근거 보강 | 통과 | `claims_to_verify` 잠금, 공식 가격표 1차 출처 확인, 미확인 항목은 체감 표현 유지 |

관찰된 회귀: 1차 초안이 목표 분량의 절반에서 끝나고 뒤에서 덧붙이는 경로가 반복됐다. 문단당 글자 수 예산으로 대응했으며, 다음 검증에서 1차 초안 충족률을 다시 확인한다.
