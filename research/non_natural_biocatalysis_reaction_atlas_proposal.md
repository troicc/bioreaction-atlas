# 从非天然酶反应地图到新反应候选：文献核查与项目设计

2026-09-12 范围调整：当前主方案以[英文研究方案](research_proposal_EN.md)和[先例覆盖协议 v0.2](coverage_protocol_v02.md)为准，先测量覆盖与表示依赖性。本文保留此前文献核查和设计理由；其中条件重排、前瞻候选与三周交付安排不再是当前优先任务。

截至 2026 年 9 月 10 日的定向研究与初始方案。本文讨论如何利用已发表的非天然酶反应、条件和非酶催化先例，帮助选择新的酶催化研究方向。后续已开始实现，最新状态见 [implementation_status.md](implementation_status.md)；尚无经过科学评估的效果结论或新反应实验验证。

## 1. 结论

可以把已知非天然酶反应编码到 Schwaller 的 RXNFP 表示空间，检索相似反应并展示分类区域。技术上可行，而且具有整理知识、查找先例和提出假设的用途。但是，酶反应映射、非天然酶数据库和基于反应相似性的酶推荐均已有先例。只完成收集、编码和绘图，研究贡献有限。

更值得研究的是：**以已经实现的非天然酶反应为起点，在非酶催化文献中寻找值得转移到酶体系的反应，并检验哪些相似性和催化条件信息真正有助于这一选择。** 地图是浏览入口，候选反应的排序和证据是核心结果。

这与实验中的“先确定哪个新反应值得试”直接相关。它仍不能保证初始活性，也不要求先训练一个新的蛋白模型。三周内合理的目标是一个范围明确的数据集、一项历史发现回溯实验和少量有依据的前瞻候选；“全领域完整收集”和“证明全新反应可行”不应作为同一期交付承诺。

## 2. 已经有人做到了哪一步

| 工作 | 与本思路直接相关的内容 | 差异及边界 |
|---|---|---|
| Kreutter、Schwaller、Reymond，2021 | 将酶反应用 RXNFP 编码、通过 TMAP 展示，并按酶类别观察聚类 | 已有“酶反应放入反应地图”的直接先例；其地图分析不包含酶描述 |
| EnzEngDB，2026 专刊 | 汇集非天然酶工程反应；相关代码包含 RXNFP，论文比较工程酶与天然酶反应空间 | 已有数据收集与空间比较；完整覆盖和条件语义仍需逐来源核查 |
| EC-BLAST，2014 | 以键变化、反应中心和整体结构比较酶反应 | 多层反应相似性不是新方法 |
| BridgIT，2019 | 依据反应中心周围结构，给新反应/孤儿反应推荐酶；使用历史数据版本验证 | 相似性推荐和历史回溯都已有先例；主要在生化反应与酶指认背景下评估 |
| RetroBioCat Database，2023 | 收集用于合成的酶催化数据，并提供相似性搜索和分析 | 不能把另建生物催化数据库作为天然创新点 |
| CATNIP，2025 | 用酶—底物实验矩阵和化学/序列空间，指导反应适配性筛选 | 证明空间导航可以有实验用途，但主要是特定酶化学中的适配性发现 |
| ChemEnzyRetroPlanner，2025 | 用 RXNFP 等工具支持有机—酶混合合成规划及酶类别推荐 | “将有机合成与酶催化连接”也已被研究；数据集类别不等于物理可行性边界 |

原始来源：[酶促反应 Transformer](https://pubs.rsc.org/en/content/articlehtml/2021/sc/d1sc02362d)、[EnzEngDB 论文](https://academic.oup.com/nar/article/54/D1/D564/8373944)、[EnzEngDB 分析代码](https://github.com/fhalab/EnzymeEngineeringDB)、[EC-BLAST](https://www.nature.com/articles/nmeth.2803)、[BridgIT](https://pubmed.ncbi.nlm.nih.gov/30910961/)、[RetroBioCat Database](https://pubs.acs.org/doi/abs/10.1021/acscatal.3c01418)、[CATNIP](https://www.nature.com/articles/s41586-025-09519-5)、[ChemEnzyRetroPlanner](https://www.nature.com/articles/s41467-025-65898-3)。

这些先例证明该想法有技术基础，也提高了原创性门槛。当前检索没有确认一个完全覆盖“非天然金属酶种子 → 非酶催化候选 → 催化环境与活化方式排序 → 历史反应发现验证”的成熟通用系统；这只是检索状态，不能据此宣称首创。

## 3. 这里的 map 是什么

这里对应的是 RXNFP 反应表示与 TMAP 地图，而不是 SynthAtlas 的路线展示，也不是 RXNMapper 的原子映射。RXNFP 从反应 SMILES 计算向量，TMAP 把这些向量的邻域关系可视化。官方代码支持独立生成指纹和地图，无须依赖 SynthEx。[RXNFP 官方仓库](https://github.com/rxn4chemistry/rxnfp)

实际做法是让非天然酶反应与非酶催化反应使用同一编码器，先在原始高维表示中检索近邻，再将联合数据绘图。不能以二维图上的直线距离替代反应相似度，也不能分别绘制两张地图后比较坐标。地图上的位置取决于所选语料、距离和布局，不是一个固定的自然科学坐标系。

应将反应净变化与催化条件分别保存。为了比较跨催化环境的净转化，可以构建不含条件的结构视图；为了评价能否迁移，则另行使用完整条件。后一层不能被前一层的高相似度替代。

## 4. 从“相似”到“值得实验”缺少什么

考虑三个都会形成 C–N 键的反应：酰胺形成、金属催化偶联、卡宾 N–H 插入。它们可能共享一个宽泛成键标签，却涉及不同底物活化与催化过程。同样的元素连接变化，不足以推导同一个铜酶平台都能完成它们。

有用的候选需要同时回答：

1. **发生什么结构变化？** 成断键、反应中心及其邻近官能团是否相近。
2. **靠什么产生反应性？** 金属、辅因子、光照、氧化还原搭档、活性中间体证据是否提供可迁移的化学依据。
3. **为什么选这个酶平台？** 是已有相同中间体化学、可比配位环境，还是只有总体结构相似。
4. **转移还缺什么？** 例如反应依赖游离小分子配体、特殊介质、另一种供电子方式，或可能出现竞争路径。
5. **证据有多强？** 文献已测、作者提出的机理、计算解释和项目推测必须分开。

条件差异是待分析的迁移障碍，不能简单设置“有机溶剂 = 酶内不可行”等绝对规则。酶体系可能改变反应路径，因此检索也不应只寻找完全相同的传统催化循环。

对 Fe→Cu 平台，不应只存“酶名”和“Cu”。应分别记录蛋白骨架、金属添加/置换方式、天然与实际使用的辅因子、配体/配位信息、光或电子来源、缓冲体系和反应表现。C–O/C–N/C–S/C–C 成键类别本身不足以推断其机理。

## 5. 数据应怎样收集

### 5.1 收集反应能力和催化环境，避免被突变记录淹没

建议建立三个关联层级：

| 层级 | 主要记录 | 用途 |
|---|---|---|
| 反应能力 | 反应物/产物、成断键、反应类别、最早公开来源 | 判断是在换底物还是扩展新的反应模式 |
| 催化体系 | 蛋白、金属/辅因子、必要伙伴、条件、实验形式 | 建立可迁移先例及其边界 |
| 实验测量 | 变体、底物、转化率/产率/TTN/选择性、失败或未检出、测量出处 | 支持具体证据与后续模型 |

一个反应测了 100 个突变体，不能算成 100 次反应发现。一个反应拓展了 50 个芳基取代底物，也不等于 50 类新催化能力。新底物、新成键类别、同中间体的新反应分支、新活化方式应分级标注，避免夸大“新反应”的数量。

特别应区分初始活性与进化后的最好表现。只保存最佳突变体，会让一个经过长期优化才成立的反应看起来像可直接迁移的通用能力。没有报道初始活性时标为未知，不从最终产率倒推。

### 5.2 可复用资源及实际缺口

优先复用 EnzEngDB、RetroBioCat 和原始论文/SI，不从零重复录入全部记录。EnzEngDB 当前论文的汇总口径与旧分析仓库文件不同，应按固定版本记录；论文也明确指出数据来源偏向单一实验室，不能把它当成完整领域。[EnzEngDB](https://academic.oup.com/nar/article/54/D1/D564/8373944)

对已取得的 EnzymeEngineeringDB 固定 V6 CSV，文件级核查得到：1342 行、36 个 DOI；cofactor 字段为 heme 1194 行、PLP 117 行、Fe(II) 31 行，记录日期从 2016-11-25 到 2024-09-27。它没有形成 Cu 置换、光驱动 flavin 或更广泛人工金属酶的完整覆盖。**这些数字仅描述该旧文件，不代表整个现行数据库。** 可复查的提交和散列保存在 [data_source_audit.json](/Users/EasyMaker/Documents/AI4C/research/data_source_audit.json)。

因此，增量整理近期金属置换/光金属酶催化，并统一“反应能力—催化体系—条件”的关联，是有实际价值的数据工作。不过数据补全是否足够成为科研贡献，仍取决于覆盖独特性、质量及下游用途。

### 5.3 范围建议

三周第一版可聚焦 **非天然金属酶反应及其非酶催化先例**：用已有 heme 数据作种子，重点补充非血红素金属置换和光金属酶体系。PLP、flavin、硫胺素等列为后续扩展，先建立清晰的覆盖表，而非承诺全部录完。

筛选文献时从综述引用和已有数据库获得初始列表，再回到原论文/SI核对；把研究组、蛋白骨架、反应类型和年份放在覆盖表里。来源多样性优先于重复底物数。

详细字段至少包括：DOI、最早公开日期、页码/图表/条目、底物与产物结构、实际成断键、蛋白与变体、金属与辅因子、添加剂、光照、氧化还原伙伴、缓冲液/pH、温度、溶剂比例、时间、酶形式、结果指标、阴性对照和缺失状态。机理字段附证据等级；不能用 LLM 的推断填补文献未提供的事实。

## 6. 可以形成的研究问题

建议使用工作题目：**Prioritizing new-to-nature biocatalytic reactions from abiotic precedents**，即“利用非酶催化先例，为新的非天然酶反应排优先级”。

具体问题是：**在相同候选库内，反应中心与催化环境的信息，是否比普通 RXNFP 近邻更能优先找出后来被酶催化实现的转化？**

第一版可采用两阶段流程：

- RXNFP、DRFP 或反应中心指纹从非酶催化语料检索一批结构相关的反应。
- 结合种子酶体系与候选的活化方式、金属/配体和环境信息进行重排，输出证据而非“成功概率”。

结构近邻、已知反应模式、机理相近和“截至检索日未找到酶促实现记录”分别展示。不要把几个手工分数相乘后宣称得到了可行性概率。小数据下无需先训练新基础模型；轻量排序可以作为研究原型，但本身不自动构成算法创新。

必要比较包括：随机/热门反应优先、底物结构近邻、净反应指纹近邻、仅人工反应类别/辅因子规则、以及加入具体催化环境的方案。所有方案共享同一候选库、同一已知酶反应种子和相同时间截止。若条件规则已经解释全部收益，贡献属于化学知识组织与实证研究，而非新的深度学习方法。

## 7. 无新增湿实验时，如何验证它对发现有用

### 7.1 历史回溯

选择一个截止时间，只使用该时间前已公开的酶反应和非酶催化候选。系统给候选排优先级，再检查之后公开的非天然酶反应落在什么位置。以反应发现事件为单位，报告前 k 名的已知后来发现覆盖、相对随机/简单基线的富集，以及不同反应模式和来源的表现。

这比“画出的区域看起来合理”更接近研究价值，但历史回溯不是新方法：BridgIT 已用旧版和新版生化数据库验证推荐。因此本项目的差异必须来自非天然催化能力、非酶催化候选来源和催化环境转移问题，而非时间划分本身。[BridgIT](https://pubmed.ncbi.nlm.nih.gov/30910961/)

### 7.2 三个关键限制

**不能用答案来创建全部候选。** 不能只选后来成功的反应及几个明显不相干的对照，再报告高命中率。候选库应从截止日前可获取的非酶文献按预先规则建立，并记录纳入/排除标准。先做广义反应家族匹配筛选可以，但所有方法要共享该筛选。

**未被报道不等于不能发生。** 其他候选是未标注，不是实验失败。历史发现覆盖检验的是能否找回已知后来发现，不是实验成功率，也不直接给出前瞻精确率。热门反应更容易被研究和发表，需要加入文献频率基线，并说明发表选择偏差。

**时间限制要进入所有信息来源。** 预印本可能早于期刊；现代 LLM 和预训练编码器可能见过后来的答案。严格历史测试优先使用不需训练的结构指纹、截止前的语料及可核查版本；当前 LLM 的回溯解释只能作为另列的探索性结果。

另应先审查候选覆盖：有些酶反应开启了传统小分子体系尚未实现的路径，根本不在旧的非酶反应库里。它们是该检索方法无法覆盖的一类创新，应单独报告，不能悄悄排除后只宣称高召回。

## 8. 具体文献案例及其用途

以下案例用于建立提取和评估规则，尚未完成其全部先例链的人工核查，不是项目新预测。

| 案例 | 能说明什么 | 对数据与评估的要求 |
|---|---|---|
| 2016 cytochrome c 催化 C–Si 成键 | 已有 heme 卡宾化学能够扩展到新的成键对象 | 从原文追踪非酶先例，区分初始活性与进化后的表现 |
| 2022 期刊发表的 aziridine→azetidine Stevens 重排 | 酶环境可能改变中间体竞争路径，超出简单复制传统催化反应 | 已有 2021 年预印本；不能以 2022 为严格发现截止；候选库未包含时计入覆盖缺口 |
| 2025 Cu 置换非血红素酶 ene 反应 | 金属身份与活化方式是反应能力的重要信息 | 不能把天然 Fe 酶标签作为实际催化体系 |
| 2025 Cu 置换酶 C–N 偶联 | 金属置换与外部反应伙伴需要联合记录 | 不能把单独的铜元素相似度当作迁移依据 |
| 2026 Ni 置换 PsEFE 的 C–S 偶联 | 配位环境改造、金属置换和光驱动可共同扩展反应能力 | 期刊在线日期为 2026 年；严格时间测试还需核查更早公开版本 |

来源：[C–Si 成键](https://pubmed.ncbi.nlm.nih.gov/27885032/)、[Stevens 重排及公开稿件](https://authors.library.caltech.edu/records/4n9cr-qyw64)、[Cu ene 反应](https://www.nature.com/articles/s41929-025-01350-5)、[Cu C–N 偶联](https://pubmed.ncbi.nlm.nih.gov/40811552/)、[Ni C–S 偶联](https://www.nature.com/articles/s44160-026-01003-w)。

Stevens 案例尤其重要：如果只寻找“已有小分子催化反应的酶化版本”，可能错过蛋白环境改变竞争路径所带来的发现。地图的可用范围因此应明确为“先例引导的候选优先排序”，而非全面发现引擎。

## 9. 三周应交付什么

| 时间 | 工作 | 可检查产物 |
|---|---|---|
| 第 1 周 | 复用数据；明确范围；补录公开金属置换/光金属酶论文；核查若干历史发现的先例链 | 覆盖表、反应能力清单、结构与条件记录、最早公开日期 |
| 第 2 周 | 统一编码；高维近邻检索；轻量重排；按预定义规则运行历史测试 | 共同候选库、各基线排名、错误类型、覆盖缺口 |
| 第 3 周 | 汇总结果；整理少量截至当前未检索到酶促实现的候选；完成地图和短文 | 可浏览地图、历史回溯结果、3–5 张候选证据卡、4–6 页研究报告 |

数量目标应服从核查质量。少量独立发现事件只能支持探索性结论，不能靠增加同一论文中的底物数伪造样本量。计算上以冻结指纹和检索为主，主要时间花在化学数据核对，而非显卡训练。

候选证据卡应回答：拟议反应是什么；对应哪个已知酶催化能力；最接近的非酶先例是什么；为什么两者有可迁移之处；仍有哪些关键差异；现有证据支持到哪一步；最小实验首先需要分辨什么。候选未做实验时，明确标记“待验证”。

## 10. 申请价值与原创性判断

单纯数据库和地图属于有用的基础设施，与 EnzEngDB 及已有酶反应地图高度重叠。若形成跨研究组、条件语义明确的数据资产，并能展示真实历史发现的候选优先级改善，则可成为更有内容的申请项目。若再通过消融说明改善来自某种可泛化的表示或排序方法，方法贡献才更强。若能做少量前瞻实验，才进一步接近新反应发现的证据。

这里不应声称“首次将酶反应放入 RXNFP 空间”“首次利用反应相似性推荐酶”或“首次做历史回溯”。也不能把反应分类区域解释成酶催化可行性区域。更准确的研究陈述是：**检验反应相似性在非酶化学向非天然酶催化迁移中的适用范围，并研究催化环境信息能否改善候选选择。**

对于已有 SynthAudit，结构标准化、来源追溯和报告模块可以复用。项目重心将从检查已有路线转向提出有依据的实验候选。这样既保留工程投入，也更贴近实验背景与反应表示研究的交点。

## 参考来源

1. Kreutter, D., Schwaller, P. & Reymond, J.-L. *Predicting enzymatic reactions with a molecular transformer*. Chemical Science, 2021. [原文](https://pubs.rsc.org/en/content/articlehtml/2021/sc/d1sc02362d)。
2. Schwaller et al. *Mapping the space of chemical reactions using attention-based neural networks*. Nature Machine Intelligence, 2021. [官方代码与说明](https://github.com/rxn4chemistry/rxnfp)。
3. Long et al. *Enzyme Engineering Database (EnzEngDB): a platform for sharing and interpreting sequence–function relationships across protein engineering campaigns*. NAR 54(D1), D564–D571，2026；2025-12 在线发表. [原文](https://academic.oup.com/nar/article/54/D1/D564/8373944)。
4. EnzymeEngineeringDB. [分析代码仓库](https://github.com/fhalab/EnzymeEngineeringDB)。本地核查 V6 固定提交：bae30c9b45cb8a4eab1d6facd9314994f086cf9b。
5. Rahman et al. *EC-BLAST: a tool to automatically search and compare enzyme reactions*. Nature Methods, 2014. [原文](https://www.nature.com/articles/nmeth.2803)。
6. Hadadi et al. *Enzyme annotation for orphan and novel reactions using knowledge of substrate reactive sites*. PNAS, 2019. [原文记录](https://pubmed.ncbi.nlm.nih.gov/30910961/)。
7. *RetroBioCat Database: A Platform for Collaborative Curation and Automated Meta-Analysis of Biocatalysis Data*. ACS Catalysis, 2023. [原文](https://pubs.acs.org/doi/abs/10.1021/acscatal.3c01418)。
8. Paton et al. *Connecting chemical and protein sequence space to predict biocatalytic reactions*. Nature, 2025. [原文](https://www.nature.com/articles/s41586-025-09519-5)。
9. Wang et al. *A virtual platform for automated hybrid organic-enzymatic synthesis planning*. Nature Communications 16, 10929，2025. [原文](https://www.nature.com/articles/s41467-025-65898-3)。
10. Kan et al. *Directed evolution of cytochrome c for carbon-silicon bond formation: Bringing silicon to life*. Science, 2016. [原文记录](https://pubmed.ncbi.nlm.nih.gov/27885032/)。
11. Miller et al. *Biocatalytic One-Carbon Ring Expansion of Aziridines to Azetidines via a Highly Enantioselective [1,2]-Stevens Rearrangement*. JACS, 2022；2021 年已有公开预印本. [原文及稿件](https://authors.library.caltech.edu/records/4n9cr-qyw64)。
12. Mu et al. *Unlocking Lewis acid catalysis in non-haem enzymes for an abiotic ene reaction*. Nature Catalysis, 2025. [原文](https://www.nature.com/articles/s41929-025-01350-5)。
13. Shen et al. *Enantioconvergent benzylic C(sp3)–N coupling with a copper-substituted nonheme enzyme*. Science, 2025. [原文记录](https://pubmed.ncbi.nlm.nih.gov/40811552/)。
14. Wang et al. *Engineering non-haem enzymes for nickel-catalysed C(sp2)–S coupling via ligand-to-metal charge transfer photocatalysis*. Nature Synthesis 5, 835–845，2026. [原文](https://www.nature.com/articles/s44160-026-01003-w)。
