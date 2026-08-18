(() => {
  const data = window.HANDBOOK_DATA;
  if (!data?.documents) return;

  const annotations = data.documents.find((document) => document.id === "annotations");
  if (!annotations) return;

  const table = `| # | 注释位置 | 英文 Official Annotations | 现行主规则对应编号 | 中文稿状态 | 校订说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 9.3「其他所有示意」标题 | 9.5.4 | 9.5.5 | 已校正 | 现行主规则中“其他所有示意”已编号为 9.5.5 |
| 2 | 9.4 标题 | 9.5.4.1 | 9.5.5.1 | 已校正 | 条款重新编号 |
| 3 | 9.4 正文，第 1 处 | 9.5.4.1 | 9.5.5.1 | 已校正 | 同上 |
| 4 | 9.4 正文，第 2 处 | 9.5.4.1 | 9.5.5.1 | 已校正 | 同上 |
| 5 | 9.5 标题 | 9.5.4.2 | 9.5.5.2 | 已校正 | 条款重新编号 |
| 6 | 9.5 正文 | 9.5.4.2 | 9.5.5.2 | 已校正 | 同上 |
| 7 | 12.9「伸展的手臂或腿部」标题 | 12.19 | 12.9 | 已校正 | 英文注释中的明显编号/排版错误 |
| 8 | 15.10「处理多个规则违背」正文 | 9.5.4.1 | 9.5.5.1 | 已校正 | 与现行 9.5 编号体系保持一致 |
| 9 | 8.5「明显改变飞盘位置」正文 | 18.2.6 | 18.2.5 | 待校正 | 现行 18.2.5 才规定无争议 Travel 后比赛不中断并纠正轴心点 |
| 10 | 10.1「不需要验盘的情况」正文 | 18.2.5.3 | 18.2.4.3 | 待校正 | 现行 18.2.4.3 才规定建立轴心点前不得开始 wind-up / throwing motion |
| 11 | 13.13「界内攻防转换后的轴心脚位置」正文 | 18.2.5.1 | 18.2.4.1 | 待校正 | 现行 18.2.4.1 才规定在错误位置建立轴心点构成 Travel |
| 12 | 17.6「防守方接盘犯规无争议后在进攻得分区取得盘权」正文 | 14.2 | 14.3 | 待校正 | 现行 14.3 才规定未形成得分时移动到最近得分线建立轴心点 |
| 13 | 18.5「双人防守」正文 | 18.1.4 | 18.1.3.1 | 待校正 | 现行 18.1.3.1 明确规定非法站位纠正后才能恢复读秒 |
| 14 | 18.8「防盘违规后防盘队员没有调整读秒」标题 | 18.1.5 | 18.1.4 | 待校正 | 现行 18.1.4 是相关 Marking Violation 处理条款 |
| 15 | 18.9「性质严重的防盘违规」标题 | 18.1.5.3 | 18.1.4.3 | 待校正 | 现行 18.1.4.3 才是 egregious marking infraction |
| 16 | 18.10「跑动接盘减速过程中传盘」标题 | 18.2.2.1 | 18.2.1.1 | 待校正 | 现行 18.2.1.1 是跑动/跳跃接盘后直接出盘的例外 |
| 17 | 18.11「作出走步示意」标题 | 18.2.5 | 18.2.4 | 待校正 | 现行 18.2.4 定义构成 Travel 的各种情形 |
| 18 | 18.11 正文 | 18.2.2.1 | 18.2.1.1 | 待校正 | 与现行跑动接盘直接出盘条款对应 |
| 19 | 18.12「助跑出盘」标题 | 18.2.5.3 | 18.2.4.3 | 待校正 | 与建立轴心点前不得开始掷盘动作对应 |
| 20 | 18.13「拍盘（Tipping）」标题 | 18.2.5.5 | 18.2.4.5 | 待校正 | 现行 18.2.4.5 规定故意 bobble / fumble / delay 以移动属于 Travel |
| 21 | 18.14「走步示意后继续比赛」标题 | 18.2.6 | 18.2.5 | 待校正 | 现行 18.2.5 才是无争议 Travel 后继续比赛的处理程序 |
| 22 | 18.14 正文 | 18.2.6 | 18.2.5¹ | 待校正 | 现行 18.2.5 是该处理程序；如采用最细一级引用，可进一步指向 18.2.5.1 |
| 23 | 18.15「走步违例后的比赛恢复」标题 | 18.2.7 | 18.2.6 | 待校正 | 现行 18.2.6 才规定 Travel 后完成传盘所产生的 Travel Violation 处理 |`;

  const text = [
    "本中文《WFDF 团队飞盘规则 2025–2028 官方注释》以 WFDF 发布的英文 Rules of Ultimate 2025–2028 Official Annotations 为主要翻译和校订依据。",
    "在对英文《Official Annotations》与现行《WFDF Rules of Ultimate 2025–2028》主规则进行逐条核对时，我们发现部分规则交叉引用编号与现行主规则的实际编号不一致。这些差异主要表现为规则修订后的条款重新编号，以及少量明显的编号或排版错误。",
    "为避免读者因引用不存在的条款，或跳转到编号仍存在但内容已经改变的条款而产生误解，本中文校订版会在不改变官方注释原有规则解释、案例事实和处理结论的前提下，对能够通过上下文和现行主规则明确确认的交叉引用编号进行校正。",
    "因此，部分中文注释中的规则编号会有意与英文 Official Annotations PDF 不同。",
    "需要特别说明：",
    "• 校订仅针对规则交叉引用编号；",
    "• 注释正文的规则解释和案例结论不因这些编号校正而改变；",
    "• 下表完整记录目前确认的 23 处编号差异；",
    "• 其中部分编号此前已经在中文校订过程中修正，其余编号将在本轮校订中按现行主规则修正；",
    "• 如果 WFDF 后续发布新版、勘误版或更新后的 Official Annotations，本项目将再次以 WFDF 正式文本为准进行核对。",
    `已确认的规则引用编号差异\n${table}`,
  ];

  const declaration = {
    id: "annotations-revision-notice",
    key: "",
    title: "关于英文《Official Annotations》中规则引用编号的校订说明",
    paragraphs: text.map((zh) => ({ zh, en: "", page: null })),
  };

  annotations.sections = [
    declaration,
    ...annotations.sections.filter((section) =>
      section.id !== declaration.id &&
      section.title !== "修订公告" &&
      section.title !== "目录" &&
      section.key !== "Contents"
    ),
  ];

  const decorateRevisionNoticeToc = () => {
    const link = document.querySelector('#toc a[href="#annotations-revision-notice"]');
    if (!link) return;
    const titleNode = link.querySelector(".toc-title") || link;
    const zh = titleNode.querySelector(".toc-title-zh");
    const en = titleNode.querySelector(".toc-title-en");
    if (zh?.textContent === "修订公告" && en?.textContent === "Revision Notice") return;
    titleNode.innerHTML = '<span class="toc-title-zh">修订公告</span><span class="toc-title-en" lang="en">Revision Notice</span>';
  };

  window.addEventListener("DOMContentLoaded", () => {
    decorateRevisionNoticeToc();
    const toc = document.querySelector("#toc");
    // app.js replaces #toc children when switching documents. Observe only those
    // direct replacements; observing the whole subtree would also see our own
    // titleNode.innerHTML update and recursively trigger this callback.
    if (toc) new MutationObserver(decorateRevisionNoticeToc).observe(toc, { childList: true });
  });
})();
