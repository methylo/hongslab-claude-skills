#!/usr/bin/env python3
"""AI 흔적 지수 — 후보 추출기 (판정은 하지 않는다).

`03-anti-traces.md` §11은 "각 표현을 발견하면 먼저 §5-1의 판정을 적용해
위반인지 정한 뒤 합산한다"로 정의한다. 발견은 기계가 할 수 있고 판정은 할 수
없다. 이 스크립트는 **발견까지만** 한다. 위반 여부, 등급, 수정 여부는 편집자가
정한다.

사전을 이 파일에 복사하지 않는다. 실행 시점에 `03-anti-traces.md` §10을 직접
파싱한다. 정본이 바뀌면 이 스크립트의 결과도 따라 바뀐다.

사용:
    python3 scripts/scan-traces.py --canon {BASE}/references/03-anti-traces.md \\
                                   --manuscript 원고.md
    python3 scripts/scan-traces.py --canon ... --manuscript ... --json

출력: 후보 목록(분류·표현·줄·문맥)과 본문 글자 수, 1,000자 환산 분모.
종료코드: 0 정상 / 2 입력 오류

한계 — 사전 표기와 글자가 같은 것만 잡는다. `~라고 할 수 있다`는 잡지만
`~다고 할 수 있다`는 놓친다. 범주 1~8의 구조적 흔적(§5-3 문단 구성, §6 조합,
§7 챗봇 말투)은 아예 대상이 아니다. **이 결과는 바닥값이지 전부가 아니다.**
편집자는 이 목록으로 기계적 대조를 건너뛰고, 구조와 변이는 직접 읽어 본다.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SECTION_10 = re.compile(r"^##\s*10\.", re.M)
NEXT_SECTION = re.compile(r"^##\s+", re.M)
FRAGMENT_MIN = 3          # ~로 쪼갠 조각 중 이 길이 이상만 검색에 쓴다
WINDOW = 30               # 여러 조각이 한 표현으로 묶이는 최대 간격(자)


def parse_dictionary(canon_text: str) -> dict:
    """§10 한국어 AI 상투 표현 사전을 {분류: [표현, ...]}로 파싱한다."""
    m = SECTION_10.search(canon_text)
    if not m:
        raise ValueError("03-anti-traces.md에서 §10 절을 찾지 못했다")
    rest = canon_text[m.end():]
    nxt = NEXT_SECTION.search(rest)
    section = rest[: nxt.start()] if nxt else rest

    block = re.search(r"```text\n(.*?)```", section, re.S)
    if not block:
        raise ValueError("§10 안에서 사전 코드 블록을 찾지 못했다")

    out = {}
    for line in block.group(1).splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
        if len(parts) != 2:
            continue
        label, exprs = parts
        out[label] = [e.strip() for e in exprs.split("/") if e.strip()]
    if not out:
        raise ValueError("§10 사전이 비어 있다")
    return out


def body_chars(text: str) -> int:
    """공백·개행을 뺀 본문 글자 수. 1,000자 환산의 분모다."""
    return len(re.sub(r"\s", "", text))


def find(expr: str, text: str):
    """`~`를 와일드카드로 보고 표현의 출현 위치를 찾는다."""
    frags = [f for f in (p.strip() for p in expr.split("~")) if len(f) >= FRAGMENT_MIN]
    if not frags:
        return
    first = frags[0]
    start = 0
    while True:
        i = text.find(first, start)
        if i < 0:
            return
        end = i + len(first)
        ok = True
        for f in frags[1:]:
            j = text.find(f, end)
            if j < 0 or j - end > WINDOW:
                ok = False
                break
            end = j + len(f)
        if ok:
            yield i, end
        start = i + 1


def protected_lines(text: str) -> set:
    """보존 조건 후보 — 코드 블록과 인용 줄. 제외하지 않고 표시만 한다."""
    marked, in_block = set(), False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_block = not in_block
            marked.add(n)
            continue
        if in_block or line.lstrip().startswith(">"):
            marked.add(n)
    return marked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", required=True, help="03-anti-traces.md 절대 경로")
    ap.add_argument("--manuscript", required=True, help="원고 파일 경로")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    a = ap.parse_args()

    canon, src = Path(a.canon), Path(a.manuscript)
    for p, name in ((canon, "정본"), (src, "원고")):
        if not p.exists():
            print(f"{name} 파일이 없다: {p}", file=sys.stderr)
            return 2

    try:
        dictionary = parse_dictionary(canon.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"정본 파싱 실패: {e}", file=sys.stderr)
        return 2

    text = src.read_text(encoding="utf-8")
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    prot = protected_lines(text)

    def line_of(pos):
        lo, hi = 0, len(starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    hits = []
    for label, exprs in dictionary.items():
        for expr in exprs:
            for i, end in find(expr, text):
                ln = line_of(i)
                hits.append({
                    "분류": label,
                    "표현": expr,
                    "줄": ln,
                    "문맥": text[max(0, i - 20):end + 20].replace("\n", " ").strip(),
                    "보존후보": ln in prot,
                })
    hits.sort(key=lambda h: (h["줄"], h["분류"]))

    chars = body_chars(text)
    result = {
        "원고": str(src),
        "본문_글자수": chars,
        "환산_분모": round(chars / 1000, 2),
        "후보_건수": len(hits),
        "보존후보_건수": sum(1 for h in hits if h["보존후보"]),
        "주의": "후보일 뿐 위반이 아니다. §5-1 판정을 적용해 위반만 합산하라.",
        "한계": "사전 표기와 글자가 같은 것만 잡는다. 형태 변이와 범주 1~8의 구조적 흔적은 직접 읽어야 한다.",
        "후보": hits,
    }

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"원고 {src.name} — 본문 {chars:,}자 (환산 분모 {result['환산_분모']})")
    print(f"§10 사전 후보 {len(hits)}건 (그중 인용·코드블록 {result['보존후보_건수']}건)\n")
    for h in hits:
        mark = " [보존후보]" if h["보존후보"] else ""
        print(f"  {h['줄']:>4}줄  {h['분류']:<8} {h['표현']}{mark}")
        print(f"        … {h['문맥']} …")
    print("\n후보일 뿐 위반이 아니다. §5-1 판정을 적용해 위반만 합산하라.")
    print("이 목록은 바닥값이다. 형태 변이와 구조적 흔적(§5-3·§6·§7)은 직접 읽어 본다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
