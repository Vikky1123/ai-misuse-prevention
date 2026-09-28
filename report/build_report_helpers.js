/* Build Chapter 3 + Chapter 4 .docx with embedded diagrams */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageBreak, PageOrientation
} = require("docx");

const ROOT = __dirname;
const ASSETS = path.join(ROOT, "report_assets");
const L2_MODEL = path.join(ROOT, "layer2_detector", "model");
const OUT = path.join(ROOT, "Chapter3_Chapter4_Report.docx");

const img = (file, w, h) => new ImageRun({
  type: "png",
  data: fs.readFileSync(file),
  transformation: { width: w, height: h },
  altText: { title: path.basename(file), description: path.basename(file), name: path.basename(file) },
});

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 480 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
  children: [new TextRun({ text, ...opts })],
  ...opts.pProps,
});

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 200 },
  children: [new TextRun({ text, bold: true, size: 32 })],
});

const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 160 },
  children: [new TextRun({ text, bold: true, size: 26 })],
});

const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 220, after: 120 },
  children: [new TextRun({ text, bold: true, size: 24 })],
});

const RICH = (runs, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 480 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
  children: runs.map(r => typeof r === "string" ? new TextRun(r) : new TextRun(r)),
});

const BULLET = (text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 80, line: 480 },
  children: [new TextRun(text)],
});

const BULLET_RICH = (runs) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 80, line: 480 },
  children: runs.map(r => typeof r === "string" ? new TextRun(r) : new TextRun(r)),
});

const NUM = (text) => new Paragraph({
  numbering: { reference: "numbers", level: 0 },
  spacing: { after: 80, line: 480 },
  children: [new TextRun(text)],
});

const FIG = (file, w, h, caption) => [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 240, after: 80 },
    children: [img(file, w, h)],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240, line: 240 },
    children: [new TextRun({ text: caption, italics: true, size: 20 })],
  }),
];

// Table helpers
const border = { style: BorderStyle.SINGLE, size: 4, color: "888888" };
const borders = { top: border, bottom: border, left: border, right: border,
                  insideHorizontal: border, insideVertical: border };

function cellPara(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing: { after: 0, line: 240 },
    children: [new TextRun({ text, bold: !!opts.bold, size: opts.size || 20 })],
  });
}

function makeTable(rows, columnWidths, headerFill = "D5E8F0") {
  const MAX_W = 8240; // A4 width minus 1.5in left + 1in right margins
  let widths = columnWidths.slice();
  const total = widths.reduce((a, b) => a + b, 0);
  if (total > MAX_W) {
    const s = MAX_W / total;
    widths = widths.map((w) => Math.round(w * s));
  }
  const fitted = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: fitted, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, ri) =>
      new TableRow({
        children: r.map((cell, ci) =>
          new TableCell({
            borders,
            width: { size: widths[ci], type: WidthType.DXA },
            shading: ri === 0 ? { fill: headerFill, type: ShadingType.CLEAR, color: "auto" } : undefined,
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [cellPara(cell, { bold: ri === 0 })],
          })
        ),
      })
    ),
  });
}

// ---------------- TITLE PAGE ----------------
const titlePage = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 1200, after: 240 },
    children: [new TextRun({
      text: "DESIGN AND IMPLEMENTATION OF AN INTEGRATED FRAMEWORK FOR ARTIFICIAL INTELLIGENCE INFORMATION MISUSE PREVENTION",
      bold: true, size: 32,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 },
    children: [new TextRun({ text: "CHAPTER THREE  &  CHAPTER FOUR", bold: true, size: 28 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({ text: "Submitted by", italics: true, size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({ text: "OKE OVIGUERONYE", bold: true, size: 24 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({ text: "Matric No: FOS/22/23/289288", size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 },
    children: [new TextRun({ text: "Department of Computer Science, Delta State University, Abraka", size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({ text: "Supervisor: Dr. M. I. Akazue", size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 0 },
    children: [new TextRun({ text: "2026", size: 22 })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

console.log("[build] title page ready");
fs.writeFileSync(path.join(ROOT, ".build_part1.json"), JSON.stringify({ ok: true }));

module.exports = {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageBreak, PageOrientation,
  ROOT, ASSETS, L2_MODEL, OUT,
  img, P, H1, H2, H3, RICH, BULLET, BULLET_RICH, NUM, FIG, makeTable,
  titlePage,
};
