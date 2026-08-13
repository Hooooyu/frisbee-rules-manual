# WFDF 中文网页版手册

静态网站。无需安装依赖。

在项目根目录运行：

```bash
python build_web_handbook.py
python -m http.server 8000 -d web
```

打开 `http://localhost:8000`。直接打开 `web/index.html` 也可阅读。

`build_web_handbook.py` 从英文 PDF 的文本层和已核查的翻译缓存生成 `web/data.js`，同时导出两份中文图示为 PNG，并将正文涉及的中英 PDF 与核查记录复制到 `web/`。页面中的 WFDF 原版文档入口指向 `https://rules.wfdf.sport/resources/`。改动源 PDF 或译文缓存后，重新运行生成脚本即可。

中文网页包含主规则、附录 v2.0、官方注释、判定流程图和发盘图五份文件；保留规则编号、原文或原图切换、全文搜索、版本说明、术语速查和图示。正式比赛以赛事公布的适用版本、英文原版与现场裁量为准。
