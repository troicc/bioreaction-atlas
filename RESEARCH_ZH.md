# 研究现状

最后更新：2026-09-20（含 F8）。本文件是**交接说明**：测量了什么、意味着什么、代码在哪里、还有什么没做。新会话接手本项目前请先读它。英文版见 [RESEARCH.md](RESEARCH.md)，两者内容对应。

---

## 1. 目标

**给定某个酶平台已经实现的反应，输出一份值得在该平台上尝试的非酶反应清单，并附上证据。**

本仓库其余一切都为此服务。哪些组件尚未服务于它，见 §7。

---

## 2. 一段话概括

反应相似性检索本应把酶化学与其非酶对应物连接起来。经过测量，它**默认不工作**：当时使用的候选语料里根本不含相关化学；即便换上正确的语料，只要酶和化学家从**不同前体**出发——而这正是生物催化的常态——四种表示里有三种会把**错误的**活化家族排得比随机还靠前。把两条路线改写到它们共享的**中间体**层面可以修复结构指纹，但修不好一个学习得到的反应嵌入，因为在那个空间里该家族根本不成为一个区域。最终结果是：一个**可用的家族筛子**，和一个**不可用的家族内排序器**。

---

## 3. 发现

### F1. 专利语料中不存在卡宾转移先例

**278** 条血红素卡宾酶种子，四种表示在 1,988 条专利池的 top-10 中**一条卡宾转移反应都没检出**。这不是表示方法的失败：扫描全部 **50,000** 行 Schneider50k，仅 **2** 条（0.004%）含取代重氮反应物，且两条都不是卡宾转移——一条是 Mitsunobu 的偶氮二甲酸酯试剂，一条是甾体铬氧化（重氮只是旁观基团）。

已发表的三张 rxnfp 反应地图全部来自专利（Schneider 50k；USPTO 1k TPL，445k 条；Pistachio）。从 50k 放大到 445k 增加的是常规转化而非方法学化学，而且 Lowe 的数据止于 2016 年 9 月。

**对此前编码器一致性研究的影响**：其 0.70%–11.07% 的跨域重叠，是在一个对该化学不存在正确答案的候选池中测出的。它证明表示之间不一致，但**不能证明任何一种表示失败了**。

报告：`outputs/candidate_pool/REPORT.md`

### F2. 检索恰好在前体不同时失效

两个家族共用一个 1,341 条候选池（卡宾 74.6%、脱氢氨基酸 25.4%）。酶种子查询合并池，top-10 按本家族占比计分，以该家族的**池内占比**为无技能基线。

| 表示 | 卡宾种子（n=278，17 篇） | PLP 种子（n=31，**5 篇**） |
|---|---:|---:|
| *无技能基线* | *74.6%* | *25.4%* |
| Morgan 差分 | 96.4%（×1.29） | **9.3%（×0.37）** |
| substrate Morgan | 93.8%（×1.26） | 14.5%（×0.57） |
| DRFP | 99.9%（×1.34） | 43.2%（×1.69） |
| RXNFP | 98.9%（×1.33） | **8.4%（×0.33）** |
| 零同族命中的种子 | 四种全为 0 | 31 条中 20 / 12 / 2 / 19 |

卡宾是**简单情形**：酶和化学家都消耗**重氮化合物**，诊断性基团出现在两边的反应 SMILES 里。PLP 不是：TrpB 消耗**丝氨酸**并在活性位点内生成氨基丙烯酸酯，而非酶路线从**已成形的脱氢丙氨酸**出发。**共享的那个对象在两边的 SMILES 里都不存在。**

**酶普遍在活性位点内从不同前体原位生成中间体，所以 PLP 这种情形才是常态。**

### F3. 归一化到中间体可以修复——但只对结构指纹有效

一条反应 SMARTS 通过 β-消除把丝氨酸、半胱氨酸、O-磷酸丝氨酸、苏氨酸改写为氨基丙烯酸酯。另两条规则把**反应物和产物两侧**都归约到未保护的游离酸。

| 表示 | 原始 | 反应物归一化 | 受体规范化 | **两侧全规范化** |
|---|---:|---:|---:|---:|
| Morgan 差分 | ×0.37 | ×3.28 | ×3.87 | **×4.82（98.1%）** |
| substrate Morgan | ×0.57 | ×1.68 | ×3.58 | ×3.95 |
| DRFP | ×1.69 | ×3.83 | ×4.30 | **×4.92（100.0%）** |
| RXNFP | ×0.33 | ×0.77 | ×0.53 | ×0.78 |
| 零同族命中种子 | 20/12/2/19 | 1/1/0/8 | 1/0/0/21 | **0/0/0/8** |

**没有模型、没有训练、没有新数据。** 卡宾数值不受影响——该族无规则适用，这是必要的对照。**非泄漏**：31 条归一化种子与池中记录无一完全相同。

### F4. RXNFP 修不好，因为该家族在它的空间里不成区域

先后提出两个解释，**均被测量证伪**：受体保护基（规范化后反而更差，0.77→0.53）、产物保护基（全规范化后回到 0.78，仍低于基线）。

于是不再推测查询，**直接测量空间**：

| 表示 | 卡宾 内/跨/**可分离** | 脱氢氨基酸 内/跨/**可分离** |
|---|---|---|
| Morgan 差分 | 0.123 / 0.009 / **+0.114** | 0.148 / 0.009 / **+0.139** |
| substrate Morgan | 0.554 / 0.434 / **+0.120** | 0.503 / 0.434 / **+0.069** |
| DRFP | 0.087 / 0.017 / **+0.070** | 0.102 / 0.017 / **+0.085** |
| RXNFP | 0.700 / 0.347 / **+0.352** | 0.363 / 0.347 / **+0.015** |

对一条归一化的 PLP 种子，RXNFP 到**卡宾**家族的平均相似度 0.629，到**本家族**仅 0.391；top-6 里是一条脱氢氨基酸反应加五条环丙烷化。

> **归一化能把查询对齐到一个家族，但造不出该表示本来就不编码的邻域。**

`scripts/family_cohesion.py` 把这做成**前置检查**——不需要种子、不需要检索，只要编码好的池子。

关于**为什么**的未检验假说：RXNFP 是为专利反应分类训练的，其几何结构沿专利类别组织。卡宾化学对应连贯的类别；而对脱氢氨基酸的共轭加成横跨硫醚合成、N-烷基化、Heck 偶联等不相关类别。

### F5. 当前产物是筛子，不是排序器

判据：**三个融合表示是否都把它排进池子前 10%**（记为 firm）。

| 平台 | 家族 | firm |
|---|---|---:|
| 血红素 | 金属卡宾 | **8 中 7** |
| PLP | 脱氢氨基酸加成 | **10 中 0** |

三种表示在**该搜哪个家族**上一致，在**家族内排序**上不一致。PLP 最佳候选的最差名次是 303 中第 43。**PLP 清单的化学是对的**——硫酚、萘硫酚、苄胺对脱氢丙氨酸的加成，正是半胱氨酸合酶做的事——所以它应被当作**十篇待读论文**，而非排好序的十个候选。

回溯核对：卡宾清单包含卡宾对 Si–H 的插入，即 2016 年细胞色素 c 变体被改造去做的那个转化。酶催化 Si–H 插入本就在种子集中，所以这是**排序确实追踪可迁移性的证据，不是一次预测**。

### F6. 精确匹配的 ground truth 不存在

**639** 条酶反应中，仅 **1** 条在非酶池中有 ≥0.95 的结构匹配（1-苯基丙炔的环丙烯化）。**可迁移性发生在转化类型层面，不在底物层面**，因此标签无法自动采集。ground truth 只能来自人工裁定发现事件。

### F8. 催化环境会重排清单，幅度依家族而定

带标签的评估先失败了，这件事值得记录：把"与酶反应相似"定义为"已知可迁移"，0.3 阈值下卡宾池 23 个正样本、PLP 池 **3 个**，且随阈值成倍变化。**无法做带标签评估。**

因此改为报告**迁移障碍**——一条已记录的操作要在蛋白体系中运行需要改变什么。每条轴陈述的是蛋白能耐受什么，不需要可迁移性标签。**未记录的条件单独计为 unknown，绝不计为"已清除"。**

各排序下 top-10 的平均障碍数，对照池均值：

| 排序 | PLP | 血红素 |
|---|---:|---:|
| *池均值* | *0.9* | *2.0* |
| 结构（融合） | **0.1** | **1.9** |
| 障碍最少 | 0.0 | 0.0 |
| 热门 / 最新 / 随机 | 1.4 / 0.8 / 1.0 | 2.2 / 1.9 / 1.6 |

**PLP：环境信息几乎无增益**——结构排序本身已给出无障碍候选，且该池 49.0% 本就无障碍，因为 PLP 化学本就是无金属、水相、温和的。

**卡宾：增益极大**——结构排序给出 1.9，与池均值 2.0 无异（它捞的就是池子主体的 Rh/DCM 化学），而该池仅 5.4% 无障碍。两份 top-10 **重叠 0/10**。障碍排序首位是 **hemin 在水中 20°C 催化的卡宾转移**（平台自己的辅因子，在蛋白能存活的条件下运行），另有三条**无金属**卡宾化学。结构排序一条都没浮出来。

报告：`outputs/candidate_pool/TRANSFER_OBSTACLES.md`。代码：`src/bioreaction_atlas/transfer.py`、`scripts/recommend_candidates.py --order`。

### F7. 建设过程中发现的数据质量问题

- **同论文泄漏**抬高表观检索质量：排除与查询共享来源 DOI 的候选后，酶库内部 top-10 一致性由 42.8–62.5% 降至 16.6–37.7%。
- 固定 EnzymeEngineeringDB V6 文件中的**两处出处缺陷**：一条记录的编码转化（N–H 官能化）与其论文主题（分子内 C(sp3)–H 胺化）不符；另一条的产物遗漏了含硫底物。
- Schneider50k 中 **79%** 的行在 agents 段携带催化条件，而 `structure_view` 将其丢弃；其中仅 7.6% 含过渡金属。
- 一次 Reaxys 导出中包含 **1 篇撤稿论文**、10 篇综述、10 篇会议摘要。

---

## 4. 代码地图

### 库 —— `src/bioreaction_atlas/`

| 模块 | 用途 |
|---|---|
| `activation.py` | 活化家族、成员筛查、agents 段解析、`acceptor_consumed`、`family_screen` |
| `intermediates.py` | `normalize_reactants`（前体→中间体）、`canonicalize`（两侧→未保护核心） |
| `transfer.py` | 迁移障碍：介质、温度、平台金属、外部配体、蛋白致命试剂 |
| `methodology.py` | 文献反应批量录入；筛查、文献类型过滤、家族标注 |
| `rdf.py` | RD File 读取；按 variation 展开；Reaxys 字段映射 |
| `reaxys_pdf.py` | 从 Reaxys PDF 导出中恢复引文与条件层 |
| `coverage.py` | 协议 v0.2 四状态机与 C/N 核算（**已实现，从未在真实事件上运行**） |
| `corpus.py`、`encoders.py`、`consistency.py` | 既有：语料、四种表示、一致性指标 |
| `cards.py`、`maps.py`、`map_view.py` | 证据卡与离线地图 |
| `evaluation.py` | 既有的 v1 单截止日期排序设计。**与 `coverage.py` 相互独立，不可混用。** |

### 脚本 —— `scripts/`

| 脚本 | 作用 |
|---|---|
| `rdf_to_csv.py` | RD File → 导入 CSV。**务必先跑 `--list-fields`** |
| `import_methodology.py` | CSV → 语料。`--normalize` 接纳原位生成路线，`--no-screen` 保留带标签的混合池 |
| `reaxys_pdf_citations.py` | 从 PDF 导出恢复引文 |
| `recommend_candidates.py` | **交付物。** 给定平台输出排序清单；`--order` 切换排序/基线 |
| `cross_family_retrieval.py` | F2/F3 测量 |
| `family_cohesion.py` | F4 前置检查 |
| `family_match_rate.py` | F1 测量 |
| `coverage_status.py`、`event_worksheet.py`、`seed_coverage_registry.py` | 覆盖审计（未使用） |

### 文档

| 路径 | 内容 |
|---|---|
| `research/activation_family_map.md` | 每个酶平台该挖哪类非酶化学；共享前体 vs 共享中间体 |
| `docs/BUILDING_THE_CANDIDATE_POOL.md` | Reaxys 检索与导出；每族一个把手；会悄悄放宽查询的设置 |
| `docs/RECOMMENDING_CANDIDATES.md` | 清单如何构建、不主张什么 |
| `docs/COVERAGE_AUDIT.md` | 未执行的审计的逐事件流程 |
| `outputs/candidate_pool/REPORT.md` | F1 |
| `outputs/candidate_pool/CROSS_FAMILY.md` | F2、F3、F4 |
| `outputs/candidate_pool/TRANSFER_OBSTACLES.md` | F8 |
| `outputs/encoder_consistency/REPORT.md` | 早期编码器一致性研究；CI 从 `summary.json` 重新生成并比对 |

### 本地数据 —— `data/local/`（gitignore，受许可限制）

| 路径 | 内容 |
|---|---|
| `pools/carbene.json` | 2,426 条记录、999 个结构、1,075 篇论文、1888–2026 |
| `pools/plp.json` | 359 条记录、347 个结构、约 148 篇论文、1932–2026 |
| `pools/combined_full/` | 两族合并、两侧全规范化、四种表示已编码。**用这一个。** |
| `reference_demo/` | 酶种子：639 条反应、36 个 DOI；辅因子 heme 1194 / PLP 117 / Fe(II) 13 |
| `candidates/` | 生成的候选清单 |

---

## 5. 从零重建

```bash
# 1. Reaxys 导出：Reactions 标签页，RD File 格式。详见 docs/BUILDING_THE_CANDIDATE_POOL.md
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf --list-fields
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf --family metal_carbene --out pool.csv
PYTHONPATH=src .venv/bin/python scripts/import_methodology.py pool.csv --out data/local/pools/x.json --prefix X

# 2. 两侧规范化后编码（规范化片段见 CROSS_FAMILY 报告内的代码）
for b in morgan substrate drfp; do
  PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli encode data/local/pools/combined_full.json \
    --backend $b --allow-unreviewed --out data/local/pools/combined_full/$b
done
PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli encode data/local/pools/combined_full.json \
  --backend rxnfp --model-dir data/local/public/rxnfp --allow-unreviewed --out data/local/pools/combined_full/rxnfp

# 3. 信任任何表示之前，先确认该家族在其空间中成区域
PYTHONPATH=src .venv/bin/python scripts/family_cohesion.py

# 4. 产出清单（--order 可切换 structure/obstacles/popularity/recency/random）
PYTHONPATH=src .venv/bin/python scripts/recommend_candidates.py --family aminoacrylate_addition --cofactor PLP
```

---

## 6. 本项目自我约束的规则

这些规则**由代码和测试强制执行**，不只是写在文档里。

- **不给可行性分数，不给成功概率。** 候选带证据和顺序，绝不带一个暗示已校准似然的数字。
- **imported 不等于已核对。** 文献标识符不是经核查的实验步骤。
- **出版年份不等于已核实的最早公开日期。**
- **不推断机理。** `mechanism_evidence` 在有人读原文之前保持 `未说明`。
- **Top-k 未命中不等于语料缺失。**
- **有争议的判断记录为属性，不写进成员资格。** `acceptor_consumed` 是范例：Heck 算不算 PLP 先例，两种口径都可报告。
- **未决项保留在分母中。**
- **标签是答案 key，不是训练数据。** 一个由结构决定的确定性标签，只会教会模型那条规则，而非化学。

---

## 7. 尚未完成

按对目标的阻塞程度排序。

**① 除"同一家族"外，没有"值得一试"的定义。** F6 表明标签无法自动采集。唯一出路是人工裁定约 20 个发现事件——`research/coverage_protocol_v02.md` 与 `docs/COVERAGE_AUDIT.md` 已完整定义流程，`src/bioreaction_atlas/coverage.py` 已实现核算，而**标注事件数为零**。当前状态：C=0，U=5，N=5。

**② 家族内排序仍然没有*结构*信号。** F5 结论不变。F8 部分回答了它：催化环境对卡宾清单有决定性重排，对 PLP 清单几乎无作用。仍未建立的是**同一障碍层级内部**的排序——卡宾前五名全是零障碍，没有任何东西能区分它们。

**③ 基线已存在**（`--order popularity|recency|random`），但它们比较的是**排序之间**，不是正确性。没有任何排序被证明能预测迁移，因为 ① 未完成。

**④ 约十四个家族只做了两个。** 其余见 `research/activation_family_map.md`。ThDP↔NHC 被卡住：固定 V6 文件中**没有 ThDP 种子**，必须先从文献策展（南京大学 Huang Xiaoqiang 组在 ThDP 改造上最活跃）。

**⑤ PLP 种子集是 5 篇论文的 31 条反应。** 论文级 n=5 是 F2–F4 发表的最硬限制。卡宾是 17 篇的 278 条。

**⑥ 一个已知的池子缺口。** 非酶路线可以从**酶自己用的前体**原位生成受体，而基于受体的子结构查询完全漏掉这条路线。`import_methodology.py --normalize` 现已能接纳此类反应，相应的检索方案也已写好，但**那次导出尚未执行**。

**⑦ 没有存档 DOI。** 仓库已公开且 CI 全绿；Zenodo 尚未连接，`CITATION.cff` 中只有 GitHub handle。

---

## 8. 可复现性

**168 项测试**，其中 167 项在 CI 上于 Python 3.11 与 3.12 仅凭 checkout 运行。CI 另行从 `summary.json` 重新生成 `outputs/encoder_consistency/REPORT.md` 并在不一致时失败，因此该报告中任何指标都无法被手工改写。Reaxys 原始导出、模型权重与含详细来源的派生记录保留在 `data/local/`；仅聚合结果入库。
