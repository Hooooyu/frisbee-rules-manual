(() => {
  const data = window.HANDBOOK_DATA;
  const reader = document.querySelector("#reader");
  if (!data || !reader) return;

  const referencePattern = /\b([A-H]?\d+(?:\.\d+)+)\b/g;
  const numberedRulePattern = /^((?:[A-H]?\d+)(?:\.\d+)+)\.\s*/;
  const referencesByNumber = new Map();
  let previewSequence = 0;
  let activePreview = null;
  let activeTrigger = null;

  const ruleNumber = (text) => (String(text).match(numberedRulePattern) || [])[1] || "";
  const ruleDepth = (number) => number ? number.split(".").length : 0;
  const isDescendantRule = (candidate, parent) => Boolean(candidate && parent && candidate.startsWith(`${parent}.`));

  data.documents.forEach((document) => {
    document.sections.forEach((section) => {
      section.paragraphs.forEach((paragraph, paragraphIndex, paragraphs) => {
        const number = ruleNumber(paragraph.zh);
        if (!number) return;

        // A reference to a parent rule should include its complete subtree. Unnumbered
        // continuation paragraphs belong to the preceding numbered rule and are kept too.
        const relatedParagraphs = [paragraph];
        for (let index = paragraphIndex + 1; index < paragraphs.length; index += 1) {
          const nextParagraph = paragraphs[index];
          const nextNumber = ruleNumber(nextParagraph.zh);
          if (!nextNumber || isDescendantRule(nextNumber, number)) {
            relatedParagraphs.push(nextParagraph);
            continue;
          }
          break;
        }

        const entry = { number, document, section, paragraphIndex, paragraphs: relatedParagraphs };
        if (!referencesByNumber.has(number)) referencesByNumber.set(number, []);
        referencesByNumber.get(number).push(entry);
      });
    });
  });

  const currentDocumentId = () => document.querySelector('.document-button[aria-current="page"]')?.dataset.document || data.documents[0]?.id || "rules";

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
    button.setAttribute("aria-label", `展开规则 ${number}`);
    button.setAttribute("aria-expanded", "false");
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
    paragraph.classList.toggle("has-rule-reference", Boolean(paragraph.querySelector(".rule-reference")));
  };

  const closeActivePreview = () => {
    activePreview?.remove();
    if (activeTrigger?.isConnected) {
      activeTrigger.setAttribute("aria-expanded", "false");
      activeTrigger.removeAttribute("aria-controls");
    }
    activePreview = null;
    activeTrigger = null;
  };

  const flashTarget = (target) => {
    reader.querySelectorAll(".reference-target").forEach((element) => element.classList.remove("reference-target"));
    target.classList.add("reference-target");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => target.classList.remove("reference-target"), 2600);
  };

  const jumpToReference = (entry) => {
    closeActivePreview();
    const documentButton = document.querySelector(`[data-document="${entry.document.id}"]`);
    if (documentButton && documentButton.getAttribute("aria-current") !== "page") documentButton.click();

    requestAnimationFrame(() => {
      const section = document.getElementById(entry.section.id);
      const target = section?.querySelector(`[data-search-index="${entry.paragraphIndex}"]`) || section;
      if (target) flashTarget(target);
    });
  };

  const appendPreviewParagraphs = (container, entry) => {
    const rootDepth = ruleDepth(entry.number);
    let lastRelativeDepth = 0;

    entry.paragraphs.forEach((paragraph) => {
      const rawText = String(paragraph.zh || "").trim();
      if (!rawText) return;

      const number = ruleNumber(rawText);
      const line = document.createElement("p");
      line.className = "reference-inline-rule";

      if (number) {
        lastRelativeDepth = Math.max(0, ruleDepth(number) - rootDepth);
        const numberElement = document.createElement("strong");
        numberElement.textContent = `${number}.`;
        const body = rawText.replace(numberedRulePattern, "").trim();
        line.append(numberElement, document.createTextNode(body ? ` ${body}` : ""));
      } else {
        line.classList.add("reference-inline-continuation");
        line.textContent = rawText;
      }

      line.style.setProperty("--reference-depth", String(Math.min(lastRelativeDepth, 4)));
      container.append(line);
    });
  };

  const createInlinePreview = (entry, sourceParagraph) => {
    const preview = document.createElement("aside");
    preview.id = `rule-reference-preview-${++previewSequence}`;
    preview.className = "reference-inline";
    ["level-3", "level-4", "level-5"].forEach((level) => {
      if (sourceParagraph.classList.contains(level)) preview.classList.add(level);
    });
    preview.setAttribute("role", "note");
    preview.setAttribute("aria-label", `规则 ${entry.number} 引用内容`);

    const marker = document.createElement("span");
    marker.className = "reference-inline-marker";
    marker.setAttribute("aria-hidden", "true");
    marker.textContent = "↳";

    const copy = document.createElement("div");
    copy.className = "reference-inline-copy";
    appendPreviewParagraphs(copy, entry);

    const jump = document.createElement("button");
    jump.type = "button";
    jump.className = "reference-inline-jump";
    jump.textContent = "定位原条款";
    jump.setAttribute("aria-label", `定位到规则 ${entry.number}`);
    jump.addEventListener("click", () => jumpToReference(entry));

    preview.append(marker, copy, jump);
    return preview;
  };

  const toggleReference = (trigger) => {
    if (trigger === activeTrigger) {
      closeActivePreview();
      return;
    }

    const entry = resolveReference(trigger.dataset.ruleReference, trigger.dataset.sourceDocument || currentDocumentId());
    if (!entry) return;
    const sourceParagraph = trigger.closest("p[data-search-index]");
    if (!sourceParagraph) return;

    closeActivePreview();
    const preview = createInlinePreview(entry, sourceParagraph);
    sourceParagraph.insertAdjacentElement("afterend", preview);
    trigger.setAttribute("aria-expanded", "true");
    trigger.setAttribute("aria-controls", preview.id);
    activePreview = preview;
    activeTrigger = trigger;
  };

  reader.addEventListener("click", (event) => {
    const trigger = event.target.closest(".rule-reference");
    if (!trigger) return;
    toggleReference(trigger);
  });

  let scheduled = false;
  const decorate = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      if (activePreview && !activePreview.isConnected) closeActivePreview();
      reader.querySelectorAll("p[data-search-index]").forEach(decorateParagraph);
    });
  };

  new MutationObserver(decorate).observe(reader, { childList: true, subtree: true });
  decorate();
})();
