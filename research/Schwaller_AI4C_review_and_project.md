# Schwaller 研究脉络、AI4C 进展与短期申请项目建议

**选题状态更新：** 后续定向核查发现 Egret（2024）与原建议的“条件敏感性 + 等价表示稳定性”直接重叠，AlignReact（2026）也已结合条件与选择性预测；另补入 Schwaller 团队 2026 年的 Buchwald–Hartwig 域外预测研究。以下项目方案目前应视为待验证的预研候选，不能视为已经确认的原创方向。新增证据与继续条件详见[原创性核查补充](/Users/EasyMaker/Documents/AI4C/research/catalytic_context_novelty_check.md)。

本报告以截至 2026 年 9 月 10 日可核查的论文、预印本、官方代码和本地项目文档为依据。覆盖与化学反应表示、合成规划、催化及酶促反应相关的主要研究路线，不声称穷尽整个 AI4C，也不把论文摘要中的性能声明视为独立复现结果。2026 年的新预印本与正式发表论文分别标明。

研究情境是：具备非天然生物催化实验经验与深度学习基础，研究过天然铁酶经铜置换后的多类 C–X 成键；计划用 2–3 周、约 2000 平台算力券完成一个可用于 PhD 申请的项目，主要依赖公开数据与计算。目标是形成可讨论的科学结果，而非保证发表论文或预测导师的录取偏好。

## 1. 核心判断

**建议锚定“化学反应表示与催化条件下的泛化”，将非天然生物催化作为有辨识度的研究视角和测试场景。暂不把“发现全新酶促反应”设为三周项目的交付目标。**

这个定位保留了实验背景的价值，也与 Schwaller 从反应翻译、反应指纹、原子映射到合成推理的研究轨迹直接相接。它不要求先证明生物催化必须使用 AI，更不要求用少量突变数据训练一个通用酶模型。

优先推荐一个暂定题为 **Catalytic Context Switches: Do Reaction Models Track Changes in Selectivity?** 的小型研究。中文问题是：**相同底物在不同催化条件下产生不同主要产物时，模型是否正确响应了决定反应走向的条件变化？这样的能力能否迁移到未见过的论文、底物骨架或催化体系？**

这不是已经确认无人研究的空白。反应条件预测、条件感知表示、选择性预测都有大量先行工作。可能形成贡献的部分，是严格配对的实验数据、同等输入信息下的比较、跨来源泛化，以及一项经消融验证的表示改进。能否形成方法创新，需要小规模实验和进一步查重决定。

## 2. 生物催化是否是合适的锚点

### 2.1 三个不同的研究问题

| 决策层级 | 实验中实际要回答的问题 | 计算方法能够提供什么 | 当前项目适合程度 |
|---|---|---|---|
| 反应设想 | 哪类非天然转化值得尝试，如何建立催化循环？ | 文献类比、候选路径、竞争反应与条件约束 | 可研究推理能力；难以直接验证新发现 |
| 初始活性 | 该底物组合在这个金属—蛋白环境下是否出现可检测的催化周转？ | 有适用数据时进行优先级排序；辅助解释失败 | 最贴近核心痛点，但数据和验证最缺乏 |
| 活性优化 | 已有初始活性后，哪些突变、底物或条件提高表现？ | 主动学习、回归、少样本优化 | 较易做，但不能冒充解决初始活性问题 |

“推荐酶家族”与“预测一个新反应能否在酶内发生”不是同一任务。如果实验室已经确定平台，重新做一个家族检索器，很可能没有改变真正的决策。把项目改成突变排序，也会把问题移到第三层。

不过，有限的辅因子类别并不意味着反应能力已经确定。金属身份、配位环境、底物进入与定位、活化方式、竞争路径和催化循环再生，都可能改变净反应结果。对铜置换平台而言，酶序列几乎不变而化学行为改变，恰好说明仅凭蛋白家族标签不足以定义其反应能力。这里是化学背景能够帮助建立问题的地方。

公开实验已经展示这种区别。2025 年的 Cu 置换非血红素酶工作实现了非天然 ene 反应；另一项工作实现了铜置换非血红素酶中的对映汇聚 C–N 偶联。它们支持“金属—蛋白环境能够开辟不同化学”的事实，但不能推出某个未测的 C–O/C–N/C–S/C–C 组合必然可行，也不能据此识别任何未公开平台的具体身份。[1](https://www.nature.com/articles/s41929-025-01350-5) [2](https://pubmed.ncbi.nlm.nih.gov/40811552/)

### 2.2 AI 的必要性应该由决策收益证明

一个有用的 AI 项目，需要说明它减少了哪类实验、改善了什么排序、或者发现了什么稳定规律。模型输出漂亮的机理文字，并不能证明上述收益。模型在已知家族内预测底物适配，也不能自动外推到新的反应活化方式。

CATNIP 是值得参考的正面例子：它依托较密集的酶—底物实验测量，研究底物范围与反应发现，而非仅凭蛋白语言模型推断一切。这说明价值可能来自实验空间的组织和适当模型，并不总来自更大的神经网络。它的数据规模和验证条件，也解释了为什么不能直接照搬到少量突变记录上。[3](https://www.nature.com/articles/s41586-025-09519-5)

另一方面，2026 年 7 月的预印本《Rethinking Benchmarks and Models for Enzyme Specificity Prediction》发现，若改用更贴近发现任务的候选排序与未见酶/底物测试，一些已有模型无法超过序列相似性基线。这既支持对实用性的怀疑，也意味着“指出酶模型泛化不好”已经不是足够独特的选题。[4](https://arxiv.org/abs/2607.05084)

### 2.3 de novo enzyme design 与反应类型有关，但不适合当前时间窗

从头设计通常需要指定催化残基、活性位点几何或与目标反应相关的结构约束。反应与过渡态要求会直接影响设计目标，因此它并非与反应类型无关。2025 年的设计研究包括针对特定反应的活性位点构建与实验验证。[5](https://www.nature.com/articles/s41586-025-09747-9) [6](https://www.nature.com/articles/s41586-025-09136-2)

但一个结构看似合理的设计不等于具有初始活性。若无法建立实验反馈，又没有可立即复用的设计与筛选体系，三周内很容易只能交付结构图片和候选序列。对当前申请目的，这条路线的结果风险过高。

### 2.4 与 Schwaller 的契合程度

事实层面，Schwaller 已经参与酶促反应预测；因此生物催化并非与其研究无关。判断层面，更强的契合在于“如何表述、学习和推理化学反应”，而不是“使用蛋白模型”这一表面标签。他于 2022 年加入 EPFL，团队定位覆盖 AI 加速化学发现与合成。[7](https://people.epfl.ch/philippe.schwaller/?lang=en) [8](https://pubs.rsc.org/en/content/articlepdf/2021/sc/d1sc02362d)

没有公开证据能够保证某个题目会使导师眼前一亮。比较可信的申请价值来自：能提出来自实验的具体问题，识别已有工作的边界，设计公平测试，并解释正结果或负结果。领域交叉本身不是贡献；它提供了提出好问题的机会。

## 3. Schwaller 的研究历史：从反应翻译到合成决策

### 3.1 2017–2020：将反应预测变成序列学习与搜索问题

早期《Found in Translation》把化学反应预测处理为序列到序列任务，为随后用注意力模型学习反应奠定基础。Molecular Transformer 则将 Transformer 用于反应预测，并研究模型置信度与错误之间的关系。这条路线的关键是直接从大量反应实例学习，而不是逐条手写反应规则。[9](https://arxiv.org/abs/1711.04810) [10](https://arxiv.org/abs/1811.02633)

此后，单步预测进入多步逆合成搜索：既需要提出前体，也需要评价整条路线。2020 年的超图探索工作使用前向预测等信号进行路线评价。这里已经出现了后来反复讨论的难题：模型内部的“闭环一致”与实验可执行性之间仍有距离。[11](https://pubs.rsc.org/en/content/articlehtml/2020/sc/c9sc05704h)

同期的碳水化合物反应迁移学习说明，预训练模型能够向特定、选择性要求高的数据域适配。对于短期项目，这比“从头训练全领域基础模型”更有参考意义：贡献可以来自精确任务和可验证的迁移收益。[12](https://pmc.ncbi.nlm.nih.gov/articles/PMC7519051/)

### 3.2 2021–2022：反应表示、映射和实验语义

**RXNFP 与 RXNMapper 必须区分。** RXNFP 学习反应指纹，支持反应分类、相似性和化学反应空间可视化；RXNMapper 则利用注意力中的信号建立反应物和产物的原子对应关系。前者的 map 是反应空间，后者的 mapping 是原子对应。两者都不能仅凭注意力解释就宣称恢复了真实机理。[13](https://www.nature.com/articles/s42256-020-00284-w) [14](https://pmc.ncbi.nlm.nih.gov/articles/PMC8026122/)

酶促反应预测工作将酶描述与反应输入结合，检验酶信息是否有助于产物预测。它直接限制了新项目的原创性表述：“给化学模型加入酶信息”已经有先例。所用数据涉及 Reaxys，也不能假设论文出现的数据都可以直接自由重发。[8](https://pubs.rsc.org/en/content/articlepdf/2021/sc/d1sc02362d)

反应操作文本抽取则把文献描述转成实验动作，显示研究对象不只有分子结构，还包括执行过程。与此同时，DRFP 以简单的反应指纹提供了有竞争力的轻量基线。短期项目尤其应该保留这种基线：大型模型必须证明自己在目标问题上的增益。[15](https://www.nature.com/articles/s41467-021-22951-1) [16](https://pubs.rsc.org/en/content/articlehtml/2022/dd/d1dd00006c)

### 3.3 2023–2025：工具使用、评测与面向实验的优化

ChemCrow 将语言模型与化学工具连接，研究复杂任务执行。它体现了“模型协调专用能力”的路线，不等于让文本模型独立掌握所有化学计算。[17](https://www.nature.com/articles/s42256-024-00832-8)

CHORISO 强调反应预测评估中的化学相关维度，超越单一总体准确率；ChemBench 则考察化学问题回答能力及其局限。这些工作表明，严谨的数据集与评估本身符合该研究方向，但前提是揭示过去指标遗漏的重要能力，而不是只列出几个失败案例。[18](https://arxiv.org/abs/2312.09004) [19](https://www.nature.com/articles/s41557-025-01815-x)

高并行反应优化研究进一步连接实际实验决策；面向可合成性的分子优化把合成约束带入生成目标。这些路线共同关注“计算建议如何转成可执行的化学工作”，而非仅提高一个离线预测分数。[20](https://www.nature.com/articles/s41467-025-61803-0) [21](https://pubs.rsc.org/bg/content/articlepdf/2025/sc/d5sc01476j)

### 3.4 2025–2026：策略推理和更开放的合成探索

Synthegy 的预印本提出借助语言模型评价策略、引导合成与机理搜索；Synthelite 探索带有人类约束的逆合成；DynaMate 将代理工具使用扩展到分子动力学任务。它们说明当前方向更强调自然语言、领域工具和结构化化学操作的协作。工具完成一次 MD 也不能独立证明某个催化反应能够发生。[22](https://arxiv.org/abs/2503.08537) [23](https://arxiv.org/abs/2512.16424) [24](https://arxiv.org/abs/2512.10034)

Saturn 的 2024 年预印本于 2026 年正式发表，关注分子生成中的样本效率。不要将预印本年份与期刊年份混用，也不要把这一成果理解为必须依靠昂贵训练才能进入团队研究主线。[25](https://www.nature.com/articles/s42256-026-01200-4)

SynthEx 是 2026 年 8 月预印本所述的合成探索系统；SynthAtlas 是其公开展示资源。系统已经包含策略、构建、批评、改进和分析等环节，并结合结构化图编辑与搜索。其路线覆盖和求解结果是计算层面的评估，不应表述为对应比例的实验合成成功率。官方仓库也指出立体化学和可行性方面的局限；检索时完整代码尚未正式发布。[26](https://arxiv.org/abs/2608.07454) [27](https://github.com/schwallergroup/synthex)

这意味着，为它再加一个通用 critic 不是显然空缺的能力。更合理的切入点，是研究现有策略推理缺少怎样的化学证据、现有表示遗漏哪种信息，以及如何证明某种补充有效。

## 4. 相关 AI4C 的发展地图

| 路线 | 代表工作 | 已经解决或推进的部分 | 仍需区分的边界 |
|---|---|---|---|
| 单步反应预测 | Molecular Transformer、Graph2Edits、EditRetro | 序列生成、反应中心定位、分子图编辑 | 数据集内预测与新化学外推 |
| 多步合成搜索 | Segler、Retro*、SynthEx | 候选分解、搜索效率、策略组织 | 找到路线与路线可实验执行 |
| 反应表示 | RXNFP、DRFP、HiCLR、RxnCLF | 相似性、分类、条件与产率任务 | 结构近邻与催化行为近邻 |
| 化学描述语言 | ReactSeq、ConfSeq、SELFIES | 可解析结构、操作、几何信息 | 表达合法、物理合理与催化可行 |
| 化学语言模型与代理 | ChemCrow、Coscientist、Synthegy | 工具调用、实验流程、规划 | 工具正确性、证据完整性和开放域外推 |
| 反应条件与实验优化 | ORD、条件推荐、贝叶斯优化 | 条件结构化、候选排序、闭环优化 | 已知反应优化与初始活性发现 |
| 酶—反应匹配 | EnzymeMap、CLIPZyme、ReactZyme、EnzymeCAGE | 数据规范化、检索、关系学习 | 自然酶注释与非天然催化能力 |
| 酶设计与进化 | CATNIP、ArM 主动学习、de novo 设计 | 实验空间探索、活性位点设计 | 计算候选与可检测催化周转 |

表中代表性依据分别见：图编辑与搜索 [28](https://www.nature.com/articles/s41467-023-38851-5) [29](https://www.nature.com/articles/s41467-024-50617-1) [30](https://www.nature.com/articles/nature25978) [31](https://proceedings.mlr.press/v119/chen20k.html)；实验自动化与数据 [32](https://www.nature.com/articles/s41586-023-06792-0) [33](https://www.nature.com/articles/s41586-021-03213-y) [34](https://open-reaction-database.org/about)；其他条目在下文展开。

这份地图有意不展开材料生成、量子化学势能面、药物靶点预测等全部 AI4C 分支。它们可能重要，但不会明显改善当前三周项目的选择。

## 5. ReactSeq、ConfSeq 的启发与局限

### 5.1 ReactSeq 的价值不只是“换一种字符串”

ReactSeq 将化学反应组织为分子编辑操作，使模型显式处理结构变化，并用于相关生成和表征任务。它提供了结构化的归纳偏置：模型面对的对象不只是两端 SMILES，而包括转化操作。[35](https://www.nature.com/articles/s42256-025-01032-8)

但图编辑本身早已有研究，包括 Graph2Edits 和 EditRetro。一个新的反应语言必须说明，它与已有编辑表达相比保留了什么信息、减少了什么歧义、带来了什么下游增益。可执行的键编辑序列也不自动等于真实的电子转移、过渡态顺序或催化循环。[28](https://www.nature.com/articles/s41467-023-38851-5) [29](https://www.nature.com/articles/s41467-024-50617-1)

### 5.2 ConfSeq 处理的是三维构象信息

ConfSeq 在结构序列表达中纳入内坐标等几何信息，用于连接三维分子构象与模型学习。它与 ReactSeq 的共同点是让任务关键的信息以适合模型的形式进入输入或输出；两者承担的物理对象不同。[36](https://www.nature.com/articles/s42256-026-01250-8)

一个静态构象表达不等于过渡态模型，更不等于非天然金属酶的反应能垒预测。类似地，SELFIES 的表示约束有助于结构合法性，却不能保证分子稳定或反应成功。[37](https://github.com/the-matter-lab/selfies)

### 5.3 可借鉴的方法论

应先找出任务中不可缺失的信息，再决定是否需要新的语言。对当前问题，候选信息包括金属、配体、蛋白/突变、光照或氧化还原系统、添加剂、介质及其缺失状态。为这些信息设计统一输入是合理的，但 ORD 等体系已经能记录丰富条件；只增加一份 JSON schema 的原创性有限。[34](https://open-reaction-database.org/about)

也不宜把所有专用 Transformer 统称为通用聊天 LLM。表示学习、序列生成、聊天推理是不同方法设置，实验需要明确使用哪一种能力。

## 6. 哪些邻近方向已经拥挤

HiCLR 已经研究层次化的化学反应表示，并在产率任务中通过适配器整合条件。2026 年 8 月的 RxnCLF 预印本采用转化感知图表示和对比学习。2026 年 5 月的 HiRes 预印本则把反应先例检索与条件推荐结合。因此，“反应中心 + 条件 + 对比学习/检索”不能直接作为首创声明。[38](https://pubs.acs.org/doi/10.1021/jacsau.5c00289) [39](https://arxiv.org/abs/2608.06259) [40](https://arxiv.org/abs/2605.21420)

酶方向也已有完整谱系：RetroBioCat 面向生物催化路线设计；IBM 的酶促合成规划工作连接酶反应与规划；EnzymeMap 提供经处理的酶促反应数据；CLIPZyme、ReactZyme 与 EnzymeCAGE 分别推进酶—反应匹配、评测和结构信息利用。单纯将反应编码器与蛋白编码器做双塔对齐，难以构成独立创新。[41](https://pubmed.ncbi.nlm.nih.gov/33604511/) [42](https://www.nature.com/articles/s41467-022-28536-w) [43](https://pmc.ncbi.nlm.nih.gov/articles/PMC10718068/) [44](https://arxiv.org/abs/2402.06748) [45](https://arxiv.org/abs/2408.13659) [46](https://www.nature.com/articles/s41929-026-01478-y)

非天然酶的少数据建模和主动学习同样不是空白。已有工作对非天然酶催化选择性建立数据模型，也有人工金属酶的大规模突变测量与优化研究。这些可以成为基线或数据来源，却不应在申请中描述成刚刚提出的方向。[47](https://pmc.ncbi.nlm.nih.gov/articles/PMC10602048/) [48](https://pmc.ncbi.nlm.nih.gov/articles/PMC10964965/) [49](https://pmc.ncbi.nlm.nih.gov/articles/PMC11273458/)

## 7. SynthAudit 的真实资产与科学缺口

本地项目已经形成较完整的审计工程：结构与反应中心检查、证据接口、来源记录、可控扰动及研究问题文档。其科学边界声明明确区分表示合法性、语料新颖性、证据支持和实验可行性，这是一项重要的方法学基础。

根据当前文档，已报告的评估主要包括 200 条人工构造的反事实样例、提示变体、少量 ReactSeq 示例及接口契约；部分提示测试并未实际调用语言模型，多项研究问题仍标为未运行。**这些是工程验证或测试资产，不能作为已完成的真实化学总体评测。** 本报告是对文档状态的核查，不是重新执行整个测试套件。[50](/Users/EasyMaker/Documents/SynthAudit/docs/TECHNICAL_REPORT.md)

判断如下：问题不在于项目使用了他人的原创系统，科学工作本来就会建立在前人基础上；缺口在于尚未形成一条独立的、由真实数据支持的经验结论。上游已经有批评和改进机制，因此追加更多 checker，未必能改变这一点。

适合复用的模块是结构标准化、原子对应与图编辑记录、来源版本、实验记录追溯和报告生成。新研究应独立命名和界定科学问题，底层复用这些资产即可。没必要为新项目重写完整界面，也没必要一次执行全部旧研究问题。

涉及 SynthAudit 的结果仍遵守其公开声明：它估计表示有效性、语料新颖性与证据支持的合理性，不能建立实验可行性、产率、选择性、安全性或放大能力。[51](/Users/EasyMaker/Documents/SynthAudit/docs/SCIENTIFIC_CLAIMS.md)

## 8. 推荐项目：催化条件切换下的反应表示与预测

### 8.1 一个主问题、两种需要区分的变化

主问题是：**在输入信息相同的前提下，显式组织催化条件是否改善模型对真实产物走向变化的预测，并在跨论文测试中保持这种收益？**

实验需要同时包含两类变化：

- **化学变化**：同一底物组合在实验测得的不同催化条件下，主要产物发生变化。模型应该正确变化。
- **表示变化**：相同化学记录仅改变 SMILES 遍历顺序、组分排列或等价命名。模型应该基本保持不变。

还必须有“条件有变化但主要产物未变”的实验对照，否则一个遇到条件差异就切换答案的模型也会显得聪明。表示扰动用于检查稳定性，不能当作新增独立实验样本。

这套设计将化学敏感性与表示稳定性放在一起评估。它的价值取决于数据质量与公平比较；这不是在未查证的情况下宣称一个新的理论框架。

### 8.2 三周内的具体任务

第一版采用**候选产物排序**，不承担开放式全产物生成。每道题提供底物、完整可获得条件、两个或少量候选产物，要求选择主要产物。候选产品在每个条件下都同样可见；目标标签、产率、论文标题中的结论性文字不得进入输入。

对于同一底物的两条实验记录，分别询问模型，再检查两条是否都正确。未报道的交叉组合不自动作为失败反应。只有实际测量过的配对才用于条件切换的实证结论；同时改变了多项条件的记录标注为复合条件变化，不能声称识别了单一金属的因果效应。

第一阶段优先化学/区域选择性，因为产物连接关系更容易统一核对。对映与非对映选择性可作为扩展，但必须保存绝对构型和具体产物通道，不能只比较 ee 的正负号。

这项任务检验的是已记录条件下的产物区分能力。由于候选集合来自已知结果，它**不能证明**系统能够发现全新酶促反应，不能计算未知反应的实验成功率。它是通往更大问题的一个可证伪组成部分。

### 8.3 为什么保留生物催化子集

主体可以使用较容易获取的有机/金属催化配对；生物催化子集集中体现“序列或家族相近，催化条件与反应行为不同”。它不承担全部统计样本量，也不要求公开未发表数据。

已有的 myoglobin 实验显示，金属/近端配位环境改变可以影响环丙烷化与 Y–H 插入的竞争。这比随机配一个“错误酶”作为负例更接近实际化学，但仍需逐条核对原文与补充信息。[52](https://pubs.acs.org/doi/abs/10.1021/acs.joc.8b00946)

对铜置换平台的经验可以用于辨别模型是否遗漏关键上下文、审查反应配对是否公平、解释可迁移先例的限制。它不需要成为一个训练集，也不需要透露未发表结构。

### 8.4 已找到的公开数据线索

| 线索 | 能提供什么 | 纳入前必须核查什么 |
|---|---|---|
| 2018 myoglobin 金属/配位调节 | 竞争反应的化学选择性改变 | 是否同底物、同测量条件；金属和突变是否共同改变 |
| 2024 Pd 催化二烯杂环化 | 配体调节区域选择性 | 优化表中哪些对照只改配体，哪些同时改温度/前体 |
| 2025 Ni/Co 电催化 C–H 环化 | 不同金属催化体系的化学分流 | 底物匹配与复合条件差异；不能简化为孤立金属效应 |
| 2024 烯烃氯氟化 | 介质组成引起立体选择性变化 | 产物通道和实验条件编码，需要独立的立体化学核查 |
| EnzEngDB | 非天然酶反应、变体、部分选择性记录 | 数据版本、重复、产物构型、实验失败字段语义 |

这些是**数据候选来源，不是已经建成的配对基准**。前三类原始论文分别见 [52](https://pubs.acs.org/doi/abs/10.1021/acs.joc.8b00946) [53](https://www.nature.com/articles/s41467-024-49803-y) [54](https://www.nature.com/articles/s41929-025-01306-9)，氯氟化见 [55](https://www.nature.com/articles/s41557-024-01561-6)。

### 8.5 方法：先比较信息组织，再决定是否训练

建议把输入分为三块：底物及候选产物的结构变化；可观测的催化条件；可观测的实验环境。金属、配体、酶/变体、光照、氧化还原搭档和缺失字段应显式保存。未知金属价态不能凭元素名称补写；从产物反推的机理标签不能伪装为预测前已知特征。

第一版采用冻结编码器、检索和固定提示，不训练新基础模型。比较普通串接输入与分字段输入，必要时用已有反应指纹和条件特征对近邻先例重新排序。只有在足够独立的训练数据出现后，才训练线性模型、小型 MLP 或轻量交互适配器。

如果要做一个“语言”元素，可以写可解析的简短条件记录，但将其定位为实验变量，而不是先命名一门新语言再寻找用途。核心消融是：相同信息、相近 token 预算下，结构化表达能否稳定胜过普通文字或直接拼接？

### 8.6 必须有的基线

| 基线 | 输入与用途 | 解释边界 |
|---|---|---|
| 频率或固定候选 | 建立最基本参照 | 不能只报告单条正确率 |
| Morgan/DRFP 近邻 | 检查结构相似性的能力 | 缺条件版本只作信息消融 |
| 结构 + 条件的简单检索 | 同等信息的轻量强基线 | 防止“更多信息”被误称为“更好架构” |
| 同一语言模型、完整原始条件 | 通用文本基线 | 固定模型版本、提示和温度 |
| 同一模型 + 普通检索 | 排除收益仅来自补充先例 | 与新方法共享语料与检索数量 |
| 分字段表示/上下文重排 | 待验证的方法 | 必须胜过相同输入信息的对照 |

RXNFP 或 HiCLR 若能顺利运行，可补充为已有表示基线；不要为了复现所有大模型而挤掉数据核查时间。缺条件的结构模型无法区分完全相同的底物输入，这属于输入信息上的必然限制，不能包装成一个意外科学发现。

### 8.7 划分、指标和泄漏控制

主划分以论文或实验系列为组。一个底物对应的所有条件、同系列突变、等价 SMILES 和重复记录必须在同一组；反应骨架高度相近的论文还需另做聚类检查。随机拆分只能作为容易设置的对照。

主要指标为**配对两条都正确的比例**，同时报告单条正确率、真实切换对中的正确响应率、同结果条件对的稳定性、等价表示一致性，以及按独立论文分组的结果。置信区间以论文或实验系列重采样；不能把几十个同系列底物当作几十次独立机制验证。

两个候选逐题独立随机选择时，两条都对的概率是 25%；若系统被告知答案必须一一对应且禁止相同，则随机基线变成 50%。因此不要加入这种配对提示，应分别提问再配对评分。候选排列随机化，保证两个产物在每条题目中均可见。

封闭模型的预训练污染无法仅靠论文留出消除。不得声称留出论文就是模型从未见过；报告这一限制，使用不同来源和可检查的开源模型作补充。若有新近公开且时间可核查的文献，可做附加时间分析，但仍应避免过强的无污染声明。

### 8.8 可以形成什么结果

最强的短期结果是：在严格配对的实验记录上，完整条件文本模型出现一种可重复的失败；某种明确的信息组织或检索策略改善了它；改善在跨论文设置中仍存在，并通过等价表示和同结果对照排除简单捷径。

次强结果是：同等信息的简单条件基线已足够，复杂表示没有收益。只要数据和统计可信，这也是有价值的研究结论，应修改假设并解释信息瓶颈，而不是增加代理数量来掩盖负结果。

较弱结果是：只展示二维反应地图、十几个精挑样例，或在随机拆分上取得更高分。它们适合作为演示，不足以单独构成主要科学主张。

## 9. 公开数据可行性核查

### 9.1 EnzEngDB：有用的入口，尚不是现成测试集

论文发表于 Nucleic Acids Research 2026 年数据库专刊。论文汇总口径与代码仓库当前文件口径不同，不能把不同版本的反应数、变体数拼在一起。数据库的主题与非天然酶催化高度相关。[56](https://academic.oup.com/nar/article/54/D1/D564/8373944)

对公开仓库固定版本 V6 文件的本地计数如下。这些是文件统计，不是化学独立样本或已验证切换的数量。

| 字段/统计 | 核查值 | 含义 |
|---|---:|---|
| CSV 数据行 | 1342 | 一行不等于一个独立酶反应 |
| 非空 canonical reaction | 1341 | 其中 640 个不同字符串 |
| 论文 DOI | 36 | 比行数更接近来源多样性 |
| 非空变体氨基酸序列 | 1259 | 不能直接当作不同变体数 |
| 非缺失选择性字段 | 697 | 696 条符合简单数值格式；尚未统一构型含义 |
| 非空 failed_substrates 单元格 | 69 | 仅 3 个不同非缺失字符串，绝非 69 次独立失败实验 |
| 含 warnings / errors 的行 | 249 / 16 | 需要进一步化学核查 |

固定提交为 `bae30c9b45cb8a4eab1d6facd9314994f086cf9b`，原始文件 SHA-256 为 `abe6bd9f0c1dcc3487b6a2a595d427b70c6714b9a2bfd1c195e50b702ffe9245`。可追溯文件见 [57](https://raw.githubusercontent.com/fhalab/EnzymeEngineeringDB/bae30c9b45cb8a4eab1d6facd9314994f086cf9b/data/protein-evolution-database_V6.csv)。

按论文、反应物和去立体化学后的产物连接关系做初筛，确有多变体与选择性符号变化的候选组。但 ee 符号可能涉及不同非对映产物通道，不能将符号反转直接计为催化选择性切换。当前没有据此宣布建成任何真实配对数据集。

仓库 README 声称 MIT，而核查时 LICENSE 文件为空；数据再分发权限尚未核实。研究可以先记录出处、派生统计和提取脚本，在公开打包原始数据前明确许可。数据库记录缺失也不能被转换为“不反应”标签。

### 9.2 一个可按时完成的备用方向

《Systematic engineering of artificial metalloenzymes for new-to-nature reactions》提供同一 streptavidin 平台上 400 个双突变体、五类反应的测量，代码与数据公开。它适合研究跨反应的少样本迁移或负迁移。[48](https://pmc.ncbi.nlm.nih.gov/articles/PMC10964965/) [58](https://github.com/JeschekLab/Systematic-engineering-of-ArMs)

可以问：已测某一反应的突变景观，是否帮助在另一反应中更快找到高活性变体？比较随机、单反应模型、共享模型、简单氨基酸描述符，并以找到高活性变体所需实验数为指标。

这一备用方向数据更整齐，但原论文已经做过机器学习，后续人工金属酶主动学习也很成熟。必须围绕跨反应迁移明确查重，且不能把结果描述为预测了新反应的初始活性。它是确定期限下的备用计算研究，不是当前核心痛点的完整答案。

## 10. 21 天执行计划与退出条件

| 时间 | 工作 | 可检查产物 | 继续/调整依据 |
|---|---|---|---|
| 第 1–2 天 | 逐条核查 3–5 篇原文/SI；建立 10–15 个候选配对；跑最小文本基线 | 数据字典、源定位、20–30 条已核对实验记录或明确缺口 | 数据是否真能配对；任务是否过于简单；是否只有表示错误 |
| 第 3–5 天 | 扩到至少约 30 个配对、争取 8 个以上独立来源；加入同结果对照 | 冻结的开发集、分组方案、来源清单 | 这是计划目标，不是已确认存在的样本量；达不到则缩小结论 |
| 第 6–9 天 | 固定 3–4 个关键基线；等价表示和候选顺序控制 | 第一张完整结果表与错误分类 | 先确认同等信息比较成立 |
| 第 10–13 天 | 一个表示/检索改动；进行必要消融 | 能明确归因的比较结果 | 无增益则保留负结果，不增大项目规模 |
| 第 14–17 天 | 冻结方法；完成留出来源测试；若数据顺利再扩至 60–100 配对 | 论文分组统计、置信区间、化学案例 | 不为追求样本量纳入模糊记录 |
| 第 18–21 天 | 写 4–6 页研究短文、精简仓库与申请材料 | 报告、数据说明、复现实验命令、3 张核心图 | 所有结论有对应证据 |

如果只有两周，第 14 天即停止新方法开发，以已核实数据和结果写成短报告。不要把最后几天用于部署复杂网站。

**48 小时数据门槛很重要。** 如果只有零散成功案例、没有可比实验条件，不能继续声称要做条件切换基准。可以缩为明确标注的案例研究，或者转入上一节的公开矩阵备用方向。若完整条件基线已接近满分，也应改变测试难度或结束该假设，不必强行制造一个“模型缺陷”。

## 11. 算力、产物与申请表达

### 11.1 算力安排

2000 算力券不是确定的人民币预算或 GPU 小时数，尚未核查平台兑换和显卡实例配置。不能仅凭“5060”假设显存容量，也不应承诺能微调某个参数规模模型。

建议前 48 小时只做 CPU 数据处理和小规模推理；基线明确后，约一半额度用于冻结模型特征与重复推理，约两成用于可选轻量训练，其余保留给最终留出测试与失败重跑。平台券是否覆盖外部语言模型 API 需要另查，因此默认核心实验不依赖收费 API。

这项研究的主要成本是核查文献、统一产物和条件、排除泄漏，而非训练。无需从头预训练化学或蛋白基础模型，也不需要开展全体系 QM/MM。

### 11.2 三张应该出现在申请材料中的图

1. 一个真实实验配对：相同底物、条件变化、不同产物，标明完整来源和模型输出。
2. 按论文留出的结果比较：包括同等信息基线、置信区间和主要消融。
3. 两个能力的关系：对真实化学变化的正确响应，与对等价表示变化的稳定性；按有机/生物催化子域分别报告。

反应空间地图可以辅助解释，但不能替代上述结果。所有例子应从系统性测试中抽取，明确它们是否代表常见错误。

### 11.3 如何写进申请

尚未完成时，可以使用这种研究动机：

> My experience with metal-substituted enzymes made me question when reaction similarity supports transfer of catalytic behavior. I am studying whether reaction models respond correctly to experimentally observed changes in catalytic context, using matched outcomes and evaluation across independent literature sources.

完成后再把实际样本量、基线、结果与限制填入，不提前写成 “developed a model that discovers new-to-nature reactions”。如果最终只是一个高质量基准，也应据实突出实验问题形式化、数据核查和重要失败模式，而非虚构算法突破。

可以把长期 PhD 问题定义为：如何将反应变化、催化环境和证据不确定性联合表示，用于选择值得实验验证的反应假设？短期项目检验其中一个必要能力，后续再加入少量前瞻实验，才逐步接近未知反应发现。

## 12. 推荐的阅读顺序

先重读 RXNFP、Molecular Transformer 和酶促反应 Transformer，分清表示、预测和酶信息的既有作用。随后读 ReactSeq 与 HiCLR，重点看输入、训练目标和消融，而不只看漂亮的反应地图。再读 SynthEx 的方法及限制，理解系统已有的 critic 和结构校正范围。

对酶方向，优先读 CATNIP 和 2026 年的酶特异性基准预印本，理解密集实验数据与发现相关测试的差别。最后选择 3–5 篇催化分流原始实验论文核查 SI；这些原始记录将比继续泛读十篇综述更直接决定项目能否成立。

## 参考来源

所有网页来源检索截止日为 2026-09-10。原始论文、官方代码与数据优先；以下年份为期刊年份或明确标出的预印本年份。对原始实验论文的来源确认，不等于已经逐条完成补充信息的数据提取。

1. Mu et al. *Unlocking Lewis acid catalysis in non-haem enzymes for an abiotic ene reaction*. Nature Catalysis, 2025. https://www.nature.com/articles/s41929-025-01350-5
2. Shen et al. *Enantioconvergent benzylic C(sp3)–N coupling with a copper-substituted nonheme enzyme*. Science, 2025. DOI: 10.1126/science.adt5986. https://pubmed.ncbi.nlm.nih.gov/40811552/
3. Paton et al. *Connecting chemical and protein sequence space to predict biocatalytic reactions* (CATNIP). Nature, 2025. https://www.nature.com/articles/s41586-025-09519-5
4. Mahood, Komorníková, Pluskal and Chatterjee. *Rethinking Benchmarks and Models for Enzyme Specificity Prediction*. arXiv 预印本, 2026-07. https://arxiv.org/abs/2607.05084
5. Braun et al. *Computational enzyme design by catalytic motif scaffolding* (RiffDiff). Nature；2025-12 在线发表，2026 年卷期. https://www.nature.com/articles/s41586-025-09747-9
6. *Complete computational design of high-efficiency Kemp elimination enzymes*. Nature, 2025. https://www.nature.com/articles/s41586-025-09136-2
7. EPFL. Philippe Schwaller 官方个人页. https://people.epfl.ch/philippe.schwaller/?lang=en
8. Kreutter, Schwaller and Reymond. *Predicting enzymatic reactions with a molecular transformer*. Chemical Science, 2021. https://pubs.rsc.org/en/content/articlepdf/2021/sc/d1sc02362d
9. Schwaller et al. *Found in Translation: Learning Robust Neural Machine Translation Models for Chemical Reaction Prediction*. 2017 预印本；Chemical Science, 2018. https://arxiv.org/abs/1711.04810
10. Schwaller et al. *Molecular Transformer: A Model for Uncertainty-Calibrated Chemical Reaction Prediction*. ACS Central Science, 2019. https://arxiv.org/abs/1811.02633
11. Schwaller et al. *Predicting retrosynthetic pathways using transformer-based models and a hyper-graph exploration strategy*. Chemical Science, 2020. https://pubs.rsc.org/en/content/articlehtml/2020/sc/c9sc05704h
12. *Predicting the regioselectivity and stereoselectivity of carbohydrate reactions using a transformer model*. 2020. https://pmc.ncbi.nlm.nih.gov/articles/PMC7519051/
13. Schwaller et al. *Mapping the space of chemical reactions using attention-based neural networks*. Nature Machine Intelligence, 2021. https://www.nature.com/articles/s42256-020-00284-w
14. Schwaller et al. *Extraction of organic chemistry grammar from unsupervised learning of chemical reactions*. Science Advances, 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8026122/
15. Vaucher et al. *Inferring experimental procedures from text-based representations of chemical reactions*. Nature Communications, 2021. https://www.nature.com/articles/s41467-021-22951-1
16. Probst, Schwaller and Reymond. *Reaction classification and yield prediction using the differential reaction fingerprint DRFP*. Digital Discovery, 2022. https://pubs.rsc.org/en/content/articlehtml/2022/dd/d1dd00006c
17. Bran et al. *Augmenting large language models with chemistry tools*. Nature Machine Intelligence, 2024. https://www.nature.com/articles/s42256-024-00832-8
18. Sabanza Gil et al. *Holistic chemical evaluation reveals pitfalls in reaction prediction models*. 2023 预印本. https://arxiv.org/abs/2312.09004
19. Mirza et al. *A framework for evaluating the chemical knowledge and reasoning abilities of large language models against the expertise of chemists* (ChemBench). Nature Chemistry, 2025. https://www.nature.com/articles/s41557-025-01815-x
20. 高并行化学反应优化原始研究. Nature Communications, 2025. https://www.nature.com/articles/s41467-025-61803-0
21. 可合成性引导分子优化原始研究. Chemical Science, 2025. DOI: 10.1039/D5SC01476J. https://pubs.rsc.org/bg/content/articlepdf/2025/sc/d5sc01476j
22. Synthegy 原始研究. arXiv, 2025；后发表于 Matter, 2026, DOI: 10.1016/j.matt.2026.102812. https://arxiv.org/abs/2503.08537
23. Synthelite 原始预印本. 2025-12. https://arxiv.org/abs/2512.16424
24. DynaMate 原始预印本. 2025-12. https://arxiv.org/abs/2512.10034
25. Saturn 原始研究. 2024 预印本；Nature Machine Intelligence, 2026. https://www.nature.com/articles/s42256-026-01200-4
26. SynthEx 原始预印本. 2026-08. https://arxiv.org/abs/2608.07454
27. Schwaller group. SynthEx 官方仓库及限制说明. https://github.com/schwallergroup/synthex；展示资源 https://synthatlas.epfl.ch/
28. Graph2Edits 原始研究. Nature Communications, 2023. https://www.nature.com/articles/s41467-023-38851-5
29. EditRetro 原始研究. Nature Communications, 2024. https://www.nature.com/articles/s41467-024-50617-1
30. Segler et al. *Planning chemical syntheses with deep neural networks and symbolic AI*. Nature, 2018. https://www.nature.com/articles/nature25978
31. Chen et al. Retro\*: Learning Retrosynthetic Planning with Neural Guided A\* Search. ICML, 2020. https://proceedings.mlr.press/v119/chen20k.html
32. Boiko et al. *Autonomous chemical research with large language models*. Nature, 2023. https://www.nature.com/articles/s41586-023-06792-0
33. Shields et al. *Bayesian reaction optimization as a tool for chemical synthesis*. Nature, 2021. https://www.nature.com/articles/s41586-021-03213-y
34. Open Reaction Database. 官方说明与数据模型. https://open-reaction-database.org/about
35. Xiong et al. *Bridging chemistry and artificial intelligence by a reaction description language*. Nature Machine Intelligence, 2025. https://www.nature.com/articles/s42256-025-01032-8；代码 https://github.com/jiachengxiong/ReactSeq
36. Xiong et al. *Bridging three-dimensional molecular structures and artificial intelligence with a conformation description language*. Nature Machine Intelligence, 2026. https://www.nature.com/articles/s42256-026-01250-8；代码 https://github.com/jiachengxiong/ConfSeq
37. SELFIES 官方代码与设计说明. https://github.com/the-matter-lab/selfies
38. Wu et al. *HiCLR: Knowledge-Induced Hierarchical Contrastive Learning with Retrosynthesis Prediction Yields a Reaction Foundation Model*. JACS Au, 2025. https://pubs.acs.org/doi/10.1021/jacsau.5c00289
39. Zheng et al. *RxnCLF: Contrastive Transformation-Aware Reaction Foundation Model for Improved Reactivity Prediction*. arXiv 预印本, 2026-08. https://arxiv.org/abs/2608.06259
40. Sathyanarayana et al. *HiRes: Inspectable Precedent Memory for Reaction Condition Recommendation*. arXiv 预印本, 2026-05. https://arxiv.org/abs/2605.21420
41. RetroBioCat 原始研究. Nature Catalysis, 2021. DOI: 10.1038/s41929-020-00556-z. https://pubmed.ncbi.nlm.nih.gov/33604511/
42. *Biocatalysed synthesis planning using data-driven learning*. Nature Communications, 2022. https://www.nature.com/articles/s41467-022-28536-w
43. EnzymeMap 原始研究. 2023. https://pmc.ncbi.nlm.nih.gov/articles/PMC10718068/；代码 https://github.com/hesther/enzymemap
44. Mikhael et al. *CLIPZyme: Reaction-Conditioned Virtual Screening of Enzymes*. 2024 预印本. https://arxiv.org/abs/2402.06748
45. *ReactZyme: A Benchmark for Enzyme-Reaction Prediction*. NeurIPS Datasets and Benchmarks, 2024. https://arxiv.org/abs/2408.13659
46. EnzymeCAGE 原始研究. Nature Catalysis, 2026. https://www.nature.com/articles/s41929-026-01478-y
47. Clements et al. 非天然酶催化选择性建模原始研究. JACS, 2023. DOI: 10.1021/jacs.3c03639. https://pmc.ncbi.nlm.nih.gov/articles/PMC10602048/
48. Vornholt et al. *Systematic engineering of artificial metalloenzymes for new-to-nature reactions*. Science Advances, 2021. DOI: 10.1126/sciadv.abe4208. https://pmc.ncbi.nlm.nih.gov/articles/PMC10964965/
49. 人工金属酶机器学习优化原始研究. ACS Central Science, 2024. DOI: 10.1021/acscentsci.4c00258. https://pmc.ncbi.nlm.nih.gov/articles/PMC11273458/
50. SynthAudit 本地文档：README.md、docs/TECHNICAL_REPORT.md、docs/RESEARCH_QUESTIONS.md、docs/CURRENT_STATUS.md。核查路径 `/Users/EasyMaker/Documents/SynthAudit`；非公开项目来源。
51. SynthAudit. docs/SCIENTIFIC_CLAIMS.md。核查路径 `/Users/EasyMaker/Documents/SynthAudit/docs/SCIENTIFIC_CLAIMS.md`；非公开项目来源。
52. *Chemoselective Cyclopropanation over Carbene Y–H Insertion Catalyzed by an Engineered Carbene Transferase*. JOC, 2018. https://pubs.acs.org/doi/abs/10.1021/acs.joc.8b00946
53. *Ligand control of regioselectivity in palladium-catalyzed heteroannulation reactions of 1,3-Dienes*. Nature Communications, 2024. https://www.nature.com/articles/s41467-024-49803-y
54. von Münchow et al. *Enantioselective C–H annulations enabled by either nickel- or cobalt-electrocatalysed C–H activation for catalyst-controlled chemodivergence*. Nature Catalysis, 2025. https://www.nature.com/articles/s41929-025-01306-9
55. *Diastereodivergent nucleophile–nucleophile alkene chlorofluorination*. Nature Chemistry, 2024. https://www.nature.com/articles/s41557-024-01561-6
56. EnzEngDB 数据库论文. Nucleic Acids Research 54(D1), D564, 2026. https://academic.oup.com/nar/article/54/D1/D564/8373944
57. EnzymeEngineeringDB 官方数据仓库，固定提交 bae30c9b45cb8a4eab1d6facd9314994f086cf9b. https://github.com/fhalab/EnzymeEngineeringDB/tree/bae30c9b45cb8a4eab1d6facd9314994f086cf9b
58. JeschekLab. *Systematic-engineering-of-ArMs* 官方代码和数据. https://github.com/JeschekLab/Systematic-engineering-of-ArMs；Zenodo https://zenodo.org/records/5084377
