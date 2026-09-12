# 参考反应库的覆盖边界与扩充方案

日期：2026-09-10。用户已确认其本人或同事可使用 Reaxys / CAS SciFinder 中至少一个。本文件是收集与评估方案，不表示已取得商业数据库数据。

## 当前地图实际包含什么

本地文件逐行统计，见 [审计结果](reference_coverage_audit.json)，可用 `.venv/bin/python scripts/audit_reference_coverage.py` 复现。

| 层次 | 规模 | 能说明什么 |
|---|---:|---|
| 已下载 Schneider50k | 50,000 行、50 个类别标签，每类恰好 1,000 行 | 一个选定的反应分类基准 |
| 当前使用的专利样本 | 2,000 行，包含上述 50 个标签 | 在该基准内抽样，并非全部专利 |
| 地图中的专利结构点 | 1,988 个 | 当前结构标准化后的去重结果 |
| 地图中的酶反应结构点 | 640 个 | 固定 EnzymeEngineeringDB V6 来源的结构去重结果 |

该专利基准同时包含保护、脱保护、官能团转化等记录，不能把所有点直接称为“小分子催化反应”。把 2,000 条扩大为 50,000 条会增加固定类别内的实例，不能补齐基准以外的反应类型。所有导入记录仍未核查原文 / SI，也没有成为已验证的非酶先例。

50 类是这个参考数据集的标签数量，不是 RXNFP 输入的硬限制。新的、符合编码器输入要求的反应也可以编码；但编码成功并不证明这种表示能准确判断新反应家族的相似性。当前模型对目标任务是否有效仍需评估。

## 可执行的研究范围

两到三周内建立“所有发表过的小分子催化反应”的完整数据库不现实。适合本项目的问题是：**在预先界定的反应家族和检索范围内，结合结构与条件的信息能否改善非酶先例到酶反应的候选排序？**

不需要把整个候选库同时画出来。先在完整本地索引的原始指纹空间检索，再显示种子反应与相关邻域。二维图只用于查看结果；不能用屏幕上的远近替代原始空间检索。扩大候选库后需要重新生成相应索引，目前软件尚未连接 Reaxys / SciFinder 的实时查询。

建议先选 1–2 个具有明确底物活化方式的反应家族。C–N / C–O / C–S / C–C 只是成键分类，不足以定义家族；同一种键可能由完全不同的机理形成。用户的铁换铜体系的具体活化机制尚未在本项目中确定，不据金属和成键种类替用户猜测机理。

## 三种数据来源的作用

1. **公开背景库**：公开专利反应和 ORD 可提供较广的结构背景及可复现的对照。ORD 支持下载结构化反应及实验信息，但不保证完整覆盖所有期刊与最新方法。[ORD 官方说明](https://docs.open-reaction-database.org/en/stable/overview.html)
2. **目标家族期刊库**：使用可访问的 Reaxys / SciFinder 查询底物活化模式、反应物与产物子结构、成键变化，并逐步扩展金属、试剂和条件范围。Reaxys 收录期刊、专利及其他化学资料，入库存在时间差；数据库检索仍需要回到原文核查。[Reaxys 官方覆盖说明](https://www.elsevier.support/reaxys/answer/what-content-is-included-in-reaxys)
3. **人工核查的关键先例**：对相关方法论文及 SI 记录代表性反应、条件和证据定位。最初可将 30–50 篇方法论文、100–300 条代表性记录作为工作量目标，而非科学充分性保证。根据试收集难度调整，不为了达到数量稀释质量。

同一篇文章的几十个底物拓展示例可以用于结构检索，但不应全部计作不同反应发现。保留论文、方法家族、代表性转化和实验记录之间的关系；优先覆盖不同活化与转化模式，其次增加底物多样性。

## 第一次检索应怎样做

先做一个小试收集：围绕一个已知酶反应体系，选取约 5–10 篇非酶方法论文，完成代表性结构与条件核对，检查能否按现有模板录入。检索时不要一开始限定为“Cu + 水相 + 室温”，否则会排除有转移价值但原条件不同的先例。先获得化学相关候选，再用条件差异评估迁移难点。

按实际数据库与机构许可保存可导出的结构格式和文献元数据；有反应文件 / reaction SMILES 时保留原件，只有单分子 SDF 时还需要反应物 / 产物的角色关系，不能直接拼成反应。结构无法导出时可从原文 / SI 人工核对录入。现有中英文模板已经支持非酶体系，无需另建互不兼容的表格。

保存：检索日期、数据库、查询结构 / 文本、筛选条件、结果数量、纳入排除理由、导出文件版本。允许的个人检索导出不自动等于允许批量镜像、模型训练或公开再分发；公开项目应按数据许可和可公开的原文证据组织可复现部分。

## 怎样知道库是否够用

先诊断候选覆盖，再判断排序。在探索性试验中选少量已知非天然酶反应发现，核查本地库是否包含更早发表且化学上有对应关系的非酶先例。没有覆盖时区分：查询漏检、原文未收录、结构提取失败，或确实没有确认到对应先例。不能把“没找到”写成“从未发表”。

正式历史评估必须另行冻结候选库构建规则与日期，并保留覆盖不到的发现事件。不能先看测试发现的答案、专门补入其前驱论文，再把结果称为前瞻发现能力。比较至少包括结构相似检索、条件信息加入后的排序，以及简单基线；按独立论文 / 发现事件划分，避免同一论文底物示例泄漏。

仅展示相似反应地图，研究贡献仍有限。这个范围内可以争取的结果是有证据的候选覆盖分析、跨催化体系检索的失败模式，以及经独立评估的排序改善；并不预设会得到正向结果。

## English handoff: first literature collection batch

Use the existing English workbook and mark the system as nonenzymatic using its dropdown. Start with 5–10 method papers in one agreed activation / transformation family. This is a pilot collection, not a complete literature census.

For each representative reaction, retain:

- Reactant and product structures, with stereochemistry where reported; keep the original exported reaction file when available.
- DOI, earliest verified public date, and exact scheme / table / SI page and compound numbers.
- Catalyst, metal, ligand, additives, reaction partners, solvent, temperature, time, atmosphere, and light / electrochemical requirements when reported.
- Reported yield and its measurement type; distinguish isolated yield, conversion, and other activity measurements.
- The transformation family and any mechanistic claim with its source; mark inferred mechanisms separately.
- Query provenance, inclusion reason, missing fields, and review status. Missing information is not a negative experimental result.

Select diverse representative transformations before exhaustively transcribing substrate scopes. Preserve original records and do not merge conditions across experiments. Keep subscription-database exports local unless their use and redistribution are permitted.

## 地图操作

打开原路径 `outputs/bioreaction_atlas_v02/reference_demo/map/reaction_map.html`：悬停点看 RDKit 绘制的结构；点击点在下方固定详情；通过来源记录下拉框切换各条条件；点击 SVG 链接查看完整尺寸图。所有结构图存储在相邻的 `reaction_structures/`，离线可用，移动地图时要保留整个 map 文件夹。

图上画的是当前标准化结构视图，不自动标注反应中心，也不会把缺失条件补到箭头上。反应原始记录中的组分角色、条件与核查状态仍以来源证据为准。
