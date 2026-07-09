# PLINDER 2024-04/v1 元数据审计

审计日期：2026-07-09

## 文件概况

- PL50 split：435,624 行，4 列；
- 非冗余 annotation：267,667 行，488 列；
- annotation 中每行对应一个唯一 `system_id`；
- 78,811 个不同 PDB entry；
- 36,662 个不同 canonical SMILES。

## 官方 PL50 split

| split | 系统数 | cluster 数 |
|---|---:|---:|
| train | 255,463 | 120,753 |
| validation | 13,896 | 6,380 |
| test | 15,132 | 5,842 |
| removed | 151,133 | 84,091 |

`removed` 不是可用训练数据，必须排除。

YAML 中记录的去泄漏图配置为：

- `pli_qcov` threshold 20，depth 2；
- `pocket_qcov` threshold 50，depth 2；
- `protein_lddt_weighted_sum` threshold 70，depth 1；
- 测试采样 cluster 使用 directed `pli_qcov` threshold 70；
- validation cluster 使用 `pocket_qcov` threshold 50。

这些阈值属于 PLINDER v1 官方配置，后续不得在观察测试结果后修改。

## Annotation 与 split 的连接结果

| split | annotation 行数 |
|---|---:|
| train | 153,452 |
| validation | 8,101 |
| test | 8,766 |
| removed | 87,547 |
| 未匹配 | 9,801 |

未匹配行不能直接分配进训练集。需要确认版本差异或系统 ID 覆盖原因。

## 第一轮候选过滤

初步过滤条件：

1. `suitable_for_ml_training == True`；
2. 非共价配体；
3. 非离子、非 artifact、非 invalid；
4. 单配体链；
5. 单 interacting protein chain；
6. 配体重原子数在 6–80 之间。

过滤结果：

| split | 候选系统数 |
|---|---:|
| train | 61,070 |
| validation | 1,791 |
| test | 5,045 |
| removed | 46,095 |
| 未匹配 | 4,402 |

最终可用集合暂时只包括 train/validation/test，共 67,906 个系统。该数字仍是候选值，不是最终数据集版本。

## 候选集合性质

| 属性 | 均值 | 中位数 | 5%–95% |
|---|---:|---:|---:|
| 分子量 | 439.0 | 409.1 | 147.1–852.4 |
| 配体重原子数 | 29.8 | 27 | 10–58 |
| QED | 0.368 | 0.342 | 0.044–0.782 |
| 相互作用残基数 | 8.33 | 8 | 2–16 |
| 口袋残基数 | 24.61 | 24 | 8–43 |

## 关键发现

1. 数据规模足够，不需要一开始下载所有结构；
2. `removed` 占比很高，表明去泄漏会显著减少可用数据；
3. annotation v1 没有直接提供统一的 affinity 字段，因此亲和力任务仍需 PDBbind/BindingDB；
4. 候选配体的分子量上尾较长，后续需要决定是否收紧药物样分子范围；
5. v1 非冗余 annotation 中 `ligand_is_covalent=True` 数量较大，必须复查该字段语义和典型样本，不能盲目过滤；
6. 9,801 行 annotation 没有匹配 PL50 split，暂时隔离。

## 下一步

1. 从 train/validation/test 各抽取少量 system ID；
2. 核验结构文件下载路径和单系统体积；
3. 人工检查普通配体、共价配体和异常大分子样本；
4. 冻结 `metadata-manifest-v0.1` 后再下载结构。
