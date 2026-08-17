(() => {
  const data = window.HANDBOOK_DATA;
  const reader = document.querySelector("#reader");
  if (!data || !reader) return;

  const referencePattern = /\b([A-H]?\d+(?:\.\d+)+)\b/g;
  const numberedRulePattern = /^((?:[A-H]?\d+)(?:\.\d+)+)\.\s*/;
  const documentsById = new Map(data.documents.map((document) => [document.id, document]));
  const referencesByNumber = new Map();

  const ruleNumber = (text) => (String(text).match(numberedRulePattern) || [])[1] || "";

  data.documents.forEach((document) => {
    document.sections.forEach((section) => {
      section.paragraphs.forEach((paragraph, paragraphIndex, paragraphs) => {
        const number = ruleNumber(paragraph.zh);
        if (!number) return;

        const relatedParagraphs = [paragraph];
        for (let index = paragraphIndex + 1; index < paragraphs.length; index += 1) {
          if (ruleNumber(paragraphs[index].zh)) break;
          relatedParagraphs.push(paragraphs[index]);
        }

        const entry = {
          number,
          document,
          section,
          paragraphIndex,
          paragraphs: relatedParagraphs,
        };
        if (!referencesByNumber.has(number)) referencesByNumber.set(number, []);
        referencesByNumber.get(number).push(entry);
      });
    });
  });

  const currentDocumentId = () => document.querySelector(".document-button[aria-current=\"page\"]")?.dataset.document || data.documents[0]?.id || "rules";

  const referencePriority = (sourceDocumentId, number) => {
    if (/^[A-H]/.test(number)) return ["appendix", sourceDocumentId, "rules", "annotations"];
    if (sourceDocumentId === "rules") return ["rules", "appendix", "annotations"];
    if (sourceDocumentId === "annotations") return ["rules", "annotations", "appendix"];
    if (sourceDocumentId === "appendix") return ["rules", "appendix", "annotations"];
    return [sourceDocumentId, "rules", "appendix", "annotations"];
  };

  const resolveReference = (number, sourceDocumentId) => {
    const entries = referencesByNumber.get(number) || [];
    if (!entries.length) return null;
    const priority = referencePriority(sourceDocumentId, number);
    for (const documentId of priority) {
      const match = entries.find((entry) => entry.document.id === documentId);
      if (match) return match;
    }
    return entries[0];
  };

  const createReferenceButton = (number, sourceDocumentId) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "rule-reference";
    button.dataset.ruleReference = number;
    button.dataset.sourceDocument = sourceDocumentId;
    button.setAttribute("aria-label", `查看规则 ${number}`);
    button.textContent = number;
    return button;
  };

  const decorateTextNode = (node, sourceDocumentId) => {
    const text = node.nodeValue;
    referencePattern.lastIndex = 0;
    let match;
    let lastIndex = 0;
    let changed = false;
    const fragment = document.createDocumentFragment();

    while ((match = referencePattern.exec(text))) {
      const number = match[1];
      if (!resolveReference(number, sourceDocumentId)) continue;
      changed = true;
      fragment.append(document.createTextNode(text.slice(lastIndex, match.index)));
      fragment.append(createReferenceButton(number, sourceDocumentId));
      lastIndex = match.index + match[0].length;
    }

    if (!changed) return;
    fragment.append(document.createTextNode(text.slice(lastIndex)));
    node.replaceWith(fragment);
  };

  const decorateParagraph = (paragraph) => {
    if (paragraph.dataset.referencesChecked === "true") return;
    paragraph.dataset.referencesChecked = "true";
    const sourceDocumentId = currentDocumentId();
    const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || parent.closest(".rule-number, .rule-reference, .search-keyword")) return NodeFilter.FILTER_REJECT;
        referencePattern.lastIndex = 0;
        return referencePattern.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => decorateTextNode(node, sourceDocumentId));
  };

  const dialog = document.createElement("dialog");
  dialog.className = "reference-dialog";
  dialog.setAttribute("aria-labelledby", "reference-dialog-title");
  dialog.innerHTML = `
    <article class="reference-card">
      <header class="reference-dialog-header">
        <div>
          <p class="reference-kicker">引用条款</p>
          <h3 id="reference-dialog-title"></h3>
        </div>
        <button class="reference-icon-close" type="button" aria-label="关闭引用条款">×</button>
      </header>
      <div class="reference-dialog-body">
        <p class="reference-meta"></p>
        <div class="reference-copy"></div>
        <details class="reference-source">
          <summary>查看英文原文</summary>
          <div class="reference-source-copy" lang="en"></div>
        </details>
      </div>
      <footer class="reference-dialog-actions">
        <button class="reference-jump" type="button">定位到原条款</button>
        <button class="reference-close" type="button">关闭</button>
      </footer>
    </article>`;
  document.body.append(dialog);

  const dialogTitle = dialog.querySelector("#reference-dialog-title");
  const dialogMeta = dialog.querySelector(".reference-meta");
  const dialogCopy = dialog.querySelector(".reference-copy");
  const sourceDetails = dialog.querySelector(".reference-source");
  const sourceCopy = dialog.querySelector(".reference-source-copy");
  const jumpButton = dialog.querySelector(".reference-jump");
  let activeEntry = null;
  let opener = null;

  const paragraphMarkup = (text, isFirst) => {
    const paragraph = document.createElement("p");
    if (isFirst) {
      const match = String(text).match(numberedRulePattern);
      if (match) {
        const number = document.createElement("span");
        number.className = "reference-rule-number";
        number.textContent = `${match[1]}.`;
        paragraph.append(number, document.createTextNode(` ${String(text).slice(match[0].length)}`));
        return paragraph;
      }
    }
    paragraph.textContent = text;
    return paragraph;
  };

  const openReference = (entry, trigger) => {
    activeEntry = entry;
    opener = trigger;
    dialogTitle.textContent = `规则 ${entry.number}`;
    const sectionLabel = [entry.section.key, entry.section.title].filter(Boolean).join(" ");
    dialogMeta.textContent = `${entry.document.label}${sectionLabel ? ` · ${sectionLabel}` : ""}`;
    dialogCopy.replaceChildren(...entry.paragraphs.map((paragraph, index) => paragraphMarkup(paragraph.zh, index === 0)));

    const english = entry.paragraphs.map((paragraph) => paragraph.en).filter(Boolean);
    sourceDetails.hidden = english.length === 0;
    sourceDetails.open = reader.classList.contains("show-source") && english.length > 0;
    sourceCopy.replaceChildren(...english.map((text) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = text;
      return paragraph;
    }));

    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    dialog.querySelector(".reference-icon-close")?.focus();
  };

  const closeDialog = () => {
    if (typeof dialog.close === "function" && dialog.open) dialog.close();
    else dialog.removeAttribute("open");
  };

  const flashTarget = (target) => {
    reader.querySelectorAll(".reference-target").forEach((element) => element.classList.remove("reference-target"));
    target.classList.add("reference-target");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => target.classList.remove("reference-target"), 2600);
  };

  const jumpToReference = () => {
    if (!activeEntry) return;
    const entry = activeEntry;
    closeDialog();

    const documentButton = document.querySelector(`[data-document="${entry.document.id}"]`);
    if (documentButton && documentButton.getAttribute("aria-current") !== "page") documentButton.click();

    requestAnimationFrame(() => {
      const section = document.getElementById(entry.section.id);
      const target = section?.querySelector(`[data-search-index="${entry.paragraphIndex}"]`) || section;
      if (target) flashTarget(target);
    });
  };

  reader.addEventListener("click", (event) => {
    const trigger = event.target.closest(".rule-reference");
    if (!trigger) return;
    const entry = resolveReference(trigger.dataset.ruleReference, trigger.dataset.sourceDocument || currentDocumentId());
    if (entry) openReference(entry, trigger);
  });

  dialog.querySelector(".reference-icon-close").addEventListener("click", closeDialog);
  dialog.querySelector(".reference-close").addEventListener("click", closeDialog);
  jumpButton.addEventListener("click", jumpToReference);
  dialog.addEventListener("click", (event) => { if (event.target === dialog) closeDialog(); });
  dialog.addEventListener("close", () => {
    opener?.focus({ preventScroll: true });
    opener = null;
  });

  let scheduled = false;
  const decorate = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      reader.querySelectorAll("p[data-search-index]").forEach(decorateParagraph);
    });
  };

  new MutationObserver(decorate).observe(reader, { childList: true, subtree: true });
  decorate();
})();
