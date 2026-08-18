#!/usr/bin/env python3
"""
build_report.py v2 — 보고서 데이터(JSON) → section0.xml 자리표시자 치환 통합 스크립트

v1 대비 개선 사항:
1. 표 행 가변화 — 지원대상·평가항목·문의처 표가 데이터 길이만큼 행을 동적 복제
2. 셀 컨텍스트 치환 — 토큰 고유화로 순서 꼬임 제거
3. 표 무결성 검증 — 행 수 일치·연락처 중복·미교체 토큰 종합 보고
4. 단일 스크립트 — 보강 스크립트 없이 1회 실행으로 모든 자리표시자 처리

사용법:
    python3 build_report.py --work <unpacked_dir> --data <report_data.json>
"""

import argparse
import json
import re
import sys
from pathlib import Path


# 단순 1:1 자리표시자 치환 매핑
SIMPLE_TOKENS = {
    "[기관명]": "기관명",
    "[YYYY-NN]": "공고번호",
    "[보고서·공고문 제목 입력]": "제목",
    "[보고서·공고 안내 문구를 2~3줄 이내로 작성합니다. 사업의 목적, 추진 주체, 신청 대상의 범위를 한 문단으로 압축합니다.]": "안내문구",
    "[발신 기관·부서명]": "발신",
    "[통계청·정부공식 자료에서 인용한 핵심 수치 또는 추세를 1~2문장으로 제시. 추상 형용사 대신 행동·상태·결과를 기술합니다.]": "추진_필요성_수치",
    "[세부 근거 1: 비교 수치, 비율, 변화율 등 정량 데이터로 작성합니다.]": "추진_필요성_세부",
    "[현황 진단: 위 수치가 정책·교육·현장에 시사하는 바를 2~3줄로 설명합니다.]": "추진_필요성_시사",
    "[목적 1: 사업이 달성하려는 직접 성과를 행동형 동사로 기술합니다. 예) ~를 양성한다.]": "추진_목적_1",
    "[목적 2: 사업이 기여하는 간접 효과를 2줄 이내로 기술합니다.]": "추진_목적_2",
    "[정식 명칭]": "사업명",
    "[총 ○○억 ○○백만원 / 기관부담 ○○ · 자부담 ○○]": "사업예산",
    "[핵심 활동 1: 사업의 첫 번째 기둥을 2~3줄로 압축 기술합니다.]": "사업내용_1",
    "[핵심 활동 2: 사업의 두 번째 기둥. 활동 단위·결과 단위로 끊어 작성합니다.]": "사업내용_2",
    "[제외 대상 1: 한 줄 안에 핵심 조건만 기술합니다.]": "제외대상_1",
    "[제외 대상 2: 단서가 있는 경우 별표(*)로 부연합니다.]": "제외대상_2",
    "[부연 사항: 적용 예외, 인정 사례, 증빙 방법 등을 9pt로 처리합니다.]": "제외부연",
    "[접수 채널: 온라인 시스템 URL, 방문·우편 주소 등을 한 줄로 정리합니다.]": "신청_채널",
    "[제출 서류: 필수 ① ② ③ / 선택 ④ ⑤ 형식으로 항목 단위로 분리합니다.]": "신청_서류",
    "[가점 항목 1: 1점 / 인정 증빙: ○○ 확인서]": "가점_1",
    "[가점 항목 2: 1점 / 기업당 최대 2점까지 인정]": "가점_2",
    "[중복 지원 제한·환수 등 핵심 제재 사항을 한 줄로 명시합니다.]": "유의_1",
    "[사업 포기·미이행 시 적용되는 참여 제한 기간과 범위를 명시합니다.]": "유의_2",
    "[본 공고문에 명시되지 않은 사항은 관계 법령 및 운영 지침에 따른다는 일반 단서.]": "유의_3",
}


def esc(s):
    """XML 특수 문자 이스케이프."""
    if not isinstance(s, str):
        s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def expand_data(data):
    """공고일자·사업기간 등 합성 필드를 생성."""
    expanded = dict(data)

    y = data.get("공고일자_연", "")
    m = data.get("공고일자_월", "")
    d = data.get("공고일자_일", "")
    expanded["공고일자_라인"] = f"{y}년 {m}월 {d}일" if y and m and d else ""

    period = data.get("사업기간", "")
    months = data.get("사업기간_개월", "")
    if period and months:
        expanded["사업기간_라인"] = f"{period} (총 {months}개월)"
    elif period:
        expanded["사업기간_라인"] = period
    else:
        expanded["사업기간_라인"] = ""

    src = data.get("추진_필요성_출처", "")
    expanded["추진_필요성_출처_라인"] = f"* 출처: {src}" if src else ""

    # 제외대상이 list 형태면 인덱스로 분해
    excludes = data.get("제외대상", [])
    if isinstance(excludes, list):
        for i, val in enumerate(excludes[:2], start=1):
            expanded[f"제외대상_{i}"] = val

    return expanded


def replace_simple(xml, data):
    """Phase 1. 단순 1:1 자리표시자 치환."""
    if data.get("공고일자_라인"):
        xml = xml.replace("[YYYY]년 [MM]월 [DD]일", data["공고일자_라인"])
    if data.get("사업기간_라인"):
        xml = xml.replace("[YYYY.MM.DD ~ YYYY.MM.DD] (총 [N]개월)", data["사업기간_라인"])
    if data.get("추진_필요성_출처_라인"):
        xml = xml.replace(
            "* 출처: 통계청 [통계명], [발표연도] / [URL 또는 보고서 식별번호]",
            data["추진_필요성_출처_라인"]
        )

    for token, key in SIMPLE_TOKENS.items():
        value = data.get(key, "")
        if value:
            xml = xml.replace(token, esc(value))

    return xml


def render_row(row_template, row_index, data_dict, token_map):
    """row 템플릿에 1행 데이터를 채워 새 row XML 생성."""
    row_xml = row_template
    for token, data_key in token_map.items():
        value = data_dict.get(data_key, "")
        row_xml = row_xml.replace(token, esc(value))

    # 셀 id 속성을 행 번호로 고유화 (id 충돌 방지)
    row_xml = re.sub(
        r'(id=")(\d+)(")',
        lambda m: f'{m.group(1)}{m.group(2)}{row_index:02d}{m.group(3)}',
        row_xml
    )
    # cellAddr rowAddr 갱신
    row_xml = re.sub(r'rowAddr="\d+"', f'rowAddr="{row_index}"', row_xml)

    return row_xml


def expand_table_rows(xml, marker_start, marker_end, rowcnt_token, data_list, token_map):
    """공통 함수: 표의 row 템플릿을 데이터 길이만큼 복제."""
    pattern = f'{marker_start}(.*?){marker_end}'
    m = re.search(pattern, xml, re.DOTALL)
    if not m:
        return xml, 0
    row_template = m.group(1)

    new_rows = ""
    for i, item in enumerate(data_list, start=1):
        new_rows += render_row(row_template, i, item, token_map)

    xml = re.sub(pattern, new_rows, xml, count=1, flags=re.DOTALL)

    actual_row_count = 1 + len(data_list)  # 헤더 + 데이터
    xml = xml.replace(rowcnt_token, f'rowCnt="{actual_row_count}"')

    return xml, len(data_list)


def fill_step_table(xml, step_list):
    """진행 단계 표(고정 5단계)의 단계명·일정 토큰 치환."""
    filled = 0
    for i in range(5):
        name_token = f"[단계명_{i+1}]"
        sched_token = f"[일정_{i+1}]"
        if i < len(step_list):
            step = step_list[i]
            xml_new = xml.replace(name_token, esc(step.get("이름", "")))
            xml_new = xml_new.replace(sched_token, esc(step.get("일정", "")))
            if xml_new != xml:
                filled += 1
            xml = xml_new
    return xml, filled


def integrity_check(xml, data):
    """무결성 검증: 미교체 토큰·표 행 수·연락처 중복·금지어."""
    result = {
        "미교체_자리표시자": [],
        "연락처_중복": [],
        "표_행수": {},
        "금지어_검출": {},
        "결함_수": 0,
    }

    remaining = re.findall(r"\[([^\]]{2,80})\]", xml)
    result["미교체_자리표시자"] = sorted(set(remaining))
    if remaining:
        result["결함_수"] += 1

    text_parts = re.findall(r"<hp:t>([^<]*)</hp:t>", xml)
    full_text = "\n".join(text_parts)

    # 표 행 수 검증
    row_counts = re.findall(r'rowCnt="(\d+)"', xml)
    expected = {
        "지원대상": 1 + len(data.get("지원대상", [])),
        "평가항목": 1 + len(data.get("평가항목", [])),
        "문의": 1 + len(data.get("문의", [])),
    }
    # 표 순서: 지원대상(0), 진행단계(1), 평가항목(2), 문의(3)
    if len(row_counts) >= 4:
        actual = {
            "지원대상": int(row_counts[0]),
            "평가항목": int(row_counts[2]),
            "문의": int(row_counts[3]),
        }
        for key in expected:
            ok = expected[key] == actual[key]
            result["표_행수"][key] = {"기대": expected[key], "실제": actual[key], "일치": ok}
            if not ok:
                result["결함_수"] += 1

    # 연락처 중복 검출 (원본 미중복 → 본문 중복)
    if data.get("문의"):
        phones = [c.get("연락처", "") for c in data["문의"]]
        unique_phones = set([p for p in phones if p])
        original_has_dup = len(phones) - len([p for p in phones if p]) != 0 or len(unique_phones) != len([p for p in phones if p])
        if not original_has_dup:
            for p in unique_phones:
                if full_text.count(p) > 1:
                    result["연락처_중복"].append(p)
        if result["연락처_중복"]:
            result["결함_수"] += 1

    # 금지어
    banned = ["혁신적인", "획기적인", "완벽한", "매우", "쉽게", "빠르게"]
    for w in banned:
        c = full_text.count(w)
        if c > 0:
            result["금지어_검출"][w] = c
            result["결함_수"] += 1

    return result


def build(work_dir, data_file):
    section_path = work_dir / "Contents" / "section0.xml"
    if not section_path.is_file():
        raise SystemExit(f"section0.xml을 찾을 수 없습니다: {section_path}")

    data_raw = json.loads(data_file.read_text(encoding="utf-8"))
    data = expand_data(data_raw)

    xml = section_path.read_text(encoding="utf-8")

    # Phase 1: 단순 치환
    xml = replace_simple(xml, data)

    # Phase 2: 표 행 동적 복제
    xml, n_support = expand_table_rows(
        xml,
        "<!--SUPPORT_ROW_TEMPLATE_START-->",
        "<!--SUPPORT_ROW_TEMPLATE_END-->",
        'rowCnt="SUPPORT_ROWCNT"',
        data.get("지원대상", []),
        {"[구분_ROW]": "구분", "[요건_ROW]": "요건", "[내용_ROW]": "내용", "[규모_ROW]": "규모"}
    )
    xml, n_eval = expand_table_rows(
        xml,
        "<!--EVAL_ROW_TEMPLATE_START-->",
        "<!--EVAL_ROW_TEMPLATE_END-->",
        'rowCnt="EVAL_ROWCNT"',
        data.get("평가항목", []),
        {"[평가항목_ROW]": "항목", "[배점_ROW]": "배점", "[평가내용_ROW]": "내용"}
    )
    xml, n_contact = expand_table_rows(
        xml,
        "<!--CONTACT_ROW_TEMPLATE_START-->",
        "<!--CONTACT_ROW_TEMPLATE_END-->",
        'rowCnt="CONTACT_ROWCNT"',
        data.get("문의", []),
        {"[문의기관_ROW]": "기관", "[문의연락처_ROW]": "연락처", "[문의내용_ROW]": "내용"}
    )

    # Phase 3: 진행 단계 표
    xml, n_steps = fill_step_table(xml, data.get("단계", []))

    section_path.write_text(xml, encoding="utf-8")

    # Phase 4: 무결성 검증
    result = integrity_check(xml, data)

    print("=" * 60)
    print("build_report.py v2 — 빌드 완료")
    print("=" * 60)
    print(f"\n[표 행 복제 결과]")
    print(f"  지원대상: {n_support}행")
    print(f"  평가항목: {n_eval}행")
    print(f"  문의처: {n_contact}행")
    print(f"  진행단계: {n_steps}/5단계 치환")

    print(f"\n[무결성 검증]")
    print(f"  미교체 자리표시자: {len(result['미교체_자리표시자'])}건")
    if result["미교체_자리표시자"]:
        for t in result["미교체_자리표시자"][:10]:
            print(f"    - [{t}]")

    print(f"\n  표 행 수 일치:")
    for key, info in result["표_행수"].items():
        mark = "OK" if info["일치"] else "FAIL"
        print(f"    [{mark}] {key}: 기대 {info['기대']}행 / 실제 {info['실제']}행")

    print(f"\n  연락처 중복: {len(result['연락처_중복'])}건")
    for p in result["연락처_중복"]:
        print(f"    - {p}")

    print(f"\n  금지어 검출: {len(result['금지어_검출'])}건")
    for w, c in result["금지어_검출"].items():
        print(f"    - {w}: {c}회")

    print(f"\n[종합] 결함 {result['결함_수']}건 검출됨")

    if result["결함_수"] > 0:
        print("\n[경고] 결함이 있습니다. 위 항목을 확인하세요.")
        sys.exit(1)
    else:
        print("\n[통과] 모든 무결성 검증 통과")


def main():
    parser = argparse.ArgumentParser(description="보고서 데이터를 section0.xml에 주입 (v2)")
    parser.add_argument("--work", type=Path, required=True, help="언팩된 hwpx 작업 디렉토리")
    parser.add_argument("--data", type=Path, required=True, help="보고서 데이터 JSON 파일")
    args = parser.parse_args()
    build(args.work, args.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
