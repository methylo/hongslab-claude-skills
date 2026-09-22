#!/usr/bin/env python3
"""완성 원고의 제목 제외 본문 글자 수를 세고 길이 프로필 충족 여부를 판정한다.

이 스크립트가 길이 계약의 단일 기준이다. 프로필의 하한·상한·목표치는
여기에서만 정의하고, `SKILL.md`와 `general-column-composition.md`는 이 값을 인용한다.

사용법:
    python3 scripts/count.py 원고.md
    python3 scripts/count.py 원고.md --profile standard_column
    cat 원고.md | python3 scripts/count.py - --profile short_voice_column
    python3 scripts/count.py 원고.md --min 1800 --max 2200

계산 규칙:
- 첫 줄이 `# 제목` 형태이거나 본문과 빈 줄로 분리된 한 줄이면 제목으로 보고 제외한다.
- 본문 뒤에 붙이는 메타 줄(`문체 기준:`, `AI 흔적 지수:`, `확인 메모` 블록)은 세지 않는다.
- 공백·줄바꿈은 세지 않는다. 문장부호는 센다.
- 문단별 글자 수도 함께 돌려준다. 기준값은 `hong-voice-reference/04-examples.md`
  승인 원문 18개 문단 실측이다(중앙값 174자, 사분범위 87~244자).
- 마크다운 표식(#, *, -, >, 인라인 코드 백틱)은 세지 않는다.

`gap`은 하한까지의 거리, `to_target`은 목표치까지의 거리다. 보강할 때는 `to_target`을 채운다.
`gap`만큼만 채우면 매번 하한에 착지해 `near_floor`가 다시 켜진다.

종료 코드 1은 "범위 밖"이라는 뜻이며 실행 오류가 아니다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# (하한, 상한, 목표치). 목표치는 산술 중앙값이 아니라 겨냥할 분량이다.
PROFILES = {
    "short_voice_column": (1300, 1500, 1400),
    "standard_column": (2000, 3000, 2400),
}

# 승인 원문 실측값. 문단이 이보다 크게 짧으면 리듬이 아니라 전개가 빠진 것으로 본다.
PARAGRAPH_FLOOR = 100

# 본문 뒤에 붙는 메타 줄. 원고 분량에 포함하지 않는다.
META_LINE = re.compile(r"^\s*(문체\s*기준\s*:|AI\s*흔적\s*지수\s*:)")
META_BLOCK_HEAD = re.compile(r"^\s*확인\s*메모\s*$")


def split_title(text: str) -> tuple[str, str]:
    lines = text.strip().split("\n")
    if not lines:
        return "", ""
    first = lines[0].strip()
    if first.startswith("#"):
        return first.lstrip("#").strip(), "\n".join(lines[1:])
    # 제목 뒤에 빈 줄이 오고 본문이 이어지는 형태
    if len(lines) > 2 and lines[1].strip() == "" and len(first) <= 60:
        return first, "\n".join(lines[2:])
    return "", text


def strip_meta(body: str) -> tuple[str, int]:
    """본문 뒤 메타 줄을 걷어내고, 제외한 줄 수를 함께 돌려준다."""
    kept: list[str] = []
    dropped = 0
    in_block = False
    for line in body.split("\n"):
        stripped = line.strip()
        if in_block:
            if stripped == "" or stripped.startswith("-"):
                dropped += 1 if stripped else 0
                continue
            in_block = False
        if META_BLOCK_HEAD.match(line):
            in_block = True
            dropped += 1
            continue
        if META_LINE.match(line):
            dropped += 1
            continue
        kept.append(line)
    return "\n".join(kept), dropped


def body_chars(body: str) -> int:
    t = body
    t = re.sub(r"```.*?```", "", t, flags=re.S)      # 코드 블록 제외
    t = re.sub(r"`([^`]*)`", r"\1", t)               # 인라인 코드 표식만 제거
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)   # 소제목 표식
    t = re.sub(r"^\s{0,3}[-*+>]\s+", "", t, flags=re.M)   # 불릿·인용 표식
    t = t.replace("*", "").replace("_", "")
    t = re.sub(r"\s+", "", t)
    return len(t)


def paragraph_stats(body: str) -> dict:
    """문단별 글자 수와 얇은 문단 위치를 돌려준다. 보강할 자리를 특정하는 데 쓴다."""
    raw = [b for b in re.split(r"\n\s*\n", body) if b.strip()]
    sizes = [body_chars(b) for b in raw]
    sizes = [s for s in sizes if s > 0]
    if not sizes:
        return {"count": 0, "median": 0, "thin": [], "thin_run": 0}
    ordered = sorted(sizes)
    median = ordered[len(ordered) // 2]
    thin = [f"{i + 1}번({s}자)" for i, s in enumerate(sizes) if s < PARAGRAPH_FLOOR]
    run = best = 0
    for s in sizes:
        run = run + 1 if s < PARAGRAPH_FLOOR else 0
        best = max(best, run)
    return {"count": len(sizes), "median": median, "sizes": sizes,
            "thin_count": len(thin), "thin": thin[:6], "thin_run": best}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="원고 파일 경로. '-'이면 표준 입력")
    ap.add_argument("--profile", choices=sorted(PROFILES), default="short_voice_column")
    ap.add_argument("--min", type=int, default=None, help="사용자 지정 하한")
    ap.add_argument("--max", type=int, default=None, help="사용자 지정 상한")
    args = ap.parse_args()

    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    title, raw_body = split_title(text)
    body, meta_lines = strip_meta(raw_body)
    count = body_chars(body)
    paragraphs = paragraph_stats(body)

    low, high, target = PROFILES[args.profile]
    if args.min is not None or args.max is not None:
        if args.min is not None:
            low = args.min
        if args.max is not None:
            high = args.max
        target = (low + high) // 2

    if count < low:
        verdict, gap = "미달", low - count
    elif count > high:
        verdict, gap = "초과", count - high
    else:
        verdict, gap = "충족", 0

    near_floor = verdict == "충족" and count < low + (high - low) * 0.25

    print(json.dumps({
        "title": title,
        "body_chars": count,
        "meta_lines_excluded": meta_lines,
        "profile": args.profile,
        "range": [low, high],
        "target": target,
        "verdict": verdict,
        "gap": gap,
        "to_target": max(0, target - count),
        "near_floor": near_floor,
        "paragraphs": paragraphs,
        "paragraph_note": (
            f"{paragraphs['thin_run']}개 문단이 연속으로 {PARAGRAPH_FLOOR}자 미만이다. "
            "판단만 적고 이유·결과·조건이 빠졌는지 본다"
            if paragraphs["thin_run"] >= 3 else ""),
        "note": "하한 근접. 계약 위반은 아니지만 판단의 전개·적용 조건을 보강할 자리가 있는지 본다" if near_floor else "",
    }, ensure_ascii=False, indent=2))
    return 0 if verdict == "충족" else 1


if __name__ == "__main__":
    raise SystemExit(main())
