# 第一阶段实施清单

## 数据与目录

- [x] 建立本地项目仓库
- [x] 建立 `data/targets/egfr/`
- [x] 下载并核验 EGFR canonical sequence
- [x] 下载并核验首批 EGFR PDB/AlphaFold structures
- [x] 提取首批 EGFR ligand-centred binding pockets
- [x] 建立并审计 `data/ligands/egfr_known_ligands.csv`
- [x] 建立统一数据表及字段字典

## 工具环境

- [x] 配置 RDKit 基础分析环境
- [x] 完成 ESM-2 小样本 smoke test
- [x] 配置 SaProt 35M + Foldseek 并完成 EGFR smoke test
- [x] 配置 Uni-Mol v1 84M 并完成 8 个 EGFR 配体 smoke test
- [x] 固定 TargetDiff 代码/环境并通过 4 个 EGFR 10 Å 输入兼容性检查
- [ ] 在 NVIDIA 云端下载 checkpoint 并完成 TargetDiff 生成 smoke test
- [x] 固定 DecompDiff 代码/环境并通过 EGFR pocket 静态格式检查
- [ ] 构建 EGFR reference-ligand/AlphaSpace 分解输入并完成云端 smoke test
- [x] 配置 Vina/Meeko docking 环境并通过导入检查
- [ ] 完成 EGFR 共晶配体 redocking 验证
- [x] 配置 PoseBusters/ADMET-AI 并完成已知配体 smoke test

## 约定产出

```text
data/
├── targets/
│   └── egfr/
├── ligands/
│   └── egfr_known_ligands.csv
└── pockets/
    └── egfr_pocket.pdb

outputs/
├── protein_embeddings/
└── molecule_embeddings/
```

原始结构、模型权重和生成 embeddings 默认不上传 GitHub；仓库只保存下载脚本、来源清单、轻量元数据和可复现实验配置。

## 第 12 步统一表

- 统一表：`data/unified/egfr_known_ligands_unified_v0.1.csv`
- 审计文件：`data/unified/egfr_known_ligands_unified_v0.1.audit.json`
- 字段字典：`docs/unified-data-schema.md`
- 构建脚本：`scripts/build_unified_egfr_table.py`

当前采用“一个靶点条件/口袋 × 一个候选分子 = 一行”的设计。4 个 EGFR 10 Å 口袋 × 8 个已知 EGFR 抑制剂 smoke set = 32 行。PLI、docking、SA、diversity、novelty 与 Pareto 字段先预留，后续实验逐步填入。
