async (page) => {
  const base = "http://127.0.0.1:8876";
  const root = "/Users/lai/Documents/marketing/edm-visual-generator";
  const cases = [
    { id: "P01", file: "wireframe.html", gate: "BLOCKED" },
    { id: "P02", file: "editable_edm.html", gate: "CONDITIONAL" },
    { id: "P03", file: "wireframe.html", gate: "BLOCKED" },
    { id: "P04", file: "editable_edm.html", gate: "CONDITIONAL" }
  ];
  const results = [];

  for (const item of cases) {
    const errors = [];
    const onConsole = (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    };
    page.on("console", onConsole);
    await page.setViewportSize({ width: 600, height: 900 });
    await page.goto(`${base}/pilot/${item.id}/${item.file}`, { waitUntil: "networkidle" });
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map((img) => img.decode().catch(() => null)));
    });
    await page.screenshot({ path: `${root}/pilot/${item.id}/desktop_preview.png` });
    await page.screenshot({ path: `${root}/pilot/${item.id}/full_edm.png`, fullPage: true });

    const widths = {};
    for (const width of [320, 375, 390, 414]) {
      await page.setViewportSize({ width, height: 844 });
      await page.waitForTimeout(60);
      widths[width] = await page.evaluate(() => {
        const cta = document.querySelector(".primary-cta");
        const canvas = document.querySelector(".email-canvas, .canvas");
        return {
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
          canvasWidth: canvas ? Math.round(canvas.getBoundingClientRect().width) : null,
          brokenImages: [...document.images].filter((img) => !img.complete || img.naturalWidth === 0).length,
          ctaVisible: cta ? cta.getBoundingClientRect().width > 0 && cta.getBoundingClientRect().height >= 44 : null,
          ctaSingleLine: cta ? cta.scrollHeight <= cta.clientHeight + 1 : null,
          bodyFont: getComputedStyle(document.body).fontFamily
        };
      });
    }

    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: `${root}/pilot/${item.id}/mobile_preview.png` });
    page.off("console", onConsole);
    results.push({ id: item.id, gate: item.gate, consoleErrors: errors, widths });
  }
  return results;
}
