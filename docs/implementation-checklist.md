# 第一阶段实施清单

## 数据与目录

- [x] 建立本地项目仓库
- [ ] 建立 `data/targets/egfr/`
- [ ] 下载并核验 EGFR canonical sequence
- [ ] 下载并核验 EGFR PDB/AlphaFold structures
- [ ] 提取 EGFR binding pocket
- [ ] 建立 `data/ligands/egfr_known_ligands.csv`
- [ ] 建立统一数据表及字段字典

## 工具环境

- [x] 配置 RDKit 基础分析环境
- [x] 完成 ESM-2 小样本 smoke test
- [ ] 配置 SaProt
- [ ] 配置 Uni-Mol
- [ ] 配置 TargetDiff
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
