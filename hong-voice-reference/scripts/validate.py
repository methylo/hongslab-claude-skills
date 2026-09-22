#!/usr/bin/env python3
"""hong-voice-reference 정본 무결성 검사기.

이 스킬은 다른 글쓰기·편집 스킬이 호출하는 문체 정본이다.
사본 난립과 조항 모순이 실제로 발생했던 이력이 있어, 갱신할 때마다
아래를 정적으로 검사한다.

  1. 필수 파일 존재
  2. 각 파일 머리의 버전·갱신일 표기와 SKILL.md version 일치
  3. 파일명·절 번호 참조가 실재하는 대상을 가리키는가
  4. 알려진 내부 모순 재발 여부 (회귀 검사)
  5. 우선순위 사다리에 04-examples가 등재되어 있는가
  6. 정본 자신이 자기 금지어를 쓰고 있지 않은가

사용: python3 scripts/validate.py
종료코드: 0 통과 / 1 실패
"""

import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"

REQUIRED_REFS = [
    "00-caller-blocks.md",
    "01-voice.md",
    "02-glossary.md",
    "03-anti-traces.md",
    "04-examples.md",
    "05-corrections.md",
]

# SKILL.md에 있어야 하는 절 (헤딩 단위)
REQUIRED_HEADINGS = [
    "파일과 읽는 시점",
    "적용 순서",
    "우선순위",
    "절대 규칙",
    "갱신 절차",
    "무결성 점검",
    "변경 이력",
]

# 회귀 검사 — 고쳤던 모순이 되살아났는지 본다
REGRESSIONS = [
    # (파일, 패턴, 설명)
    ("references/02-glossary.md", r"→\s*홍작가_글쓰기표현사전",
     "우선순위 사다리에 옛 파일명이 되살아남"),
    ("references/02-glossary.md", r"→\s*anti-ai-traces\s*$",
     "우선순위 사다리에 옛 파일명이 되살아남"),
    ("references/01-voice.md", r"\(18~22단어\)",
     "3단 배치 단어 수 구간 겹침이 되살아남"),
    ("references/01-voice.md", r"단문\(15단어 이하\)과 중문\(18~25단어\)",
     "단문·중문 사이 16~17 공백이 되살아남"),
    ("references/01-voice.md", r"\| 단문 \| 15어절 이하",
     "실측과 어긋나는 15어절 단문 상한이 되살아남"),
    ("references/01-voice.md", r"승인 원문 100문장을 실측해 정했다",
     None),  # 존재해야 하는 문장 — 아래에서 반전 처리
    ("references/01-voice.md", r"기준의 이동을 통해",
     "한 문장 정의가 금지어 `~을 통해`를 다시 씀"),
    ("references/03-anti-traces.md", r"^> 보강 참고: 전체 분류 체계",
     "출처 선행어가 다시 빠짐"),
]

# 정본 본문(예시·금지어 목록 제외)이 자기 금지어를 쓰는지
SELF_BAN = ["혁신적인", "획기적인", "완벽한", "강력한", "효과적으로"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def strip_examples(text: str) -> str:
    """코드블록·표·❌✅ 예시·금지어 목록 줄을 제거한 '정본의 산문'만 남긴다."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    keep = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith(("|", ">", "*", "-", "#")):
            continue
        if "❌" in s or "✅" in s:
            continue
        keep.append(s)
    return "\n".join(keep)


def main() -> int:
    errors, warnings = [], []

    # ── 1. 필수 파일 ──────────────────────────────
    if not SKILL_FILE.is_file():
        print(json.dumps({"ok": False, "errors": ["SKILL.md 없음"]}, ensure_ascii=False))
        return 1
    skill = read(SKILL_FILE)

    for name in REQUIRED_REFS:
        if not (REF_DIR / name).is_file():
            errors.append(f"필수 파일 없음: references/{name}")

    extra = {p.name for p in REF_DIR.glob("*.md")} - set(REQUIRED_REFS)
    for name in sorted(extra):
        warnings.append(f"목록에 없는 파일: references/{name}")

    # ── 2. 버전·갱신일 표기 ────────────────────────
    m = re.search(r"^version:\s*(\S+)", skill, re.M)
    version = m.group(1) if m else None
    if not version:
        errors.append("SKILL.md frontmatter에 version 없음")

    for name in REQUIRED_REFS:
        path = REF_DIR / name
        if not path.is_file():
            continue
        head = read(path)[:400]
        vm = re.search(r"`v(\d+\.\d+\.\d+)`", head)
        dm = re.search(r"갱신 (\d{4}-\d{2}-\d{2})", head)
        if not vm:
            errors.append(f"버전 표기 없음: {name}")
        elif version and vm.group(1) != version:
            errors.append(f"버전 불일치: {name} v{vm.group(1)} ≠ SKILL.md v{version}")
        if not dm:
            errors.append(f"갱신일 표기 없음: {name}")

    # ── 3. 파일명·절 번호 참조 ─────────────────────
    sections = {}
    for name in REQUIRED_REFS:
        path = REF_DIR / name
        if not path.is_file():
            continue
        body = read(path)
        nums = set()
        for mm in re.finditer(r"^##\s*(\d+)[\.\s]", body, re.M):
            nums.add(mm.group(1))
        for mm in re.finditer(r"^###\s*(\d+-\d+)[\.\s]", body, re.M):
            nums.add(mm.group(1))
        sections[name] = nums

    targets = [("SKILL.md", skill)] + [
        (n, read(REF_DIR / n)) for n in REQUIRED_REFS if (REF_DIR / n).is_file()
    ]
    for label, body in targets:
        for mm in re.finditer(r"(0[0-5]-[a-z-]+\.md)", body):
            if mm.group(1) not in REQUIRED_REFS:
                errors.append(f"없는 파일 참조: {label} → {mm.group(1)}")
        for mm in re.finditer(r"`?(0[1-5]-[a-z-]+\.md)`?\s*§(\d+(?:-\d+)?)", body):
            f_, sec = mm.group(1), mm.group(2)
            if f_ in sections and sec not in sections[f_]:
                errors.append(f"없는 절 참조: {label} → {f_} §{sec}")
        if "[[" in body:
            errors.append(f"위키링크 잔재: {label}")
        if "/opt/data" in body:
            errors.append(f"볼트 절대 경로 잔재: {label}")

    # ── 4. SKILL.md 필수 절 ────────────────────────
    for h in REQUIRED_HEADINGS:
        if not re.search(rf"^#{{1,4}}\s*.*{re.escape(h)}", skill, re.M):
            errors.append(f"SKILL.md 필수 절 없음: {h!r}")

    # ── 5. 우선순위 사다리에 04 등재 ────────────────
    for label, body in [("SKILL.md", skill),
                        ("02-glossary.md", read(REF_DIR / "02-glossary.md"))]:
        ladder = re.search(r"```text\n(사실·원문.*?)\n```", body, re.S)
        if not ladder:
            errors.append(f"우선순위 사다리를 찾지 못함: {label}")
        elif "04-examples" not in ladder.group(1):
            errors.append(f"우선순위 사다리에 04-examples 미등재: {label}")

    # ── 6. 회귀 검사 ──────────────────────────────
    for rel, pattern, desc in REGRESSIONS:
        path = SKILL_DIR / rel
        if not path.is_file():
            continue
        found = bool(re.search(pattern, read(path), re.M))
        if desc is None:          # 반드시 있어야 하는 문장
            if not found:
                errors.append(f"필수 근거 문장 없음: {rel} — {pattern}")
        elif found:
            errors.append(f"회귀: {rel} — {desc}")

    # ── 7. 정본이 자기 금지어를 쓰는가 ───────────────
    for label, body in targets:
        prose = strip_examples(body)
        for w in SELF_BAN:
            if w in prose:
                warnings.append(f"정본 산문에 금지어: {label} — {w!r}")

    result = {
        "ok": not errors,
        "version": version,
        "checks": {
            "refs": sum((REF_DIR / n).is_file() for n in REQUIRED_REFS),
            "headings": sum(
                bool(re.search(rf"^#{{1,4}}\s*.*{re.escape(h)}", skill, re.M))
                for h in REQUIRED_HEADINGS
            ),
            "regressions_clean": not any(
                bool(re.search(p, read(SKILL_DIR / r), re.M)) != (d is None)
                for r, p, d in REGRESSIONS
                if (SKILL_DIR / r).is_file()
            ),
        },
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
