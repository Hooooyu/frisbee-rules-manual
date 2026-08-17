(() => {
  const appendix = window.HANDBOOK_DATA?.documents?.find((document) => document.id === "appendix");
  const signals = appendix?.sections?.find((section) => section.id === "appendix-signals");
  if (!signals) return;

  signals.figure = {
    description: "WFDF Appendix v2.0：手势 1–24 官方配图。",
    image: "assets/figures/appendix-hand-signals.png",
    sourceImage: "assets/figures/appendix-hand-signals.png",
    alt: "WFDF 团队飞盘规则手势 1 至 24 官方示意图",
  };
})();
