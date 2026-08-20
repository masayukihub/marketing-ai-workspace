async (page) => {
  const errors = [];
  const onConsole = (msg) => { if (msg.type() === "error") errors.push(msg.text()); };
  page.on("console", onConsole);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("http://127.0.0.1:8876/research/phase5_visual_review.html", { waitUntil: "networkidle" });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map((img) => img.decode().catch(() => null)));
  });
  const desktop = await page.evaluate(() => ({
    scoreControls: document.querySelectorAll('[data-score-grid] select').length,
    scoreValuesEmpty: [...document.querySelectorAll('[data-score-grid] select')].every((el) => el.value === ""),
    decisionsEmpty: [...document.querySelectorAll('[data-field="overall_decision"]')].every((el) => el.value === ""),
    reasonsEmpty: [...document.querySelectorAll('[data-field="human_reason"]')].every((el) => el.value === ""),
    brokenImages: [...document.images].filter((img) => !img.complete || img.naturalWidth === 0).length,
    imageCount: document.images.length,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth
  }));
  await page.screenshot({ path: "/Users/lai/Documents/marketing/edm-visual-generator/research/phase5_visual_review_preview.png" });

  const responsive = {};
  for (const width of [320, 375, 390, 414, 768]) {
    await page.setViewportSize({ width, height: 900 });
    responsive[width] = await page.evaluate(() => {
      const button = document.querySelector('#exportCsv');
      return {
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
        exportButtonSingleLine: button.scrollHeight <= button.clientHeight + 1,
        brokenImages: [...document.images].filter((img) => !img.complete || img.naturalWidth === 0).length
      };
    });
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#exportCsv").click();
  const download = await downloadPromise;
  await download.saveAs("/private/tmp/phase5_visual_human_review_test.csv");
  page.off("console", onConsole);
  return { desktop, responsive, consoleErrors: errors, downloadName: download.suggestedFilename() };
}
