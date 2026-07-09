# 第一阶段实施清单

## 数据与目录

- [x] 建立本地项目仓库
- [x] 建立 `data/targets/egfr/`
- [x] 下载并核验 EGFR canonical sequence
- [x] 下载并核验首批 EGFR PDB/AlphaFold structures
- [x] 提取首批 EGFR ligand-centred binding pockets
- [x] 建立并审计 `data/ligands/egfr_known_ligands.csv`
- [ ] 建立统一数据表及字段字典

## 工具环境

- [x] 配置 RDKit 基础分析环境
- [x] 完成 ESM-2 小样本 smoke test
- [x] 配置 SaProt 35M + Foldseek 并完成 EGFR smoke test
- [x] 配置 Uni-Mol v1 84M 并完成 8 个 EGFR 配体 smoke test
- [x] 固定 TargetDiff 代码/环境并通过 4 个 EGFR 10 Å 输入兼容性检查
- [ ] 在 NVIDIA 云端下载 checkpoint 并完成 TargetDiff 生成 smoke test
- [ ] 配置 DecompDiff
- [ ] 配置 docking 工具
- [ ] 配置 ADMET 评价工具

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
