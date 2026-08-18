#!/usr/bin/env python3
"""
pack_hwpx.py — 디렉토리 → .hwpx 패키징

HWPX는 ZIP 컨테이너이며, mimetype 파일이 반드시 첫 엔트리(ZIP_STORED, 비압축)여야
한다. 나머지 파일은 ZIP_DEFLATED(압축)로 저장한다.

사용법:
    python3 pack_hwpx.py <work_dir> <output.hwpx>
"""

import argparse
import sys
import zipfile
from pathlib import Path


def pack(work_dir: Path, output: Path) -> None:
    if not work_dir.is_dir():
        raise SystemExit(f"디렉토리를 찾을 수 없습니다: {work_dir}")

    mimetype_file = work_dir / "mimetype"
    if not mimetype_file.is_file():
        raise SystemExit("mimetype 파일이 없습니다. HWPX 구조가 아닙니다.")

    # 출력 디렉토리 보장
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w") as zf:
        # 1. mimetype을 첫 엔트리로, 비압축으로 저장
        zf.write(mimetype_file, "mimetype", compress_type=zipfile.ZIP_STORED)

        # 2. 나머지 파일을 압축 저장
        for path in sorted(work_dir.rglob("*")):
            if path.is_file() and path.name != "mimetype":
                rel = path.relative_to(work_dir).as_posix()
                zf.write(path, rel, compress_type=zipfile.ZIP_DEFLATED)

    print(f"패키징 완료: {work_dir} -> {output}")
    print(f"  엔트리 수: {len(zipfile.ZipFile(output).namelist())}")


def main() -> int:
    parser = argparse.ArgumentParser(description="디렉토리를 .hwpx로 패키징")
    parser.add_argument("work_dir", type=Path, help="작업 디렉토리 경로")
    parser.add_argument("output", type=Path, help="출력 .hwpx 파일 경로")
    args = parser.parse_args()

    pack(args.work_dir, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
