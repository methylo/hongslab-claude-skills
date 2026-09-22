#!/usr/bin/env python3
"""edit-writing-room 내부 정합성 검사기.

이 스킬은 축(역할·출력·강도)과 조달 규칙이 SKILL.md와 references/ 양쪽에
나뉘어 있다. 한쪽만 고쳐 어긋난 이력이 실제로 있어(3.1.0의 절대 경로 전환 뒤
최종 체크가 '본문으로 넘겼다'로 남아 있던 건), 갱신할 때마다 아래를 정적으로
검사한다.

  1. frontmatter 버전과 변경 이력 최상단 버전 일치
  2. references/ 필수 파일 존재, 본문의 파일 참조가 실재하는가
  3. 축 3종이 SKILL.md에 정의되어 있는가
  4. 조달 규칙이 SKILL.md(보내는 쪽)와 editor-brief.md(받는 쪽)에서 대칭인가
  5. 출력 템플릿에 선행 필드가 있는가
  6. 알려진 회귀 재발 여부

사용: python3 scripts/self-check.py
종료코드: 0 통과 / 1 실패
"""

import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"

REQUIRED_REFS = ["reader-brief.md", "editor-brief.md", "fallback-voice.md"]
AXES = ["역할", "출력", "강도"]
OUTPUT_VALUES = ["제안", "선택반영", "전체반영"]
ROLE_VALUES = ["독자", "편집자", "편집실", "병렬"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main() -> int:
    errors, warnings = [], []

    if not SKILL_FILE.exists():
        print(json.dumps({"ok": False, "errors": ["SKILL.md 없음"]}, ensure_ascii=False))
        return 1
    skill = read(SKILL_FILE)

    # 1. 버전 일치
    m = re.search(r"^version:\s*([0-9.]+)\s*$", skill, re.M)
    fm_ver = m.group(1) if m else None
    if not fm_ver:
        errors.append("frontmatter에 version이 없다")
    hist = re.search(r"^- (\d+\.\d+\.\d+)", skill[skill.find("## 변경 이력"):], re.M)
    hist_ver = hist.group(1) if hist else None
    if fm_ver and hist_ver and fm_ver != hist_ver:
        errors.append(f"frontmatter version({fm_ver})과 변경 이력 최상단({hist_ver})이 다르다")

    # 2. 참조 파일
    for name in REQUIRED_REFS:
        if not (REF_DIR / name).exists():
            errors.append(f"references/{name} 없음")
    # {BASE}/references/... 는 hong-voice-reference 정본의 파일이므로 제외한다
    for ref in set(re.findall(r"(?<!\{BASE\}/)references/([a-z0-9-]+\.md)", skill)):
        if ref.startswith(("0", "1")) and ref not in REQUIRED_REFS:
            continue  # 정본 3층 파일명(01-voice.md 등)
        if not (REF_DIR / ref).exists():
            errors.append(f"SKILL.md가 없는 파일을 참조한다: references/{ref}")

    # 3. 축 정의
    if "## 호출 축 세 가지" not in skill:
        errors.append("축 정의 절(## 호출 축 세 가지)이 없다")
    for ax in AXES:
        if not re.search(rf"^\|\s*{ax}\s*\|", skill, re.M):
            errors.append(f"축 표에 '{ax}' 행이 없다")
    for v in OUTPUT_VALUES:
        if v not in skill:
            errors.append(f"출력 축 값 '{v}'가 SKILL.md에 없다")
    if "역할 = 독자`이면 출력은 `제안`으로 고정" not in skill:
        errors.append("역할=독자의 출력 축 고정 규칙이 없다")

    # 4. 조달 대칭
    editor = read(REF_DIR / "editor-brief.md") if (REF_DIR / "editor-brief.md").exists() else ""
    send = "문체 정본 4층 경로는 넘기지 않는다" in skill
    recv = "문체 정본 4층 경로는 받지 않는다" in editor
    if send != recv:
        errors.append(
            "선택 반영 조달 규칙이 비대칭이다 "
            f"(SKILL.md 보내는 쪽={send}, editor-brief 받는 쪽={recv})"
        )
    if send and "선택 반영 재호출" not in editor:
        errors.append("editor-brief.md에 '선택 반영 재호출' 절이 없다")

    # 4b. 강도별 조달 분기
    if "역할·단계 | 강도" not in skill:
        errors.append("조달표가 강도별로 분기되어 있지 않다")
    if "판정 보류" not in skill or "판정 보류" not in editor:
        errors.append("판정 보류 경로가 SKILL.md와 editor-brief.md 양쪽에 있지 않다")
    if "04-examples를 정본의 호출 규격" not in skill and "4층을 조건부로 두는 이유" not in skill:
        errors.append("04-examples 조건부 조달 근거가 없다")
    if re.search(r"BASE \+ 4개 경로 전부", skill):
        errors.append("회귀: 강도와 무관하게 4개 경로를 전부 넘기는 규칙이 되살아났다")

    # 4c. 도구 연결
    tool = SKILL_DIR / "scripts" / "scan-traces.py"
    if not tool.exists():
        errors.append("scripts/scan-traces.py 없음")
    else:
        src = read(tool)
        if "03-anti-traces.md" not in src:
            errors.append("scan-traces.py가 정본 §10을 파싱하지 않는다")
        for lit in ("중요한 역할을 한다", "급변하는 시대"):
            if lit in src:
                errors.append(f"회귀: 사전 표현('{lit}')이 스크립트에 복사되어 있다")
    if "scan-traces.py" not in skill or "scan-traces.py" not in editor:
        errors.append("scan-traces.py 연결이 SKILL.md와 editor-brief.md 양쪽에 있지 않다")

    # 4d. 정본 운영 보완 (3.5.0)
    if "scripts/validate.py" not in skill or "정본 건강 점검" not in skill:
        errors.append("STEP 0에 정본 건강 점검이 걸려 있지 않다")
    if "점검 실패를 이유로 멈추거나" not in skill:
        errors.append("건강 점검 실패 시 중단 금지 규정이 없다")
    if "교정 카드 적재.md" not in skill:
        errors.append("교정 카드 적재 경로가 STEP 5에 없다")
    if skill.count("교정 카드 적재.md") < 2:
        warnings.append("적재 경로가 교정 카드·거절 패턴 양쪽에 걸려 있는지 확인하라")

    # 5. 선행 필드
    for label, text in (("SKILL.md", skill), ("editor-brief.md", editor)):
        if "선행:" not in text:
            errors.append(f"{label}의 제안 템플릿에 선행 필드가 없다")

    # 6. 회귀 검사
    if "경로가 아니라 본문으로 서브에이전트에 넘겼다" in skill:
        errors.append("회귀: 3.1.0에서 절대 경로로 바꾼 전달 방식이 '본문'으로 되돌아갔다")
    if re.search(r"^\|\s*모드\s*\|\s*독자만", skill, re.M):
        errors.append("회귀: 역할 축이 다시 단일 '모드' 다이얼로 합쳐졌다")
    for v in ROLE_VALUES:
        if v not in skill:
            warnings.append(f"역할 축 값 '{v}'가 본문에 보이지 않는다")

    result = {"ok": not errors, "version": fm_ver, "errors": errors, "warnings": warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
