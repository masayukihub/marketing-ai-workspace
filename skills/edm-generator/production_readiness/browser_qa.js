const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const base = process.env.EDM_BASE_URL || "http://127.0.0.1:8876";
const outputDir = path.join(root, "production_output");
const widths = [320, 375, 414, 768, 1280, 1920];

async function metrics(page) {
  return page.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
    brokenImages: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
    controlsMin44px: [...document.querySelectorAll("button, a.button, select, input, .mobile-header a")]
      .filter((node) => node.getClientRects().length > 0)
      .every((node) => node.getBoundingClientRect().height >= 44),
    clickablesSingleLine: [...document.querySelectorAll("button, a.button, nav a, .mobile-header a, .status")]
      .filter((node) => node.getClientRects().length > 0)
      .every((node) => node.scrollHeight <= node.clientHeight + 1),
    consoleMarker: document.documentElement.dataset.theme,
  }));
}

async function responsiveSweep(page) {
  const result = {};
  for (const width of widths) {
    await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
    result[width] = await metrics(page);
  }
  return result;
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_EXECUTABLE || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/research/production_readiness_dashboard.html`, { waitUntil: "networkidle" });
  const dashboardInitial = await page.evaluate(() => ({
    caseCount: document.querySelectorAll("article.case").length,
    metricCount: document.querySelectorAll(".metric").length,
    visualCandidateCount: [...document.querySelectorAll(".case__score .status")].filter((node) => node.textContent.trim() === "VISUAL_DELIVERABLE_CANDIDATE").length,
    designEvidence: [...document.querySelectorAll(".case__score b")].map((node) => node.textContent.trim()),
    sectionHeadsStacked: [...document.querySelectorAll(".section__head")].every((node) => getComputedStyle(node).display === "block"),
  }));
  const firstBlocker = page.locator("details.blocker").first();
  if (await firstBlocker.count()) await firstBlocker.locator("summary").click();
  await page.screenshot({ path: path.join(outputDir, "phase8_readiness_dashboard_desktop.png"), fullPage: true });
  const dashboardResponsive = await responsiveSweep(page);

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/research/manual_approval_queue.html`, { waitUntil: "networkidle" });
  const queueInitial = await page.evaluate(() => ({
    cardCount: document.querySelectorAll("[data-approval-card]").length,
    ids: [...document.querySelectorAll("[data-approval-card]")].map((node) => node.dataset.approvalId),
    blankDecisionCount: [...document.querySelectorAll('[data-field="human_decision"]')].filter((node) => node.value === "").length,
    blankReviewerCount: [...document.querySelectorAll('[data-field="reviewer"]')].filter((node) => node.value === "").length,
  }));
  const firstCard = page.locator("[data-approval-card]").first();
  await firstCard.locator('[data-field="human_decision"]').selectOption("APPROVE");
  await firstCard.locator('[data-field="reviewer"]').fill("Browser QA Human Placeholder");
  await page.reload({ waitUntil: "networkidle" });
  const persistence = await page.locator("[data-approval-card]").first().evaluate((card) => ({
    decision: card.querySelector('[data-field="human_decision"]').value,
    reviewer: card.querySelector('[data-field="reviewer"]').value,
  }));
  page.on("dialog", (dialog) => dialog.accept());
  await page.locator("#clear-local").click();
  const cleared = await page.locator("[data-approval-card]").first().evaluate((card) => ({
    decision: card.querySelector('[data-field="human_decision"]').value,
    reviewer: card.querySelector('[data-field="reviewer"]').value,
  }));
  const queueDownloadPromise = page.waitForEvent("download");
  await page.locator("#export-approvals").click();
  const queueDownload = await queueDownloadPromise;
  const queueCsvPath = path.join(outputDir, "phase8_human_approvals_blank.csv");
  await queueDownload.saveAs(queueCsvPath);
  const queueCsvRows = fs.readFileSync(queueCsvPath, "utf8").replace(/^\uFEFF/, "").trimEnd().split(/\r?\n/);
  const queueCsvValid = queueCsvRows.length === 3 && queueCsvRows[0].includes("approval_id") && queueCsvRows[0].includes("human_decision");
  await page.screenshot({ path: path.join(outputDir, "phase8_manual_queue_desktop.png"), fullPage: true });
  const queueResponsive = await responsiveSweep(page);

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/research/phase8_visual_delivery_review.html`, { waitUntil: "networkidle" });
  const finalReviewInitial = await page.evaluate(() => ({
    fullImagePresent: Boolean(document.querySelector('.visual-review--desktop img')),
    finalStatus: document.querySelector('.section__head .status')?.textContent.trim(),
    fieldCount: document.querySelectorAll('[data-review-field]').length,
    decisionOptions: [...document.querySelectorAll('#overall_decision option')].map((node) => node.value).filter(Boolean),
    blankReviewFields: [...document.querySelectorAll('[data-review-field]')].filter((node) => node.value === "").length,
  }));
  await page.screenshot({ path: path.join(outputDir, "phase8_visual_review_desktop.png"), fullPage: true });
  const reviewResponsive = await responsiveSweep(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(outputDir, "phase8_visual_review_mobile.png"), fullPage: true });
  const reviewDownloadPromise = page.waitForEvent("download");
  await page.locator("#export-phase8-review").click();
  const reviewDownload = await reviewDownloadPromise;
  const reviewCsvPath = path.join(outputDir, "phase8_lock_ultra_final_review_blank.csv");
  await reviewDownload.saveAs(reviewCsvPath);
  const reviewCsvRows = fs.readFileSync(reviewCsvPath, "utf8").replace(/^\uFEFF/, "").trimEnd().split(/\r?\n/);
  const reviewCsvValid = reviewCsvRows.length === 2 && reviewCsvRows[0].includes("visual_delivery_quality") && reviewCsvRows[0].includes("overall_decision");

  const responsiveRows = [...Object.values(dashboardResponsive), ...Object.values(queueResponsive), ...Object.values(reviewResponsive)];
  const responsivePass = responsiveRows.every((row) => row.noHorizontalOverflow && row.brokenImages === 0 && row.controlsMin44px && row.clickablesSingleLine && row.consoleMarker === "phase7-almanac");
  const status = dashboardInitial.caseCount === 2 && dashboardInitial.metricCount === 12 && dashboardInitial.visualCandidateCount === 1 &&
    dashboardInitial.designEvidence.every((value) => value === "100.0%") && dashboardInitial.sectionHeadsStacked &&
    queueInitial.cardCount === 2 && queueInitial.ids.includes("APR-LOCK-FINAL") && queueInitial.ids.includes("APR-SHARED-ESP") &&
    queueInitial.blankDecisionCount === 2 && queueInitial.blankReviewerCount === 2 && persistence.decision === "APPROVE" &&
    persistence.reviewer === "Browser QA Human Placeholder" && cleared.decision === "" && cleared.reviewer === "" && queueCsvValid &&
    finalReviewInitial.fullImagePresent && finalReviewInitial.finalStatus === "VISUAL_DELIVERABLE_CANDIDATE" && finalReviewInitial.fieldCount === 8 &&
    finalReviewInitial.blankReviewFields === 8 && JSON.stringify(finalReviewInitial.decisionOptions) === JSON.stringify(["APPROVE", "MINOR_REVISION", "MAJOR_REVISION", "REJECT"]) &&
    reviewCsvValid && responsivePass && consoleErrors.length === 0 ? "PASS" : "FAIL";

  const report = {status, dashboardInitial, dashboardResponsive, queueInitial, persistence, cleared, queueCsvValid, queueResponsive, finalReviewInitial, reviewCsvValid, reviewResponsive, responsivePass, consoleErrors};
  fs.writeFileSync(path.join(root, "production_registry", "browser_qa.json"), `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  await browser.close();
  process.exit(status === "PASS" ? 0 : 1);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
