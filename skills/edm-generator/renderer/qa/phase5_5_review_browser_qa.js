const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "../..");
const base = "http://127.0.0.1:8876";
const outputDir = path.join(root, "output", "playwright", "phase5_5");

(async () => {
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_EXECUTABLE || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const results = {};

  await page.goto(`${base}/research/switchbot_brand_reverse_engineering.html`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  results.reverse_engineering = await page.evaluate(() => ({
    sample_sections: document.querySelectorAll(".sample[id^='SBG_']").length,
    approved_images: document.querySelectorAll(".approved-proof img").length,
    broken_loaded_images: [...document.images].filter((image) => image.complete && image.naturalWidth === 0).length,
    horizontal_overflow: document.documentElement.scrollWidth > window.innerWidth
  }));
  await page.screenshot({ path: path.join(root, "research", "switchbot_brand_reverse_engineering_preview.png") });
  results.reverse_engineering.responsive = {};
  for (const width of [320, 375, 414, 768]) {
    await page.setViewportSize({ width, height: 900 });
    results.reverse_engineering.responsive[width] = await page.evaluate(() => ({
      no_horizontal_overflow: document.documentElement.scrollWidth <= window.innerWidth,
      broken_loaded_images: [...document.images].filter((image) => image.complete && image.naturalWidth === 0).length
    }));
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/research/brand_calibration_review.html`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  results.brand_calibration_review = await page.evaluate(() => ({
    case_forms: document.querySelectorAll("[data-review-case]").length,
    score_selects: document.querySelectorAll(".score-grid select").length,
    feel_selects: document.querySelectorAll('[data-field="real_switchbot_edm"]').length,
    all_human_fields_blank: [...document.querySelectorAll("[data-case][data-field]")].every((node) => node.value === ""),
    approved_reference_images: document.querySelectorAll(".anchor-tile img").length,
    comparison_images: document.querySelectorAll(".comparison img").length,
    broken_loaded_images: [...document.images].filter((image) => image.complete && image.naturalWidth === 0).length,
    horizontal_overflow: document.documentElement.scrollWidth > window.innerWidth
  }));
  await page.screenshot({ path: path.join(root, "research", "brand_calibration_review_preview.png") });
  results.brand_calibration_review.responsive = {};
  for (const width of [320, 375, 414, 768]) {
    await page.setViewportSize({ width, height: 900 });
    results.brand_calibration_review.responsive[width] = await page.evaluate(() => {
      const button = document.querySelector("#exportCsv");
      return {
        no_horizontal_overflow: document.documentElement.scrollWidth <= window.innerWidth,
        export_button_min_44px: button.getBoundingClientRect().height >= 44,
        export_button_single_line: button.scrollHeight <= button.clientHeight + 1,
        broken_loaded_images: [...document.images].filter((image) => image.complete && image.naturalWidth === 0).length
      };
    });
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#exportCsv").click();
  const download = await downloadPromise;
  const downloadPath = "/private/tmp/brand_calibration_human_review_test.csv";
  await download.saveAs(downloadPath);
  results.brand_calibration_review.csv_export = {
    suggested_filename: download.suggestedFilename(),
    saved: fs.existsSync(downloadPath),
    lines: fs.readFileSync(downloadPath, "utf8").trim().split(/\r?\n/).length
  };

  await browser.close();
  fs.writeFileSync(path.join(outputDir, "review_pages_qa.json"), `${JSON.stringify(results, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
