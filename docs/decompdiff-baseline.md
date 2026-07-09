# DecompDiff baseline configuration

## Pinned source and license

- Repository: `https://github.com/bytedance/DecompDiff`
- Commit: `ed4e7d8202c077cc4bd1b9ca626e173c24007f2a`
- Code license: CC BY-NC 4.0
- Publication: ICML 2023

This is suitable for non-commercial academic research, but its license is not
interchangeable with TargetDiff's MIT license.

## Why it is not a drop-in replacement for TargetDiff

The official sampler is indexed-dataset based. It loads a preprocessed
protein-ligand example and requires decomposition metadata such as:

- reference ligand and ligand atom masks;
- arm/scaffold assignments and centers;
- AlphaSpace2 subpockets;
- processed LMDB and split/index files;
- atom-count prior files;
- a pretrained DecompDiff checkpoint.

Therefore, a protein-only 10 Å PDB is not sufficient. The helper
`pocket_pdb_to_pocket` exists in the source but the official sampling path does
not use it to construct all required decomposition fields.

## EGFR integration route

1. Use a full EGFR co-crystal protein structure, not the already clipped pocket.
2. Export the bound reference ligand as a sanitized SDF while preserving its
   crystallographic coordinates and covalent status.
3. Run the official `extract_subcomplex`/AlphaSpace2 preprocessing.
4. Create the processed dataset entry and test index expected by the sampler.
5. Validate `ref_prior` first; only then compare beta/subpocket priors.
6. Run 10-sample smoke generation on the same EGFR complex used for TargetDiff.

The first candidate is `2ITZ` (L858R–gefitinib), because it is non-covalent.
`4G5J` (WT–afatinib) should not be the first DecompDiff example because its
reference ligand is covalently linked to Cys797.

## Current status

- official source pinned;
- cloud environment specified;
- 10 Å protein pockets pass static PDB-format checks;
- the full DecompDiff parser was not executed locally because its
  PyTorch-Geometric stack is isolated to the CUDA cloud environment;
- EGFR reference-ligand SDF and AlphaSpace decomposition are not yet complete;
- no checkpoint sampling or generated molecule is claimed.
