#!/usr/bin/env python3
"""voice-note-writing 스킬의 구조·계약을 정적 검증한다.

문체 기준은 외부 스킬 hong-voice-reference가 소유한다.
이 검증기는 (1) 워크플로우 참조 파일 존재, (2) 정본 호출이 실제 실행 절에
박혀 있는지, (3) 옛 사본 경로가 SKILL.md와 references/·scripts/에 남아 있는지,
(4) frontmatter version과 changelog 최신 항목이 같은지, (5) 길이 프로필 숫자가
count.py와 문서에서 일치하는지, (6) 용어 충돌·미설치 스킬 인계가 남았는지를 본다.

의존 스킬 설치 여부는 패키징 배치에 따라 달라지므로 오류가 아니라 경고로 낸다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_DIR / "SKILL.md"

WORKFLOW_REFS = [
    "references/analysis-schema.md",
    "references/general-column-composition.md",
    "references/judgment-pilot.md",
    "references/public-introduction-mode.md",
    "references/research-gate.md",
    "references/speech-correction-dictionary.md",
    "references/verification-protocol.md",
    "references/worked-examples.md",
    "references/output-modes.md",
    "references/modes-optional.md",
    "references/common-pitfalls.md",
    "references/changelog.md",
]

# 문체 기준은 hong-voice-reference 스킬이 소유한다. 이 스킬에는 사본을 두지 않는다.
STYLE_REFS = []

# 헤딩 단위로 존재해야 하는 필수 절 (절을 통째로 삭제하면 잡힌다)
REQUIRED_HEADINGS = [
    "읽기 규칙",
    "Step 4.5",
    "문체 기준 로드",
    "Step 9",
    "Step 10",
    "문체 최소 카드",
    "Verification Checklist",
]

# 본문 어디에도 남아 있으면 안 되는 옛 경로·서술
STYLE_FORBIDDEN = [
    "references/hong-voice.md",
    "references/hong-expression-glossary.md",
    "references/anti-ai-traces.md",
    "references/hong-positive-examples.md",
    "/opt/data/obsidian-vault",
    "문체 기준 3종 (내장)",
    "문체 기준 3종을",
    "문체 기준 3종 사본",
]

# 파일로 남아 있으면 안 되는 사본
STYLE_COPY_PATHS = [
    "references/hong-voice.md",
    "references/hong-expression-glossary.md",
    "references/anti-ai-traces.md",
    "references/hong-positive-examples.md",
]


def _section(text: str, heading_fragment: str):
    """헤딩 한 개의 본문만 잘라 돌려준다. 없으면 None."""
    m = re.search(rf"^(#{{1,4}})\s*.*{re.escape(heading_fragment)}.*$", text, re.M)
    if not m:
        return None
    level = len(m.group(1))
    start = m.end()
    nxt = re.search(rf"^#{{1,{level}}}\s", text[start:], re.M)
    return text[start:start + nxt.start()] if nxt else text[start:]


def _is_changelog_line(body: str, pos: int) -> bool:
    """변경 이력 서술이면 잔재로 세지 않는다."""
    line_start = body.rfind("\n", 0, pos) + 1
    line_end = body.find("\n", pos)
    line = body[line_start:line_end if line_end != -1 else len(body)]
    return bool(re.match(r"\s*-\s*(v?\d+\.\d+\.\d+|\d단계|미해소|이전)", line))

CONTRACT_TERMS = [
    "direct-completion",
    "judgment-pilot",
    "evidence-assisted",
    "short_voice_column",
    "standard_column",
    "channel_defined",
    "selected_pilot_id",
    "rejected_directions",
    "claims_to_verify",
]

SCHEMA_KEYS = ["judgment:", "length_profile:", "research:", "review:", "final_writer:"]

# 옛 명칭·경로 잔재. 하나라도 남으면 정리가 끝나지 않은 것으로 본다.
FORBIDDEN = [
    "/opt/data",
    "write-voice",
    "delegate_task",
    "metadata:\n  hermes",
    "01 매일 루틴 글쓰기",   # 저장 위치는 사용자가 지정한다
    "overlap",              # 기존 글 중복 관문은 v2.3.0에서 삭제됐다
    "write-brunch",         # 현재 환경에 설치되지 않은 스킬로 인계하지 않는다
    "selected_judgment",    # Source Brief 필드명은 judgment.selected로 통일됐다
    "실행 모드 한 줄",        # 문체 기준 한 줄과 실행 모드(direct-completion 계열)를 섞지 않는다
    "목표 중앙값의 80%",      # 하한보다 낮아 발동하지 않던 규칙. v3.3.0에서 제거
    "수정 전 N.N",           # 신규 생성 원고는 §11에 따라 1회 계량한다. v3.4.0
    "세 층을 순서대로 읽는다",  # 읽기는 일괄, 적용만 순서. v3.4.0
]


def frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("frontmatter 시작 구분자 없음")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("frontmatter 종료 구분자 없음")
    block = text[4:end]
    name = ""
    description = ""
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value in {">", ">-", "|", "|-"}:
                parts: list[str] = []
                for following in lines[index + 1:]:
                    if following.startswith("  "):
                        parts.append(following.strip())
                    else:
                        break
                description = " ".join(parts)
            else:
                description = value.strip("\"'")
    return name, description


def _profiles_from_count_py() -> dict[str, tuple[int, int, int]]:
    """길이 프로필의 단일 기준은 count.py다. 문서는 이 값을 인용만 한다."""
    src = (SKILL_DIR / "scripts/count.py").read_text(encoding="utf-8")
    found = {}
    for name, low, high, target in re.findall(
            r'"(\w+)":\s*\((\d+),\s*(\d+),\s*(\d+)\)', src):
        found[name] = (int(low), int(high), int(target))
    return found


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    text = SKILL_FILE.read_text(encoding="utf-8")
    description = ""

    try:
        name, description = frontmatter(text)
        if name != "voice-note-writing":
            errors.append(f"스킬명 불일치: {name!r} (기대값 voice-note-writing)")
        if not 0 < len(description) <= 1024:
            errors.append(f"description 길이 범위 초과: {len(description)}자 (1~1024)")
        if "음성 글쓰기" not in description:
            errors.append("description에 호출명 '음성 글쓰기' 없음")
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))

    if len(text) > 100_000:
        errors.append("SKILL.md가 100,000자를 넘음")

    for relative in WORKFLOW_REFS + STYLE_REFS:
        if not (SKILL_DIR / relative).is_file():
            errors.append(f"필수 파일 없음: {relative}")

    # (1) 필수 절이 헤딩 단위로 존재하는가 — 절을 통째로 지우면 잡힌다
    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^#{{1,4}}\s*{re.escape(heading)}", text, re.M):
            errors.append(f"필수 절 없음: {heading!r}")

    # (2) 정본 호출 지시가 '문체 기준 로드' 절 안에 실제로 있는가
    load_sec = _section(text, "문체 기준 로드")
    if load_sec is None:
        errors.append("'문체 기준 로드' 절을 찾지 못함")
    else:
        for token in ("hong-voice-reference", "Base directory",
                      "01-voice.md", "02-glossary.md", "03-anti-traces.md"):
            if token not in load_sec:
                errors.append(f"'문체 기준 로드' 절에 {token!r} 없음")

    # (3) Step 9가 3층을 순서대로 적용하라고 지시하는가
    step9 = _section(text, "Step 9")
    if step9 is None:
        errors.append("'Step 9' 절을 찾지 못함")
    else:
        for token in ("hong-voice-reference", "01-voice.md", "02-glossary.md", "03-anti-traces.md"):
            if token not in step9:
                errors.append(f"Step 9에 {token!r} 없음")

    # (4) 폴백 카드 절이 실제로 존재하는가 (언급이 아니라 절)
    if not re.search(r"^#{1,4}\s*문체 최소 카드", text, re.M):
        errors.append("'문체 최소 카드' 절이 헤딩으로 존재하지 않음")

    # (5) 옛 사본 경로 잔존 — SKILL.md + references/ + scripts/ 전부 스캔
    scan_files = [SKILL_FILE] + sorted((SKILL_DIR / "references").glob("*.md"))
    for path in scan_files:
        body = path.read_text(encoding="utf-8")
        for token in STYLE_FORBIDDEN:
            for m in re.finditer(re.escape(token), body):
                line = body[:m.start()].count("\n") + 1
                if _is_changelog_line(body, m.start()):
                    continue
                errors.append(f"옛 문체 경로 잔존: {path.name}:{line} {token!r}")

    # (6) 삭제 대상 사본이 파일로 남아 있는가
    for relative in STYLE_COPY_PATHS:
        if (SKILL_DIR / relative).is_file():
            errors.append(f"삭제해야 할 문체 사본이 남아 있음: {relative}")

    # (7) 의존 대상 스킬이 설치되어 있고 필요한 파일을 갖고 있는가
    dep = SKILL_DIR.parent / "hong-voice-reference"
    if not dep.is_dir():
        warnings.append("의존 스킬을 형제 경로에서 찾지 못함: hong-voice-reference (패키지 배치에 따라 정상일 수 있다. 설치 전에는 폴백으로만 동작)")
    else:
        for f in ("01-voice.md", "02-glossary.md", "03-anti-traces.md",
                  "04-examples.md", "05-corrections.md"):
            if not (dep / "references" / f).is_file():
                errors.append(f"의존 스킬 파일 없음: hong-voice-reference/references/{f}")

    # 스크립트 2종
    for script in ["scripts/validate.py", "scripts/count.py"]:
        if not (SKILL_DIR / script).is_file():
            errors.append(f"필수 스크립트 없음: {script}")

    # (8) frontmatter version과 changelog 최신 항목이 같은가
    version = ""
    m = re.search(r"^\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", text, re.M)
    if not m:
        errors.append("frontmatter에 metadata.version 없음")
    else:
        version = m.group(1)
        changelog_path = SKILL_DIR / "references/changelog.md"
        if changelog_path.is_file():
            cl = changelog_path.read_text(encoding="utf-8")
            head = re.search(r"^-\s*v([0-9]+\.[0-9]+\.[0-9]+)\s*변경", cl, re.M)
            if not head:
                errors.append("changelog.md에서 최신 버전 항목을 찾지 못함")
            elif head.group(1) != version:
                errors.append(
                    f"버전 불일치: frontmatter {version} vs changelog 최신 {head.group(1)}")

    # (9) 길이 프로필 숫자가 count.py와 문서에서 일치하는가
    profiles = _profiles_from_count_py()
    for expected in ("short_voice_column", "standard_column"):
        if expected not in profiles:
            errors.append(f"count.py PROFILES에 {expected} 없음 또는 target 미정의")
    gcc = SKILL_DIR / "references/general-column-composition.md"
    gcc_text = gcc.read_text(encoding="utf-8") if gcc.is_file() else ""
    for name, (low, high, target) in profiles.items():
        for token in (f"{target:,}자", f"{low:,}~{high:,}"):
            if token not in text and token not in gcc_text:
                errors.append(f"분량 표기 불일치: {name}의 {token!r}이 문서에 없음")
        stale = f"{(low + high) // 2:,}"
        if stale != f"{target:,}" and stale in text:
            errors.append(f"분량 표기 잔재: {name}의 옛 산술 중앙값 {stale!r}이 SKILL.md에 남음")

    # (10) 기본 경로에서 발동해야 하는 규칙이 SKILL.md에 있는가
    if "저장하기 / 조금 고치기" not in text:
        errors.append("저장 3선택지 규칙이 SKILL.md 기본 경로에 없음")
    if "문체 기준 표기" not in text:
        errors.append("'문체 기준 표기' 절 이름이 SKILL.md에 없음")
    if "한 번에 읽는다" not in text:
        errors.append("문체 3층 일괄 읽기 지시가 SKILL.md에 없음")
    if "현재 N.N (등급)" not in text:
        errors.append("AI 흔적 지수 1회 계량 형식(`현재 N.N (등급)`)이 SKILL.md에 없음")

    combined = "\n".join(
        (SKILL_DIR / relative).read_text(encoding="utf-8")
        for relative in WORKFLOW_REFS
        if (SKILL_DIR / relative).is_file()
    )
    for term in CONTRACT_TERMS:
        if term not in text and term not in combined:
            errors.append(f"계약어 누락: {term}")

    schema_path = SKILL_DIR / "references/analysis-schema.md"
    if schema_path.is_file():
        schema = schema_path.read_text(encoding="utf-8")
        for key in SCHEMA_KEYS:
            if key not in schema:
                errors.append(f"analysis-schema 슬롯 누락: {key}")

    pilot_path = SKILL_DIR / "references/judgment-pilot.md"
    if pilot_path.is_file():
        pilot = pilot_path.read_text(encoding="utf-8")
        if "전체 원고를 쓰지 않고 사용자 선택에서 멈춘다" not in pilot:
            errors.append("판단 파일럿 정지 관문 문구 없음")

    # SKILL.md와 워크플로우 참조 파일에는 Hermes 잔재가 없어야 한다.
    # 변경 이력(changelog.md)은 전환 기록이므로 구명칭이 등장해도 잔재로 세지 않는다.
    HISTORY_FILES = {"references/changelog.md"}
    body_text = text.split("## 원본 이력", 1)[0]
    scan = {"SKILL.md": body_text}
    for relative in WORKFLOW_REFS:
        if relative in HISTORY_FILES:
            continue
        path = SKILL_DIR / relative
        if path.is_file():
            scan[relative] = path.read_text(encoding="utf-8")
    for label, body in scan.items():
        for token in FORBIDDEN:
            if token in body:
                errors.append(f"전환 잔재 발견: {label}에 {token!r}")

    checks = {
        "version": version,
        "skill_chars": len(text),
        "description_chars": len(description),
        "workflow_refs": sum((SKILL_DIR / r).is_file() for r in WORKFLOW_REFS),
        "required_headings": sum(bool(re.search(rf"^#{{1,4}}\s*{re.escape(h)}", text, re.M)) for h in REQUIRED_HEADINGS),
        "dep_skill": (SKILL_DIR.parent / "hong-voice-reference").is_dir(),
        "contract_terms": sum(t in text or t in combined for t in CONTRACT_TERMS),
    }
    print(json.dumps({"ok": not errors, "checks": checks, "errors": errors,
                      "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
