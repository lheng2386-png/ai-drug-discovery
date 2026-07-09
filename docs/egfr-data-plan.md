# EGFR 数据准备规范

## 范围

第一批靶点条件固定为：

- EGFR WT；
- EGFR L858R；
- EGFR T790M；
- EGFR C797S；
- 有数据时保留常见复合突变，但与单突变分开标记。

## 数据源优先级

1. UniProt：规范序列、功能域和位点编号；
2. RCSB PDB：实验结构、链、配体、突变和实验质量；
3. BindingDB/ChEMBL：活性类型、数值、单位和 assay 元数据；
4. PLINDER/PDBbind/CrossDocked：用于模型输入或基线复现时记录其派生关系。

不从二手图片、博客或无来源的整理表直接复制结构与活性标签。

## 结构纳入规则

- 优先人源 EGFR kinase domain；
- 明确记录 residue numbering 与 canonical sequence 的映射；
- 优先含共晶配体且口袋完整的结构；
- 记录分辨率、缺失残基、替代构象、金属和辅因子；
- 对不同质子化、晶体水和共价配体处理保留配置记录；
- C797 共价抑制剂与非共价抑制剂分层评价。

## 最小清单字段

- `target_id`
- `uniprot_id`
- `variant`
- `sequence_version`
- `pdb_id`
- `chain_id`
- `experimental_method`
- `resolution`
- `ligand_id`
- `ligand_smiles`
- `covalent`
- `binding_site_residues`
- `source_url`
- `retrieved_at`
- `split`
- `notes`

## 泄漏控制

- 若某个已知配体作为生成条件，它不能同时作为该测试样本的新颖性参照之外的答案标签；
- 同一化合物、盐型、近重复结构和同一 scaffold 不跨训练/测试；
- EGFR 变体共享大量序列和口袋结构，因此变体留一不能替代真正的 cold-target 测试；
- unseen-target 与 unseen-family 集合在建模前冻结。

## 第一批产出

1. 经人工核验的 EGFR 结构清单；
2. 每个变体至少一个可运行口袋；若公开结构不足，明确记录缺口；
3. 统一口袋提取配置；
4. 已知配体去重与 scaffold 审计；
5. 一个 TargetDiff 单口袋输入包。

具体 PDB 条目不在此预填，避免未经核验的结构、突变或配体信息进入实验。选取时必须逐条核对权威数据库。
