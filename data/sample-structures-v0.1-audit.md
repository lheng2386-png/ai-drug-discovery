# 最小结构样本 v0.1 审计

审计日期：2026-07-09

## 选择原则

- 固定随机种子：train 20260709、validation 20260710、test 20260711；
- 来自 PLINDER 2024-04/v1 PL50 官方 split；
- train/validation/test 各 2 个；
- 非共价、非辅因子、非寡聚体、非 artifact；
- Lipinski 配体；
- 单配体链、单 interacting protein chain；
- 12–45 个配体重原子；
- 分子量 180–550；
- QED 不低于 0.4；
- 口袋残基数 10–45；
- 6 个样本都位于 `wi.zip` 分片，降低下载成本。

样本清单见 `sample-structures-v0.1.csv`。

## 文件完整性

| system ID | split | FASTA records | receptor PDB atoms | SDF files |
|---|---|---:|---:|---:|
| `3wik__1__1.A__1.B` | train | 1 | 2,810 | 1 |
| `5wim__1__1.A__1.B` | train | 1 | 2,205 | 1 |
| `5wio__1__1.A__1.E` | validation | 1 | 1,167 | 1 |
| `5wip__1__1.A__1.E` | validation | 1 | 1,168 | 1 |
| `5wi0__2__1.B__1.D` | test | 1 | 3,711 | 1 |
| `5wi1__2__1.B__1.E` | test | 1 | 3,712 | 1 |

每个样本均包含：

- `system.cif`；
- `system.pdb`；
- `receptor.cif`；
- `receptor.pdb`；
- `sequences.fasta`；
- `chain_mapping.json`；
- 一个配体 SDF。

部分系统有 `water_mapping.json`，该文件不是所有系统必有，因此第一版模型不得依赖它。

## 初步结论

1. PLINDER 的系统目录结构足以同时提供完整蛋白、复合物和配体三维坐标；
2. FASTA 与 receptor PDB 可作为完整蛋白编码输入；
3. annotation 中的 `ligand_interacting_residues` 可作为 holo-oracle 口袋残基定义；
4. SDF 由 RDKit 生成并包含三维坐标；
5. 已创建项目专用 RDKit 环境，并完成分子 sanitize 与坐标级距离复核。

## 程序化验证结果

验证命令：

```bash
conda run -n drug-align-analysis \
  python scripts/validate_sample_structures.py
```

汇总：

- RDKit sanitize：6/6 通过；
- 配体重原子数与 metadata 一致：6/6；
- 单条蛋白 FASTA：6/6；
- 根据配体坐标重算的 6 Å 口袋非空：6/6；
- SDF 与 metadata 的规范化立体 SMILES 完全一致：5/6。

唯一不一致样本为 `5wi1__2__1.B__1.E`：

```text
SDF:      O=C1OCCCC1=CNc1ccccc1
metadata: O=C1OCCC/C1=C\Nc1ccccc1
```

两者原子数和基本连接一致，但 metadata 含双键立体方向，SDF 解析结果未保留该方向。该样本应标记为 `stereo_mismatch`，不能静默视为完全一致。

重算的 6 Å 口袋残基数分别为 20、24、13、19、21、18。除 `5wio`（重算 13，metadata 16）和 `5wip`（重算 19，metadata 20）外，与 metadata 一致。差异可能来自 PLINDER 口袋定义不等同于简单的 6 Å 重原子阈值，因此主实验必须保留“官方口袋”和“重算 6 Å 口袋”两个版本。

PLINDER 残基标签如 `1.A_36_17` 的含义为：

- `1.A`：源结构链；
- `36`：PDB/结构残基号；
- `17`：结构链内部顺序索引，不是完整 FASTA 的通用索引。

构建模型输入时必须先用结构残基号映射到 PDB 序列，再与完整 FASTA 对齐。不能直接将最后一位用于 ESM-2 residue embedding 索引。

## 下一步

1. 将 `stereo_mismatch` 和 pocket-definition mismatch 写入后续数据质控规则；
2. 建立 metadata manifest v0.1；
3. 再决定是否扩大到 100 个系统；
4. 在结构质控稳定前不提取 ESM-2/Uni-Mol embedding。
