import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = process.cwd();
const english = process.argv.includes('--english');
const schema = JSON.parse(await fs.readFile(path.join(root, english ? 'templates/en/schema.json' : 'templates/schema.json'), 'utf8'));
const translated = english ? JSON.parse(await fs.readFile(path.join(root,'templates/en/workbook_text.json'),'utf8')) : null;
const outDir = path.join(root, english ? 'outputs/bioreaction_atlas_v02' : 'outputs/bioreaction_atlas_v01');
await fs.mkdir(path.join(outDir, 'previews'), {recursive: true});
const wb = Workbook.create();
const col = n => { let s = ''; for (n++; n > 0; n = Math.floor((n-1)/26)) s = String.fromCharCode(65+(n-1)%26)+s; return s; };
const previews = [];
const base = (sheet, range) => {
  sheet.showGridLines = false;
  sheet.getRange(range).format = {font: {name: 'Arial', size: 11, color: '#243746'}, wrapText: true, verticalAlignment: 'center', rowHeight: 32};
  sheet.freezePanes.freezeRows(1);
};
for (const [name, spec] of Object.entries(schema.tables)) {
  const s = wb.worksheets.add(spec.sheet);
  const last = col(spec.fields.length-1);
  base(s, `A1:${last}201`);
  s.tabColor = '#167D8D';
  s.getRange(`A1:${last}1`).values = [spec.fields.map(f=>f.label)];
  s.tables.add(`A1:${last}201`, true, name === 'contexts' ? 'Contexts' : 'Measurements');
  for (let i=0; i<spec.fields.length; i++) {
    const f = spec.fields[i], c = col(i);
    s.getRange(`${c}1:${c}201`).format.columnWidth = ['conditions_raw','source_locator','reaction_smiles'].includes(f.key) ? 38 : 23;
    s.getRange(`${c}1`).format = {fill: f.required ? '#AD6800' : '#254C61', font: {bold: true, color: '#FFFFFF', size: 11}, rowHeight: 44};
    s.getRange(`${c}2:${c}201`).format.fill = f.required ? '#FFFAEB' : '#FFFFFF';
    s.getRange(`${c}2:${c}201`).setNumberFormat(f.kind === 'date' ? 'yyyy-mm-dd' : ['number','integer'].includes(f.kind) ? '0.########' : '@');
    if (f.choices) s.getRange(`${c}2:${c}201`).dataValidation = {rule: {type: 'list', values: f.choices}};
  }
  previews.push([spec.sheet, 'A1:F6', `${name}_start`]);
  previews.push([spec.sheet, name === 'contexts' ? 'G1:M6' : 'G1:L6', `${name}_values`]);
  previews.push([spec.sheet, `${name === 'contexts' ? 'U' : 'M'}1:${last}6`, `${name}_detail`]);
}

const how = wb.worksheets.add(english ? 'Instructions' : '填写说明');
const instructions = translated?.instructions || [
  ['主题', '填写规则'],
  ['模板版本', schema.schema_version],
  ['从哪里开始', '先录反应条件表的前10列（棕色表头），酶催化同时填蛋白骨架。其余条件可先保留在原文摘录，随后拆分。'],
  ['一条体系是什么', '一条反应模式 + 催化体系 + 条件。换金属、光照、溶剂或操作条件时新建体系编号；只换变体或底物通常在实验结果表新增实验。'],
  ['一条测量是什么', '实验结果表一行记录一个指标。同一实验的产率、ee、TTN分别占行，共用实验编号，测量编号各自唯一。'],
  ['发现事件怎么分', '同一项反应能力发现共用发现事件编号。50个底物或100个突变体不算50或100次发现；后续统一反应家族标签。'],
  ['最先记录哪些结果', '优先代表性反应、起始骨架的初始活性、最佳变体、关键阴性对照。第一批不必录完每篇的所有底物和突变体。'],
  ['结构可以后补', '先写主文/SI中的底物和产物编号与页码。不会写SMILES就留空，结构状态选待补结构。无需手工原子映射。'],
  ['百分数与比较符', '85%填数值85、单位%、比较符 =。小于1%填1、%、<。比较符是文本。ee可保留有定义的符号，注明其含义。'],
  ['比值如何填写', '95:5 dr：指标dr，原文结果95:5；暂留空数值，避免Excel把比值当时间。原文结果列已设文本。'],
  ['零与缺失', '0只有原文明确报告时才填。n.d.保留在原文结果并选未检出；没有报告写未报告。文献没有做过的反应不填成失败。'],
  ['金属置换', '分别记录天然金属、实验实际金属/盐、引入方法。不要把天然Fe标签复制成实验金属，也不要猜活性氧化态。'],
  ['时间与证据', '最早公开日期核查预印本与期刊。只知道年份时日期留空、年份写备注。任何数值和机理都应有图表/页码支持。'],
  ['核对状态', '初次整理可全部选待核对。只有逐项核实后再选已核对；已核对体系和结构才能进入默认检索。'],
  ['示例的用途', '填写示例表全部为虚构格式示例，不能用作论文数据或实验先例。导入器只读取反应条件和实验结果两张表。'],
  ['扩展行数', '预留200行及下拉选项。超过200行可以复制末行格式继续填写，导入器读取全部非空行。不要删除或改名表头。'],
  ['第一批目标', '先选5篇跨研究组的关键论文，每篇录1—2条体系和3—6个关键实验。填好后即可用于第一次结构与条件核查。'],
];
base(how, `A1:B${instructions.length}`);
how.getRange(`A1:B${instructions.length}`).values = instructions;
how.getRange('A1:A18').format.columnWidth = 23;
how.getRange('B1:B18').format.columnWidth = 100;
how.getRange(`A2:B${instructions.length}`).format.rowHeight = english ? 65 : 55;
how.getRange('A1:B1').format = {fill:'#254C61',font:{bold:true,color:'#FFFFFF'},rowHeight:34};
previews.push([english ? 'Instructions' : '填写说明', 'A1:B9', 'instructions_1'], [english ? 'Instructions' : '填写说明', `A10:B${instructions.length}`, 'instructions_2']);

const dict = wb.worksheets.add(english ? 'Field dictionary' : '字段字典');
const rows = [english ? ['Table', 'Field label', 'Program key', 'Required', 'Instructions', 'Allowed values'] : ['所在表', '字段名', '程序字段', '必填', '填写说明', '允许选项']];
for (const spec of Object.values(schema.tables)) for (const f of spec.fields)
  rows.push([spec.sheet, f.label, f.key, f.required ? (english ? 'Yes' : '是') : (english ? 'Conditional / optional' : '见说明/可后补'), f.description, f.choices ? (english ? 'Options: ' : '可选：') + f.choices.join(english ? '; ' : '；') : '']);
base(dict, `A1:F${rows.length}`);
dict.getRange(`A1:F${rows.length}`).values = rows;
for (const [c,w] of [['A',16],['B',24],['C',29],['D',19],['E',76],['F',57]]) dict.getRange(`${c}1:${c}${rows.length}`).format.columnWidth = w;
dict.getRange(`A2:F${rows.length}`).format.rowHeight = 60;
dict.getRange('A1:F1').format = {fill:'#254C61',font:{bold:true,color:'#FFFFFF'},rowHeight:34};
dict.tables.add(`A1:F${rows.length}`, true, 'FieldDictionary');
previews.push([english ? 'Field dictionary' : '字段字典', 'A1:F8', 'dictionary']);

const example = wb.worksheets.add(english ? 'Examples' : '填写示例');
const examples = translated?.examples || [
 ['填写场景（全部虚构）','字段','示例值','如何关联'],
 ['体系录入','体系编号 / 发现事件编号','DEMO_C01 / DEMO_DISCOVERY','同一发现事件的多个条件共用发现事件编号。'],
 ['体系录入','DOI或公开链接 / 条件出处','示例来源，非真实论文 / 示例SI p.10','正式数据必须换成真实来源及精确位置。'],
 ['体系录入','核对状态','示例','示例状态始终从检索索引排除。'],
 ['同一实验测产率','测量编号 / 实验编号 / 体系编号','DEMO_M01 / DEMO_A01 / DEMO_C01','yield；数值35；比较符 =；单位 %；检出。'],
 ['同一实验测ee','测量编号 / 实验编号 / 体系编号','DEMO_M02 / DEMO_A01 / DEMO_C01','ee；数值80；比较符 =；单位 %；检出。'],
 ['未检出对照','测量编号 / 实验编号 / 体系编号','DEMO_M03 / DEMO_A02 / DEMO_C02','新建无酶对照体系；数值留空；原文结果 n.d.；未检出。'],
 ['低于检测上限','指标 / 数值 / 比较符 / 单位','yield / 1 / < / %','原文结果 <1%；不能改成0或精确1%。'],
 ['只有化合物编号','底物至产物编号 / 结构状态','1a + 2b → 3ab / 待补结构','SMILES留空，待后续按原文结构补充。'],
 ['非酶先例','催化体系类型 / 蛋白骨架','非酶催化 / 留空','同样记录真实金属、配体、溶剂与来源；不代表酶内可行。'],
];
base(example, 'A1:D10');
example.getRange('A1:D10').values = examples;
for (const [c,w] of [['A',26],['B',39],['C',58],['D',72]]) example.getRange(`${c}1:${c}10`).format.columnWidth=w;
example.getRange('A2:D10').format.rowHeight=58;
example.getRange('A1:D1').format={fill:'#AD6800',font:{bold:true,color:'#FFFFFF'},rowHeight:36};
previews.push([english ? 'Examples' : '填写示例','A1:D10','examples']);

wb.recalculate();
console.log((await wb.inspect({kind:'table',range:english ? 'Measurements!A1:L3' : '实验结果!A1:L3',tableMaxRows:3,tableMaxCols:12,maxChars:2500})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
for (const [sheetName,range,name] of previews) {
 const blob=await wb.render({sheetName,range,scale:1,format:'png'});
 await fs.writeFile(path.join(outDir,'previews',`${name}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(path.join(outDir,english ? 'Nonnatural_Enzyme_Reaction_Collection_EN.xlsx' : '非天然酶反应收集模板.xlsx'));
console.log('Workbook exported.');
