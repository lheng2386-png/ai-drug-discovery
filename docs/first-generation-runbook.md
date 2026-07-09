# 第一次 EGFR 候选分子生成操作单

目标产物：

- `results/generation/egfr_first_batch/generated_egfr_candidates.sdf`
- `results/generation/egfr_first_batch/generated_egfr_candidates.csv`
- `results/generation/egfr_first_batch/basic_properties.csv`

## 推荐显卡

第一轮建议租 **RTX 3090 24 GB，Ubuntu 20.04，CUDA 11.x**。

理由：TargetDiff 官方环境是 Python 3.8、PyTorch 1.13.1、CUDA 11.6、PyG 2.2.0。RTX 3090/Ampere 与该旧栈兼容性最好。RTX 5090 更强，但更可能需要 CUDA 12.x 和新版 PyTorch，第一轮 baseline 复现不建议用它。

如果出现可复现 OOM：

1. 先把 `batch_size` 从 8 降到 4 或 2；
2. 仍不行再租 A6000/A40 48 GB；
3. 不建议第一轮直接租多卡。

## TargetDiff 生成

云端进入仓库根目录后：

```bash
bash scripts/cloud/setup_targetdiff.sh "$PWD"
```

把官方 checkpoint 放到：

```text
external/targetdiff/pretrained_models/pretrained_diffusion.pt
```

先小样本：

```bash
bash scripts/cloud/run_targetdiff_egfr_generation.sh "$PWD" 25 4 cuda:0
```

确认成功后跑第一批：

```bash
bash scripts/cloud/run_targetdiff_egfr_generation.sh "$PWD" 250 8 cuda:0
```

说明：脚本会对 `data/pockets/egfr/*_pocket_10A.pdb` 逐个采样。若有 4 个口袋、每个 250 个样本，理论原始样本数为 1000；实际有效分子数会因为重构失败、RDKit 无效、断裂分子和去重而下降。

## DecompDiff 生成

DecompDiff 官方 sampler 不是直接输入一个 pocket PDB。它需要：

- checkpoint；
- processed protein-ligand dataset；
- index `.pkl`；
- reference ligand 分解信息；
- AlphaSpace/subpocket 或 ref prior 相关字段。

因此必须先准备 EGFR reference-ligand processed entry。准备好后设置：

```bash
export DECOMPDIFF_CKPT=/path/to/decompdiff/checkpoint.pt
export DECOMPDIFF_ORI_DATA=/path/to/processed/original/data
export DECOMPDIFF_INDEX=/path/to/test_index.pkl
export DECOMPDIFF_PRIOR_MODE=ref_prior
export DECOMPDIFF_NUM_ATOMS_MODE=ref
```

然后运行：

```bash
bash scripts/cloud/setup_decompdiff.sh "$PWD"
bash scripts/cloud/run_decompdiff_egfr_generation.sh "$PWD" 0 8 cuda:0
```

边界：如果没有 DecompDiff processed entry，不应声称完成 DecompDiff inference。

## 统一后处理

TargetDiff 会输出多个 `sdf/*.sdf` 文件。统一后处理：

```bash
conda run -n drug-evaluation python scripts/postprocess_generated_ligands.py \
  --sdf-dir results/generation/raw/targetdiff_egfr_YYYYMMDDTHHMMSSZ \
  --out-prefix results/generation/egfr_first_batch/generated_egfr_candidates
```

如果同时有 DecompDiff `result.pt`：

```bash
conda run -n drug-evaluation python scripts/postprocess_generated_ligands.py \
  --sdf-dir results/generation/raw/targetdiff_egfr_YYYYMMDDTHHMMSSZ \
  --decompdiff-pt 'results/generation/raw/decompdiff_egfr_YYYYMMDDTHHMMSSZ/**/result.pt' \
  --out-prefix results/generation/egfr_first_batch/generated_egfr_candidates
```

该脚本执行：

1. 读取 SDF / DecompDiff result；
2. RDKit sanitize；
3. 去除 disconnected molecule；
4. canonical SMILES 去重；
5. 输出统一 SDF；
6. 输出候选分子 CSV；
7. 计算基础性质：MW、LogP、TPSA、QED、HBD/HBA、rotatable bonds、ring count、formal charge、fraction Csp3。

## 合格标准

第一批候选最小合格标准：

- 至少一个 TargetDiff 口袋成功生成；
- RDKit valid unique 分子数不少于 100；
- 输出文件存在且非空；
- `postprocess_audit.json` 记录 input、valid、invalid、duplicate 数量；
- 不把原始 checkpoint、外部源码、大量 raw output 上传 GitHub。

## 下一步

生成后进入评价闭环：

1. PoseBusters 复查；
2. QED/SA/ADMET-AI；
3. Vina docking；
4. ESM-2/SaProt × Uni-Mol PLI 打分；
5. diversity/novelty；
6. Pareto 筛选。
