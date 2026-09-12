# BioReaction Atlas

2026-09-12 更新：当前研究问题与实测结果请先看[新版首页](README.md)和[英文技术报告](outputs/encoder_consistency/REPORT.md)。本文件保留原有中文安装、录入、检索和地图使用说明。

利用非酶催化先例，为新的非天然酶反应排优先级。第一阶段建立可追溯的数据和检索基线，研究反应相似性与催化环境信息是否有助于选择值得实验的转化。

第一次使用请从[从零开始理解与使用 BioReaction Atlas](docs/从零开始理解与使用BioReaction_Atlas.md)开始：包含可直接运行的查询、填表和导入步骤、四种指纹与地图原理、条件评分、评估方法及报错处理。

## 直接打开

在 Finder 中打开本项目文件夹，双击 `打开反应地图.command`，默认浏览器会打开已经生成的离线交互地图。无需启动服务器、重新安装环境或运行模型。可以缩放、悬停查看来源，并点击图例切换酶反应与专利参考层。

地图用于浏览已计算的表示空间；输入新反应进行检索使用下方的 `bioatlas neighbors` 命令。查看代码时，可用编辑器打开整个项目文件夹。

## 当前可用（v0.2）

- 中文 Excel 模板：`outputs/bioreaction_atlas_v01/非天然酶反应收集模板.xlsx`。
- 两张录入表、字段字典、填写说明和独立的虚构格式示例。原子映射与 SMILES 均可后补。
- Excel / CSV / JSON 导入和校验：唯一编号、关联关系、数值与单位、缺失值、出处、结构状态。
- [英文填写指南](docs/Collection_Guide_EN.md)及英文 Excel：`outputs/bioreaction_atlas_v02/Nonnatural_Enzyme_Reaction_Collection_EN.xlsx`。中英文下拉选项自动归一，合并保留来源、报告冲突。
- 四种可运行表示：Morgan 净反应指纹、底物 Morgan 指纹、官方 DRFP、官方权重 RXNFP。索引保存参数、来源和散列。
- [真实数据运行报告](outputs/bioreaction_atlas_v02/reference_demo/README.md)：复用1,342行旧酶库，按固定哈希独立抽取2,000行专利反应。RXNFP 编码后640个酶反应参考和1,988个专利参考构成联合地图。
- [离线交互地图](outputs/bioreaction_atlas_v02/reference_demo/map/reaction_map.html)、PNG及原始空间近邻关系；带结构图和出处的[检索证据卡](outputs/bioreaction_atlas_v02/reference_demo/rxnfp/cards/evidence_cards.md)。
- 可运行的条件一致性基线和发现事件级历史评估：固定候选池、时间核查、覆盖缺口、并列排名处理、随机/来源频率对照、按论文分组的bootstrap区间。

**等待科学数据核查的部分：前沿文献的结构和条件、严格时间划分的非酶先例池、发现事件及其先例对应关系、排序效果和前瞻候选结论。** 当前公开数据用于技术验证，不能据此报告“新反应成功率”。地图采用联合 t-SNE 展示 RXNFP 向量，未实现原版 TMAP 布局。

## 开始录入

先读 [数据收集指南](docs/数据收集指南.md)。第一批建议选 5 篇关键原始论文，每篇 1–2 条体系、3–6 个关键实验。优先覆盖不同研究组和活化方式，而非录完同一篇的全部突变体。

Excel 中 `反应条件` 一行代表“反应模式 × 催化体系 × 条件”；`实验结果` 一行代表一个实验的一个测量指标。一个实验的 yield 和 ee 共用实验编号，使用不同测量编号。相同发现事件通过发现事件编号关联。

正式数据表保持空白，格式示例在独立工作表。录入后仍可标为待核对；结构未补齐的记录可以导入，但不参与检索。

## 安装和运行

Python 3.11 或更高。本工作区已建好 `.venv`。重新安装可使用：

```bash
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -e '.[test,research,rxnfp]'
```

当前环境也支持以下不依赖 editable install 的命令。在项目根目录运行：

```bash
# 校验填好的工作簿，仅在没有错误时输出标准 JSON。
PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli validate \
  outputs/bioreaction_atlas_v01/非天然酶反应收集模板.xlsx \
  --out data/local/validation.json --normalized data/local/curated.json

# 构建索引；默认要求体系、结构均为已核对。
PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli index \
  data/local/curated.json --out data/local/index.json

# 格式示范：此 SMILES 仅展示命令语法，不是项目提出的候选。
PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli query \
  data/local/index.json 'CCO>>CC=O' --mode 非酶催化 \
  --top-k 10 --out data/local/neighbors.json

.venv/bin/python -m pytest -q
```

空白模板校验通过会输出 0 条记录，不代表已有科学数据。`data/local/` 默认忽略，供本地整理使用。

## 多人录入和新版检索流程

```bash
# 同事使用英文模板；无需翻译回中文。相同编号但内容不同会停止合并。
.venv/bin/bioatlas merge your_collection.xlsx colleague_collection.xlsx \
  --out data/local/merged.json

# 如两人已经使用相同编号体系，可显式加前缀，并自动更新关联键。
.venv/bin/bioatlas merge your_collection.xlsx colleague_collection.xlsx \
  --prefixes EM WK --out data/local/merged.json

# 将录入数据转换到多模型语料格式，再生成索引。
.venv/bin/bioatlas curated-corpus data/local/merged.json --out data/local/corpus.json
.venv/bin/bioatlas encode data/local/corpus.json --backend rxnfp \
  --model-dir data/local/public/rxnfp --out data/local/curated_rxnfp

# 查询和输出结构证据卡。这里的SMILES只示范语法。
.venv/bin/bioatlas neighbors data/local/curated_rxnfp 'CCO>>CC=O' \
  --model-dir data/local/public/rxnfp --top-k 5 --out data/local/neighbors.json
.venv/bin/bioatlas cards data/local/neighbors.json --out data/local/cards
.venv/bin/bioatlas map data/local/curated_rxnfp --out data/local/map
```

完整研究评估用法见 [EVALUATION.md](docs/EVALUATION.md)。`templates/evaluation_protocol.json` 是待填写协议；数据缺失时会明确拒绝运行，不输出虚构效果。

## 复现公开数据演示

```bash
# 仅从固定提交下载公开权重和参考文件，约53MB；校验大小、Git blob和SHA256。
.venv/bin/python scripts/fetch_public_assets.py

# 使用已获得的固定V6 CSV；整个运行在CPU上完成，无需算力券。
.venv/bin/python scripts/run_reference_demo.py --legacy /path/to/protein-evolution-database_V6.csv
```

旧CSV的固定公开下载位置记录在 `research/data_source_audit.json`。本机首次运行使用 `/tmp/ai4c_enzengdb_v6.csv`，重启后临时文件可能需要重新取得。专利池抽样在查看酶数据相似度之前由seed=17和原始行号哈希确定；默认2,000条用于技术演示。完整Schneider50k源文件已下载，但未宣称所有行都是已核查的非酶先例。

Schneider50k仅含50个类别标签，每类1,000行；扩大至完整50k仍不能覆盖全部有机反应。逐类统计见 [参考库覆盖审计](research/reference_coverage_audit.json)，期刊先例检索与英文收集交接说明见 [参考库扩充方案](research/reference_library_strategy.md)。

地图现在支持悬停反应结构预览、点击固定下方详情、逐条切换来源条件和打开完整SVG。重新打开原有HTML即可；分享或移动时需保留整个 `map/` 文件夹，包括相邻的 `reaction_structures/`。结构图仅展示当前结构视图，不自动补充缺失条件或推断反应机理。

## 表示与检索的边界

Morgan基线为产物计数减去反应物计数，radius=2、4096维、保留立体特征，使用有符号余弦相似度。DRFP为2048维、radius=3，使用二元Tanimoto；标准DRFP对反应方向对称，已用测试保留这一限制。RXNFP采用官方bert_ft的256维CLS表示与余弦相似度。超过词表或长度限制的结构显式排除，不截断。

所有表示使用相同的结构视图：去掉原子映射编号，忽略中间agents段，保留原始结构和条件作为证据。原始记录若把溶剂/试剂写在reactants段，程序不会猜测其角色；人工标准化仍有必要。当前表示不能直接识别机理或保证反应中心匹配。暂不做去盐、互变异构归一或猜补产物。未检出记录只描述被测试的目标转化，返回时保留状态。

旧版 `index/query` 接口仍提供实验级近邻，兼容v0.1；新版 `encode/neighbors` 按领域和结构合并条目、保留全部实验来源。发现事件评估要求独立候选分组和发现标签，不把突变体数当成发现数。条件一致性评分基于有出处的标准化标签，默认权重未经过拟合，不是可行性概率。

`--before YYYY-MM-DD` 仅过滤有日期及核查来源、且早于截止日的记录。它不自动证明时间无泄漏；需人工核查最早预印本及全部输入来源。`--exclude-source` 可排除一个来源，便于人工检查近邻是否来自同一篇文章。

## 数据来源与复现

当前检验使用固定版本 EnzymeEngineeringDB V6：提交 `bae30c9b45cb8a4eab1d6facd9314994f086cf9b`，散列保存在 `research/data_source_audit.json`。只在本地读取已有文件；发行目录未附原始 CSV。原数据再分发许可尚未确认，不应因代码仓库描述就推断数据许可。

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_legacy.py /path/to/protein-evolution-database_V6.csv \
  --out outputs/bioreaction_atlas_v01/legacy_technical_audit.json
```

结果：1,342 行、36 个非空 DOI；当前标准化规则下 1,324 行可生成非零指纹，639 个唯一标准反应，18 行失败或净变化为零。该结果不等于人工核对通过、领域覆盖率或推荐准确率。标准化去重口径与原文件的原始字符串去重不同。

依赖快照见 `requirements.lock.txt`。模板字段唯一来源为 `src/bioreaction_atlas/schema.py`，`templates/schema.json` 和 CSV 由 CLI 导出；Excel 创建脚本使用运行环境提供的 `@oai/artifact-tool`，不属于科研计算必需依赖。

研究背景见 [已核查的项目方案](research/non_natural_biocatalysis_reaction_atlas_proposal.md)，下一步见 [评估协议草案](research/evaluation_protocol_v01.md)。
