import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

function arg(name, fallback = "") {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

const outputDir = path.resolve(arg("--output"));
const baseUrl = arg("--base-url").replace(/\/$/, "");
if (!outputDir || !baseUrl) throw new Error("Usage: node scripts/browser_qa_v4.mjs --output <dir> --base-url <url>");

const spec = JSON.parse(await fs.readFile(path.join(outputDir, "spec", "PRODUCT_PAGE_SPEC.json"), "utf8"));
const qaDir = path.join(outputDir, "qa");
await fs.mkdir(qaDir, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" });
const consoleErrors = [];
const pageErrors = [];

async function newPage(viewport) {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(`${page.url()} :: ${message.text()}`); });
  page.on("pageerror", error => pageErrors.push(`${page.url()} :: ${error.message}`));
  return page;
}

async function brokenImages(page) {
  return page.locator("img").evaluateAll(images => images.filter(image => !image.complete || image.naturalWidth === 0).map(image => image.getAttribute("src")));
}

async function overflowNodes(page) {
  return page.locator("body *").evaluateAll(nodes => nodes.filter(node => {
    const style = getComputedStyle(node);
    if (style.position === "fixed" || style.position === "sticky") return false;
    let parent = node.parentElement;
    while (parent) {
      const parentStyle = getComputedStyle(parent);
      if (["auto", "scroll"].includes(parentStyle.overflowX)) return false;
      parent = parent.parentElement;
    }
    const rect = node.getBoundingClientRect();
    return rect.width > 0 && (rect.left < -1 || rect.right > document.documentElement.clientWidth + 1);
  }).slice(0, 20).map(node => ({ tag: node.tagName, class: node.className, text: (node.textContent || "").trim().slice(0, 60) })));
}

const desktopPage = await newPage({ width: 1440, height: 1000 });
await desktopPage.goto(`${baseUrl}/preview/amazon_pdp_preview.html`, { waitUntil: "networkidle" });
const firstSrc = await desktopPage.locator("#mainProductImage").getAttribute("src");
await desktopPage.locator(".thumb").nth(1).click();
const secondSrc = await desktopPage.locator("#mainProductImage").getAttribute("src");
const consumerText = await desktopPage.locator("#amazonRoot").innerText();
const desktopHtml = await desktopPage.content();
const forbiddenConsumerTokens = ["Need Verification", "Pending Verification", "Blocked", "Fixture Only", "Auto Draft", "Product Knowledge", "Review Draft"];
const desktop = {
  product_image_count: await desktopPage.locator(".thumb").count(),
  aplus_module_count: await desktopPage.locator(".aplus > picture > img, .aplus > img").count(),
  thumbnail_interaction: firstSrc !== secondSrc,
  broken_images: await brokenImages(desktopPage),
  spec_hash_visible: (await desktopPage.locator(".hash").innerText()).includes(spec.meta.spec_sha256),
  forbidden_consumer_tokens: forbiddenConsumerTokens.filter(token => consumerText.includes(token)),
  rating_status: await desktopPage.locator("[data-rating-status]").getAttribute("data-rating-status"),
  fabricated_rating_tokens: [/[★☆]/u, />\s*(?:4\.0|4\.5)\s*</].filter(pattern => pattern.test(desktopHtml)).map(String),
};
await desktopPage.screenshot({ path: path.join(qaDir, "amazon-preview-desktop.png"), fullPage: true });

const mobilePage = await newPage({ width: 390, height: 844 });
await mobilePage.goto(`${baseUrl}/preview/amazon_pdp_preview.html`, { waitUntil: "networkidle" });
await mobilePage.getByRole("button", { name: "390px" }).click();
const mobileAplusSources = await mobilePage.locator(".aplus picture img").evaluateAll((images) => images.map((image) => image.currentSrc));
const mobileReadability = JSON.parse(await fs.readFile(path.join(qaDir, "mobile-readability-gate.json"), "utf8"));
const mobile = {
  viewport: "390x844",
  mode_applied: await mobilePage.locator("#amazonRoot").evaluate(node => node.classList.contains("mobile")),
  root_width: await mobilePage.locator("#amazonRoot").evaluate(node => Math.round(node.getBoundingClientRect().width)),
  document_width: await mobilePage.evaluate(() => document.documentElement.scrollWidth),
  overflow_nodes: await overflowNodes(mobilePage),
  broken_images: await brokenImages(mobilePage),
  aplus_mobile_asset_count: mobileAplusSources.filter((source) => source.includes("/design/aplus/mobile/")).length,
  mobile_readability_gate: mobileReadability.status,
};
await mobilePage.screenshot({ path: path.join(qaDir, "amazon-preview-mobile.png"), fullPage: true });

async function reviewCheck(relative, screenshot, expectedMocks = null, expectedFinals = null) {
  const page = await newPage({ width: 1440, height: 1000 });
  await page.goto(`${baseUrl}/${relative}`, { waitUntil: "networkidle" });
  const result = {
    title: await page.title(),
    spec_hash_visible: (await page.locator(".hash").innerText()).includes(spec.meta.spec_sha256),
    broken_images: await brokenImages(page),
    unit_mocks: await page.locator(".unit-mock").count(),
    final_images: await page.locator(".final-img").count(),
  };
  if (expectedMocks !== null) result.expected_unit_mocks = expectedMocks;
  if (expectedFinals !== null) result.expected_final_images = expectedFinals;
  await page.screenshot({ path: path.join(qaDir, screenshot), fullPage: true });
  await page.close();
  return result;
}

const story = await reviewCheck("review/story_review.html", "story-review-desktop.png");
const layout = await reviewCheck("review/layout_review.html", "layout-review-desktop.png", 14, null);
const design = await reviewCheck("review/design_review_cn.html", "design-review-desktop.png", null, 14);
const designHtml = await fs.readFile(path.join(outputDir, "review", "design_review_cn.html"), "utf8");
design.trace_markers = ["Selected Reference", "Decision Reason", "Learned Principle", "SwitchBot Adaptation", "Why This Layout", "What Was Not Copied"].filter(marker => designHtml.includes(marker));

const mobileReviewPage = await newPage({ width: 390, height: 844 });
await mobileReviewPage.goto(`${baseUrl}/review/design_review_cn.html`, { waitUntil: "networkidle" });
const mobileReviewHeaderHeight = await mobileReviewPage.locator(".top").evaluate(node => Math.round(node.getBoundingClientRect().height));
const anchorResults = {};
for (const id of ["gallery-review", "aplus-review", "qa-review"]) {
  await mobileReviewPage.locator(`a[href="#${id}"]`).click();
  let targetTop = Number.POSITIVE_INFINITY;
  for (let attempt = 0; attempt < 25; attempt += 1) {
    await mobileReviewPage.waitForTimeout(100);
    targetTop = await mobileReviewPage.locator(`#${id}`).evaluate((node) => Math.round(node.getBoundingClientRect().top));
    if (targetTop >= mobileReviewHeaderHeight - 1 && targetTop <= 843) break;
  }
  anchorResults[id] = {
    top: targetTop,
    header_height: mobileReviewHeaderHeight,
    visible_below_header: targetTop >= mobileReviewHeaderHeight - 1,
    within_viewport: targetTop >= mobileReviewHeaderHeight - 1 && targetTop <= 843,
  };
}
const mobileReview = {
  viewport: "390x844",
  header_height: mobileReviewHeaderHeight,
  document_width: await mobileReviewPage.evaluate(() => document.documentElement.scrollWidth),
  overflow_nodes: await overflowNodes(mobileReviewPage),
  broken_images: await brokenImages(mobileReviewPage),
  anchors: anchorResults,
};
await mobileReviewPage.screenshot({ path: path.join(qaDir, "design-review-mobile.png"), fullPage: true });
let reference = null;
if (spec.reference_application?.mode === "ON") {
  const page = await newPage({ width: 1440, height: 1000 });
  await page.goto(`${baseUrl}/reference/reference_decision_review.html`, { waitUntil: "networkidle" });
  const text = await page.locator("body").innerText();
  reference = {
    title: await page.title(),
    decision_rows: await page.locator("section").nth(2).locator("tbody tr").count(),
    accepted_14: text.includes("Accepted 14 / 14"),
    levoit_excluded: text.includes("Levoit") && text.includes("EXCLUDED"),
    broken_images: await brokenImages(page),
  };
  await page.screenshot({ path: path.join(qaDir, "reference-decision-review-desktop.png"), fullPage: true });
  await page.close();
}

const failures = [];
if (desktop.product_image_count !== 7) failures.push("Amazon Preview product image count is not 7");
if (desktop.aplus_module_count !== 7) failures.push("Amazon Preview A+ module count is not 7");
if (!desktop.thumbnail_interaction) failures.push("Thumbnail interaction did not update main image");
if (!desktop.spec_hash_visible || !story.spec_hash_visible || !layout.spec_hash_visible || !design.spec_hash_visible) failures.push("Spec hash is missing from one or more pages");
if (desktop.broken_images.length || mobile.broken_images.length || story.broken_images.length || layout.broken_images.length || design.broken_images.length) failures.push("Broken images detected");
if (desktop.forbidden_consumer_tokens.length) failures.push(`Consumer view exposes internal status: ${desktop.forbidden_consumer_tokens.join(", ")}`);
if (desktop.fabricated_rating_tokens.length || !["unavailable", "confirmed"].includes(desktop.rating_status)) failures.push("Preview contains fabricated or invalid Rating data");
if (!mobile.mode_applied || mobile.root_width > 390 || mobile.document_width > 390 || mobile.overflow_nodes.length) failures.push("390px layout overflows or mobile mode is not applied");
if (mobile.aplus_mobile_asset_count !== 7 || mobile.mobile_readability_gate !== "PASS") failures.push("390px A+ mobile assets or readability gate did not pass");
if (layout.unit_mocks !== 14 || design.final_images !== 14) failures.push("Review page visual count is not 7 product + 7 A+");
if (design.trace_markers.length !== 6) failures.push("Design Review Decision Trace is incomplete");
if (mobileReview.document_width > 390 || mobileReview.overflow_nodes.length || mobileReview.broken_images.length || mobileReview.header_height > 60 || Object.values(mobileReview.anchors).some(item => !item.visible_below_header || !item.within_viewport)) failures.push("390px Design Review navigation or anchor readability failed");
if (reference && (reference.decision_rows !== 14 || !reference.accepted_14 || !reference.levoit_excluded || reference.broken_images.length)) failures.push("Reference Selection / Decision Trace review did not pass");
if (consoleErrors.length || pageErrors.length) failures.push("Browser console/page errors detected");

const result = {
  status: failures.length ? "Fail" : "Pass",
  checked_at: new Date().toISOString(),
  spec_sha256: spec.meta.spec_sha256,
  pages: { desktop, mobile, story, layout, design, mobile_review: mobileReview, reference },
  console_errors: consoleErrors,
  page_errors: pageErrors,
  failures,
};
await fs.writeFile(path.join(qaDir, "browser-qa.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
await desktopPage.close();
await mobilePage.close();
await mobileReviewPage.close();
await browser.close();
console.log(JSON.stringify(result, null, 2));
if (result.status !== "Pass") process.exitCode = 1;
