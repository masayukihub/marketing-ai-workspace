async (page) => {
  const base = "http://127.0.0.1:8876";
  const cases = { P01: 1, P02: 5, P03: 1, P04: 5 };
  const results = {};

  for (const [id, expectedRows] of Object.entries(cases)) {
    const errors = [];
    const onConsole = (msg) => { if (msg.type() === "error") errors.push(msg.text()); };
    page.on("console", onConsole);
    await page.setViewportSize({ width: 1200, height: 900 });
    await page.goto(`${base}/pilot/${id}/design_review.html`, { waitUntil: "networkidle" });
    const desktop = await page.evaluate(({ expectedRows }) => {
      const iframe = document.querySelector("iframe");
      const childImages = iframe?.contentDocument ? [...iframe.contentDocument.images] : [];
      return {
        campaignPanels: document.querySelectorAll(".campaign .panel").length,
        moduleRows: document.querySelectorAll(".trace tbody tr").length,
        expectedRows,
        iframeLoaded: Boolean(iframe?.contentDocument?.body),
        brokenChildImages: childImages.filter((img) => !img.complete || img.naturalWidth === 0).length,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth
      };
    }, { expectedRows });

    const responsive = {};
    for (const width of [320, 390, 768]) {
      await page.setViewportSize({ width, height: 844 });
      responsive[width] = await page.evaluate(() => ({
        noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
        iframeFits: document.querySelector("iframe").getBoundingClientRect().width <= window.innerWidth
      }));
    }
    page.off("console", onConsole);
    results[id] = { desktop, responsive, consoleErrors: errors };
  }

  return results;
}
