# 核心术语表

| 术语 | 本项目中的含义 |
|---|---|
| Target | 希望小分子结合并调节其功能的蛋白质靶点 |
| Binding pocket | 蛋白表面可容纳配体的局部三维区域 |
| Ligand | 能与蛋白结合的小分子 |
| De novo generation | 从条件和概率模型中生成新的分子结构 |
| Docking | 给定蛋白和已有小分子，预测其结合姿态 |
| Binding affinity | 实验测得的结合强弱，如 Kd、Ki；计算 docking score 不是实验亲和力 |
| Pose | 小分子在蛋白结合区域中的三维位置与构象 |
| RMSD | 两个对应三维结构间的均方根偏差 |
| SE(3) equivariance | 输入整体旋转/平移时，坐标输出按相同方式变化 |
| QED | 综合多项理化性质的类药性代理指标 |
| SA score | 合成难度代理指标；常见实现中分数越低越易合成 |
| ADMET | 吸收、分布、代谢、排泄与毒性 |
| Validity | 生成结果能否形成价态合理、可解析的化学分子 |
| Uniqueness | 有效生成分子去重后的比例 |
| Novelty | 相对训练集未出现；必须说明按 SMILES、scaffold 还是相似度定义 |
| Diversity | 候选集合内部结构差异，常用 Morgan fingerprint Tanimoto 计算 |
| Scaffold | 分子的核心骨架，常用 Bemis–Murcko scaffold 定义 |
| Pareto dominance | 一个候选在所有目标不差且至少一个目标更好 |
| Pareto front | 不被其他候选支配的解集合 |
| Reranking | 不改变生成器，仅用额外分数重新排列候选 |

