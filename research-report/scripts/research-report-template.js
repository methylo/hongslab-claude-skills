/**
 * research-report-template.js
 * 리서치 보고서 .docx 생성 템플릿
 *
 * 사용법:
 *   node research-report-template.js config.json output.docx
 *
 * config.json 구조:
 * {
 *   "title": "글쓰기 도구 시장 동향 2026",
 *   "subtitle": "AI Writing Tools Market Trends",
 *   "description": "강의·교육 자료의 근거가 되는 리서치/분석 보고서",
 *   "date": "2026년 3월 9일 (KST)",
 *   "author": "홍작가 (HONGS LAB)",
 *   "version": "v1.0",
 *   "category": "리서치 보고서 | 내부 참고용",
 *   "headerText": "HONGS LAB  |  AI 글쓰기 도구 시장 동향 2026",
 *   "sections": [
 *     { "heading": "1. 요약 (Executive Summary)", "level": 1, "body": "..." },
 *     { "heading": "왜 이 주제를 조사하는가", "level": 2, "body": "..." },
 *     { "heading": "발견 1: ...", "level": 2, "body": "...",
 *       "table": { "headers": ["도구","강점","한계"], "widths": [2200,4000,3160],
 *                  "rows": [["ChatGPT","...","..."]] } },
 *     ...
 *   ],
 *   "sources": [
 *     { "ref": "OpenAI", "title": "Introducing GPT-5.4", "date": "2026.03.05" },
 *     ...
 *   ]
 * }
 */

const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel,
        BorderStyle, WidthType, ShadingType,
        PageNumber, TableOfContents } = require("docx");

// ── Design Tokens (보고서 템플릿 표준) ──
const COLOR = {
  primary:  "1B3A5C",   // H1, H2, 메타 라벨
  accent:   "2E75B6",   // H3, 구분선, CONTENTS 라벨
  darkText: "1A1A1A",   // 본문
  grayText: "555555",   // 부가 정보, 헤더/푸터
  headerBg: "D5E8F0",   // 테이블 헤더 배경
  border:   "B0C4D8",   // 테이블 테두리, 구분선
};

const FONT = "Arial";
const PAGE = { width: 12240, height: 15840 }; // US Letter (DXA)
const MARGIN = { top: 1440, right: 1440, bottom: 1440, left: 1440 };
const TABLE_WIDTH = 9360; // PAGE.width - MARGIN.left - MARGIN.right

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: COLOR.border };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const CELL_MARGINS = { top: 80, bottom: 80, left: 120, right: 120 };

// ── Heading / Paragraph 빌더 ──
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
}

function makeHeading(text, level) {
  if (level === 1) return h1(text);
  if (level === 2) return h2(text);
  return h3(text);
}

function bodyPara(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 140, line: 340 }, ...opts,
    children: [new TextRun({ text, size: 21, font: FONT, color: COLOR.darkText })]
  });
}

function boldRun(text) { return new TextRun({ text, bold: true, size: 21, font: FONT, color: COLOR.darkText }); }
function normalRun(text) { return new TextRun({ text, size: 21, font: FONT, color: COLOR.darkText }); }
function grayRun(text) { return new TextRun({ text, size: 20, font: FONT, color: COLOR.grayText }); }

// ── 테이블 빌더 ──
function headerCell(text, width) {
  return new TableCell({
    borders: BORDERS, width: { size: width, type: WidthType.DXA },
    shading: { fill: COLOR.headerBg, type: ShadingType.CLEAR },
    margins: CELL_MARGINS,
    children: [new Paragraph({ spacing: { after: 0 },
      children: [new TextRun({ text, bold: true, size: 20, font: FONT, color: COLOR.primary })] })]
  });
}

function dataCell(text, width) {
  return new TableCell({
    borders: BORDERS, width: { size: width, type: WidthType.DXA },
    margins: CELL_MARGINS,
    children: [new Paragraph({ spacing: { after: 0 },
      children: [new TextRun({ text, size: 20, font: FONT, color: COLOR.darkText })] })]
  });
}

function buildTable(tableData) {
  const widths = tableData.widths || tableData.headers.map(() => Math.floor(TABLE_WIDTH / tableData.headers.length));
  const headerRow = new TableRow({
    children: tableData.headers.map((h, i) => headerCell(h, widths[i]))
  });
  const dataRows = tableData.rows.map(row =>
    new TableRow({ children: row.map((cell, i) => dataCell(cell, widths[i])) })
  );
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows]
  });
}

// ── 타이틀 페이지 빌더 ──
function buildTitlePage(cfg) {
  const children = [];
  // 상단 여백
  for (let i = 0; i < 8; i++) children.push(new Paragraph({ spacing: { after: 0 }, children: [] }));

  // RESEARCH REPORT 라벨
  children.push(new Paragraph({ spacing: { after: 160 }, children: [
    new TextRun({ text: "RESEARCH REPORT", size: 22, font: FONT, color: COLOR.accent, bold: true, characterSpacing: 200 })
  ] }));

  // 악센트 라인
  children.push(new Paragraph({ spacing: { after: 300 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: COLOR.accent, space: 1 } }, children: [] }));

  // 제목
  children.push(new Paragraph({ spacing: { after: 120 }, children: [
    new TextRun({ text: cfg.title, size: 56, bold: true, font: FONT, color: COLOR.primary })
  ] }));

  // 영문 부제
  if (cfg.subtitle) {
    children.push(new Paragraph({ spacing: { after: 400 }, children: [
      new TextRun({ text: cfg.subtitle, size: 30, font: FONT, color: COLOR.grayText })
    ] }));
  }

  // 설명
  children.push(new Paragraph({ spacing: { after: 600 }, children: [
    new TextRun({ text: cfg.description, size: 24, font: FONT, color: COLOR.grayText })
  ] }));

  // 구분선
  children.push(new Paragraph({ spacing: { after: 300 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: COLOR.border, space: 1 } }, children: [] }));

  // 메타 정보
  const ml = { size: 21, font: FONT, color: COLOR.primary, bold: true };
  const mv = { size: 21, font: FONT, color: COLOR.grayText };
  const metaItems = [
    ["작성일        ", cfg.date],
    ["작성자        ", cfg.author],
    ["버전            ", cfg.version],
    ["분류            ", cfg.category],
  ];
  for (const [label, value] of metaItems) {
    children.push(new Paragraph({ spacing: { after: 100 }, children: [
      new TextRun({ text: label, ...ml }), new TextRun({ text: value, ...mv })
    ] }));
  }

  return children;
}

// ── 목차 페이지 빌더 ──
function buildTOCPage() {
  return [
    new Paragraph({ spacing: { after: 80 }, children: [
      new TextRun({ text: "CONTENTS", size: 28, font: FONT, color: COLOR.accent, bold: true, characterSpacing: 160 })
    ] }),
    new Paragraph({ spacing: { after: 400 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: COLOR.accent, space: 6 } }, children: [] }),
    new TableOfContents("목차", { hyperlink: true, headingStyleRange: "1-2" })
  ];
}

// ── 본문 빌더 ──
function buildBody(sections, sources) {
  const children = [];

  for (const sec of sections) {
    children.push(makeHeading(sec.heading, sec.level));

    if (sec.body) {
      // 문단 분리: \n\n 기준
      const paragraphs = sec.body.split("\n\n").filter(p => p.trim());
      for (const para of paragraphs) {
        children.push(bodyPara(para));
      }
    }

    // 테이블 캡션 + 테이블
    if (sec.tableCaption) {
      children.push(new Paragraph({ spacing: { before: 160, after: 80 }, children: [
        new TextRun({ text: sec.tableCaption, bold: true, size: 20, font: FONT, color: COLOR.accent })
      ] }));
    }
    if (sec.table) {
      children.push(buildTable(sec.table));
      children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
    }
  }

  // 출처 섹션
  if (sources && sources.length > 0) {
    children.push(h1("5. 출처 및 부록"));
    children.push(h2("출처 목록"));
    for (const s of sources) {
      children.push(new Paragraph({ spacing: { after: 140, line: 340 }, children: [
        boldRun(`[${s.ref}] `),
        normalRun(`${s.title} (${s.date}). `),
        grayRun("(접근일: " + (s.accessDate || new Date().toISOString().slice(0, 10)) + ")")
      ] }));
    }
  }

  return children;
}

// ── 헤더/푸터 빌더 ──
function buildHeader(headerText) {
  return new Header({ children: [new Paragraph({
    spacing: { after: 0 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: COLOR.accent, space: 4 } },
    children: [grayRun(headerText)]
  })] });
}

function buildFooter() {
  return new Footer({ children: [new Paragraph({
    spacing: { after: 0 }, alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "- ", size: 16, font: FONT, color: COLOR.grayText }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, font: FONT, color: COLOR.grayText }),
      new TextRun({ text: " -", size: 16, font: FONT, color: COLOR.grayText }),
    ]
  })] });
}

// ── 문서 조립 ──
function buildDocument(cfg) {
  const pageProps = { page: { size: PAGE, margin: MARGIN } };
  const hdr = buildHeader(cfg.headerText || `HONGS LAB  |  ${cfg.title}`);
  const ftr = buildFooter();

  return new Document({
    styles: {
      default: { document: { run: { font: FONT, size: 21 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 32, bold: true, font: FONT, color: COLOR.primary },
          paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 26, bold: true, font: FONT, color: COLOR.primary },
          paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 22, bold: true, font: FONT, color: COLOR.accent },
          paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
      ]
    },
    sections: [
      // Section 1: 타이틀 페이지 (헤더/푸터 없음)
      { properties: { ...pageProps }, children: buildTitlePage(cfg) },
      // Section 2: 목차 페이지
      { properties: { ...pageProps }, headers: { default: hdr }, footers: { default: ftr }, children: buildTOCPage() },
      // Section 3: 본문
      { properties: { ...pageProps }, headers: { default: hdr }, footers: { default: ftr }, children: buildBody(cfg.sections, cfg.sources) }
    ]
  });
}

// ── CLI 실행 ──
async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node research-report-template.js config.json output.docx");
    process.exit(1);
  }

  const config = JSON.parse(fs.readFileSync(args[0], "utf-8"));
  const outputPath = args[1];

  const doc = buildDocument(config);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Generated: ${outputPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
