const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const base = process.env.EDM_BASE_URL || "http://127.0.0.1:8876";
const cases = process.argv.slice(2).length > 0
  ? process.argv.slice(2)
  : ["PILOT-A-LOCK-ULTRA", "PILOT-B-DAILY-STATION"];

async function ready(page) {
  await page.evaluate(async () => {
    [...document.images].forEach((image) => { image.loading = "eager"; });
    await document.fonts.ready;
    await Promise.race([
      Promise.all([...document.images].map((image) => image.decode().catch(() => null))),
      new Promise((resolve) => setTimeout(resolve, 5000))
    ]);
  });
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_EXECUTABLE || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });
  const results = {};

  for (const caseId of cases) {
    const outputDir = path.join(root, "production_output", caseId);
    const page = await browser.newPage({ viewport: { width: 600, height: 900 }, deviceScaleFactor: 1 });
    const consoleErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error" && !message.text().includes("chrome-extension")) consoleErrors.push(message.text());
    });
    await page.goto(`${base}/production_output/${caseId}/editable_edm.html`, { waitUntil: "domcontentloaded" });
    await ready(page);
    const desktop = await page.evaluate(() => ({
      productionStatus: document.body.dataset.productionStatus,
      renderMode: document.body.dataset.renderMode,
      totalLengthPx: document.documentElement.scrollHeight,
      documentWidthPx: Math.round(document.querySelector(".email-canvas").getBoundingClientRect().width),
      moduleCount: document.querySelectorAll("[data-module]").length,
      moduleSequence: [...document.querySelectorAll("[data-module]")].map((node) => node.dataset.module),
      imageCount: document.images.length,
      brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
      ctaCount: document.querySelectorAll("a.sb-cta").length,
      validHttpLinks: [...document.links].every((link) => /^https:\/\//.test(link.href)),
      runtimeTokens: document.querySelectorAll("[data-runtime-token]").length,
      footerComponent: document.querySelector("[data-footer-component]")?.dataset.footerComponent || null,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth
    }));
    await page.screenshot({ path: path.join(outputDir, "desktop_preview.png") });
    await page.screenshot({ path: path.join(outputDir, "full_edm.png"), fullPage: true });

    await page.setViewportSize({ width: 390, height: 844 });
    await ready(page);
    await page.screenshot({ path: path.join(outputDir, "mobile_preview.png") });

    const responsive = {};
    for (const width of [320, 375, 390, 414, 768]) {
      await page.setViewportSize({ width, height: 900 });
      responsive[width] = await page.evaluate(() => ({
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
        brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
        ctasMin44px: [...document.querySelectorAll("a.sb-cta")].every((node) => node.getBoundingClientRect().height >= 44),
        ctasSingleLine: [...document.querySelectorAll("a.sb-cta")].every((node) => node.scrollHeight <= node.clientHeight + 1)
      }));
    }
    await page.close();
    results[caseId] = {
      status: desktop.brokenImages === 0 && !desktop.horizontalOverflow && consoleErrors.length === 0 && Object.values(responsive).every((item) => item.noHorizontalOverflow && item.brokenImages === 0 && item.ctasMin44px && item.ctasSingleLine) ? "PASS" : "FAIL",
      desktop,
      responsive,
      consoleErrors,
      files: {
        desktop_preview: `production_output/${caseId}/desktop_preview.png`,
        mobile_preview: `production_output/${caseId}/mobile_preview.png`,
        full_edm: `production_output/${caseId}/full_edm.png`
      }
    };
  }
  await browser.close();
  const output = path.join(root, "production_output", "browser_qa.json");
  fs.writeFileSync(output, `${JSON.stringify(results, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
