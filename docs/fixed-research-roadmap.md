# 固定技术路线与阶段门

## 路线锁定

最终课题固定为：

**面向未见靶点泛化的 PLI–ADMET 反馈引导靶点条件化分子生成方法研究。**

后续允许调整数据、模型实现和实验预算，但不再把主问题改回单纯 DTI、亲和力预测或生成后重排序。

## 总体闭环

靶点条件 → TargetDiff/DecompDiff 生成 → 物理与化学检查 → PLI/ADMET/SA 评价 → Pareto 选择 → 奖励或偏好反馈 → 下一轮生成。

反馈闭环的判据是：评价信号必须进入重采样、引导采样、奖励学习或生成器参数优化。只对同一批候选排序属于 baseline，不属于最终方法。

## 阶段 A：数据与可复现基础

任务：

- 建立 EGFR WT、L858R、T790M、C797S 的序列、结构、口袋和已知配体清单；
- 记录每个结构的来源、实验方法、分辨率、链、配体、突变和许可；
- 建立训练/验证/测试隔离规则；
- 在云端复现 TargetDiff 单口袋推理。

通过标准：

- 一个命令能够对一个 EGFR 口袋生成候选；
- 输出可被 RDKit 读取并通过统一 schema 记录；
- 数据来源和口袋定义可追溯；
- 不使用测试靶点配体作为训练或条件信息。

## 阶段 B：Level 1 评价闭环

任务：

- 每个口袋先生成 100 个候选，稳定后扩至 1000；
- 计算 validity、uniqueness、novelty、diversity；
- 运行几何/碰撞/PoseBusters 检查；
- 计算 PLI、QED、SA、ADMET/毒性及不确定性；
- 建立统一的 molecule-level 结果表；
- 比较 hard filter、weighted sum 和 Pareto。

通过标准：

- TargetDiff、post-filter、Pareto reranking 三个 baseline 可重复；
- 每一项指标有方向、量纲、缺失值和失败处理规则；
- Pareto 候选不是由测试标签或人工主观挑选产生。

## 阶段 C：Level 2 奖励闭环

任务：

- 从多目标结果构造优/劣分子对；
- 控制同靶点、同骨架和模型评分偏差；
- 训练并校准 reward/preference model；
- 将奖励用于候选重排序或有限的引导采样；
- 报告奖励黑客、分布外失效和不确定性。

通过标准：

- 奖励模型在按靶点和骨架隔离的数据上优于简单评分加权；
- 改善不仅来自生成更多样本；
- 至少有一个外部或正交评价器支持结果。

## 阶段 D：Level 3 生成闭环

任务：

- 采用偏好优化、条件微调或采样引导，使反馈影响新生成分布；
- 固定采样预算，与所有 baseline 公平比较；
- 完成条件和反馈信号消融；
- 分析亲和力、ADMET、SA 和多样性之间的冲突。

核心结果：

`feedback-guided generation > Pareto reranking > post-filter > TargetDiff`

这一顺序是待检验假设，不是预设结论。

## 阶段 E：泛化验证

分三级进行：

1. EGFR WT/突变体：验证突变敏感性与选择性；
2. held-out kinase：按靶点隔离验证冷靶点泛化；
3. unseen family：按家族隔离验证跨家族外推。

划分时同时审计：

- 蛋白序列相似性；
- 口袋结构相似性；
- 配体 Bemis–Murcko scaffold；
- 复合物和 assay 重复；
- 已知配体条件造成的信息泄漏。

## 统一结果表最小字段

- `target_id`, `target_variant`, `structure_id`, `pocket_id`
- `generator`, `checkpoint`, `seed`, `sample_id`
- `smiles`, `scaffold`, `validity`, `posebusters_pass`
- `pli_score`, `affinity_score`, `affinity_uncertainty`
- `qed`, `sa_score`, `admet_*`, `toxicity_*`
- `novelty`, `diversity`, `pareto_rank`
- `split`, `seen_target`, `seen_family`, `known_ligand_used`

## 近期唯一优先级

先完成阶段 A。当前不训练奖励模型，不微调 TargetDiff，也不租用高价 GPU 长时间批量生成。单口袋 smoke test 成功后再扩大预算。
