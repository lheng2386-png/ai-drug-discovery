# AI Drug Discovery Research

研究题目：**面向未见靶点泛化的 PLI–ADMET 反馈引导靶点条件化分子生成方法研究**

完整技术表述：**基于 PLM 靶点表征、3D 口袋图与已知配体约束的 PLI–ADMET 反馈引导靶点条件化分子生成与 Pareto 多目标优化**

## 固定研究主线

本项目不止做“生成后筛选”。核心问题是：

> 能否把蛋白–配体相互作用、ADMET、物理合理性和可合成性评价转化为奖励、偏好或硬约束，使其真正影响下一轮靶点条件化分子生成，并提高对未见靶点的泛化能力？

系统由九个模块构成：

1. 靶点输入；
2. PLM、3D 口袋图和已知配体组成的靶点条件；
3. TargetDiff/DecompDiff 靶点条件化生成；
4. 物理合理性与 PoseBusters 检查；
5. Uni-Mol 分子表征；
6. 蛋白质–分子跨模态对齐；
7. PLI/亲和力评价；
8. ADMET、QED、SA 与毒性评价；
9. Pareto 选择及反馈引导。

此前完成的口袋级跨模态对齐与 PLINDER 数据管线继续保留，作为第 6、7 模块的数据和方法基础，不再单独作为最终课题。

## 实施层级

- **Level 1：评价闭环。** TargetDiff 生成 → PLI/ADMET/物理/合成评价 → Pareto 选择。
- **Level 2：奖励闭环。** 根据 Pareto 优劣构造偏好数据，训练奖励模型并用于重排序或引导采样。
- **Level 3：生成闭环。** 用偏好优化或条件微调让反馈直接改变生成器，验证其优于单纯 generate-then-filter。

主实验对照固定为：

1. TargetDiff；
2. TargetDiff + post-filter；
3. TargetDiff + Pareto reranking；
4. Ours：feedback-guided generation。

## 第一执行对象

- 主靶点：EGFR WT、L858R、T790M、C797S；
- 扩展激酶：ALK、JAK2、CDK2、BRAF、SRC、ABL1、VEGFR2；
- 最终泛化：严格的 held-out target 与 unseen-family 测试。

EGFR 变体实验用于验证突变敏感性和选择性，但不能单独证明“未见靶点泛化”；该结论必须由按靶点或家族隔离的测试集支持。

## 当前状态

- 已建立 EGFR 序列、WT/突变结构、10 Å 口袋及 ChEMBL 已知配体数据；
- 已完成 ESM-2、SaProt、Uni-Mol 与 8 个已知配体 ADMET/PoseBusters smoke test；
- 已固定 TargetDiff/DecompDiff 代码版本并完成输入兼容性检查；
- 已建立第一版 target-conditioned 统一数据表：4 个 EGFR 10 Å 口袋 × 8 个已知配体 = 32 条评价记录；
- Vina/Meeko 环境已配置，但尚未完成共晶配体 redocking；
- 尚未训练模型，尚未生成 EGFR 候选；
- 下一步是在 NVIDIA 云端完成 TargetDiff 单口袋生成与 EGFR redocking 基线；
- 所有计算结果均视为计算预测，不替代实验亲和力、毒理或临床证据。

## 关键文档

- [固定技术路线与阶段门](docs/fixed-research-roadmap.md)
- [研究问题与可检验假设](docs/research_questions.md)
- [EGFR 数据准备规范](docs/egfr-data-plan.md)
- [PLINDER 数据协议](docs/experiment-01-data-protocol.md)
- [环境清单](environment/system_info.md)
- [分子评价工具链](docs/evaluation-toolchain.md)
- [统一数据表字段字典](docs/unified-data-schema.md)
- [风险清单](docs/risks.md)
- [阅读清单](papers/reading_list.md)
