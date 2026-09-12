# 催化条件切换项目的原创性核查

检索截至 2026 年 9 月 10 日。结论：广义的“反应模型能否响应催化条件变化”已有直接先行研究，不能作为新问题申报。“真实实验配对下的主要产物切换”可能提供更聚焦的评估，但目前尚未确认其独立原创性。项目应先进行小规模预研，暂缓大规模标注与新模型开发。

## 最接近的先行研究

| 工作 | 已经研究的内容 | 对候选项目的影响 |
|---|---|---|
| Reid & Sigman，Nature 2019 | 将不对称催化的定量选择性信息迁移到新的反应组分 | “催化经验迁移”和“选择性泛化”不是新概念 |
| Egret，Research 2024 | 针对相同反应物和产物、不同条件的产率变化学习表示；同时处理等价 SMILES 稳定性 | 与原方案提出的“条件敏感 + 表示稳定”直接重叠，尽管预测目标不同 |
| HiCLR，JACS Au 2025 | 层次化反应表示，并在产率预测中整合条件信息 | “反应中心表示加条件适配器”不能直接声称方法创新 |
| AlignReact，Journal of Cheminformatics 2026 | 原子对应、反应中心与条件适配；评估区域/对映选择性及部分域外划分 | 改成选择性目标或增加域外划分，也不足以自动建立新意 |
| Neves et al.，Nature Computational Science 2026 | Schwaller 共同指导的 Buchwald–Hartwig 域外反应预测、条件推荐与实验验证 | 与导师契合，但不能宣称其研究缺少条件与泛化问题 |

来源分别见 [Reid & Sigman](https://www.nature.com/articles/s41586-019-1384-z)、[Egret](https://pmc.ncbi.nlm.nih.gov/articles/PMC10777739/)、[HiCLR](https://pubs.acs.org/doi/10.1021/jacsau.5c00289)、[AlignReact](https://link.springer.com/article/10.1186/s13321-026-01201-w)、[Buchwald–Hartwig 域外预测](https://www.nature.com/articles/s43588-026-01017-6)。

Egret 使用的相同反应分组共有 11,831 组、84,125 条记录，其主要目标是产率预测。因此它并不等同于跨多类化学分流的产物配对测试；但其训练动机与原方案重叠程度很高，必须列入最近邻工作。不能靠把“产率”换成“产物”就默认获得研究贡献。[Egret](https://pmc.ncbi.nlm.nih.gov/articles/PMC10777739/)

AlignReact 的选择性评估也需要细读：区域选择性数据采用计算能垒；对映选择性任务采用磷酸催化硫醇加成数据，并包含底物/催化剂的域外测试。它不是已证实覆盖所有真实产物切换的通用评测，但足以排除“首次联合反应中心、条件和选择性”的表述。[AlignReact 方法与评估](https://link.springer.com/article/10.1186/s13321-026-01201-w)

Schwaller 团队 2026 年的工作使用产率阈值定义二分类结果，研究未见底物上的预测，仍限于训练所覆盖的试剂空间。这与主要产物分流任务不同；它说明当前研究正在认真处理条件决策及泛化，而非只会预测反应模板。[Buchwald–Hartwig 域外预测](https://www.nature.com/articles/s43588-026-01017-6)

## 当前可以与不可以主张的内容

可以主张的事实是：现有相关方法已经研究条件、选择性、表示稳定性及域外泛化。当前定向检索尚未核实一个与“跨来源、真实主要产物切换、同结果对照、同等信息模型比较”完全相同的基准。后一句只表述检索状态，不构成“无人做过”的证据。

以下表述不成立：首次让 AI 理解反应条件；首次发现同底物可有不同产物；首次把催化剂加入反应模型；首次联合条件敏感性与等价表示稳定性；只靠新增数据集或一种划分就证明了模型的化学推理能力。

“真实配对”可能减少底物差异带来的混淆，“配对两条均正确”可能揭示总体准确率遗漏的错误。但是这只是评估设计的价值。若没有可重复的新发现、独特且可靠的数据资产或经验证的方法收益，研究贡献仍然有限。几十条手选难题最多支撑初步案例分析。

## 值得进一步检验的科学假设

更聚焦的候选假设是：**模型能识别常见催化条件，却不能在未见的底物—催化体系组合中迁移决定产物分流的条件效应；这种不足可能来自训练数据覆盖，也可能来自表示或信息组织。**

它仍然不是已经确认的新问题。它的优势是可以把原因分开验证，而不是把任何预测失败都解释成“不懂化学”。

1. 缺信息：输入未记录关键催化剂、介质或操作。先补齐输入；这属于数据问题。
2. 缺先例：完整条件模型失败，补充恰当类比后成功。支持先例检索问题，不支持编码器必然有缺陷。
3. 错误组织或迁移：同一模型拿到相同完整信息及相同先例，在一种表示下失败、另一种表示下稳定改善。才有条件讨论信息组织的贡献。
4. 任务/数据含混：记录不匹配、产物标签不唯一、条件同时改变多个因素。应修订任务，不能算作模型失败。

方法研究可以考虑学习同一底物在两个条件下的选择性差值，再测试这种差异能否迁移到其他底物；必须比较直接预测后作差、近邻迁移和现有条件模型。差值学习本身也不是新算法，只有特定化学问题上的新证据才能支持贡献。

## 三天预研的判断门槛

选 10–20 个经过原文/SI 核实的实验配对，覆盖数个独立来源，同时加入同结果条件对照。该规模用于查错和判断可行性，不能支持全领域结论。模型分别接收完整条件、完整条件加相同先例、以及相同信息的结构化版本；可运行时加入已有条件感知模型，但需要正确适配其输出任务。

若完整条件基线已经解决任务，不建议继续扩充一个容易的基准。若错误主要来自缺失条件或标签问题，先修数据。若完整信息下仍有稳定的跨来源失败，再扩大样本、核对邻近研究，并决定研究问题应落在数据覆盖、先例迁移还是表示方法上。

特别不能将 Egret 的现成产率输出直接与候选产物分类准确率对比。需要适配共同任务、设置同等信息输入，并将这种适配成本纳入三周预算。

对于 PhD 申请，小型但可靠的研究能够证明科研判断力；这与独立论文级创新是不同门槛。当前方案值得投入几天预研，但尚不足以承诺整个三周都围绕它展开。

## 来源

1. Reid, J. P. & Sigman, M. S. *Holistic prediction of enantioselectivity in asymmetric catalysis*. Nature 571, 343–348 (2019). [原文](https://www.nature.com/articles/s41586-019-1384-z)。
2. Yin, X. et al. *Enhancing Generic Reaction Yield Prediction through Reaction Condition-Based Contrastive Learning*. Research 7, 0292 (2024). [原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10777739/)，DOI 10.34133/research.0292。
3. Wu, J. et al. *HiCLR: Knowledge-Induced Hierarchical Contrastive Learning with Retrosynthesis Prediction Yields a Reaction Foundation Model*. JACS Au (2025). [原文](https://pubs.acs.org/doi/10.1021/jacsau.5c00289)。
4. Zeng, K. et al. *A general-purpose framework for chemical reaction representation with atomic correspondence and flexible condition adaptation*. Journal of Cheminformatics 18, 96 (2026). [原文](https://link.springer.com/article/10.1186/s13321-026-01201-w)。
5. Neves, P. et al. *Robust out-of-distribution prediction of Buchwald–Hartwig reactions*. Nature Computational Science，2026-08-10. [原文](https://www.nature.com/articles/s43588-026-01017-6)。
