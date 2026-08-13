(() => {
  const data = window.HANDBOOK_DATA;
  const documentsRoot = document.querySelector("#documents");
  const toc = document.querySelector("#toc");
  const reader = document.querySelector("#reader");
  const title = document.querySelector("#document-title");
  const subtitle = document.querySelector("#document-subtitle");
  const effective = document.querySelector("#effective-date");
  const search = document.querySelector("#search");
  const results = document.querySelector("#search-results");
  const sourceToggle = document.querySelector("#source-toggle");
  const dialog = document.querySelector("#image-dialog");
  const dialogImage = dialog.querySelector("img");
  const tocToggle = document.querySelector("#toc-toggle");
  const sidebarBackdrop = document.querySelector("#sidebar-backdrop");
  let current = data.documents[0];
  let searchHighlightTimer;
  const setTocOpen = (open) => {
    document.body.classList.toggle("toc-open", open);
    tocToggle?.setAttribute("aria-expanded", String(open));
  };

  const escape = (value) => String(value).replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
  const annotationEnglishTitles = {
    Introduction: "Introduction", Principles: "Principles",
    1: "Spirit of the Game", 2: "Playing Field", 3: "Equipment",
    4: "Point, Goal and Game", 5: "Teams", 6: "Starting a Game",
    7: "The Pull", 8: "State of Play", 9: "Stall Count", 10: "Check",
    11: "Out-of-Bounds", 12: "Receivers and Positioning", 13: "Turnovers",
    14: "Scoring", 15: "Calling Fouls, Infractions and Violations",
    16: "Continuation after a Call", 17: "Fouls", 18: "Infractions and Violations",
    19: "Safety Stoppages", 20: "Time-Outs"
  };
  const bilingualTitle = (value, fallbackEnglish = "") => {
    const match = String(value).match(/^(.*?)\s*[（(]([^()（）]*[A-Za-z][^()（）]*)[）)]$/);
    return match ? { zh: match[1], en: match[2] } : { zh: value, en: fallbackEnglish };
  };
  const sectionEnglishTitle = (section) => {
    if (current?.id === "annotations") return annotationEnglishTitles[section.key] || "";
    return data.documents.find((item) => item.id === "rules")?.sections.find((item) => item.key === section.key)?.title.match(/[（(]([^()（）]*[A-Za-z][^()（）]*)[）)]$/)?.[1] || "";
  };
  const titleMarkup = (value, className, fallbackEnglish = "") => {
    const { zh, en } = bilingualTitle(value, fallbackEnglish);
    return `<span class="${className}"><span class="${className}-zh">${escape(zh)}</span>${en ? `<span class="${className}-en" lang="en">${escape(en)}</span>` : ""}</span>`;
  };
  const sectionKey = (section) => ["Introduction", "Definitions", "Legal License"].includes(section.key) || section.key.startsWith("appendix-") ? "" : section.key;
  const appendixLabel = (section) => section.key.startsWith("appendix-") ? `附录 ${section.key.at(-1).toUpperCase()}：${section.title}` : "";
  const displaySectionTitle = (section) => appendixLabel(section) || section.title;
  const sectionName = (section) => `${section.key === "Introduction" ? "" : `${section.key} `}${section.title}`;
  const ruleNumber = (text) => (String(text).match(/^((?:[A-H]?\d+)(?:\.\d+)+)\.\s*/) || [])[1] || "";
  const ruleLevel = (number) => number ? Math.min(number.split(".").length, 5) : 0;
  function renderParagraph(paragraph, index) {
    const number = ruleNumber(paragraph.zh);
    if (!number) return `<p data-search-index="${index}" data-source="${escape(paragraph.en)}">${escape(paragraph.zh)}</p>`;
    return `<p class="rule-line level-${ruleLevel(number)}" data-search-index="${index}" data-source="${escape(paragraph.en)}"><span class="rule-number">${escape(number)}.</span> ${escape(paragraph.zh.slice(number.length + 2).trim())}</p>`;
  }

  function renderDocument(document) {
    current = document;
    title.textContent = document.title;
    subtitle.textContent = document.subtitle;
    effective.textContent = document.effective;
    documentsRoot.innerHTML = data.documents.map((item) => `<button class="document-button" type="button" data-document="${item.id}" aria-current="${item.id === document.id ? "page" : "false"}">${item.label}</button>`).join("");
    toc.innerHTML = document.sections.map((section, index, sections) => {
      const label = appendixLabel(section);
      const nextKey = sections[index + 1]?.key || "";
      const hasChildren = section.key.startsWith("appendix-") && new RegExp(`^${section.key.at(-1).toUpperCase()}\\d`).test(nextKey);
      if (label) return hasChildren ? `<h3 class="toc-chapter">${escape(label)}</h3>` : `<a class="toc-chapter toc-chapter-link" href="#${section.id}">${escape(label)}</a>`;
      const key = sectionKey(section);
      return `<a class="${key ? "" : "toc-group"}" href="#${section.id}">${key ? `<span class="toc-key">${escape(key)}</span>` : ""}${titleMarkup(section.title, "toc-title", sectionEnglishTitle(section))}</a>`;
    }).join("");
    reader.classList.remove("show-source");
    sourceToggle.setAttribute("aria-pressed", "false");
    sourceToggle.textContent = document.kind === "diagram" ? "显示英文原图" : "显示英文原文";
    reader.innerHTML = document.sections.map((section) => {
      const diagram = section.image ? `<div class="diagram-reader"><p>${escape(section.description)}</p><button type="button" data-image="${section.image}" data-source-image="${section.sourceImage}" data-alt="${escape(section.alt)}"><img class="translated-diagram" src="${section.image}" alt="${escape(section.alt)}"><img class="source-diagram" src="${section.sourceImage}" alt="${escape(section.alt)} 英文原图"></button></div>` : "";
      const figure = section.figure ? `<figure class="rule-figure"><figcaption>${escape(section.figure.description)}</figcaption><button type="button" data-image="${section.figure.image}" data-source-image="${section.figure.sourceImage}" data-alt="${escape(section.figure.alt)}"><img class="translated-diagram" src="${section.figure.image}" alt="${escape(section.figure.alt)}"><img class="source-diagram" src="${section.figure.sourceImage}" alt="${escape(section.figure.alt)} 英文原图"></button></figure>` : "";
      const content = section.paragraphs.map(renderParagraph).join("");
      return `<section class="rule-section" id="${section.id}"><h2><span class="section-number">${escape(sectionKey(section))}</span>${titleMarkup(displaySectionTitle(section), "section-title", sectionEnglishTitle(section))}</h2>${diagram}${content}${figure}</section>`;
    }).join("") || '<p class="empty">此文件正在整理为网页结构。请暂时使用上方的 WFDF 原版文档入口。</p>';
    window.location.hash = "top";
  }

  function searchContent(query) {
    const needle = query.trim().toLocaleLowerCase();
    if (!needle) {
      results.hidden = true;
      results.innerHTML = "";
      return;
    }
    const matches = [];
    data.documents.forEach((document) => document.sections.forEach((section) => {
      const sectionSearchable = `${section.key} ${section.title} ${section.description || ""} ${section.keywords || ""} ${section.sourceKeywords || ""}`.toLocaleLowerCase();
      if (sectionSearchable.includes(needle)) matches.push({ document, section, paragraph: { zh: section.description || section.title }, paragraphIndex: -1 });
      section.paragraphs.forEach((paragraph, paragraphIndex) => {
        const searchable = `${section.key} ${section.title} ${paragraph.zh} ${paragraph.en}`.toLocaleLowerCase();
        if (searchable.includes(needle)) matches.push({ document, section, paragraph, paragraphIndex });
      });
    }));
    results.hidden = false;
    const visible = matches;
    visible.forEach((match) => { match.resultParagraph = match.paragraphIndex; match.resultQuery = needle; });
    results.innerHTML = `<p>${matches.length ? `找到 ${matches.length} 条结果` : "没有找到相关规则"}</p>${visible.map((match) => `<button type="button" data-result-document="${match.document.id}" data-result-section="${match.section.id}"><b>${escape(match.document.label)} · ${escape(sectionName(match.section))}</b><span>${escape(match.paragraph.zh)}</span></button>`).join("")}`;
    results.querySelectorAll("button[data-result-document]").forEach((button, index) => {
      button.dataset.resultParagraph = String(visible[index].resultParagraph);
      button.dataset.resultQuery = visible[index].resultQuery;
    });
    const status = results.querySelector("p");
    status?.setAttribute("data-result-status", "");
    if (status) status.textContent = `找到 ${matches.length} 条结果 · 当前显示 1-${Math.min(matches.length, 12)} 条`;
    results.onscroll = () => {
      const items = [...results.querySelectorAll("button[data-result-document]")];
      const top = results.getBoundingClientRect().top;
      const bottom = results.getBoundingClientRect().bottom;
      const first = items.findIndex((item) => item.getBoundingClientRect().bottom > top);
      const last = items.findLastIndex((item) => item.getBoundingClientRect().top < bottom);
      const status = results.querySelector("[data-result-status]");
      if (status && first >= 0) status.textContent = `找到 ${matches.length} 条结果 · 当前显示 ${first + 1}-${Math.max(first + 1, last + 1)} 条`;
    };
  }

  function highlightSearchTarget(section, paragraphIndex, query) {
    clearTimeout(searchHighlightTimer);
    reader.querySelectorAll(".search-target").forEach((element) => element.classList.remove("search-target"));
    reader.querySelectorAll(".search-keyword").forEach((element) => element.replaceWith(document.createTextNode(element.textContent)));
    const target = paragraphIndex >= 0 ? section.querySelector(`[data-search-index="${paragraphIndex}"]`) : section.querySelector("h2");
    if (!target) return;
    target.classList.add("search-target");
    const pattern = new RegExp(query.replace(/[.*+?^${}()|[\\]\\]/g, "\\\\$&"), "giu");
    const walker = document.createTreeWalker(target, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      pattern.lastIndex = 0;
      if (!pattern.test(node.nodeValue)) return;
      pattern.lastIndex = 0;
      const fragment = document.createDocumentFragment();
      let last = 0;
      node.nodeValue.replace(pattern, (match, offset) => { fragment.append(node.nodeValue.slice(last, offset)); const mark = document.createElement("mark"); mark.className = "search-keyword"; mark.textContent = match; fragment.append(mark); last = offset + match.length; return match; });
      fragment.append(node.nodeValue.slice(last));
      node.replaceWith(fragment);
    });
    searchHighlightTimer = setTimeout(() => {
      target.classList.remove("search-target");
      target.querySelectorAll(".search-keyword").forEach((element) => element.replaceWith(document.createTextNode(element.textContent)));
    }, 3000);
    requestAnimationFrame(() => {
      const rect = target.getBoundingClientRect();
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const top = Math.min(maxScroll, Math.max(0, window.scrollY + rect.top + rect.height / 2 - window.innerHeight / 2));
      window.scrollTo({ top, behavior: "smooth" });
    });
  }

  documentsRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-document]");
    if (!button) return;
    renderDocument(data.documents.find((document) => document.id === button.dataset.document));
    setTocOpen(false);
  });

  toc.addEventListener("click", (event) => { if (event.target.closest("a")) setTocOpen(false); });
  tocToggle?.addEventListener("click", () => setTocOpen(!document.body.classList.contains("toc-open")));
  sidebarBackdrop?.addEventListener("click", () => setTocOpen(false));
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") setTocOpen(false); });

  results.addEventListener("click", (event) => {
    const button = event.target.closest("[data-result-document]");
    if (!button) return;
    renderDocument(data.documents.find((document) => document.id === button.dataset.resultDocument));
    const target = document.getElementById(button.dataset.resultSection);
    if (target) highlightSearchTarget(target, Number(button.dataset.resultParagraph), button.dataset.resultQuery);
    results.hidden = true;
  });

  search.addEventListener("input", () => searchContent(search.value));
  search.addEventListener("keydown", (event) => { if (event.key === "Escape") { search.value = ""; searchContent(""); search.blur(); } });
  sourceToggle.addEventListener("click", () => {
    const enabled = reader.classList.toggle("show-source");
    sourceToggle.setAttribute("aria-pressed", String(enabled));
    sourceToggle.textContent = enabled ? (current.kind === "diagram" ? "隐藏英文原图" : "隐藏英文原文") : (current.kind === "diagram" ? "显示英文原图" : "显示英文原文");
  });
  reader.addEventListener("click", (event) => {
    const button = event.target.closest("[data-image]");
    if (!button) return;
    dialogImage.src = reader.classList.contains("show-source") ? button.dataset.sourceImage : button.dataset.image;
    dialogImage.alt = button.dataset.alt;
    dialog.showModal();
  });
  dialog.addEventListener("click", (event) => { if (event.target === dialog || event.target.tagName === "BUTTON") dialog.close(); });

  renderDocument(current);
})();
