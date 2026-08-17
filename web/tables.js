(() => {
  const reader = document.querySelector("#reader");
  const toc = document.querySelector("#toc");
  if (!reader) return;

  const splitRow = (line) => {
    const placeholder = "\u0000";
    const value = line.trim().replace(/\\\|/g, placeholder).replace(/^\|/, "").replace(/\|$/, "");
    return value.split("|").map((cell) => cell.replaceAll(placeholder, "|").trim());
  };

  const isTableRow = (line) => {
    const trimmed = line.trim();
    return trimmed.startsWith("|") && trimmed.endsWith("|") && splitRow(trimmed).length >= 2;
  };

  const isSeparatorRow = (line) => isTableRow(line) && splitRow(line).every((cell) => /^:?-{3,}:?$/.test(cell));

  const alignmentFor = (separator) => {
    const left = separator.startsWith(":");
    const right = separator.endsWith(":");
    if (left && right) return "center";
    if (right) return "right";
    return "left";
  };

  const findTable = (text) => {
    const lines = text.split(/\r?\n/);
    for (let start = 0; start < lines.length - 1; start += 1) {
      if (!isTableRow(lines[start]) || !isSeparatorRow(lines[start + 1])) continue;
      let end = start + 2;
      while (end < lines.length && isTableRow(lines[end])) end += 1;
      const header = splitRow(lines[start]);
      const separators = splitRow(lines[start + 1]);
      if (header.length !== separators.length) continue;
      return {
        prefix: lines.slice(0, start).join(" ").replace(/\s+/g, " ").trim(),
        suffix: lines.slice(end).join(" ").replace(/\s+/g, " ").trim(),
        header,
        alignments: separators.map(alignmentFor),
        rows: lines.slice(start + 2, end).map(splitRow),
      };
    }
    return null;
  };

  const setCellAlignment = (cell, alignment) => {
    cell.classList.add(`align-${alignment}`);
  };

  const makeTable = (parsed, paragraph) => {
    const wrapper = document.createElement("div");
    wrapper.className = "rule-table-scroll";
    ["level-3", "level-4", "level-5"].forEach((level) => {
      if (paragraph.classList.contains(level)) wrapper.classList.add(level);
    });
    wrapper.setAttribute("role", "region");
    wrapper.setAttribute("tabindex", "0");

    const ruleNumber = paragraph.querySelector(".rule-number")?.textContent.trim();
    wrapper.setAttribute("aria-label", `${ruleNumber || "规则"} 示例表格`);

    const table = document.createElement("table");
    table.className = "rule-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    parsed.header.forEach((value, index) => {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = value;
      setCellAlignment(th, parsed.alignments[index] || "left");
      headerRow.append(th);
    });
    thead.append(headerRow);
    table.append(thead);

    const tbody = document.createElement("tbody");
    parsed.rows.forEach((values) => {
      const row = document.createElement("tr");
      parsed.header.forEach((_, index) => {
        const td = document.createElement("td");
        td.textContent = values[index] || "";
        setCellAlignment(td, parsed.alignments[index] || "left");
        row.append(td);
      });
      tbody.append(row);
    });
    table.append(tbody);
    wrapper.append(table);
    return wrapper;
  };

  const enhanceParagraph = (paragraph) => {
    if (paragraph.dataset.tableChecked === "true") return;
    paragraph.dataset.tableChecked = "true";
    const parsed = findTable(paragraph.textContent);
    if (!parsed) return;

    const number = paragraph.querySelector(".rule-number");
    const numberText = number?.textContent || "";
    let prefix = parsed.prefix;
    if (numberText && prefix.startsWith(numberText)) prefix = prefix.slice(numberText.length).trim();

    paragraph.replaceChildren();
    if (number) paragraph.append(number);
    if (prefix) paragraph.append(document.createTextNode(`${number ? " " : ""}${prefix}`));

    const table = makeTable(parsed, paragraph);
    paragraph.insertAdjacentElement("afterend", table);

    if (parsed.suffix) {
      const followup = document.createElement("p");
      followup.className = "rule-table-followup";
      followup.textContent = parsed.suffix;
      table.insertAdjacentElement("afterend", followup);
    }
  };

  const fixKnownTitles = () => {
    const english = "Seeding Pools (Semi-Random Seeding)";
    const sectionTitle = reader.querySelector("#appendix-e3 .section-title-en");
    if (sectionTitle && sectionTitle.textContent !== english) sectionTitle.textContent = english;
    const tocTitle = toc?.querySelector('a[href="#appendix-e3"] .toc-title-en');
    if (tocTitle && tocTitle.textContent !== english) tocTitle.textContent = english;
  };

  let scheduled = false;
  const decorate = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      reader.querySelectorAll("p[data-search-index]").forEach(enhanceParagraph);
      fixKnownTitles();
    });
  };

  new MutationObserver(decorate).observe(reader, { childList: true, subtree: true });
  if (toc) new MutationObserver(decorate).observe(toc, { childList: true, subtree: true });
  decorate();
})();
