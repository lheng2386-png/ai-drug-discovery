# 数据登记

## PLINDER 2024-04/v1

用途：实验 01 的蛋白–配体结构检索与冷启动评测。

### 已下载文件

| 文件 | 大小 | MD5 |
|---|---:|---|
| `raw/plinder/2024-04-v1/plinder-pl50.parquet` | 6,183,470 bytes | `7c25b620eeebc5845cb5f367d4ee8c13` |
| `raw/plinder/2024-04-v1/plinder-pl50.yaml` | 522 bytes | `709d5664fa93b14c5aab74be082d8124` |
| `raw/plinder/2024-04-v1/annotation_table_nonredundant.parquet` | 277,039,884 bytes | `3cd5b0cacd0fd57c0471986beec89b14` |
| `raw/plinder/2024-04-v1/systems/wi.zip` | 197,319,893 bytes | `f9b3da723c8765b5bdd7cc790c647b32` |

### 官方来源

```text
https://storage.googleapis.com/plinder/2024-04/v1/splits/plinder-pl50.parquet
https://storage.googleapis.com/plinder/2024-04/v1/splits/plinder-pl50.yaml
https://storage.googleapis.com/plinder/2024-04/v1/index/annotation_table_nonredundant.parquet
https://storage.googleapis.com/plinder/2024-04/v1/systems/wi.zip
```

### 下载原则

- 原始数据不提交 Git；
- 暂未下载完整 annotation 表和结构压缩包；
- 下载结构前先冻结过滤条件和 metadata manifest；
- 任何重新下载都必须核验文件大小与 MD5。

### 最小结构样本

`sample-structures-v0.1.csv` 固定了 6 个系统：

- train：2；
- validation：2；
- test：2。

所有系统都位于 `wi.zip`，从而避免为少量人工检查下载多个结构分片。解压结果保存在忽略提交的 `raw/plinder/2024-04-v1/sample-systems-v0.1/`。

## PDBbind

状态：尚未下载。

用途：第二阶段亲和力回归与排序验证，不作为第一版结构检索的唯一 split。
