# 第 1 周执行单

## 本周目标

形成对研究任务的正确心智模型，完成本机/云端环境规划，并能用自己的语言解释 TargetDiff、DiffDock 和 CrossDocked2020 的角色。

## 阅读任务

### 1. TargetDiff

- 论文：<https://openreview.net/pdf?id=kJqXEPXMsE0>
- 第一遍只读 Abstract、Introduction、Figure 1、Conclusion；
- 第二遍读 Problem Definition、Diffusion Process、Experiments；
- 记录：输入、输出、条件信息、加噪对象、去噪网络、数据 split、指标、局限。

### 2. DiffDock

- 论文：<https://openreview.net/pdf?id=kKF8_K-mBbS>
- 重点回答：为什么它是 docking 而不是新分子生成？
- 记录平移、旋转和扭转三个自由度以及 confidence model 的作用。

### 3. CrossDocked2020

- 论文：<https://pubmed.ncbi.nlm.nih.gov/32865404/>
- 重点回答：cross-docked pose 是什么？数据切分为什么会高估新靶点泛化？

## 每篇论文笔记模板

```text
研究问题：
输入：
输出：
模型：
数据：
评价指标：
最重要的实验结论：
我不理解的概念：
复现所需资源：
作者承认的局限：
与本课题的关系：
```

## 环境任务

1. 选择按小时计费的 GPU 平台；
2. 创建 Ubuntu x86_64、24 GB NVIDIA GPU、32 GB RAM 以上的实例；
3. 只运行环境检查命令；
4. 保存实例镜像名称、GPU、驱动、磁盘、计费方式；
5. 在确认规格后再开始 TargetDiff 环境安装。

## 周末自测

1. TargetDiff 的输入和输出分别是什么？
2. 为什么三维生成模型需要 SE(3) 等变性？
3. DiffDock 为什么不能直接生成新化学结构？
4. docking score 与实验 binding affinity 有什么区别？
5. validity、uniqueness、novelty、diversity 分别测量什么？
6. 为什么随机数据切分可能高估 DTA 或生成模型的泛化？

## 预期产出

- 三篇论文各一页笔记；
- 一张 TargetDiff 数据流图；
- 一份云端环境记录；
- 一份未理解问题列表；
- 一个是否进入第 2 周的判断。

