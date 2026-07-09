# ESM-2 池化表示 v0.1 审计

审计日期：2026-07-09

## 配置

- 模型：`esm2_t6_8M_UR50D`；
- 参数量：8M；
- 层数：6；
- 表示层：最后一层（6）；
- embedding 维度：320；
- PyTorch：2.12.1（conda-forge）；
- fair-esm：2.0.0；
- 设备：Apple M1 MPS；
- 模型状态：`eval()`；
- 推理状态：`torch.inference_mode()`。

该模型只用于本地 smoke test，不作为最终论文模型。正式实验至少需要比较更大的 ESM-2 checkpoint 和 SaProt。

## 产出

- 数组：`embeddings/esm2_t6_8M_UR50D/sample-pooled-v0.1.npz`；
- 可审计摘要：`data/processed/sample-esm2-pooling-v0.1.csv`；
- 提取脚本：`scripts/extract_esm2_sample_embeddings.py`。

NPZ 数组：

| key | shape |
|---|---|
| `system_ids` | `(6,)` |
| `full_mean` | `(6, 320)` |
| `official_pocket_mean` | `(6, 320)` |
| `pocket_6a_mean` | `(6, 320)` |

## 验证结果

- 6/6 完整蛋白表示成功；
- 6/6 官方主链口袋表示成功；
- 6/6 重算 6 Å 口袋表示成功；
- 所有数值均为 finite；
- 重复运行的最大绝对差为 0，当前配置下结果确定；
- 没有训练或更新 ESM-2 参数。

## 初步观察

完整蛋白与官方口袋 mean embedding 的余弦相似度范围约为 0.652–0.994。

官方口袋与 6 Å 口袋：

- 4 个口袋定义完全一致，对应表示余弦为 1；
- `5wio` 的余弦约为 0.9987；
- `5wip` 的余弦约为 0.9996。

这说明提取管线能反映口袋索引变化，但 6 个样本远不足以支持“口袋表示优于完整蛋白”或任何泛化结论。

## OpenMP 兼容问题及处理

最初通过 pip 安装的 PyTorch 与 Conda 科学计算栈加载了两份 OpenMP runtime，程序主动中止。未使用 `KMP_DUPLICATE_LIB_OK` 绕过。

修复方式：

1. 卸载 pip PyTorch；
2. 从 conda-forge 安装 PyTorch 2.12.1；
3. fair-esm 保留为 pip 包；
4. 重新运行后 MPS 推理成功。

该处理避免了可能造成静默数值错误的不安全运行库绕过。

## 下一步

1. 将元数据 manifest 扩大到 100 个系统；
2. 优先提取完整序列与口袋索引，不立即下载全部结构；
3. 评估 8M 模型在 100 个样本上的时间和内存；
4. 再决定正式实验使用 35M、150M 或更大的 ESM-2；
5. 分子侧随后建立 Morgan fingerprint 基线，再接入 Uni-Mol。
