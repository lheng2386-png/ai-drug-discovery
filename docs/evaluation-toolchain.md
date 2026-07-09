# 分子评价工具链

本阶段建立的是可复现的**计算筛选工具链**，不是实验活性或安全性结论。

## 已配置组件

| 组件 | 版本 | 当前用途 | 不能据此声称 |
|---|---:|---|---|
| RDKit | 2026.03.3（本机 smoke test） | QED、理化描述符、构象生成 | 可合成、无毒或具有活性 |
| PoseBusters | 0.6.5 | 检查生成分子的化学与三维几何合理性 | 与 EGFR 结合 |
| ADMET-AI | 2.0.1 | 批量预测 ADMET 端点，供排序与 Pareto 分析 | 临床安全或实验 ADMET |
| AutoDock Vina | 1.2.7 | 后续进行正交 docking 评价 | docking score 等于结合自由能 |
| Meeko | 0.7.1 | 后续准备 Vina 的 PDBQT 输入 | 自动得到可靠质子化状态 |

环境创建：

```bash
conda env create -f environment/drug-evaluation.yml
conda activate drug-evaluation
```

运行已知 EGFR 配体 smoke test：

```bash
python scripts/evaluate_egfr_known_ligands_smoke.py
```

输出：

- `results/evaluation/egfr_known_ligands_smoke.csv`
- `data/egfr-evaluation-smoke-audit.json`

## Docking 的验证门槛

Vina 当前仅完成 Python binding 与输入准备工具的安装验证。正式给生成分子打分前必须：

1. 确定结构、链、共晶配体和口袋中心；
2. 明确蛋白/配体质子化、电荷和保留水策略；
3. 对共晶配体进行 redocking；
4. 报告重原子 RMSD、随机种子、box 和 exhaustiveness；
5. redocking 通过后，才对同一结构设置下的候选分子作相对排序。

建议把 docking 作为正交评价信号之一，而不是唯一亲和力标签。

## 多目标评价中的位置

后续统一表至少保留以下信号：

- 亲和力代理：PLI predictor + 经验证的 docking；
- 类药性：QED 与基础理化描述符；
- 可合成性：SA score，并在高排名候选上追加路线级检查；
- 安全性：ADMET-AI 预测及适用域/不确定性；
- 三维有效性：PoseBusters；
- 多样性/新颖性：指纹相似度、scaffold 和训练集近邻。

所有模型预测字段使用工具名前缀，避免与实验字段混淆。

