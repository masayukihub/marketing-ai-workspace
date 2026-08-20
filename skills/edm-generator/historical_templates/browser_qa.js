const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const cases = ["HIST-VAL-001", "HIST-VAL-002", "HIST-VAL-003", "HIST-VAL-004"];

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });
  const results = [];
  for (const caseId of cases) {
    const file = path.join(root, "output", "historical_template_tests", caseId, "editable_edm.html");
    const url = pathToFileURL(file).href;
    const page = await browser.newPage({ viewport: { width: 600, height: 900 }, deviceScaleFactor: 1 });
    const consoleErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    await page.goto(url, { waitUntil: "load" });
    await page.evaluate(async () => {
      await document.fonts.ready;
      [...document.images].forEach((image) => { image.loading = "eager"; });
      await Promise.race([
        Promise.all([...document.images].map((image) => image.decode().catch(() => null))),
        new Promise((resolve) => setTimeout(resolve, 2500))
      ]);
    });
    const out = path.dirname(file);
    await page.screenshot({ path: path.join(out, "generated_full.png"), fullPage: true });
    await page.screenshot({ path: path.join(out, "generated_desktop.png") });

    const widths = {};
    for (const width of [320, 375, 414, 768, 1280]) {
      await page.setViewportSize({ width, height: width === 1280 ? 800 : 844 });
      await page.waitForTimeout(30);
      widths[width] = await page.evaluate(() => ({
        viewport: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
        brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
        canvasWidth: Math.round(document.querySelector(".email-canvas").getBoundingClientRect().width),
        ctaCount: document.querySelectorAll(".cta-box a").length,
        footerPresent: Boolean(document.querySelector(".deep-footer"))
      }));
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, "generated_mobile.png") });

    await page.setViewportSize({ width: 600, height: 900 });
    const measurement = await page.evaluate(() => {
      const rows = [...document.querySelectorAll("[data-region]")].map((section) => ({
        region: section.dataset.region,
        target: Number(section.dataset.targetRatio),
        height: Math.round(section.getBoundingClientRect().height)
      }));
      const actualMean = rows.reduce((sum, row) => sum + row.height, 0) / rows.length;
      const targetMean = rows.reduce((sum, row) => sum + row.target, 0) / rows.length;
      rows.forEach((row) => {
        row.actualNormalized = Number((row.height / actualMean).toFixed(3));
        row.targetNormalized = Number((row.target / targetMean).toFixed(3));
      });
      const error = rows.reduce((sum, row) => sum + Math.abs(row.actualNormalized - row.targetNormalized), 0) / rows.length;
      const rhythmScore = Math.max(0, Math.round(100 - error * 70));
      return {
        templateId: document.body.dataset.templateId,
        referenceId: document.body.dataset.referenceId,
        regionCount: rows.length,
        regionOrder: rows.map((row) => row.region),
        rows,
        rhythmScore,
        historicalInheritanceDeclared: Number(document.body.dataset.historicalInheritance),
        controlledAdaptationDeclared: Number(document.body.dataset.controlledAdaptation),
        newDesignDeclared: Number(document.body.dataset.newDesign),
        ctaPresent: Boolean(document.querySelector(".cta-box a")),
        footerPresent: Boolean(document.querySelector(".deep-footer")),
        productImagesUseLocalApprovedAssets: [...document.images].every((image) => image.getAttribute("src").startsWith("assets/"))
      };
    });
    const structuralSimilarity = Math.round(
      100 * 0.4 + measurement.rhythmScore * 0.35 + (measurement.footerPresent ? 100 : 0) * 0.15 + (measurement.ctaPresent ? 100 : 0) * 0.1
    );
    const result = {
      caseId,
      ...measurement,
      similarityType: "browser-measured generated rhythm vs visually-extracted historical rhythm; not pixel similarity",
      structuralVisualSimilarity: structuralSimilarity,
      widths,
      consoleErrors,
      qaPass: Object.values(widths).every((row) => row.noHorizontalOverflow && row.brokenImages === 0 && row.footerPresent) && consoleErrors.length === 0
    };
    fs.writeFileSync(path.join(out, "browser_visual_qa.json"), JSON.stringify(result, null, 2));
    results.push(result);
    await page.close();
  }
  await browser.close();
  const summary = {
    generatedAt: new Date().toISOString(),
    caseCount: results.length,
    passCount: results.filter((row) => row.qaPass).length,
    averageStructuralVisualSimilarity: Number((results.reduce((sum, row) => sum + row.structuralVisualSimilarity, 0) / results.length).toFixed(1)),
    results
  };
  fs.writeFileSync(path.join(root, "output", "historical_template_tests", "browser_qa.json"), JSON.stringify(summary, null, 2));
  process.stdout.write(`${JSON.stringify({ passCount: summary.passCount, caseCount: summary.caseCount, averageStructuralVisualSimilarity: summary.averageStructuralVisualSimilarity })}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
