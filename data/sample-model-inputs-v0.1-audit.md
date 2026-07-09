# 模型输入 v0.1 审计

审计日期：2026-07-09

## 产出

`data/processed/sample-model-inputs-v0.1.csv` 为 6 个固定系统提供：

- 完整蛋白 FASTA；
- PLINDER 官方 interacting residues；
- PLINDER 官方 neighboring residues；
- 根据配体重原子重新计算的 6 Å pocket residues；
- 原始链与 receptor PDB 重映射链；
- 结构–FASTA 对齐一致率；
- 配体 SDF 路径。

生成命令：

```bash
conda run -n drug-align-analysis \
  python scripts/build_model_inputs.py
```

## 映射验证

- 6/6 样本只有一个目标 FASTA record；
- 6/6 结构链与完整 FASTA 对齐的已映射残基 identity 为 1.0；
- 所有官方口袋和 6 Å 口袋索引均位于完整 FASTA 范围内；
- 6/6 口袋非空；
- train、validation、test 各 2 个系统。

## 官方口袋与 6 Å 口袋

| system ID | 官方主链 neighboring | 外部链 neighboring | 重算 6 Å | 关系 |
|---|---:|---:|---:|---|
| `3wik__1__1.A__1.B` | 20 | 0 | 20 | 完全一致 |
| `5wim__1__1.A__1.B` | 24 | 0 | 24 | 完全一致 |
| `5wio__1__1.A__1.E` | 15 | 1 | 13 | 6 Å 为官方主链子集 |
| `5wip__1__1.A__1.E` | 20 | 0 | 19 | 6 Å 为官方主链子集 |
| `5wi0__2__1.B__1.D` | 21 | 0 | 21 | 完全一致 |
| `5wi1__2__1.B__1.E` | 18 | 0 | 18 | 完全一致 |

差异说明：

- PLINDER 官方 neighboring 定义并不总与简单 6 Å 重原子距离完全相同；
- `5wio` 还包含一条不在目标 FASTA/receptor 映射中的外部链残基；
- 第一版 ESM-2 输入仅能索引主链残基；
- 外部链残基必须保留在审计字段，未来多链模型再纳入。

## 建模约定

第一版比较三种蛋白输入：

1. `full_sequence`：完整蛋白；
2. `official_neighboring_residues`：官方主链口袋；
3. `pocket_6a_residues`：坐标重算的 6 Å 主链口袋。

口袋输入保存为完整序列上的稀疏残基索引，不把不连续残基直接拼成“伪蛋白序列”。提取 ESM-2 时先编码完整序列，再按这些索引池化。

## 下一步

1. 对完整序列提取一个小型 ESM-2 checkpoint 的 residue embeddings；
2. 比较 mean pooling、口袋 mean pooling 和距离加权 pooling；
3. 暂不训练跨模态投影层；
4. 在 embedding 形状与索引完全通过 smoke test 后，再扩大样本。
