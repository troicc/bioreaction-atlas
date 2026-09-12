"""One authoritative field dictionary for Excel, CSV and validation."""

VERSION = "0.1.0"


def f(key, label, description, required=False, choices=None, kind="text"):
    return dict(key=key, label=label, description=description,
                required=required, choices=choices, kind=kind)


CONTEXTS = [
    f("context_id", "体系编号", "自定且唯一，如 MU2025_ENE_C01。改变反应模式、金属或条件时新增体系。", True),
    f("discovery_id", "发现事件编号", "同一项反应能力发现共用编号；不要按突变体或底物计数。如 MU2025_ENE。", True),
    f("source", "DOI或公开链接", "优先原论文 DOI；预印本可用永久链接。", True),
    f("source_locator", "条件出处", "主文/SI页码、图表编号、实验条目；例如 SI p.12 General procedure A。", True),
    f("reaction_name", "反应名称", "使用作者名称；例如 abiotic ene reaction。", True),
    f("catalysis_mode", "催化体系类型", "按该条实验实际使用的催化体系填写。", True, ["酶催化", "非酶催化", "无催化剂对照"]),
    f("scaffold", "蛋白骨架", "实际骨架名；非酶记录可空，酶未明示填 未报告。变体放实验表。"),
    f("metal_cofactor", "实际金属及辅因子", "以实验为准。如 Cu(II)；仅知加铜盐时保留盐名，不推测活性价态。", True),
    f("conditions_raw", "原文条件摘录", "可先整体记录缓冲液、pH、温度、时间、浓度、添加剂及用量；标清单位。", True),
    f("record_status", "核对状态", "待核对可先录入；已核对表示结构、来源、条件已逐项核实。示例不进入检索。", True, ["待核对", "已核对", "示例"]),
    f("paper_title", "论文标题", "按原文录入。"),
    f("lab", "研究组", "便于覆盖统计，可填 PI 姓名/单位。"),
    f("first_public_date", "最早公开日期", "YYYY-MM-DD，取预印本/期刊中最早已查证的公开日期。只有年份时留空，备注年份。", kind="date"),
    f("date_evidence", "日期核查来源", "支持最早日期的链接；未排查预印本时不要当成严格历史划分依据。"),
    f("bond_classes", "成键类别", "多个类别用分号分隔；C-C/C-N/C-O/C-S/C-Si/其他。不能代替反应机理。"),
    f("native_metal_cofactor", "天然金属及辅因子", "天然 Fe 与实验 Cu 分开。未知留空。"),
    f("metal_installation", "金属引入方式", "加盐置换/引入配合物/重构等，原文怎么说就怎么写。"),
    f("enzyme_form", "酶形式", "纯化酶/裂解液/全细胞等。"),
    f("buffer_ph", "缓冲液与pH", "缓冲液名称、浓度、pH；未报告留空。"),
    f("solvent", "溶剂及比例", "水/共溶剂，注明 v/v 等。"),
    f("temperature_c", "温度(°C)", "单一数值；室温/范围保留在原文条件，不猜数值。", kind="number"),
    f("time_h", "时间(h)", "换算为小时；原始值保留在条件摘录。", kind="number"),
    f("partners_light", "添加剂及光电条件", "配体、电子供体、氧化剂/还原剂、光波长/功率、气氛及用量。"),
    f("loading", "底物及催化剂用量", "底物浓度、酶/金属用量、当量，必须带单位。"),
    f("mechanism", "活化方式或中间体", "可留空；有内容时必须说明证据类型与出处。"),
    f("mechanism_evidence", "机理证据类型", "把实验证据、作者提议、项目推测分开。", choices=["实验支持", "作者提出", "项目假设", "未说明"]),
    f("mechanism_locator", "机理出处", "机理研究具体图表、页码或链接；项目假设说明理由。"),
    f("notes", "备注", "别名、年份、不确定项、来源版本或范围说明。"),
]

EXPERIMENTS = [
    f("measurement_id", "测量编号", "每行唯一，如 MU2025_ENE_A01_YIELD。", True),
    f("assay_id", "实验编号", "同一实验多个指标共用；换底物、变体、重复实验时新增编号。", True),
    f("context_id", "体系编号", "必须对应反应条件表的一条体系。", True),
    f("source_locator", "结果出处", "SI页码/表格/行号/化合物编号，需能定位这个数值。", True),
    f("compound_ids", "底物至产物编号", "如 1a + 2b → 3ab；未检出时标记目标产物编号，不当作已生成。", True),
    f("stage", "实验阶段", "起始骨架、筛选或优化后的结果要分开。", True, ["初始活性", "筛选中间体", "进化后结果", "底物拓展", "对照", "未说明"]),
    f("outcome", "产物检出状态", "未检出只针对本实验和该产物；没报道实验不是阴性。", True, ["检出", "未检出", "未报告", "不明确"]),
    f("metric", "指标", "一行一个指标；产率和 ee 写两行并共用实验编号。", True, ["yield", "conversion", "ee", "dr", "TTN", "relative_activity", "product_detected", "other"]),
    f("value", "数值", "百分数填 85 表示 85%；<1 填数值1、比较符<。未知留空，0必须来自报告。", kind="number"),
    f("qualifier", "比较符", "数值存在时必填。约数选 ~；不要把 <1 当成精确 1。", choices=["=", "<", "<=", ">", ">=", "~"]),
    f("unit", "单位", "数值存在时必填。yield/conversion/ee 用 %；TTN用 turnovers。", choices=["%", "turnovers", "ratio", "boolean", "other"]),
    f("raw_result", "原文结果", "保留原始表示，如 >99% ee、95:5 dr、n.d.。数值为空时必填。"),
    f("variant", "酶变体", "原文名称及突变；未报告可写 未报告。非酶或无酶对照可空。"),
    f("reaction_smiles", "反应SMILES", "反应物>试剂>产物 或 反应物>>产物；保留立体信息，不要求原子映射。可后补。"),
    f("structure_status", "结构状态", "只有已核对结构才参与默认检索。未知产物不得补猜测结构。", choices=["待补结构", "待核对", "已核对"]),
    f("product_role", "产物角色", "未检出或对照的 SMILES 可描述测试目标，需标为测试目标。", choices=["观察产物", "测试目标", "未说明"]),
    f("measurement_method", "测定方法", "分离产率/GC/HPLC/NMR；ee的手性方法；标准和误差来源。"),
    f("replicates", "重复次数", "原文明确才填。独立重复原始数值可使用不同实验编号。", kind="integer"),
    f("uncertainty_raw", "误差及说明", "如 mean ± SD, n=3；不把 SD 当 SEM。"),
    f("sequence_accession", "序列或数据库编号", "UniProt/PDB/GenBank 等；可先留空。"),
    f("notes", "备注", "产物命名、检测限、控制类型、结构补充来源等。"),
]

TABLES = {"contexts": {"sheet": "反应条件", "fields": CONTEXTS},
          "experiments": {"sheet": "实验结果", "fields": EXPERIMENTS}}


def metadata():
    return {"schema_version": VERSION, "tables": TABLES}
