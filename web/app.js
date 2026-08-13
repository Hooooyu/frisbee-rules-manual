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
  let current = data.documents[0];

  const escape = (value) => String(value).replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
  const bilingualTitle = (value) => {
    const match = String(value).match(/^(.*?)\s*[（(]([^()（）]*[A-Za-z][^()（）]*)[）)]$/);
    return match ? { zh: match[1], en: match[2] } : { zh: value, en: "" };
  };
  const titleMarkup = (value, className) => {
    const { zh, en } = bilingualTitle(value);
    return `<span class="${className}"><span class="${className}-zh">${escape(zh)}</span>${en ? `<span class="${className}-en" lang="en">${escape(en)}</span>` : ""}</span>`;
  };
  const sectionKey = (section) => ["Introduction", "Definitions", "Legal License"].includes(section.key) || section.key.startsWith("appendix-") ? "" : section.key;
  const appendixLabel = (section) => section.key.startsWith("appendix-") ? `附录 ${section.key.at(-1).toUpperCase()}：${section.title}` : "";
  const displaySectionTitle = (section) => appendixLabel(section) || section.title;
  const sectionName = (section) => `${section.key === "Introduction" ? "" : `${section.key} `}${section.title}`;
  const ruleNumber = (text) => (String(text).match(/^((?:[A-H]?\d+)(?:\.\d+)+)\.\s*/) || [])[1] || "";
  const ruleLevel = (number) => number ? Math.min(number.split(".").length, 5) : 0;
  function renderParagraph(paragraph) {
    const number = ruleNumber(paragraph.zh);
    if (!number) return `<p data-source="${escape(paragraph.en)}">${escape(paragraph.zh)}</p>`;
    return `<p class="rule-line level-${ruleLevel(number)}" data-source="${escape(paragraph.en)}"><span class="rule-number">${escape(number)}.</span> ${escape(paragraph.zh.slice(number.length + 2).trim())}</p>`;
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
      return `<a class="${key ? "" : "toc-group"}" href="#${section.id}">${key ? `<span class="toc-key">${escape(key)}</span>` : ""}${titleMarkup(section.title, "toc-title")}</a>`;
    }).join("");
    reader.classList.remove("show-source");
    sourceToggle.setAttribute("aria-pressed", "false");
    sourceToggle.textContent = document.kind === "diagram" ? "显示英文原图" : "显示英文原文";
    reader.innerHTML = document.sections.map((section) => {
      const diagram = section.image ? `<div class="diagram-reader"><p>${escape(section.description)}</p><button type="button" data-image="${section.image}" data-source-image="${section.sourceImage}" data-alt="${escape(section.alt)}"><img class="translated-diagram" src="${section.image}" alt="${escape(section.alt)}"><img class="source-diagram" src="${section.sourceImage}" alt="${escape(section.alt)} 英文原图"></button></div>` : "";
      const figure = section.figure ? `<figure class="rule-figure"><figcaption>${escape(section.figure.description)}</figcaption><button type="button" data-image="${section.figure.image}" data-source-image="${section.figure.sourceImage}" data-alt="${escape(section.figure.alt)}"><img class="translated-diagram" src="${section.figure.image}" alt="${escape(section.figure.alt)}"><img class="source-diagram" src="${section.figure.sourceImage}" alt="${escape(section.figure.alt)} 英文原图"></button></figure>` : "";
      const content = section.paragraphs.map(renderParagraph).join("");
      return `<section class="rule-section" id="${section.id}"><h2><span class="section-number">${escape(sectionKey(section))}</span>${titleMarkup(displaySectionTitle(section), "section-title")}</h2>${diagram}${content}${figure}</section>`;
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
      if (sectionSearchable.includes(needle)) matches.push({ document, section, paragraph: { zh: section.description || section.title } });
      section.paragraphs.forEach((paragraph) => {
        const searchable = `${section.key} ${section.title} ${paragraph.zh} ${paragraph.en}`.toLocaleLowerCase();
        if (searchable.includes(needle)) matches.push({ document, section, paragraph });
      });
    }));
    results.hidden = false;
    const visible = matches.slice(0, 12);
    results.innerHTML = `<p>${matches.length ? `找到 ${matches.length} 条结果` : "没有找到相关规则"}</p>${visible.map((match) => `<button type="button" data-result-document="${match.document.id}" data-result-section="${match.section.id}"><b>${escape(match.document.label)} · ${escape(sectionName(match.section))}</b><span>${escape(match.paragraph.zh)}</span></button>`).join("")}`;
  }

  documentsRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-document]");
    if (!button) return;
    renderDocument(data.documents.find((document) => document.id === button.dataset.document));
  });

  results.addEventListener("click", (event) => {
    const button = event.target.closest("[data-result-document]");
    if (!button) return;
    renderDocument(data.documents.find((document) => document.id === button.dataset.resultDocument));
    document.getElementById(button.dataset.resultSection)?.scrollIntoView({ behavior: "smooth", block: "start" });
    search.value = "";
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
