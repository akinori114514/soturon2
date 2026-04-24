import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import pptxgen from "pptxgenjs";

const SLIDE_W = 13.333;
const SLIDE_H = 7.5;

function extractYamlBlock(markdown) {
  const match = markdown.match(/```yaml\s*([\s\S]*?)```/);
  if (!match) {
    throw new Error("outline.md に YAML ブロックが見つかりません。");
  }
  return match[1];
}

function normalizeSources(sources) {
  if (!sources || (Array.isArray(sources) && sources.length === 0)) {
    return "(要出典)";
  }
  if (Array.isArray(sources)) {
    return sources.join("; ");
  }
  return String(sources);
}

function addTitle(slide, text, spec) {
  slide.addText(text, {
    x: spec.margins.left,
    y: spec.layout.titleY,
    w: spec.layout.contentW,
    h: spec.layout.titleH,
    fontFace: spec.fonts.title,
    fontSize: spec.sizes.title,
    color: spec.colors.text,
    bold: true,
  });
}

function addBullets(slide, bullets, spec, box) {
  if (!bullets || bullets.length === 0) return;
  const runs = bullets.map((text) => ({
    text,
    options: { bullet: { indent: spec.bullet.indent, hanging: spec.bullet.hanging } },
  }));
  slide.addText(runs, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fontFace: spec.fonts.body,
    fontSize: spec.sizes.body,
    color: spec.colors.text,
    valign: "top",
    lineSpacingMultiple: 1.15,
  });
}

function addSources(slide, sources, spec) {
  const sourceText = `Sources: ${normalizeSources(sources)}`;
  slide.addText(sourceText, {
    x: spec.margins.left,
    y: spec.layout.sourcesY,
    w: spec.layout.contentW,
    h: spec.layout.sourcesH,
    fontFace: spec.fonts.body,
    fontSize: spec.sizes.sources,
    color: spec.colors.muted,
    valign: "top",
  });
}

function addTitleSlide(slide, data, spec) {
  slide.addText(data.title, {
    x: spec.margins.left,
    y: 1.2,
    w: spec.layout.contentW,
    h: 1.2,
    fontFace: spec.fonts.title,
    fontSize: 44,
    color: spec.colors.text,
    bold: true,
    align: "center",
    valign: "mid",
  });

  if (data.bullets && data.bullets.length > 0) {
    slide.addText(data.bullets.join("\n"), {
      x: spec.margins.left,
      y: 2.8,
      w: spec.layout.contentW,
      h: 1.6,
      fontFace: spec.fonts.body,
      fontSize: spec.sizes.subtitle,
      color: spec.colors.text,
      align: "center",
      valign: "top",
    });
  }
}

function addBulletSlide(slide, data, spec) {
  addTitle(slide, data.title, spec);
  addBullets(slide, data.bullets, spec, {
    x: spec.margins.left,
    y: spec.layout.bodyY,
    w: spec.layout.contentW,
    h: spec.layout.bodyH,
  });
}

function addTwoColumnSlide(slide, data, spec) {
  addTitle(slide, data.title, spec);

  const gap = 0.4;
  const colW = (spec.layout.contentW - gap) / 2;
  const leftX = spec.margins.left;
  const rightX = spec.margins.left + colW + gap;
  const colY = spec.layout.bodyY;
  const colH = spec.layout.bodyH;
  let leftY = colY;
  let rightY = colY;

  if (data.left_title) {
    slide.addText(data.left_title, {
      x: leftX,
      y: leftY,
      w: colW,
      h: 0.4,
      fontFace: spec.fonts.body,
      fontSize: spec.sizes.small,
      color: spec.colors.accent,
      bold: true,
    });
    leftY += 0.4;
  }

  if (data.right_title) {
    slide.addText(data.right_title, {
      x: rightX,
      y: rightY,
      w: colW,
      h: 0.4,
      fontFace: spec.fonts.body,
      fontSize: spec.sizes.small,
      color: spec.colors.accent,
      bold: true,
    });
    rightY += 0.4;
  }

  addBullets(slide, data.left_bullets, spec, {
    x: leftX,
    y: leftY,
    w: colW,
    h: colH - (leftY - colY),
  });

  addBullets(slide, data.right_bullets, spec, {
    x: rightX,
    y: rightY,
    w: colW,
    h: colH - (rightY - colY),
  });
}

function addFigureSlide(slide, data, spec) {
  addTitle(slide, data.title, spec);
  const hasBullets = data.bullets && data.bullets.length > 0;
  const bulletH = hasBullets ? 0.9 : 0;

  if (hasBullets) {
    addBullets(slide, data.bullets, spec, {
      x: spec.margins.left,
      y: spec.layout.bodyY,
      w: spec.layout.contentW,
      h: bulletH,
    });
  }

  const figY = spec.layout.bodyY + bulletH + 0.1;
  const figH = spec.layout.bodyH - bulletH - 0.3;
  slide.addShape(spec.shapeType.rect, {
    x: spec.margins.left,
    y: figY,
    w: spec.layout.contentW,
    h: figH,
    line: { color: spec.colors.accent, width: 1 },
    fill: { color: spec.colors.light },
  });

  slide.addText("図・表（差し替え）", {
    x: spec.margins.left,
    y: figY + figH / 2 - 0.2,
    w: spec.layout.contentW,
    h: 0.4,
    fontFace: spec.fonts.body,
    fontSize: spec.sizes.small,
    color: spec.colors.muted,
    align: "center",
    valign: "mid",
  });

  if (data.figure && data.figure.label) {
    slide.addText(data.figure.label, {
      x: spec.margins.left,
      y: figY + figH + 0.05,
      w: spec.layout.contentW,
      h: 0.3,
      fontFace: spec.fonts.body,
      fontSize: spec.sizes.small,
      color: spec.colors.text,
      align: "center",
      valign: "top",
    });
  }
}

async function main() {
  const root = process.cwd();
  const outlinePath = path.join(root, "outline.md");
  const specPath = path.join(root, "deck_spec.yml");
  const outlineMd = fs.readFileSync(outlinePath, "utf8");
  const outlineYaml = extractYamlBlock(outlineMd);
  const outline = yaml.load(outlineYaml);

  if (!outline || !Array.isArray(outline.slides)) {
    throw new Error("outline.md の YAML に slides 配列が必要です。");
  }

  const specRaw = yaml.load(fs.readFileSync(specPath, "utf8"));
  const spec = {
    fonts: specRaw.fonts,
    colors: specRaw.colors,
    sizes: specRaw.font_sizes,
    margins: specRaw.margins,
    bullet: specRaw.bullet,
    layout: {},
  };

  spec.layout.contentW = SLIDE_W - spec.margins.left - spec.margins.right;
  spec.layout.titleY = spec.margins.top;
  spec.layout.titleH = 0.6;
  spec.layout.bodyY = spec.layout.titleY + spec.layout.titleH + 0.2;
  spec.layout.sourcesH = 0.4;
  spec.layout.sourcesY = SLIDE_H - spec.margins.bottom - spec.layout.sourcesH;
  spec.layout.bodyH = spec.layout.sourcesY - spec.layout.bodyY - 0.1;

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "卒論発表";
  pptx.theme = {
    headFontFace: spec.fonts.title,
    bodyFontFace: spec.fonts.body,
    lang: "ja-JP",
  };
  spec.shapeType = pptx.ShapeType;

  for (const slideData of outline.slides) {
    const slide = pptx.addSlide();
    const layout = slideData.layout || "bullets";

    if (layout === "title") {
      addTitleSlide(slide, slideData, spec);
    } else if (layout === "two-column") {
      addTwoColumnSlide(slide, slideData, spec);
    } else if (layout === "figure") {
      addFigureSlide(slide, slideData, spec);
    } else {
      addBulletSlide(slide, slideData, spec);
    }

    addSources(slide, slideData.sources, spec);
  }

  const distDir = path.join(root, "dist");
  fs.mkdirSync(distDir, { recursive: true });
  const outPath = path.join(distDir, "deck.pptx");
  await pptx.writeFile({ fileName: outPath });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
