The official code for the paper: \
[**ϕ-Noise: Training-Free Temporal Video Conditioning via Phase-Based Noise Manipulation**](https://arxiv.org/pdf/2605.24509)

Our method, *Φ-Noise*, enables motion and structure conditioning for diffusion-based video generation. By utilizing low-frequency components in either the spatial or temporal dimensions, it facilitates precise motion transfer and supports three key applications:
- Image-to-video motion Transfer
- Text-to-video Motion Transfer
- Cut-n-Drag (interactive user control over object trajectories and spatial placement)

<!-- add gif HERE -->

### Contents ###
- `phi_noise_utils.py`: core frequency-mixing utilities.
- `video_processing_utils.py`: Video utilities: preprocessing and adjusting sizes/lengths.
- `Wan2.2_phi-noise/`: A fork of [Wan2.2 official GitHub](https://github.com/Wan-Video/Wan2.2) with small adjustments for the integration of our method.

### Highlights ###
- *Φ-Noise* is **training-free** temporal conditioning via phase/magnitude mixing in frequency domain.
- this code (`freq_mix_temporal` and `freq_mix_spatial` in [phi_noise_utils.py])(phi_noise_utils.py#L1-L220) can be integrated easily with any diffusion-based video model.
- We supply an example integration for Wan2.2 model [Wan2.2_phi-noise/generate.py](Wan2.2_phi-noise/generate.py#L1-L520).


### Installation ###
*Φ-Noise* uses [PyTorch](https://pytorch.org/) for frequecny decomposition (`torch.fft` module). \
For installation instruction of Wan2.2, please refer to [Wan2.2/INSTALL.md](https://github.com/Wan-Video/Wan2.2/blob/main/INSTALL.md).

### Example Usage ###

1) As utilities in your own code (recommended):

```python
from phi_noise_utils import freq_mix_temporal, freq_mix_spatial

# freq_mix_temporal expects lists like [latents] and returns a list
latents = freq_mix_temporal(noise_list, latents_ref_list, alpha=3, gamma=30.0)

# freq_mix_spatial mixes spatial phase; returns a tensor
out = freq_mix_spatial(latents_hi, latents_lo, alpha=3, gamma=4.0, dims=("h","w"))
```

2) Run the Wan example script (multi-GPU via torch.distributed.run). Make sure both the workspace root and the Wan folder are on `PYTHONPATH` so `phi_noise_utils` and `wan` import correctly. Example command (adjust `--nproc_per_node`, `CUDA_VISIBLE_DEVICES`, and `--ckpt_dir`):

```bash
export PYTHONPATH=/dev/shm/ofir/phi-noise:/dev/shm/ofir/phi-noise/Wan2.2_phi-noise
export CUDA_VISIBLE_DEVICES=0,1
/home/nvidia/miniconda3/envs/wan_ofir/bin/python -m torch.distributed.run \
  --nproc_per_node 2 --master_port 29501 Wan2.2_phi-noise/generate.py \
  --ulysses_size 2 --task t2v-A14B --size "832*480" --sample_steps 20 \
  --ckpt_dir /path/to/checkpoints --offload_model False --convert_model_dtype \
  --dit_fsdp --prompt "A yellow helicopter is flying in the beach. Camera is fixed and static. Fixed Background." \
  --pn_ref_path guidance_exmaples/preprocessed_14B-low_81f_duck.mp4 --pn_task t2v_mt \
  --pn_gamma 3 --pn_alpha 4
```

**Citation**
```
@article{abramovich2025phinoise,
  title   = {ϕ-Noise: Training-Free Temporal Video Conditioning
            via Phase-Based Noise Manipulation},
  author  = {Abramovich, Ofir and Cohen, Nadav Z. and
            Rosenthal, Adi and Shamir, Ariel},
  journal = {arXiv preprint},
  year    = {2025},
}
```

### Acknowledgments ###
This repository uses a fork of [Wan2.2](https://github.com/Wan-Video/Wan2.2) codebase.

**License**
See `LICENSE.txt` in the repository root.
