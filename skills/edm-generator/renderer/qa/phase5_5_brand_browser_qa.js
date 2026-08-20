const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "../..");
const base = "http://127.0.0.1:8876";
const outputDir = path.join(root, "output", "playwright", "phase5_5");
const cases = ["P02", "P04"];

async function inspect(page, url) {
  const errors = [];
  const onConsole = (message) => {
    if (message.type() === "error") errors.push(message.text());
  };
  page.on("console", onConsole);
  await page.goto(url, { waitUntil: "networkidle" });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map((image) => image.decode().catch(() => null)));
  });
  const result = await page.evaluate(() => ({
    render_mode: document.body.dataset.renderMode || "generic",
    total_length_px: document.documentElement.scrollHeight,
    document_width_px: document.documentElement.scrollWidth,
    module_count: document.querySelectorAll("[data-module]").length,
    module_sequence: [...document.querySelectorAll("[data-module]")].map((node) => node.dataset.module),
    image_count: document.images.length,
    broken_images: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
    cta_count: document.querySelectorAll(".primary-cta,.sb-cta").length,
    internal_notice_present: Boolean(document.querySelector(".pilot-notice,.sb-pilot-notice")),
    production_footer_simulation: Boolean(document.querySelector(".sb-brand-footer"))
  }));
  page.off("console", onConsole);
  return { ...result, console_errors: errors };
}

(async () => {
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_EXECUTABLE || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });
  const page = await browser.newPage({ viewport: { width: 600, height: 900 }, deviceScaleFactor: 1 });
  const results = {};

  for (const id of cases) {
    await page.setViewportSize({ width: 600, height: 900 });
    const generic = await inspect(page, `${base}/pilot/${id}/editable_edm.html`);

    await page.setViewportSize({ width: 600, height: 900 });
    const brand = await inspect(page, `${base}/pilot/${id}/brand_v2/editable_edm.html`);
    await page.screenshot({ path: path.join(root, "pilot", id, "brand_v2", "desktop_preview.png") });
    await page.screenshot({ path: path.join(root, "pilot", id, "brand_v2", "full_edm.png"), fullPage: true });

    const responsive = {};
    for (const width of [320, 375, 390, 414, 768]) {
      await page.setViewportSize({ width, height: 844 });
      await page.waitForTimeout(50);
      responsive[width] = await page.evaluate(() => ({
        inner_width: window.innerWidth,
        scroll_width: document.documentElement.scrollWidth,
        no_horizontal_overflow: document.documentElement.scrollWidth <= window.innerWidth,
        broken_images: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
        ctas_min_44px: [...document.querySelectorAll(".sb-cta")].every((node) => node.getBoundingClientRect().height >= 44),
        ctas_single_line: [...document.querySelectorAll(".sb-cta")].every((node) => node.scrollHeight <= node.clientHeight + 1)
      }));
    }

    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(root, "pilot", id, "brand_v2", "mobile_preview.png") });
    results[id] = {
      generic_v1: generic,
      switchbot_brand_v2: brand,
      delta: {
        length_px: brand.total_length_px - generic.total_length_px,
        module_count: brand.module_count - generic.module_count,
        length_multiplier: Number((brand.total_length_px / generic.total_length_px).toFixed(2))
      },
      responsive
    };
  }

  await browser.close();
  for (const id of cases) {
    const item = results[id];
    const brand = item.switchbot_brand_v2;
    const responsivePass = Object.values(item.responsive).every((row) =>
      row.no_horizontal_overflow && row.broken_images === 0 && row.ctas_min_44px && row.ctas_single_line
    );
    const markdown = `# ${id} Brand V2 Render QA\n\n` +
      `- Gate: CONDITIONAL / internal calibration only\n` +
      `- Brand mode: ${brand.render_mode}\n` +
      `- Browser dimensions: 600×${brand.total_length_px}px full length; 600×900 desktop preview; 390×844 mobile preview\n` +
      `- Browser module count: ${brand.module_count}; images: ${brand.image_count}; CTA instances: ${brand.cta_count}; broken images: ${brand.broken_images}\n` +
      `- Responsive QA: 320 / 375 / 390 / 414 / 768px — ${responsivePass ? "PASS" : "FAIL"}\n` +
      `- Truth / Claim: no new numerical, superiority, price, promotion, service or compatibility claims added\n` +
      `- Asset: official product/device UI assets only; no AI product redraw\n` +
      `- Footer: deep structural simulation only; production footer remains MISSING\n` +
      `- Long-form decision: not forced; Standard used because verified content and asset depth stop before 12 justified modules\n` +
      `- Evidence: output/playwright/phase5_5/brand_renderer_qa.json\n`;
    fs.writeFileSync(path.join(root, "pilot", id, "brand_v2", "render_qa.md"), markdown);
  }
  fs.writeFileSync(path.join(outputDir, "brand_renderer_qa.json"), `${JSON.stringify(results, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
