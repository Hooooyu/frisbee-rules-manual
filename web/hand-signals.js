(() => {
  const signals = [
    ["01-foul.png", "手势 1：犯规（Foul）"],
    ["02-violation.png", "手势 2：违例（Violation）"],
    ["03-goal.png", "手势 3：得分（Goal）"],
    ["04-contest.png", "手势 4：争议（Contest）"],
    ["05-accepted.png", "手势 5：接受（Accepted）"],
    ["06-retracted.png", "手势 6：撤回（Retracted）"],
    ["07-in-out-of-bounds.png", "手势 7：界内或界外（In / Out-of-bounds）"],
    ["08-disc-down.png", "手势 8：飞盘落地（Disc down）"],
    ["09-disc-up.png", "手势 9：飞盘在空中（Disc up）"],
    ["10-pick.png", "手势 10：阻挡（Pick）"],
    ["11-travel.png", "手势 11：走步（Travel）"],
    ["12-marking-infraction.png", "手势 12：防盘违规（Marking Infraction）"],
    ["13-turnover.png", "手势 13：攻防转换（Turnover）"],
    ["14-timing-violation.png", "手势 14：时间限制违例（Timing Violation）"],
    ["15-pulling-violation.png", "手势 15：开盘违例（Pulling Violation）"],
    ["16-time-out.png", "手势 16：暂停（Time-out）"],
    ["17-spirit-stoppage.png", "手势 17：飞盘精神暂停（Spirit Stoppage）"],
    ["18-stoppage.png", "手势 18：比赛中断（Stoppage）"],
    ["19-personnel-ratio-male.png", "手势 19：男性对位（Personnel Ratio: Male Matching）"],
    ["20-personnel-ratio-female.png", "手势 20：女性对位（Personnel Ratio: Female Matching）"],
    ["21-play-has-stopped.png", "手势 21：比赛已停止（Play has stopped）"],
    ["22-who-made-the-call.png", "手势 22：谁作出示意（Who made the call）"],
    ["23-did-not-affect-play.png", "手势 23：未影响比赛动作（Did not affect the play）"],
    ["24-match-point.png", "手势 24：赛点（Match Point）"],
  ];

  const reader = document.querySelector("#reader");
  if (!reader) return;

  const decorate = () => {
    const section = reader.querySelector("#appendix-signals");
    if (!section || section.dataset.handSignalsReady === "true") return;
    const paragraphs = [...section.children].filter((element) => element.matches?.("p[data-search-index]"));
    if (paragraphs.length < signals.length) return;

    section.dataset.handSignalsReady = "true";
    const grid = document.createElement("div");
    grid.className = "hand-signal-grid";

    signals.forEach(([filename, alt], index) => {
      const paragraph = paragraphs[index];
      const copy = document.createElement("span");
      copy.className = "hand-signal-copy";
      while (paragraph.firstChild) copy.appendChild(paragraph.firstChild);

      const imagePath = `assets/figures/hand-signals/${filename}`;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "hand-signal-visual";
      button.dataset.image = imagePath;
      button.dataset.sourceImage = imagePath;
      button.dataset.alt = alt;
      button.setAttribute("aria-label", `${alt}，点击查看大图`);

      const image = document.createElement("img");
      image.className = "hand-signal-image";
      image.src = imagePath;
      image.alt = alt;
      image.loading = "lazy";
      image.decoding = "async";

      button.appendChild(image);
      paragraph.classList.add("hand-signal-card");
      paragraph.append(button, copy);
      grid.appendChild(paragraph);
    });

    section.appendChild(grid);
  };

  new MutationObserver(decorate).observe(reader, { childList: true, subtree: true });
  decorate();
})();
