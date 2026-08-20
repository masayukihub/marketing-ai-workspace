const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "../..");
const outputDir = path.join(root, "output", "playwright", "phase5_5", "approved");
const base = "http://127.0.0.1:8876";
const ids = ["SBG_001", "SBG_003", "SBG_005", "SBG_006", "SBG_007", "SBG_016", "SBG_019", "SBG_020"];

(async () => {
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_EXECUTABLE || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });
  const page = await browser.newPage({ viewport: { width: 600, height: 900 }, deviceScaleFactor: 1 });
  const rows = [];

  for (const id of ids) {
    const errors = [];
    const onConsole = (message) => {
      if (message.type() === "error") errors.push(message.text());
    };
    page.on("console", onConsole);
    await page.goto(`${base}/research/mobile_evidence/html/${id}.html`, { waitUntil: "networkidle" });
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map((image) => image.decode().catch(() => null)));
    });
    const measurement = await page.evaluate(() => {
      const repeatable = [...document.querySelectorAll("table")].filter((node) =>
        [...node.attributes].some((attribute) => attribute.name === "mc:repeatable")
      );
      const primary = [...document.querySelectorAll("table")].find((node) => node.getAttribute("width") === "600");
      return {
        viewport_width: window.innerWidth,
        total_length_px: document.documentElement.scrollHeight,
        rendered_width_px: Math.round(primary?.getBoundingClientRect().width || document.body.getBoundingClientRect().width),
        recovered_repeatable_blocks: repeatable.length,
        image_count: document.images.length,
        broken_images: [...document.images].filter((image) => !image.complete || image.naturalWidth === 0).length,
        broken_image_sources: [...document.images]
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.getAttribute("src")),
        link_count: document.links.length,
        horizontal_overflow: document.documentElement.scrollWidth > window.innerWidth
      };
    });
    await page.screenshot({ path: path.join(outputDir, `${id}_recovered.png`), fullPage: true });
    page.off("console", onConsole);
    rows.push({ reference_id: id, ...measurement, console_errors: errors });
  }

  await browser.close();
  fs.writeFileSync(
    path.join(root, "output", "playwright", "phase5_5", "approved_measurements.json"),
    `${JSON.stringify(rows, null, 2)}\n`
  );
  process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
