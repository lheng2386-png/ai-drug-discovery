"""Extract deterministic ESM-2 pooled embeddings for the fixed sample."""

from __future__ import annotations

import argparse
from pathlib import Path

import esm
import numpy as np
import pandas as pd
import torch


MODEL_NAME = "esm2_t6_8M_UR50D"
REPRESENTATION_LAYER = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "mps"],
        default="auto",
    )
    return parser.parse_args()


def parse_indices(value: str) -> list[int]:
    if not value:
        return []
    return [int(item.split(":", 1)[0]) for item in value.split(";")]


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denominator)


def choose_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError("MPS was requested but is unavailable")
        return torch.device("mps")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    inputs_path = root / "data/processed/sample-model-inputs-v0.1.csv"
    output_dir = root / "embeddings" / MODEL_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    embeddings_path = output_dir / "sample-pooled-v0.1.npz"
    summary_path = root / "data/processed/sample-esm2-pooling-v0.1.csv"

    inputs = pd.read_csv(inputs_path)
    model, alphabet = esm.pretrained.esm2_t6_8M_UR50D()
    model.eval()
    device = choose_device(args.device)
    model = model.to(device)
    batch_converter = alphabet.get_batch_converter()
    batch = list(zip(inputs.system_id, inputs.full_sequence))
    labels, sequences, tokens = batch_converter(batch)
    tokens = tokens.to(device)

    with torch.inference_mode():
        output = model(tokens, repr_layers=[REPRESENTATION_LAYER])
    representations = output["representations"][REPRESENTATION_LAYER].cpu()

    full_embeddings = []
    official_embeddings = []
    pocket_6a_embeddings = []
    summary_rows = []

    for row_index, row in inputs.iterrows():
        length = len(row.full_sequence)
        residue_embeddings = representations[row_index, 1 : length + 1]
        official_indices = parse_indices(row.official_neighboring_residues)
        pocket_6a_indices = parse_indices(row.pocket_6a_residues)
        if not official_indices or not pocket_6a_indices:
            raise ValueError(f"{row.system_id}: empty pocket indices")
        if residue_embeddings.shape[0] != length:
            raise ValueError(
                f"{row.system_id}: token/residue length mismatch "
                f"{residue_embeddings.shape[0]} != {length}"
            )

        full_mean = residue_embeddings.mean(dim=0).numpy()
        official_mean = residue_embeddings[official_indices].mean(dim=0).numpy()
        pocket_6a_mean = residue_embeddings[pocket_6a_indices].mean(dim=0).numpy()
        full_embeddings.append(full_mean)
        official_embeddings.append(official_mean)
        pocket_6a_embeddings.append(pocket_6a_mean)
        summary_rows.append(
            {
                "system_id": row.system_id,
                "split": row.split,
                "sequence_length": length,
                "official_pocket_count": len(official_indices),
                "pocket_6a_count": len(pocket_6a_indices),
                "embedding_dim": int(full_mean.shape[0]),
                "full_norm": float(np.linalg.norm(full_mean)),
                "official_norm": float(np.linalg.norm(official_mean)),
                "pocket_6a_norm": float(np.linalg.norm(pocket_6a_mean)),
                "cosine_full_official": cosine(full_mean, official_mean),
                "cosine_full_pocket_6a": cosine(full_mean, pocket_6a_mean),
                "cosine_official_pocket_6a": cosine(
                    official_mean, pocket_6a_mean
                ),
                "device": str(device),
                "model": MODEL_NAME,
                "representation_layer": REPRESENTATION_LAYER,
            }
        )

    np.savez_compressed(
        embeddings_path,
        system_ids=inputs.system_id.to_numpy(),
        full_mean=np.stack(full_embeddings),
        official_pocket_mean=np.stack(official_embeddings),
        pocket_6a_mean=np.stack(pocket_6a_embeddings),
    )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(summary_path, index=False)
    print(summary.to_string(index=False))
    print(f"\nEmbeddings: {embeddings_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
