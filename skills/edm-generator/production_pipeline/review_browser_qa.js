const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const base = process.env.EDM_BASE_URL || "http://127.0.0.1:8876";

async function ready(page) {
  await page.evaluate(async () => {
    [...document.images].forEach((image) => { image.loading = "eager"; });
    await document.fonts.ready;
    await Promise.race([
      Promise.all([...document.images].map((image) => image.decode().catch(() => null))),
      new Promise((resolve) => setTimeout(resolve, 8000))
    ]);
  });
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_EXECUTABLE || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().includes("chrome-extension")) consoleErrors.push(message.text());
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(`${base}/research/end_to_end_review.html`, { waitUntil: "domcontentloaded" });
  await ready(page);
  await page.screenshot({ path: path.join(root, "production_output", "end_to_end_review_desktop.png") });

  const initial = await page.evaluate(() => ({
    caseCount: document.querySelectorAll("[data-case-id]").length,
    fieldCount: document.querySelectorAll("[data-review-field]").length,
    blankFieldCount: [...document.querySelectorAll("[data-review-field]")].filter((field) => field.value === "").length,
    anchorCount: document.querySelectorAll(".anchor-band__grid figure").length,
    productionOutputCount: document.querySelectorAll(".visual-grid img").length,
    imageCount: document.images.length,
    brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
    navFingerprintLinks: document.querySelectorAll(".topline a").length,
    footerColumns: document.querySelectorAll(".inline-footer ul").length,
    hardcodedFinalDecision: [...document.querySelectorAll('[data-review-field="final_decision"]')].some((field) => field.value !== "")
  }));

  const responsive = {};
  for (const width of [320, 375, 414, 768, 1280]) {
    await page.setViewportSize({ width, height: width === 1280 ? 800 : 900 });
    await ready(page);
    responsive[width] = await page.evaluate(() => ({
      noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      visibleOverflowNodes: [...document.querySelectorAll("body *")]
        .filter((node) => {
          const style = getComputedStyle(node);
          return style.overflowX === "visible" && node.scrollWidth > node.clientWidth + 1;
        })
        .sort((a, b) => (b.scrollWidth - b.clientWidth) - (a.scrollWidth - a.clientWidth))
        .slice(0, 12)
        .map((node) => ({ tag: node.tagName, className: node.className, clientWidth: node.clientWidth, scrollWidth: node.scrollWidth, text: node.textContent.trim().slice(0, 70) })),
      overflowNodes: [...document.querySelectorAll("body *")]
        .filter((node) => node.getBoundingClientRect().right > window.innerWidth + 1 || node.getBoundingClientRect().left < -1)
        .slice(0, 8)
        .map((node) => ({ tag: node.tagName, className: node.className, left: Math.round(node.getBoundingClientRect().left), right: Math.round(node.getBoundingClientRect().right), scrollWidth: node.scrollWidth })),
      brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
      clickablesSingleLine: [...document.querySelectorAll("button, .output-links a")].every((node) => node.scrollHeight <= node.clientHeight + 1),
      controlsMin44px: [...document.querySelectorAll("button, select")].every((node) => node.getBoundingClientRect().height >= 44)
    }));
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(root, "production_output", "end_to_end_review_mobile.png") });

  const downloadPromise = page.waitForEvent("download");
  await page.click("#export-review");
  const download = await downloadPromise;
  const csvPath = path.join(root, "production_output", "phase6_human_review_blank.csv");
  await download.saveAs(csvPath);
  const csv = fs.readFileSync(csvPath, "utf8");
  const csvRows = csv.trim().split(/\r?\n/);
  const csvValid = csvRows.length === 3 && csvRows[0].includes("brand_fit") && csvRows[0].includes("final_decision") && csvRows.slice(1).every((row) => row.endsWith('",""'));

  const status = initial.caseCount === 2 && initial.fieldCount === 14 && initial.blankFieldCount === 14 &&
    initial.anchorCount === 8 && initial.productionOutputCount === 6 && initial.brokenImages === 0 &&
    !initial.horizontalOverflow && !initial.hardcodedFinalDecision && consoleErrors.length === 0 && csvValid &&
    Object.values(responsive).every((item) => item.noHorizontalOverflow && item.brokenImages === 0 && item.clickablesSingleLine && item.controlsMin44px) ? "PASS" : "FAIL";

  const report = { status, initial, responsive, consoleErrors, csvValid, csvRows: csvRows.length };
  fs.writeFileSync(path.join(root, "production_output", "review_browser_qa.json"), `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  await browser.close();
  process.exit(status === "PASS" ? 0 : 1);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
