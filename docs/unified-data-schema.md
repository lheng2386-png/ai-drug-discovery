# 统一数据表设计：EGFR target-conditioned candidate table

本项目的统一表采用：

> **一行 = 一个靶点条件 / 口袋 × 一个候选分子**

因此，分子本身的性质会在多个靶点条件下重复出现，例如 QED、ADMET-AI、PoseBusters 分子几何检查；而 PLI、docking、选择性、Pareto 排名等字段是靶点条件相关的，后续逐步填入。

## 当前产出

- 数据表：`data/unified/egfr_known_ligands_unified_v0.1.csv`
- 审计文件：`data/unified/egfr_known_ligands_unified_v0.1.audit.json`
- 构建脚本：`scripts/build_unified_egfr_table.py`

当前版本使用 4 个 EGFR 10 Å 口袋条件和 8 个已知 EGFR 抑制剂 smoke set，得到 32 行。

## 字段分组

### 1. 靶点与口袋条件

- `target_id`
- `target_chembl_id`
- `uniprot_id`
- `target_variant`
- `expected_mutations`
- `pdb_id`
- `protein_chain`
- `structure_path`
- `pocket_id`
- `pocket_path`
- `pocket_radius_angstrom`
- `reference_ligand_resname`

这些字段描述“给模型生成或评价时看到的靶点条件”。后续做未见靶点泛化时，同样按 target condition 增加行。

### 2. 候选分子身份

- `candidate_id`
- `candidate_source`
- `generation_model`
- `generation_run_id`
- `molecule_chembl_id`
- `molecule_pref_name`
- `canonical_smiles`
- `inchikey`

当前 `candidate_source=known_ligand_seed`，后续 TargetDiff 或 DecompDiff 生成分子可使用 `targetdiff_generated`、`decompdiff_generated` 等来源。

### 3. 已知实验活性参考

- `experimental_assay_variant_mutation`
- `experimental_activity_type`
- `experimental_best_value_nm`
- `experimental_median_value_nm`
- `experimental_max_pchembl_value`
- `experimental_measurement_count`
- `known_ligand_source_url`

这些字段来自 ChEMBL 聚合表，只作为已知配体参考，不等价于当前结构口袋下的 docking 或 PLI 预测。

### 4. 分子性质与 ADMET

- `qed_rdkit`
- `molecular_weight_rdkit`
- `clogp_rdkit`
- `tpsa_chembl`
- `hbd_chembl`
- `hba_chembl`
- `rotatable_bonds_chembl`
- `sa_score`
- `toxicity_flag`
- `admet_summary_flag`
- 所有 `admet_ai_*` 字段

`sa_score` 当前预留，后续接入 SA scorer 后填入。`toxicity_flag` 是基于当前 ADMET-AI smoke-test 输出的简单筛查标记，不是实验毒性结论。

### 5. 物理合理性与结构检查

- 所有 `posebusters_*` 字段

当前 PoseBusters 只做小分子层面的核心检查；蛋白–配体复合物级别检查需要后续 docking 或生成 pose 后再运行。

### 6. 靶点相关评价

- `pli_score`
- `pli_model`
- `pli_embedding_pair_id`
- `docking_score_vina_kcal_mol`
- `docking_pose_path`
- `docking_structure_id`
- `docking_validated_redocking`

这些字段是下一阶段重点：先完成共晶配体 redocking，再对候选分子 docking；PLI 分数由 ESM-2/SaProt 与 Uni-Mol 等跨模态模型输出。

### 7. 多目标优化与反馈

- `diversity_cluster_id`
- `diversity_nearest_neighbor_tanimoto`
- `novelty_reference_dataset`
- `novelty_max_train_similarity`
- `pareto_rank`
- `pareto_selected`
- `feedback_label`
- `feedback_weight`

这些字段用于从 generate-then-filter 过渡到反馈引导生成：先做 Pareto reranking，再把 Pareto 优劣转成偏好或奖励信号。

## 设计边界

1. 当前表不是最终训练集，只是第一版实验总线。
2. ADMET 与 PoseBusters smoke-test 是计算预测和格式/几何检查，不能被表述为真实药效或真实毒理。
3. EGFR 四个变体可用于突变敏感性与选择性分析，但不能单独证明未见靶点泛化。
4. 未见靶点泛化必须在 held-out target 或 held-out family 数据划分上验证。

## 重建命令

```bash
conda run -n drug-evaluation python scripts/build_unified_egfr_table.py
```
