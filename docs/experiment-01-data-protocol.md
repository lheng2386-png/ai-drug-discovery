# 实验 01：完整蛋白与口袋局部表示的数据协议

## 1. 实验问题

在严格控制蛋白、口袋和配体相似性泄漏后，口袋局部表示是否比完整蛋白平均表示更适合冷靶点蛋白–配体检索？

本实验只验证表示与检索，不训练生成模型。

## 2. 数据选择

### 主数据：PLINDER

用途：蛋白–配体结构匹配和检索。

理由：

- 包含蛋白–配体复合物、口袋定义和丰富质量注释；
- 提供蛋白、口袋、配体及蛋白–配体相互作用相似度；
- 提供官方 train/validation/test split 和去泄漏系统；
- 能区分 novel ligand、novel pocket、novel protein 等测试场景。

第一版固定使用论文对应的 **PLINDER 2024-04/v1 PL50 split**，避免随数据更新改变结果。后续再用新版数据做外部验证。

官方入口：

- <https://plinder-org.github.io/plinder/dataset.html>
- <https://plinder-org.github.io/plinder/tutorial/dataset.html>
- <https://github.com/plinder-org/plinder>

### 辅助数据：PDBbind

用途：亲和力回归与排序验证。

PDBbind 不作为第一版检索 split 的唯一来源，原因是传统随机或简单序列划分容易残留口袋和配体相似性泄漏。

## 3. 样本单位

每个样本是一个：

```text
(protein chain, binding pocket, ligand, complex structure)
```

需要保存：

- PLINDER system ID；
- PDB ID、蛋白链和 UniProt ID；
- 完整蛋白序列；
- 口袋残基编号与坐标；
- 配体规范 SMILES、InChIKey 和三维坐标；
- 数据 split；
- 结构质量与异常标志；
- 亲和力标签及测定类型（若存在）。

多配体或多链复合物第一版只保留能够明确确定一个主要蛋白链–小分子配体关系的系统。复杂系统另存，不静默丢弃。

## 4. 口袋定义

第一版以 PLINDER 提供的口袋/相互作用定义为准，不重新根据测试配体随意调参。

模型输入使用两种口袋表示：

1. 与配体任一重原子距离不超过 6 Å 的残基；
2. PLINDER 提供的标准 pocket residues。

主结果使用官方定义，6 Å 定义作为敏感性分析。

必须防止“测试时偷看答案”：

- **holo-oracle 设置**：允许使用真实配体定义口袋，只用于研究表示上限；
- **realistic 设置**：使用已知/预测口袋或 apo/predicted structure，不允许通过测试配体定义输入。

论文中必须将两种设置分开报告。

## 5. 正样本与负样本

### 正样本

实验结构中对应的蛋白口袋–配体对。

同一口袋可能有多个已知配体，因此采用多正样本关系，不强制一对一。

### 负样本分级

1. **可靠 decoy**：有实验或 benchmark 支持的不结合/低活性分子；
2. **困难负样本**：理化性质相近、骨架相近，但未观察到目标结合；
3. **未标注样本**：数据库没有相互作用记录，不能直接称为真实负样本。

第一版训练可以使用 batch 内负样本，但损失函数和评测必须避免把已知多正样本错当负样本。

## 6. 数据划分

### 主划分

使用 PLINDER 官方 PL50 split，不重新随机拆分。

### 需要报告的测试子集

- seen-like：与训练分布接近的系统；
- cold-ligand：测试配体或 scaffold 未见；
- cold-pocket：测试口袋与训练口袋低相似；
- cold-protein：测试蛋白与训练蛋白低相似；
- double-cold：口袋/蛋白和配体均冷启动。

### 泄漏审计

每个测试样本至少记录其与训练集的：

- 最高蛋白序列 identity；
- 最高 pocket sequence identity；
- 最高 pocket structural similarity；
- 最高配体 fingerprint Tanimoto；
- scaffold 是否重复；
- PLINDER protein–ligand interaction similarity。

只写“训练和测试实体不重复”不算完成去泄漏。

## 7. 第一版模型对照

| 编号 | 蛋白输入 | 分子输入 | 交互方式 | 目的 |
|---|---|---|---|---|
| B0 | ProtBert 全蛋白 | Morgan fingerprint | 双塔距离 | ConPLex 思路基线 |
| B1 | ESM-2 全蛋白 | Morgan fingerprint | 双塔距离 | 只升级蛋白编码器 |
| B2 | ESM-2 全蛋白 | Uni-Mol | 双塔距离 | 升级分子表示 |
| B3 | ESM-2 口袋残基 | Uni-Mol | 双塔距离 | 检验局部口袋假设 |
| B4 | ESM-2 口袋残基 | Uni-Mol 原子 | cross-attention | 检验局部相互作用 |

所有模型尽量使用相同投影维度、训练样本和调参预算。

## 8. 评价指标

### 检索

- Recall@1、Recall@5、Recall@10；
- MRR；
- NDCG；
- enrichment factor（EF1%、EF5%）；
- AUROC 和 AUPR。

每个口袋面对同一个候选库检索，不能为不同模型使用不同 decoy。

### 冷启动可靠性

- 各 cold 子集相对常规测试集的性能下降；
- 性能随训练集最近邻相似度变化的曲线；
- 置信度校准：ECE、Brier score；
- 选择性预测：coverage–risk 曲线。

### 亲和力辅助验证

- RMSE、MAE；
- Pearson、Spearman；
- concordance index；
- 按测定类型分别报告，不能直接混合 Kd、Ki、IC50 后假装同质。

## 9. 统计规范

- 至少 3 个随机种子用于可训练模块；
- 按口袋 bootstrap 计算 95% 置信区间；
- B2 与 B3 是核心配对比较；
- 同时报绝对指标、差值和置信区间；
- 不只报告全局平均，必须报告 cold 子集和蛋白家族分层结果。

## 10. 实验成立标准

口袋局部表示的假设只有在以下条件同时满足时才算得到支持：

1. B3 在 cold-pocket/cold-protein 检索上稳定优于 B2；
2. 提升跨随机种子和 bootstrap 置信区间稳定；
3. 不是由参数量、候选库或数据量差异造成；
4. 在多个蛋白家族上成立，而非单一家族贡献；
5. realistic pocket 设置下仍保持方向一致。

如果只在 holo-oracle 口袋上提升，应将结论限制为表示上限，不能声称解决真实未知靶点筛选。

## 11. 第一阶段下载原则

暂不下载完整结构库。先获取：

- split 文件；
- annotation/index parquet；
- 数据字段说明；
- 100–500 个系统的 metadata 子集。

先完成：

1. split 数量统计；
2. affinity 覆盖率；
3. 冷启动子集规模；
4. 口袋、序列和配体字段可用性；
5. 磁盘空间估算。

确认数据协议后，才下载结构文件和提取 embedding。

## 12. 已知限制

- holo 复合物定义的口袋包含真实配体信息；
- “未记录相互作用”不能视为确定不结合；
- 晶体结构和数据库亲和力存在实验偏差；
- PLINDER 主要服务结构任务，不覆盖全部药理活性空间；
- PDBbind/PLINDER 与 BindingDB 的标签和实体映射需要额外清洗。
