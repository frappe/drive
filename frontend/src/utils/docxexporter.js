import * as fileSaver from "file-saver";
import {
  AlignmentType,
  BorderStyle,
  Document,
  ImageRun,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableLayoutType,
  TableRow,
  TextRun,
  WidthType,
  convertInchesToTwip,
  HorizontalPositionAlign,
  HorizontalPositionRelativeFrom,
  VerticalPositionAlign,
  VerticalPositionRelativeFrom,
  TextWrappingType,
  TextWrappingSide,
  VerticalAlign,
} from "docx";

const CELL_PADDING = 240;
const TABLE_DXA = 8640; 
const TABLE_SPACE_BEFORE = 200;
const TABLE_SPACE_AFTER = 240;
const IMG_SPACE_BEFORE = 240;
const IMG_SPACE_AFTER = 240;

const COLOR_MAP = {
  "var(--prose-color-red)": "CC2929",
  "var(--prose-color-blue)": "007BE0",
  "var(--prose-color-green)": "278F5E",
  "var(--prose-color-yellow)": "D1930D",
  "var(--prose-color-orange)": "D45A08",
  "var(--prose-color-purple)": "8642C2",
  "var(--prose-color-pink)": "CF3A96",
  "var(--prose-color-gray)": "7C7C7C",
  "var(--prose-color-teal)": "0B9E92",
  "var(--prose-color-cyan)": "32A4C7",
  "var(--surface-gray-2)": "F3F3F3",
  "var(--outline-gray-2)": "E2E2E2",
  "var(--ink-gray-3)": "C7C7C7",
};

const FONT_MAP = {
  "var(--font-caveat)": "Caveat",
  "var(--font-comic-sans)": "Comic Sans MS",
  "var(--font-comfortaa)": "Comfortaa",
  "var(--font-eb-garamond)": "EB Garamond",
  "var(--font-geist)": "Geist",
  "var(--font-ibm-plex)": "IBM Plex Sans",
  "var(--font-inter)": "Inter",
  "var(--font-jetbrains)": "JetBrains Mono",
  "var(--font-lora)": "Lora",
  "var(--font-merriweather)": "Merriweather",
  "var(--font-nunito)": "Nunito",
  fantasy: "Fantasy",
  caveat: "Caveat",
  "comic-sans": "Comic Sans MS",
  comfortaa: "Comfortaa",
  "eb-garamond": "EB Garamond",
  geist: "Geist",
  "ibm-plex": "IBM Plex Sans",
  inter: "Inter",
  jetbrains: "JetBrains Mono",
  lora: "Lora",
  merriweather: "Merriweather",
  nunito: "Nunito",
};

function cssColorToDocx(c) {
  if (!c) return;
  const t = c.trim();
  if (COLOR_MAP[t]) return COLOR_MAP[t];
  
  const hex = t.replace(/^#/, "");
  if (/^[0-9a-f]{6}$/i.test(hex)) return hex.toUpperCase();
  if (/^[0-9a-f]{3}$/i.test(hex))
    return hex.split("").map((ch) => ch + ch).join("").toUpperCase();
}

function cssFontToDocx(f) {
  if (!f) return;
  const t = f.trim();
  if (FONT_MAP[t]) return FONT_MAP[t];
  
  const first = t.split(",")[0].replace(/['"]/g, "").trim();
  return first || undefined;
}

function pxToDocxSize(px) {
  if (!px) return;
  const n = parseFloat(px);
  if (!Number.isFinite(n)) return;
  const pt = n / 1.333;
  return Math.round(pt * 2);
}

function cssFontWeightToBold(weight) {
  if (!weight) return false;
  const w = typeof weight === 'string' ? parseInt(weight) : weight;
  return w >= 600;
}

async function dataFromUrl(url) {
  const res = await fetch(url);
  const buf = await res.arrayBuffer();
  return new Uint8Array(buf);
}

function inlineToRuns(node, inherited = {}) {
  if (node.nodeType === Node.TEXT_NODE) {
    return [new TextRun({ ...inherited, text: node.nodeValue || "" })];
  }
  if (!(node instanceof HTMLElement)) return [];

  const tag = node.tagName.toLowerCase();
  const isU = tag === "u" || (node.style.textDecoration || "").includes("underline");
  const isS = tag === "s" || (node.style.textDecoration || "").includes("line-through");

  let fontFromInline;
  if (node.style && node.style.fontFamily) {
    fontFromInline = cssFontToDocx(node.style.fontFamily);
  }

  let isBold = tag === "strong" || inherited.bold;
  if (node.style && node.style.fontWeight) {
    isBold = cssFontWeightToBold(node.style.fontWeight) || isBold;
  }

  const next = {
    ...inherited,
    bold: isBold,
    italics: tag === "em" || inherited.italics,
    underline: isU ? {} : inherited.underline,
    strike: isS || inherited.strike,
    color: cssColorToDocx(node.style.color) || inherited.color,
    size: pxToDocxSize(node.style.fontSize) || inherited.size,
    font: fontFromInline || inherited.font,
  };

  const runs = [];
  node.childNodes.forEach((child) => {
    if (child.nodeName === "BR") {
      runs.push(new TextRun({ ...next, text: "", break: 1 }));
    } else {
      runs.push(...inlineToRuns(child, next));
    }
  });
  return runs;
}

function paragraphFromP(p, defaultFont) {
  const runs = [];
  p.childNodes.forEach((n) => runs.push(...inlineToRuns(n, { font: defaultFont })));
  if (!runs.length) runs.push(new TextRun({ text: "\u00A0", font: defaultFont }));

  const alignMap = {
    left: AlignmentType.LEFT,
    center: AlignmentType.CENTER,
    right: AlignmentType.RIGHT,
    justify: AlignmentType.JUSTIFIED,
  };
  return new Paragraph({
    alignment: alignMap[(p.style.textAlign || "").toLowerCase()],
    spacing: { before: 120, after: 120 },
    children: runs,
  });
}

function headingFromHx(hx, defaultFont) {
  const tag = hx.tagName.toLowerCase();
  const fallbackByTag = { h1: 40, h2: 36, h3: 32 };
  const size = pxToDocxSize(hx.style.fontSize) || fallbackByTag[tag];
  const runs = inlineToRuns(hx, { bold: true, size, font: defaultFont });

  return new Paragraph({
    spacing: { before: 240, after: 120 }, 
    children: runs.length ? runs : [new TextRun({ text: "", bold: true, size, font: defaultFont })],
  });
}

function paragraphsFromUL(ul, defaultFont) {
  const isTask = ul.getAttribute("data-type") === "taskList";
  const out = [];

  ul.querySelectorAll(":scope > li").forEach((li) => {
    const checked = (li.getAttribute("data-checked") || "").toLowerCase() === "true";

    const runs = [];
    const collect = (n) => {
      if (n.nodeName === "P") {
        runs.push(...inlineToRuns(n, { font: defaultFont }));
      } else {
        n.childNodes?.forEach(collect);
      }
    };
    li.childNodes.forEach(collect);

    if (isTask) {
      const checkbox = checked ? "\u2611 " : "\u2610 "; //list box
      out.push(
        new Paragraph({
          indent: { left: 720 },
          spacing: { before: 120, after: 120 },
          children: [
            new TextRun({ text: checkbox, font: defaultFont, size: 28 }), 
            ...(runs.length ? runs : [new TextRun({ text: "", font: defaultFont })]),
          ],
        })
      );
    } else {
      out.push(
        new Paragraph({
          spacing: { before: 120, after: 120 },
          children: runs.length ? runs : [new TextRun({ text: "", font: defaultFont })],
          numbering: { reference: "bullets", level: 0 },
        })
      );
    }
  });
  return out;
}

function paragraphsFromOL(ol, defaultFont) {
  const out = [];
  ol.querySelectorAll(":scope > li").forEach((li) => {
    const runs = [];
    const collect = (n) => {
      if (n.nodeName === "P") {
        runs.push(...inlineToRuns(n, { font: defaultFont }));
      } else {
        n.childNodes?.forEach(collect);
      }
    };
    li.childNodes.forEach(collect);
    out.push(
      new Paragraph({
        spacing: { before: 120, after: 120 }, 
        children: runs.length ? runs : [new TextRun({ text: "", font: defaultFont })],
        numbering: { reference: "numbers", level: 0 },
      })
    );
  });
  return out;
}

function countCols(tr) {
  let c = 0;
  tr.querySelectorAll("th,td").forEach((td) => {
    const cs = parseInt(td.getAttribute("colspan") || "1", 10);
    c += Number.isFinite(cs) && cs > 1 ? cs : 1;
  });
  return c;
}

function tableFromTABLE(tbl, defaultFont) {
  const borderColor = COLOR_MAP["var(--outline-gray-2)"] || "E2E2E2";
  const headerFill = COLOR_MAP["var(--surface-gray-2)"] || "F3F3F3";

  const trs = tbl.querySelectorAll(":scope > thead > tr, :scope > tbody > tr, :scope > tr");
  let totalCols = 0;
  trs.forEach((tr) => (totalCols = Math.max(totalCols, countCols(tr))));
  if (!totalCols) totalCols = 1;

  const colWidth = Math.floor(TABLE_DXA / totalCols);
  const columnWidths = Array.from({ length: totalCols }, () => colWidth);

  const rows = [];
  trs.forEach((tr) => {
    const cells = [];
    tr.querySelectorAll("th,td").forEach((cell) => {
      const isHeader = cell.tagName.toLowerCase() === "th";

      const paras = [];
      const pushP = (n) => {
        if (n.nodeName === "P") {
          const runs = inlineToRuns(n, isHeader ? { bold: true, font: defaultFont } : { font: defaultFont });
          paras.push(new Paragraph({ children: runs.length ? runs : [new TextRun({ text: "\u00A0", font: defaultFont })] }));
        } else {
          n.childNodes?.forEach(pushP);
        }
      };
      if (cell.childNodes.length) cell.childNodes.forEach(pushP);
      if (!paras.length) paras.push(new Paragraph({ children: [new TextRun({ text: "\u00A0", font: defaultFont })] }));

      const borders = {
        top: { style: BorderStyle.SINGLE, size: 8, color: borderColor },
        bottom: { style: BorderStyle.SINGLE, size: 8, color: borderColor },
        left: { style: BorderStyle.SINGLE, size: 8, color: borderColor },
        right: { style: BorderStyle.SINGLE, size: 8, color: borderColor },
      };

      cells.push(
        new TableCell({
          children: paras,
          borders,
          margins: { top: CELL_PADDING, bottom: CELL_PADDING, left: CELL_PADDING, right: CELL_PADDING },
          verticalAlign: VerticalAlign.CENTER,
          shading: isHeader ? { fill: headerFill } : undefined,
        })
      );
    });
    rows.push(new TableRow({ children: cells }));
  });

  return new Table({
    width: { size: TABLE_DXA, type: WidthType.DXA },
    alignment: AlignmentType.LEFT,
    layout: TableLayoutType.FIXED,
    columnWidths,
    rows,
  });
}

function paragraphsFromBlockquote(el, defaultFont) {
  const paras = [];
  let isFirst = true;
  let lastChildren = null;
  const openQuote = "\u201C";
  const closeQuote = "\u201D"; 
  
  const collectP = (n) => {
    if (n.nodeName === "P") {
      const runs = inlineToRuns(n, { italics: true, font: defaultFont });
      const children = isFirst 
        ? [new TextRun({ text: openQuote, italics: true, font: defaultFont }), ...runs]
        : runs;
      lastChildren = children.length ? children : [new TextRun({ text: "\u00A0", italics: true, font: defaultFont })];
      
      paras.push(
        new Paragraph({
          border: { 
            left: { 
              color: "CCCCCC", 
              size: 24,
              style: BorderStyle.SINGLE
            }
          },
          indent: { left: 720 },
          spacing: { before: 240, after: 240 },
          children: lastChildren,
        })
      );
      isFirst = false;
    } else if (n.nodeType === Node.TEXT_NODE && n.nodeValue?.trim()) {
      const text = isFirst ? openQuote + n.nodeValue : n.nodeValue;
      lastChildren = [new TextRun({ text, italics: true, font: defaultFont })];
      
      paras.push(
        new Paragraph({
          border: { 
            left: { 
              color: "CCCCCC", 
              size: 24, 
              style: BorderStyle.SINGLE
            }
          },
          indent: { left: 720 },
          spacing: { before: 240, after: 240 },
          children: lastChildren,
        })
      );
      isFirst = false;
    } else {
      n.childNodes?.forEach(collectP);
    }
  };
  
  el.childNodes.forEach(collectP);
  
  if (paras.length > 0 && lastChildren) {
    lastChildren.push(new TextRun({ text: closeQuote, italics: true, font: defaultFont }));
  }

  if (!paras.length) {
    paras.push(
      new Paragraph({
        border: { 
          left: { 
            color: "CCCCCC", 
            size: 24, 
            style: BorderStyle.SINGLE
          }
        },
        indent: { left: 720 },
        spacing: { before: 240, after: 240 },
        children: [
          new TextRun({ text: openQuote, italics: true, font: defaultFont }),
          new TextRun({ text: "\u00A0", italics: true, font: defaultFont }),
          new TextRun({ text: closeQuote, italics: true, font: defaultFont })
        ],
      })
    );
  }
  
  return paras;
}

function paragraphWithAlignedImage(bytes, el) {
  const width = parseFloat(el.getAttribute("width") || "560");
  const height = parseFloat(el.getAttribute("height") || "315");

  const datafloat = (el.getAttribute("datafloat") || "").toLowerCase();
  if (datafloat === "left" || datafloat === "right") {
    return new Paragraph({
      spacing: { before: IMG_SPACE_BEFORE, after: IMG_SPACE_AFTER },
      children: [
        new ImageRun({
          data: bytes,
          transformation: { width, height },
          floating: {
            horizontalPosition: {
              relative: HorizontalPositionRelativeFrom.MARGIN,
              align: datafloat === "left" ? HorizontalPositionAlign.LEFT : HorizontalPositionAlign.RIGHT,
            },
            verticalPosition: {
              relative: VerticalPositionRelativeFrom.PARAGRAPH,
              align: VerticalPositionAlign.TOP,
            },
            wrap: {
              type: TextWrappingType.SQUARE,
              side: TextWrappingSide.BOTH_SIDES,
              margin: { top: CELL_PADDING, bottom: CELL_PADDING, left: CELL_PADDING, right: CELL_PADDING },
            },
          },
        }),
      ],
    });
  }

  const alignAttr = (el.getAttribute("data-align") || "center").toLowerCase();
  const alignment =
    alignAttr === "left" ? AlignmentType.LEFT :
    alignAttr === "right" ? AlignmentType.RIGHT :
    AlignmentType.CENTER;

  return new Paragraph({
    alignment,
    spacing: { before: IMG_SPACE_BEFORE, after: IMG_SPACE_AFTER },
    children: [new ImageRun({ data: bytes, transformation: { width, height } })],
  });
}

export async function downloadDocxFromHtml(html, filename, settings = {}) {
  const fontSetting = settings?.font_family || settings?.fontFamily;
  
  const fontMap = {
    caveat: 'var(--font-caveat)',
    'comic-sans': 'var(--font-comic-sans)',
    comfortaa: 'var(--font-comfortaa)',
    'eb-garamond': 'var(--font-eb-garamond)',
    fantasy: 'fantasy',
    geist: 'var(--font-geist)',
    'ibm-plex': 'var(--font-ibm-plex)',
    inter: 'var(--font-inter)',
    jetbrains: 'var(--font-jetbrains)',
    lora: 'var(--font-lora)',
    merriweather: 'var(--font-merriweather)',
    nunito: 'var(--font-nunito)',
  };
  
  const fontVar = fontMap[fontSetting] || fontSetting;
  const defaultFont = cssFontToDocx(fontVar) || "Inter";
  
  const numbering = {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: "bullet",
            text: "•",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: { 
                indent: { left: 720, hanging: 360 },
                spacing: { before: 0, after: 0 } // Remove extra spacing
              },
              run: { font: defaultFont, size: 28 },
            },
          },
        ],
      },
      {
        reference: "numbers",
        levels: [
          {
            level: 0,
            format: "decimal",
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: { 
                indent: { left: 720, hanging: 360 },
                spacing: { before: 0, after: 0 } // Remove extra spacing
              },
              run: { font: defaultFont, size: 28 },
            },
          },
        ],
      },
    ],
  };

  const doc = new DOMParser().parseFromString(html, "text/html");
  const body = doc.body;
  const children = [];

  for (const node of Array.from(body.childNodes)) {
    if (node.nodeType !== Node.ELEMENT_NODE) continue;
    const el = node;
    const tag = el.tagName.toLowerCase();

    if (tag === "p") children.push(paragraphFromP(el, defaultFont));
    else if (tag === "ul") children.push(...paragraphsFromUL(el, defaultFont));
    else if (tag === "ol") children.push(...paragraphsFromOL(el, defaultFont));
    else if (/^h[1-3]$/.test(tag)) children.push(headingFromHx(el, defaultFont));
    else if (tag === "blockquote") children.push(...paragraphsFromBlockquote(el, defaultFont));
    else if (tag === "pre") {
      const runs = [];
      el.childNodes.forEach((n) => runs.push(...inlineToRuns(n, { font: defaultFont })));
      children.push(
        new Paragraph({
          spacing: { before: 120, after: 120 },
          shading: { fill: "0D0D0D" },
          children: runs.length ? runs : [new TextRun({ text: "", font: defaultFont })],
        })
      );
    } else if (tag === "table") {
      children.push(new Paragraph({ children: [new TextRun({ text: "", font: defaultFont })], spacing: { before: TABLE_SPACE_BEFORE } }));
      children.push(tableFromTABLE(el, defaultFont));
      children.push(new Paragraph({ children: [new TextRun({ text: "", font: defaultFont })], spacing: { after: TABLE_SPACE_AFTER } }));
    } else if (tag === "img") {
      const src = el.getAttribute("src");
      if (!src) continue;
      try {
        const bytes = await dataFromUrl(src);
        children.push(paragraphWithAlignedImage(bytes, el));
      } catch (e) {
        console.warn("Image fetch failed:", src, e);
      }
    } else {
      children.push(paragraphFromP(el, defaultFont));
    }
  }

  const docx = new Document({
    styles: {
      default: {
        document: {
          run: {
            font: defaultFont,
            size: 28, // 14pt base font size (28 half-points)
            color: "000000",
          },
        },
      },
      paragraphStyles: [
        {
          id: "Normal",
          name: "Normal",
          run: {
            font: defaultFont,
            size: 28, // 14pt base font size (28 half-points)
            color: "000000",
          },
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              right: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1),
            },
          },
        },
        children: children.length ? children : [new Paragraph({ children: [new TextRun({ text: "", font: defaultFont })] })],
      },
    ],
    numbering,
  });

  const blob = await Packer.toBlob(docx);
  fileSaver.saveAs(blob, filename.endsWith(".docx") ? filename : `${filename}.docx`);
}

export default downloadDocxFromHtml;
export { tableFromTABLE };