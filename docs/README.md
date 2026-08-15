# WFDF 中文规则源文档

`docs/` 是本项目唯一源资料目录：

- `WFDF团队飞盘规则2025-2028_中文校订整合版.md`：主规则中文校订稿。
- `WFDF团队飞盘规则2025-2028_附录v2.0_中文校订整合版.md`：附录中文校订稿。
- `WFDF团队飞盘规则2025-2028_官方注释_中文校订整合版.md`：官方注释中文校订稿。
- `WFDF-极限飞盘规则-判定流程图-中文转写.md`、`WFDF-极限飞盘规则-发盘图-中文转写.md`：图示 Markdown 源稿。
- `source-pdf/`：WFDF 英文原文 PDF。
- `diagram-assets/`：图示 Markdown 引用的中文 PNG 素材。
- `errata/`：勘误与验收清单，不直接参与网页生成。

在项目根目录运行 `python build_web_handbook.py`，会从上述源资料生成网页数据和网页 PNG。图示不再生成 PDF。生成物位于 `web/data.js`、`web/assets/`，不作为源文档编辑。
