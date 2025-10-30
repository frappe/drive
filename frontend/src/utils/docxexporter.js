import {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, ExternalHyperlink,
  Table, TableRow, TableCell, HeadingLevel,
  HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom,
  HorizontalPositionAlign, VerticalPositionAlign,
  TextWrappingType, TextWrappingSide
} from "docx";

async function file_from_url(url, name = "asset", defaultType = "image/jpeg") {
  try {
    const response = await fetch(url);
    const data = await response.blob();
    return new File([data], name, { type: data.type || defaultType });
  } catch (error) {
    console.warn("file_from_url error:", error);
    return new File([""], "empty.txt", { type: "text/plain" });
  }
}

async function array_buffer_from_url(url) {
  const file = await file_from_url(url);
  return await file.arrayBuffer();
}

async function data_from_url(url) {
  const array_buffer = await array_buffer_from_url(url);
  return new Uint8Array(array_buffer);
}

async function get_intrinsic_image_size(url) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight });
    img.onerror = () => resolve({ width: 0, height: 0 });
    img.crossOrigin = "anonymous";
    img.src = url;
  });
}

function scale_down(size, max_width = 600) {
  if (!size || !size.width) return size;
  if (size.width <= max_width) return size;
  const scale = max_width / size.width;
  return { width: size.width * scale, height: size.height * scale };
}

async function canvas_to_image(canvas) {
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  const url = URL.createObjectURL(blob);
  const img = new Image();
  await new Promise((resolve) => {
    img.onload = resolve;
    img.src = url;
  });
  return img;
}

function wrap_lines_in_p(html) {
  const lines = html
    .replaceAll("<br>", "\n")
    .replaceAll("<br/>", "\n")
    .replaceAll("<br />", "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line);
  return lines.map((line) => `<p>${line}</p>`).join("\n");
}

const COLORS = {
    "--red-600": "hsl(0, 70%, 50%)",
  "--orange-600": "hsl(24, 80%, 50%)",
  "--yellow-600": "hsl(48, 90%, 55%)",
  "--green-600": "hsl(142, 55%, 40%)",
  "--teal-600": "hsl(168, 60%, 40%)",
  "--cyan-600": "hsl(187, 70%, 45%)",
  "--blue-600": "hsl(217, 85%, 55%)",
  "--purple-600": "hsl(275, 70%, 55%)",
  "--pink-600": "hsl(330, 75%, 60%)",
  "--gray-600": "hsl(210, 10%, 40%)",
  /* === Prose Semantic Colors === */
  "--prose-color-red": "var(--red-600)",
  "--prose-color-orange": "var(--orange-600)",
  "--prose-color-yellow": "var(--yellow-600)",
  "--prose-color-green": "var(--green-600)",
  "--prose-color-teal": "var(--teal-600)",
  "--prose-color-cyan": "var(--cyan-600)",
  "--prose-color-blue": "var(--blue-600)",
  "--prose-color-purple": "var(--purple-600)",
  "--prose-color-pink": "var(--pink-600)",
  "--prose-color-gray": "var(--gray-600)",

  /* === Typography Defaults === */
  "--prose-font-body": "var(--font-ibm-plex)",
  "--prose-font-heading": "var(--font-lora)",
  "--prose-font-code": "var(--font-jetbrains)",

  /* === Backgrounds & Text === */
  "--prose-bg": "#ffffff",
  "--prose-text": "#111827",
};

const VARS = {
  "--font-ibm-plex": "IBM Plex Sans, Arial, sans-serif",
  "--font-lora": "Lora, Georgia, serif",
  "--font-jetbrains": 'JetBrains Mono, "Courier New", monospace',
  "--outline-gray-2": "#9ca3af",
  "--surface-gray-2": "#f3f4f6",
  "--ink-gray-3": "#9ca3af",

}


function replaceVarsTheme(s) {
  return s
    .replace(/theme\([^)]*\)/g, "")
    .replace(/var\((--[\w-]+)\)/g, (_, k) => VARS[k] || "");
}

const pxToPt = (px) => (parseFloat(px) / 1.3333333) + "pt";

function colorToHex(color) {
  const ctx = document.createElement("canvas").getContext("2d");
  ctx.fillStyle = color || "#000";
  const s = ctx.fillStyle;
  if (s.startsWith("#")) {
    return s.length === 4 ? "#" + [...s.slice(1)].map((c) => c + c).join("") : s;
  }
  const m = s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
  if (!m) return "#000000";
  const to2 = (n) => (+n).toString(16).padStart(2, "0");
  return `#${to2(m[1])}${to2(m[2])}${to2(m[3])}`;
}

function inlineCriticalStyles(html, styles = []) {
  const host = document.createElement("div");
  host.style.all = "initial";
  host.style.position = "fixed";
  host.style.left = "-100000px";
  host.innerHTML = html;
  document.body.appendChild(host);

  // Inject optional CSS (editor/print) into sandbox so computed styles include them
  if (Array.isArray(styles)) {
    styles.forEach((css) => {
      if (!css) return;
      const styleEl = document.createElement("style");
      styleEl.textContent = css;
      host.prepend(styleEl);
    });
  }

  const SEL = "h1,h2,h3,h4,h5,h6,p,li,span,a,strong,em,code,pre,mark,td,th,figcaption";

  host.querySelectorAll(SEL).forEach((el) => {
    const cs = getComputedStyle(el);

    if (!el.style.fontFamily && cs.fontFamily) {
      const fam = cs.fontFamily.split(",")[0].replace(/^["']|["']$/g, "");
      el.style.fontFamily = fam;
    }

    if (!el.style.fontSize && cs.fontSize) {
      const px = parseFloat(cs.fontSize);
      if (Number.isFinite(px)) el.style.fontSize = pxToPt(px);
    }

    if (!el.style.color && cs.color) {
      el.style.color = colorToHex(cs.color);
    }

    // Bold/Italic/Underline/Strike/Transform from computed styles
    const fw = (cs.fontWeight || "").toString();
    if (!el.style.fontWeight && (/^bold$/i.test(fw) || parseInt(fw, 10) >= 700)) {
      el.style.fontWeight = "700";
    }
    if (!el.style.fontStyle && (cs.fontStyle || "").toLowerCase() === "italic") {
      el.style.fontStyle = "italic";
    }
    const tdl = (cs.textDecorationLine || cs.textDecoration || "").toLowerCase();
    if (!el.style.textDecoration && (tdl.includes("underline") || tdl.includes("line-through"))) {
      el.style.textDecoration = [tdl.includes("underline") ? "underline" : "", tdl.includes("line-through") ? "line-through" : ""].filter(Boolean).join(" ");
    }
    const tt = (cs.textTransform || "").toLowerCase();
    if (!el.style.textTransform && (tt === "uppercase" || tt === "capitalize")) {
      el.style.textTransform = tt;
    }

    // Line-height factor + margins and first-line indent
    const lh = cs.lineHeight;
    const fs = cs.fontSize;
    if (lh && fs && lh !== "normal") {
      const lhPx = parseFloat(lh);
      const fsPx = parseFloat(fs);
      if (Number.isFinite(lhPx) && Number.isFinite(fsPx) && fsPx > 0) {
        const factor = lhPx / fsPx;
        el.setAttribute("data-line-factor", String(Math.max(0.5, Math.min(factor, 4))));
      }
      if (!el.style.lineHeight) el.style.lineHeight = lh;
    }
    if (!el.style.marginTop && cs.marginTop) el.style.marginTop = cs.marginTop;
    if (!el.style.marginBottom && cs.marginBottom) el.style.marginBottom = cs.marginBottom;
    if (!el.style.textIndent && cs.textIndent) el.style.textIndent = cs.textIndent;

    // Background color (for inline and block)
    if (!el.style.backgroundColor && cs.backgroundColor && !/rgba?\(0,\s*0,\s*0,\s*0\)/.test(cs.backgroundColor)) {
      el.style.backgroundColor = colorToHex(cs.backgroundColor);
    }
  });

  // Table borders default
  host.querySelectorAll("table,td,th").forEach((el) => {
    if (!el.style.border) el.style.border = "1px solid #9ca3af";
  });

  // dataalign normalization
  host.querySelectorAll("img[dataalign],video[dataalign]").forEach((el) => {
    const a = el.getAttribute("dataalign");
    if (a === "center") { el.style.display = "block"; el.style.marginLeft = "auto"; el.style.marginRight = "auto"; }
    if (a === "left")   { el.style.display = "block"; el.style.marginRight = "auto"; }
    if (a === "right")  { el.style.display = "block"; el.style.marginLeft  = "auto"; }
  });

  // page break nodes
  host.querySelectorAll("#page-break-div").forEach((n) => {
    const p = document.createElement("p");
    p.style.pageBreakAfter = "always";
    p.style.margin = "0";
    n.replaceWith(p);
  });

  const out = host.innerHTML;
  document.body.removeChild(host);
  return out;
}

function preprocessHTML(raw, styles = []) {
  let html = replaceVarsTheme(raw);
  html = html.replace(/color:\s*;?/gi, ""); // remove empty color decls
  return inlineCriticalStyles(html, styles);
}

// =========================
// Theme snapshot from CSS (editor/print) -> DOCX defaults
// =========================
let THEME = null;

function computeThemeSnapshot(styles = []) {
  const host = document.createElement("div");
  host.style.all = "initial";
  host.style.position = "fixed";
  host.style.left = "-100000px";
  document.body.appendChild(host);

  // inject styles
  if (Array.isArray(styles)) {
    styles.forEach((css) => {
      if (!css) return;
      const styleEl = document.createElement("style");
      styleEl.textContent = css;
      host.appendChild(styleEl);
    });
  }

  const sample = document.createElement("div");
  sample.innerHTML = `
    <p id="p">Sample</p>
    <h1 id="h1">H1</h1>
    <h2 id="h2">H2</h2>
    <h3 id="h3">H3</h3>
    <h4 id="h4">H4</h4>
    <h5 id="h5">H5</h5>
    <h6 id="h6">H6</h6>
    <pre id="pre"><code id="code">code</code></pre>
    <table id="table"><tr><th id="th">H</th><td id="td">D</td></tr></table>
  `;
  host.appendChild(sample);

  const bodyCS = getComputedStyle(sample.querySelector("#p"));
  const getFam = (cs) => (cs.fontFamily || "").split(",")[0].replace(/^["']|["']$/g, "");
  const getSizeHP = (cs) => to_halfpoint(cs.fontSize) || 24;
  const getColorHex = (cs) => (to_hex(colorToHex(cs.color)) || "111111");

  const baseFont = replaceVarsTheme(getFam(bodyCS)) || "IBM Plex Sans";
  const baseSize = getSizeHP(bodyCS);
  const baseColor = getColorHex(bodyCS);

  const headFont = replaceVarsTheme(getFam(getComputedStyle(sample.querySelector("#h1")))) || baseFont;
  const hSizes = [1,2,3,4,5,6].map((n) => getSizeHP(getComputedStyle(sample.querySelector(`#h${n}`))));

  const codeFont = replaceVarsTheme(getFam(getComputedStyle(sample.querySelector("#code")))) || 'JetBrains Mono';
  const tableCs = getComputedStyle(sample.querySelector("#td"));
  const thCs = getComputedStyle(sample.querySelector("#th"));
  const tableBorderColor = to_hex(colorToHex(tableCs.borderTopColor)) || "9ca3af";
  const thBg = (() => {
    const bg = thCs.backgroundColor;
    if (!/rgba?\(0,\s*0,\s*0,\s*0\)/.test(bg)) return to_hex(colorToHex(bg));
    return null;
  })() || "f3f4f6";

  document.body.removeChild(host);

  return {
    baseFont,
    baseSize,
    baseColor,
    headFont,
    hSizes,
    codeFont,
    tableBorderColor,
    thBg
  };
}

// =========================
// Parsing helpers
// =========================
function to_halfpoint(str) {
  if (!str) return null;
  str = String(str).trim();
  const rootPx = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;

  let num = parseFloat(str);
  if (!Number.isFinite(num)) return null;

  if (str.endsWith("px")) {
    const pt = num / 1.3333333;
    return Math.round(pt * 2);
  } else if (str.endsWith("pt")) {
    return Math.round(num * 2);
  } else if (str.endsWith("rem")) {
    const px = num * rootPx;
    const pt = px / 1.3333333;
    return Math.round(pt * 2);
  } else if (str.endsWith("em")) {
    const px = num * rootPx;
    const pt = px / 1.3333333;
    return Math.round(pt * 2);
  }
  return null;
}

function rgb_to_hex(rgb) {
  const sep = rgb.indexOf(",") > -1 ? "," : " ";
  const arr = rgb.substr(4).split(")")[0].split(sep);
  let [r, g, b] = arr.map((x) => (+x).toString(16).padStart(2, "0"));
  return r + g + b;
}

function to_hex(str) {
  if (str == null || str === "") return null;
  str = str.trim();

  if (COLORS[str]) return COLORS[str];

  let color;
  if (/^rgba?\(/i.test(str)) {
    color = rgb_to_hex(str);
  } else {
    color = str.replace(/^#/, "");
  }

  if (color.length === 3) color = color.split("").map((c) => c + c).join("");
  if (!/^[0-9A-F]{6}$/i.test(color)) return null; // bug fix (return null if invalid)
  return color;
}

function parse_border(node) {
  const style = {};
  const raw = (node.getAttribute("style") || "").split(";");

  for (let el of raw) {
    const i = el.indexOf(":");
    if (i > 0) style[el.slice(0, i).trim()] = el.slice(i + 1).trim();
  }

  let top, right, bottom, left;

  function edgeFrom(def) {
    if (!def) return null;
    const parts = def.trim().split(/\s+/);
    const size = to_halfpoint(parts[0]) * 4;
    const color = to_hex(parts.slice(2).join(" ").trim());
    return { color, size, space: 1, style: "single" };
  }

  if (style["border"]) {
    const edge = edgeFrom(style["border"]);
    if (edge) top = right = bottom = left = edge;
  }
  if (style["border-left"])  left = edgeFrom(style["border-left"]) || left;
  if (style["border-right"]) right = edgeFrom(style["border-right"]) || right;
  if (style["border-top"])   top  = edgeFrom(style["border-top"])   || top;
  if (style["border-bottom"])bottom= edgeFrom(style["border-bottom"])|| bottom;

  return { top, right, bottom, left };
}

function parse_image_floating(node) {
  const raw = (node.getAttribute("style") || "").split(";");
  const style = {};
  for (let el of raw) {
    const i = el.indexOf(":");
    if (i > 0) style[el.slice(0, i).trim()] = el.slice(i + 1).trim();
  }

  const verticalPosition = {
    relative: VerticalPositionRelativeFrom.TOP_MARGIN,
    align: VerticalPositionAlign.TOP
  };
  const margin = { top: 360000, right: 360000, bottom: 360000, left: 360000 };

  if (style["margin-left"] === "auto" && style["margin-right"] === "auto") {
    return {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.COLUMN, align: HorizontalPositionAlign.CENTER },
      verticalPosition, margin, wrap: { type: TextWrappingType.TOP_AND_BOTTOM, side: TextWrappingSide.BOTH_SIDES }
    };
  }
  if (style["float"] === "left") {
    return {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.COLUMN, align: HorizontalPositionAlign.LEFT },
      verticalPosition, margin, wrap: { type: TextWrappingType.SQUARE, side: TextWrappingSide.RIGHT }
    };
  }
  if (style["float"] === "right") {
    return {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.COLUMN, align: HorizontalPositionAlign.RIGHT },
      verticalPosition, margin, wrap: { type: TextWrappingType.SQUARE, side: TextWrappingSide.LEFT }
    };
  }
  return null;
}

function get_align(node) {
  const raw = node.getAttribute("style");
  if (raw == null) return AlignmentType.LEFT;
  const style = {};
  for (let pair of raw.split(";")) {
    const i = pair.indexOf(":");
    if (i > 0) style[pair.slice(0, i).trim()] = pair.slice(i + 1).trim();
  }
  switch (style["text-align"]) {
    case "left": return AlignmentType.LEFT;
    case "center": return AlignmentType.CENTER;
    case "justify": return AlignmentType.JUSTIFIED;
    case "right": return AlignmentType.RIGHT;
    default: return AlignmentType.LEFT;
  }
}

function parse_style(node) {
  const style = {};
  const dict = {};

  (node.getAttribute("style") || "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean)
    .forEach((pair) => {
      const i = pair.indexOf(":");
      if (i > 0) {
        const k = pair.slice(0, i).trim().toLowerCase();
        const v = pair.slice(i + 1).trim();
        dict[k] = v;
      }
    });

  // background -> shading
  const fill = to_hex(dict["background-color"]);
  if (fill) style["shading"] = { fill };

  // color
  style["color"] = to_hex(dict["color"]);

  // font
  if (dict["font-family"]) {
    let fam = dict["font-family"].split(",")[0].replace(/['"]/g, "").trim();
    fam = replaceVarsTheme(fam);
    style["font"] = fam;
  }

  // size
  style["size"] = to_halfpoint(dict["font-size"]);

  // indent from padding-left
  const indent_left = to_halfpoint(dict["padding-left"]);
  if (Number.isFinite(indent_left)) style["indent"] = { left: indent_left * 10 };

  // First line indent
  const first_line = to_halfpoint(dict["text-indent"]);
  if (Number.isFinite(first_line)) {
    if (!style["indent"]) style["indent"] = {};
    style["indent"].firstLine = first_line * 10;
  }

  // Paragraph spacing from margins (top/bottom) and line height factor
  const beforeHP = to_halfpoint(dict["margin-top"]);
  const afterHP = to_halfpoint(dict["margin-bottom"]);
  if (Number.isFinite(beforeHP) || Number.isFinite(afterHP)) {
    style["_spacing"] = {};
    if (Number.isFinite(beforeHP)) style["_spacing"].before = beforeHP * 10;
    if (Number.isFinite(afterHP)) style["_spacing"].after = afterHP * 10;
  }
  const lfAttr = parseFloat(node.getAttribute("data-line-factor"));
  if (Number.isFinite(lfAttr)) {
    if (!style["_spacing"]) style["_spacing"] = {};
    style["_spacing"].line = Math.round(Math.max(120, Math.min(lfAttr * 240, 960))); // clamp 0.5x-4x
  }

  // transforms & decorations
  const td = (dict["text-decoration"] || "").toLowerCase();
  const tt = (dict["text-transform"] || "").toLowerCase();
  if (tt === "uppercase") style["allCaps"] = true;
  if (tt === "capitalize") style["smallCaps"] = true;
  if (td.includes("line-through")) style["strike"] = true;
  if (td.includes("underline")) style["underline"] = true;
  if ((dict["font-style"] || "").toLowerCase() === "italic") style["italics"] = true;

  const fw = (dict["font-weight"] || "").toLowerCase();
  if (fw === "bold" || parseInt(fw, 10) >= 700) style["bold"] = true;

  const allow = new Set(["color","shading","size","indent","allCaps","smallCaps","strike","font","italics","underline","bold","_spacing"]);
  Object.keys(style).forEach((k) => { if (style[k] == null || !allow.has(k)) delete style[k]; });

  return style;
}

function group_orphaned_elements(container) {
  const validParents = new Set(["p","pre","div","table","h1","h2","h3","h4","h5","h6","ul","ol","figure","figcaption"]);

  function isOrphaned(element) {
    let current = element.parentElement;
    while (current && current !== container) {
      if (validParents.has(current.tagName.toLowerCase())) return false;
      current = current.parentElement;
    }
    return true;
  }

  function isInlineElement(element) {
    if (element.nodeType === Node.TEXT_NODE) return true;
    if (element.nodeType !== Node.ELEMENT_NODE) return false;
    const tagName = element.tagName.toLowerCase();
    const inlineElements = new Set([
      "a","abbr","acronym","b","bdo","big","br","button","cite","code","dfn","em","i","img","input",
      "kbd","label","map","object","q","samp","script","select","small","span","strong","sub","sup",
      "textarea","time","tt","var"
    ]);
    return inlineElements.has(tagName) || window.getComputedStyle(element).display.includes("inline");
  }

  function isWhitespaceOnly(textNode) {
    return /^\s*$/.test(textNode.textContent);
  }

  function processChildren(parent) {
    const children = Array.from(parent.childNodes);
    let i = 0;

    while (i < children.length) {
      const child = children[i];
      if (!parent.contains(child)) { i++; continue; }

      if (child.nodeType === Node.ELEMENT_NODE && !isInlineElement(child)) {
        processChildren(child); i++; continue;
      }

      const isChildOrphaned = isOrphaned(child);
      const isChildInline = isInlineElement(child);
      const isSignificantText = child.nodeType === Node.TEXT_NODE && !isWhitespaceOnly(child);

      if (isChildOrphaned && (isChildInline || isSignificantText)) {
        const orphanedGroup = [];
        let j = i;

        while (j < children.length) {
          const currentChild = children[j];
          if (!parent.contains(currentChild)) { j++; continue; }

          const isCurrentOrphaned = isOrphaned(currentChild);
          const isCurrentInline = isInlineElement(currentChild);
          const isCurrentSignificantText = currentChild.nodeType === Node.TEXT_NODE && !isWhitespaceOnly(currentChild);

          if (currentChild.nodeType === Node.ELEMENT_NODE &&
              currentChild.tagName.toLowerCase() === "br" &&
              isCurrentOrphaned) {
            orphanedGroup.push(currentChild); j++; break;
          }

          if (currentChild.nodeType === Node.ELEMENT_NODE &&
              currentChild.tagName.toLowerCase() === "img" &&
              isCurrentOrphaned) {
            const imgDisplay = window.getComputedStyle(currentChild).display;
            if (imgDisplay === "block" || imgDisplay === "block-inline") {
              if (orphanedGroup.length > 0 && orphanedGroup.some(node =>
                    node.nodeType === Node.ELEMENT_NODE || (node.nodeType === Node.TEXT_NODE && !isWhitespaceOnly(node)))) {
                break;
              }
              const imgP = document.createElement("p");
              parent.insertBefore(imgP, currentChild);
              imgP.appendChild(currentChild);
              const newChildren = Array.from(parent.childNodes);
              const imgPIndex = newChildren.indexOf(imgP);
              i = imgPIndex + 1;
              children.length = 0; children.push(...newChildren);
              break;
            } else {
              orphanedGroup.push(currentChild); j++;
            }
          } else if (isCurrentOrphaned && (isCurrentInline || isCurrentSignificantText)) {
            orphanedGroup.push(currentChild); j++;
          } else if (currentChild.nodeType === Node.TEXT_NODE && isWhitespaceOnly(currentChild)) {
            orphanedGroup.push(currentChild); j++;
          } else {
            break;
          }
        }

        const hasSignificantContent = orphanedGroup.some(node =>
          node.nodeType === Node.ELEMENT_NODE || (node.nodeType === Node.TEXT_NODE && !isWhitespaceOnly(node))
        );

        if (hasSignificantContent && orphanedGroup.length > 0) {
          const p = document.createElement("p");
          parent.insertBefore(p, orphanedGroup[0]);
          orphanedGroup.forEach((node) => { if (parent.contains(node)) p.appendChild(node); });
          const newChildren = Array.from(parent.childNodes);
          const pIndex = newChildren.indexOf(p);
          i = pIndex + 1;
          children.length = 0; children.push(...newChildren);
          if (j < children.length) continue;
        } else {
          i = j;
        }
      } else {
        i++;
      }
    }
  }
  processChildren(container);
}

// =========================
// Builders
// =========================
async function build_paragraph(node) {
  const style = parse_style(node);
  if (style.size == null) style.size = 24;
  if (style.font == null && node.nodeName === "PRE") style.font = "Courier New";

  const children = await build_child_nodes(node, style);
  const alignment = get_align(node);
  const border = parse_border(node);

  if (node.parentElement?.nodeName === "BLOCKQUOTE") {
    if (border.left == null) border.left = { color: "cbd5e1", size: 16, space: 1, style: "single" };
    if (style.indent == null || style.indent.left === 0) style.indent = { left: 80 };
  }

  return new Paragraph({ alignment, indent: style.indent, spacing: style._spacing, children, border });
}

async function build_table(node) {
  const rows = [];
  for (let row of node.querySelectorAll("tr")) {
    const cells = [];
    for (let cell of row.querySelectorAll("th, td")) {
      const style = parse_style(cell);
      const paras = [new Paragraph({ alignment: get_align(cell), indent: style.indent, spacing: style._spacing, children: await build_child_nodes(cell) })];

      const isTh = cell.nodeName === "TH";
      const cellOpts = { children: paras };

      const borderColor = to_hex((cell.getAttribute("style") || "").match(/border-color:\s*([^;]+)/)?.[1]) || "9ca3af";
      cellOpts.borders = {
        top: { size: 8, color: borderColor },
        bottom: { size: 8, color: borderColor },
        left: { size: 8, color: borderColor },
        right: { size: 8, color: borderColor }
      };

      if (isTh) {
        cellOpts.shading = { fill: "f3f4f6" }; // surface gray
      }

      cells.push(new TableCell(cellOpts));
    }
    rows.push(new TableRow({ children: cells }));
  }
  const numCols = node.querySelector("tr")?.querySelectorAll("th, td")?.length || 1;
  return new Table({
    rows,
    width: 0,
    columnWidths: Array(numCols).fill(Math.floor(9638 / numCols), 0, numCols)
  });
}

async function build_heading(node) {
  const style = parse_style(node);
  const children = await build_child_nodes(node, style);
  const alignment = get_align(node);

  let heading;
  switch (node.nodeName) {
    case "H1": heading = HeadingLevel.HEADING_1; break;
    case "H2": heading = HeadingLevel.HEADING_2; break;
    case "H3": heading = HeadingLevel.HEADING_3; break;
    case "H4": heading = HeadingLevel.HEADING_4; break;
    case "H5": heading = HeadingLevel.HEADING_5; break;
    case "H6": heading = HeadingLevel.HEADING_6; break;
  }

  const border = parse_border(node);
  return new Paragraph({ alignment, children, indent: style.indent, heading, border });
}

async function build_ul(node, instance) {
  const list = [];
  for (let li of node.querySelectorAll(":scope > li")) {
    list.push(new Paragraph({ children: await build_child_nodes(li), bullet: { level: 0, instance } }));
    if (li.querySelectorAll == null) continue;
    for (let sub_li of li.querySelectorAll("ul li")) {
      list.push(new Paragraph({ children: await build_child_nodes(sub_li), bullet: { level: 1, instance } }));
    }
  }
  return list;
}

async function build_ol(node, instance) {
  const list = [];
  for (let li of node.querySelectorAll(":scope > li")) {
    list.push(new Paragraph({ children: await build_child_nodes(li), numbering: { reference: "arabic", instance, level: 0 } }));
    if (li.querySelectorAll == null) continue;
    for (let sub_li of li.querySelectorAll("ol li")) {
      list.push(new Paragraph({ children: await build_child_nodes(sub_li), numbering: { reference: "arabic", instance, level: 1 } }));
    }
  }
  return list;
}

async function build_child_nodes(node, inherit_attr) {
  if (inherit_attr == null) inherit_attr = {};
  let values = [];
  for (let child of node.childNodes) {
    if (child.nodeName === "#text") {
      values.push(new TextRun({
        text: child.nodeValue,
        bold: inherit_attr.bold,
        italics: inherit_attr.italics,
        subScript: inherit_attr.subScript,
        superScript: inherit_attr.superScript,
        strike: inherit_attr.strike,
        underline: inherit_attr.underline ? {} : null,
        color: inherit_attr.color,
        shading: inherit_attr.shading,
        size: inherit_attr.size,
        allCaps: inherit_attr.allCaps,
        font: inherit_attr.font,
        style: inherit_attr.style
      }));
    } else if (child.nodeName === "A" && child.getAttribute("href")) {
      values.push(new ExternalHyperlink({
        children: await build_child_nodes(child, { style: "Hyperlink" }),
        link: child.getAttribute("href")
      }));
    } else if (child.nodeName === "IMG") {
      const data = await data_from_url(child.src);
      const floating = parse_image_floating(child);
      let size = { width: child.width, height: child.height };
      const intrinsic = await get_intrinsic_image_size(child.src);

      if ((size.width || 0) === 0 && (size.height || 0) === 0) size = intrinsic;
      else if (!size.width) size.width = size.height * (intrinsic.width / intrinsic.height || 1);
      else if (!size.height) size.height = size.width * (intrinsic.height / intrinsic.width || 1);

      values.push(new ImageRun({
        data,
        transformation: scale_down(size),
        floating
      }));
    } else if (child.nodeName === "CANVAS") {
      const image = await canvas_to_image(child);
      const data = await data_from_url(image.src);
      const floating = parse_image_floating(image);
      let size = { width: image.width, height: image.height };
      const intrinsic = await get_intrinsic_image_size(image.src);
      if (!size.width) size = intrinsic;

      values.push(new ImageRun({
        data,
        transformation: scale_down(size),
        floating
      }));
    } else if (node.childNodes.length > 0 && !["UL", "OL"].includes(node.nodeName)) {
      const passed = { ...inherit_attr, ...parse_style(child) };
      if (child.nodeName === "STRONG") passed.bold = true;
      if (child.nodeName === "EM") passed.italics = true;
      if (child.nodeName === "SUB") passed.subScript = true;
      if (child.nodeName === "SUP") passed.superScript = true;
      if (child.nodeName === "S") passed.strike = true;
      if (child.nodeName === "U") passed.underline = true;
      if (child.nodeName === "A") { passed.anchor = child.getAttribute("href"); passed.underline = true; }
      values = values.concat(await build_child_nodes(child, passed));
    }
  }
  return values;
}

export default async function html2docx(html, options = {}) {
  const { strict = false, styles = [] } = options || {};
  // PREPROCESS first (resolve vars/theme + stamp inline styles so Word/Pages keep them)
  let raw;
  if (typeof html === "string") {
    raw = preprocessHTML(html, styles);
  } else {
    raw = preprocessHTML(html.documentElement.outerHTML, styles);
  }

  let document = new DOMParser().parseFromString(raw, "text/html");

  // Move figcaption after figure (your rule)
  document.querySelectorAll("figure").forEach((figure) => {
    const caption = figure.querySelector("figcaption");
    if (caption) figure.after(caption);
  });

  if (!strict) {
    group_orphaned_elements(document.body);
  }

  let docx_elements = [];
  let nodes = Array.from(document.querySelectorAll("p,pre,table,h1,h2,h3,h4,h5,h6,ul,ol,div,figure,figcaption"));

  // Keep only top-level (non-nested) nodes
  nodes = nodes.filter((node) => !nodes.filter((el) => el !== node).some((el) => el.contains(node)));

  if (nodes.length === 0) {
    document = new DOMParser().parseFromString(wrap_lines_in_p(document.body.innerHTML), "text/html");
    nodes = Array.from(document.querySelectorAll("p"));
  }

  for (let node of nodes) {
    const instance = nodes.indexOf(node);
    if (["P", "PRE", "DIV", "FIGURE", "FIGCAPTION"].includes(node.nodeName)) {
      docx_elements.push(await build_paragraph(node));
    } else if (node.nodeName === "TABLE") {
      docx_elements.push(await build_table(node));
    } else if (["H1","H2","H3","H4","H5","H6"].includes(node.nodeName)) {
      docx_elements.push(await build_heading(node));
    } else if (node.nodeName === "UL") {
      docx_elements.push(...(await build_ul(node, instance)));
    } else if (node.nodeName === "OL") {
      docx_elements.push(...(await build_ol(node, instance)));
    }
  }

  const docx = new Document({
    sections: [{ children: docx_elements }],
    numbering: {
      config: [{
        reference: "arabic",
        levels: [
          { level: 0, format: "decimal", text: "%1", alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 300, hanging: 200 } } } },
          { level: 1, format: "decimal", text: "%1.%2", alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 600, hanging: 200 } } } }
        ]
      }]
    }
  });

  const blob = await Packer.toBlob(docx);
  return blob;
}
