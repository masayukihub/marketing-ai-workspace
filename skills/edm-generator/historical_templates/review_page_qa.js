const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const file = path.join(root, "research", "historical_template_validation.html");

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  await page.goto(pathToFileURL(file).href, { waitUntil: "load" });
  await page.evaluate(async () => {
    [...document.images].forEach((image) => { image.loading = "eager"; });
    await Promise.race([
      Promise.all([...document.images].map((image) => image.decode().catch(() => null))),
      new Promise((resolve) => setTimeout(resolve, 3500))
    ]);
  });
  await page.screenshot({ path: path.join(root, "output", "historical_template_tests", "review_page_desktop.png"), fullPage: false });
  const widths = {};
  for (const width of [320, 375, 414, 768, 1280, 1920]) {
    await page.setViewportSize({ width, height: width >= 1280 ? 800 : 844 });
    await page.waitForTimeout(30);
    widths[width] = await page.evaluate(() => ({
      viewport: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
      brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
      caseCount: document.querySelectorAll("[data-review-case]").length,
      humanFieldCount: document.querySelectorAll("[data-human-field]").length,
      prefilledHumanFieldCount: [...document.querySelectorAll("[data-human-field]")].filter((field) => field.value !== "").length,
      comparisonColumns: getComputedStyle(document.querySelector(".comparison")).gridTemplateColumns,
      exportButtonVisible: document.querySelector("[data-export-review]").getBoundingClientRect().height >= 44
    }));
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(root, "output", "historical_template_tests", "review_page_mobile.png"), fullPage: false });
  const finalOptions = await page.locator('[data-human-field="final_decision"]').first().locator("option").allTextContents();
  const result = {
    generatedAt: new Date().toISOString(),
    widths,
    finalDecisionOptions: finalOptions,
    consoleErrors: errors,
    pass: Object.values(widths).every((row) => row.noHorizontalOverflow && row.brokenImages === 0 && row.caseCount === 4 && row.humanFieldCount === 28 && row.prefilledHumanFieldCount === 0) &&
      JSON.stringify(finalOptions) === JSON.stringify(["未填写", "DELIVERABLE", "MINOR_REVISION", "MAJOR_REVISION", "WRONG_TEMPLATE"]) && errors.length === 0
  };
  fs.writeFileSync(path.join(root, "output", "historical_template_tests", "review_page_qa.json"), JSON.stringify(result, null, 2));
  await browser.close();
  process.stdout.write(`${JSON.stringify({ pass: result.pass, widths: Object.keys(widths), consoleErrors: errors.length })}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
