# 初始风险清单

| 风险 | 影响 | 当前缓解措施 |
|---|---|---|
| M1/8 GB 无法运行 CUDA baseline | 本机复现失败 | 采用本机分析 + 云端 NVIDIA 推理 |
| 新显卡不兼容官方 CUDA 11.6 旧栈 | CUDA kernel/PyG 扩展失败 | 第一阶段选 RTX 3090/A6000 等 Ampere 卡 |
| 旧版 CUDA/PyG/RDKit 依赖冲突 | 环境安装耗时 | 使用独立 Conda 环境，固定版本，先 smoke test |
| CrossDocked 数据与权重下载量大 | 磁盘和租机费用增加 | 先下载最小测试资源，不立即下载完整训练数据 |
| DiffDock 默认版本已变化 | 结果无法对应原论文 | 固定 commit、checkpoint 和配置 |
| Vina 分数被误称为亲和力 | 科研结论不严谨 | 全部标记为计算代理指标 |
| 数据 split 泄漏 | 高估泛化能力 | 使用官方 split，后续增加 protein/scaffold cold split |
| 只展示高分样例 | cherry-picking | 保存全部结果和失败，报告完整分布 |
| 大分子获得虚高 docking 分数 | 优化目标偏置 | 同时约束 MW、QED、SA、Lipinski 和尺寸分布 |
| ADMET 模型域外预测 | 毒性结论不可靠 | 报告预测器版本、适用域与不确定性 |
| 研究范围过大 | 12 周无法收敛 | 先 TargetDiff，后 DecompDiff；先 reranking，后 guidance |
