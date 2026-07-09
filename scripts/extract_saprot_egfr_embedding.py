#!/usr/bin/env python3
"""Run a SaProt-35M structure-aware embedding smoke test on EGFR."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import transformers
from transformers import EsmForMaskedLM, EsmTokenizer


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STRUCTURE = ROOT / "data" / "targets" / "egfr" / "structures" / "4G5J.pdb"
DEFAULT_OUTPUT = (
    ROOT / "outputs" / "protein_embeddings" / "saprot_35m_af2" / "4G5J_A.npz"
)
DEFAULT_AUDIT = ROOT / "data" / "egfr-saprot-smoke-audit.json"
MODEL_ID = "westlake-repl/SaProt_35M_AF2"
MODEL_REVISION = "316cd4017d29f4657b959365f24b57f1ee278912"


def structure_sequence(structure: Path, chain: str) -> tuple[str, str, str]:
    foldseek = shutil.which("foldseek")
    if foldseek is None:
        raise RuntimeError("foldseek is not available on PATH")

    with tempfile.TemporaryDirectory(prefix="saprot-") as tmp:
        descriptor = Path(tmp) / "descriptor.tsv"
        subprocess.run(
            [
                foldseek,
                "structureto3didescriptor",
                "-v",
                "0",
                "--threads",
                "1",
                "--chain-name-mode",
                "1",
                str(structure),
                str(descriptor),
            ],
            check=True,
        )
        candidates = []
        for line in descriptor.read_text(encoding="utf-8").splitlines():
            description, amino_acids, structural_alphabet = line.split("\t")[:3]
            if description.split()[0].endswith(f"_{chain}"):
                candidates.append((amino_acids, structural_alphabet))

    if len(candidates) != 1:
        raise RuntimeError(f"Expected one chain {chain}, found {len(candidates)}")
    amino_acids, structural_alphabet = candidates[0]
    if len(amino_acids) != len(structural_alphabet):
        raise RuntimeError("Amino-acid and 3Di sequence lengths differ")
    combined = "".join(
        amino_acid + token.lower()
        for amino_acid, token in zip(amino_acids, structural_alphabet)
    )
    return amino_acids, structural_alphabet, combined


def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure", type=Path, default=DEFAULT_STRUCTURE)
    parser.add_argument("--chain", default="A")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()

    amino_acids, structural_alphabet, combined = structure_sequence(
        args.structure, args.chain
    )
    tokenizer = EsmTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = EsmForMaskedLM.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model.eval()
    device = choose_device()
    model.to(device)

    encoded = tokenizer(combined, return_tensors="pt")
    encoded = {key: value.to(device) for key, value in encoded.items()}
    with torch.inference_mode():
        result = model(**encoded, output_hidden_states=True)
    hidden = result.hidden_states[-1][0]
    attention_mask = encoded["attention_mask"][0].bool()
    special_mask = torch.zeros_like(attention_mask)
    special_mask[0] = True
    special_mask[attention_mask.sum() - 1] = True
    residue_mask = attention_mask & ~special_mask
    residue_embeddings = hidden[residue_mask].float().cpu().numpy()
    pooled = residue_embeddings.mean(axis=0)

    if residue_embeddings.shape[0] != len(amino_acids):
        raise RuntimeError(
            f"Token/residue mismatch: {residue_embeddings.shape[0]} != {len(amino_acids)}"
        )
    if not np.isfinite(pooled).all():
        raise RuntimeError("Embedding contains non-finite values")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        pooled=pooled,
        residue_embeddings=residue_embeddings,
        amino_acid_sequence=np.array(amino_acids),
        structural_sequence=np.array(structural_alphabet),
    )
    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "input_structure": str(args.structure.relative_to(ROOT)),
        "chain": args.chain,
        "residue_count": len(amino_acids),
        "combined_token_count": len(amino_acids),
        "embedding_dimension": int(pooled.shape[0]),
        "residue_embedding_shape": list(residue_embeddings.shape),
        "device": str(device),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "foldseek_version": subprocess.check_output(
            [shutil.which("foldseek"), "version"], text=True
        ).strip(),
        "output": str(args.output.relative_to(ROOT)),
        "limitations": [
            "Smoke test only; no model training or benchmark claim.",
            "Experimental PDB input is not pLDDT-masked.",
            "The 35M checkpoint is for pipeline validation, not the final model choice.",
        ],
    }
    args.audit.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
