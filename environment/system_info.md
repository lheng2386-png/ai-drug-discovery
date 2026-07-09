# 计算环境清单

记录日期：2026-07-09

## 本机

| 项目 | 当前状态 |
|---|---|
| 设备 | MacBook Air (MacBookAir10,1) |
| 芯片 | Apple M1，8 核 |
| 内存 | 8 GB |
| 架构 | arm64 |
| 可用磁盘 | 约 65 GiB |
| 操作系统 | macOS |
| Python | 系统 Python 3.9.6 |
| Conda | 26.1.1，路径 `/Users/Apple/miniconda3` |
| VS Code | 1.128.0 |
| Git | 2.39.5 |
| NVIDIA/CUDA | 无 |
| PyTorch | 系统 Python 中未安装 |
| RDKit | 系统 Python 中未安装 |
| PyTorch Geometric | 系统 Python 中未安装 |

## 结论

本机不作为 TargetDiff、DecompDiff 或 DiffDock 的主要复现机器，原因是：

1. 官方实现主要面向 Linux、NVIDIA CUDA 与 x86_64；
2. 8 GB 统一内存不足以稳定承载模型、图数据和评测流水线；
3. Apple MPS 对旧版 PyTorch Geometric、CUDA 扩展和部分科学计算依赖的兼容性有限。

本机后续只创建独立的轻量分析环境，不污染系统 Python。

## 云端最低建议

| 项目 | 建议 |
|---|---|
| 操作系统 | Ubuntu 20.04 或 22.04，x86_64 |
| GPU | NVIDIA RTX 3090 24 GB（第一阶段首选） |
| 显存备选 | A6000/A40 48 GB（Ampere） |
| 后续现代模型 | RTX 5090 32 GB + CUDA 12.8+ |
| CPU | 8 vCPU 或以上 |
| 内存 | 32 GB 最低，64 GB 更稳妥 |
| 系统盘 | 50 GB 以上 |
| 数据盘 | 100–200 GB 起步；完整数据规模确认后再扩容 |
| 驱动 | 与 CUDA 11.6/11.7 兼容的新版本 NVIDIA 驱动 |
| 网络 | 能访问 GitHub、模型权重和数据下载地址 |

## GPU 选择结论

TargetDiff 官方测试环境是 PyTorch 1.13.1 + CUDA 11.6。NVIDIA 官方兼容矩阵显示：

- Ampere（RTX 3090/A6000/A40）从 CUDA 11.0 开始支持；
- Ada（RTX 4090）从 CUDA 11.8 开始支持；
- Blackwell（RTX 5090）从 CUDA 12.8 开始支持。

因此 RTX 3090 24 GB 是当前最稳妥的低成本复现卡。5090 留到后续使用现代 PyTorch 的 Uni-Mol、ESM 或新模型实验。

参考：

- NVIDIA RTX 5090 规格：<https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/>
- NVIDIA CUDA/架构矩阵：<https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html>
- NVIDIA Blackwell 兼容指南：<https://docs.nvidia.com/cuda/blackwell-compatibility-guide/contents.html>

## 云端启用后的第一轮检查

先记录以下输出，再安装模型依赖：

```bash
uname -a
cat /etc/os-release
nvidia-smi
df -h
free -h
python3 --version
conda --version
git --version
```

验收条件：

- `nvidia-smi` 正常显示 GPU、显存和驱动；
- 3090 应显示约 24 GB GPU 显存；
- 至少有 80 GB 可用磁盘用于第一轮环境与小数据；
- 不在 base 环境直接安装 TargetDiff 依赖。

## 本地分析环境

已创建独立 Conda 环境：

```bash
conda activate drug-align-analysis
```

主要版本：

| 包 | 版本 |
|---|---|
| Python | 3.10.20 |
| RDKit | 2026.03.3 |
| Pandas | 2.3.3 |
| PyArrow | 24.0.0 |
| Biopython | 1.87 |
| NumPy | 2.2.6 |
| SciPy | 1.15.2 |
| PyTorch | 2.12.1（conda-forge） |
| fair-esm | 2.0.0（pip） |

环境声明文件：`environment/analysis-environment.yml`。
