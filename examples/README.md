# Examples — synthetic modality generators

Ten self-contained scripts, each simulating one microscopy/imaging modality and
composing it into a mikro scene. Every script is deterministic (fixed seed), checks
its own ground truth locally, and supports `--dry-run` (generate + self-check,
upload nothing). Together they exercise every layer kind the API offers.

| Script | Modality | What it shows |
|---|---|---|
| `generator_smlm.py` | Single-molecule localization (dSTORM-like) | localization table → **PointLayer**, super-resolution render, raw blinking movie; mixed-resolution shared world |
| `generator_spt.py` | Single-particle tracking | trajectory table → **TrackLayer** (2D+t; renderer orders by `(track_id, t)` — declare the time column literally `t`) |
| `generator_hyperspectral.py` | Lambda-stack / spectral imaging | **SPECTRUM axis**, spectral **PhasorLayer** + phasor histogram, linear unmixing → one IntensityLayer per channel |
| `generator_calcium.py` | Functional calcium imaging | movie + **LabelLayer** whose picker mixes table colorBys with **sparse ΔF/F slices at time positions** |
| `generator_hcs_plate.py` | High-content screening | many fields placed by `world.grid_cell(...)`, per-well table doubling as a plate heat-map PointLayer |
| `generator_clem.py` | Correlative light–EM | one specimen, two grids, joined by a **top-level AFFINE registration edge** (rotation + scale + offset as one claim) |
| `generator_dti_tractography.py` | Diffusion MRI tractography | FA volume, DISPLACEMENT-axis field → bootstrap-inferred **VectorLayer**, streamlines as a **3D TrackLayer**, glass-brain **MeshLayer** |
| `generator_mri_multicontrast.py` | Structural MRI | T1/T2/FLAIR as one channel-axis dataset (`stage(kind=VOLUME)` = one MIP per contrast) + tissue LabelLayer |
| `generator_fmri.py` | BOLD fMRI | 4D series, GLM z-map thresholded by its contrast window, ROI picker with sparse percent-signal-change slices |
| `generator_tractography_network.py` | Tractography, graph-encoded | the SAME streamlines as the DTI script (which it imports), shipped through konnektion as a **NetworkLayer** with per-node vocabulary and taper |

## Conventions the scripts share

- Local generation first, `--dry-run` guard, then
  `with connect(App(..., services=[mikro_service])) as rt: mikro = rt.require(Mikro)`.
  The service object (`from mikro import mikro_service`) is registered on the
  app explicitly; nothing is registered by importing.
- Fields and volumes are deliberately non-square/non-cubic so a y/x transpose
  fails the self-checks instead of drawing rotated.
- One shared world per scene; each dataset's pixel/voxel/frame size lives on its
  registration edge (`world.register(ds, scale=...)`), never on the axes.
- A table's axis-typed columns, in file order, ARE its space; coordinate columns
  are declared in array order (`z, y, x` — `x, y, z` transposes silently).
- A vector layer exists only via scene bootstrap, and only under an **empty**
  `ScenePolicyInput()` — an explicit `kind=` overrides the DISPLACEMENT inference
  (see `generator_dti_tractography.py`).

## Testing

The integration suite runs every script end-to-end against the dokker test
stack — `tests/test_examples.py` stubs `arkitekt.App`/`arkitekt.connect` and lets each
script's own self-checks and round-trip assertions do the judging:

```bash
uv run pytest tests/test_examples.py -m integration
```

A new script here must be added to that file's `SCRIPTS` list (a collection-time
guard fails otherwise).

## Extra dependencies

Beyond `mikro` + numpy/xarray/pandas: `scipy` and `scikit-image`
(most scripts), `trimesh` + the `fabriks` checkout (mesh scripts), `sporadik`
(sparse matrices), `konnektion` (the network tractography). The two tractography
scripts must sit in the same directory (one imports the other's phantom).
