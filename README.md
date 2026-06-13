### An official implementatiton of the paper: ###

<div align="center">
  <h2 style="font-size:36px; margin:0;">ϕ-Noise:<br>Training-Free Temporal Video Conditioning via Phase-Based Noise Manipulation</h2>
  <img src="docs/static/logos/lab_logo.svg" alt="Image from the left" width="25%" style="display: inline-block; vertical-align: middle;" />
  <a href="https://arxiv.org/abs/2605.24509" style="display: inline-block; vertical-align: middle; margin: 0 8px;">
    <img src="https://img.shields.io/badge/arXiv-paper-b31b1b?style=flat-square&logo=arxiv&logoColor=white" alt="arXiv" />
  </a>
  <a href="https://ofirabramovich.github.io/phi-noise/" style="display: inline-block; vertical-align: middle; margin: 0 8px;">
    <img src="https://img.shields.io/badge/Web-page-1f77b4?style=flat-square&logo=github&logoColor=white" alt="Web page" />
  </a>
  <a href="https://arxiv.org/pdf/2605.24509" style="display: inline-block; vertical-align: middle; margin: 0 8px;">
    <img src="https://img.shields.io/badge/PDF-download-0066cc?style=flat-square&logo=adobeacrobatreader&logoColor=white" alt="PDF" />
  </a>
 <img src="docs/static/logos/uni_logo.png" alt="Image from the right" width="20%" style="display: inline-block; vertical-align: middle;" />
</div>


*Φ-Noise* enables motion and structure conditioning for diffusion-based video generation. By utilizing low-frequency components in either the spatial or temporal dimensions, it facilitates precise motion transfer and supports three key applications:
- Image-to-video motion Transfer
- Text-to-video Motion Transfer
- Cut-n-Drag (interactive user control over object trajectories and spatial placement)

<div align="center" style="background:#ffffff; border-radius:14px; padding:14px;">
  <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
    <div style="width:32%; min-width:220px; box-sizing:border-box;">
      <p><strong>I2V Motion Transfer</strong></p>
      <img src="docs/static/media/results/i2v.gif" alt="I2V Motion Transfer" width="100%" style="border-radius:10px;" />
    </div>
    <div style="width:32%; min-width:220px; box-sizing:border-box;">
      <p><strong>T2V Motion Transfer</strong></p>
      <img src="docs/static/media/results/t2v.gif" alt="T2V Motion Transfer" width="100%" style="border-radius:10px;" />
    </div>
    <div style="width:32%; min-width:220px; box-sizing:border-box;">
      <p><strong>Cut n' Drag</strong></p>
      <img src="docs/static/media/results/cnd.gif" alt="Cut n' Drag" width="100%" style="border-radius:10px;" />
    </div>
  </div>
</div>

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

### Usage ###

#### Φ-Noise + Wan2.2 ####
 
For a new input video, first preprocess it with `video_processing_utils.py` so the FPS, frame size, and clip length match the model requirements. This saves the preprocessed video in addition to the first frame (for I2V Motio Transfer).

Run the Wan example script (multi-GPU via torch.distributed.run). Make sure both the workspace root and the Wan folder are on `PYTHONPATH` so `phi_noise_utils` and `wan` import correctly. Example commands (adjust `--nproc_per_node`, `CUDA_VISIBLE_DEVICES`, and `--ckpt_dir`):

T2V Motion Trasfer:
```bash
export PYTHONPATH=absolute-patto/phi-noise/Wan2.2_phi-noise
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
python -m torch.distributed.run \
  --nproc_per_node 8 --master_port 29501 Wan2.2_phi-noise/generate.py \
  --ulysses_size 8 --task t2v-A14B --size "832*480" --sample_steps 20 \
  --ckpt_dir /path/to/checkpoints --offload_model False --convert_model_dtype \
  --dit_fsdp --prompt "A yellow helicopter is flying in the beach. Camera is fixed and static. Fixed Background." \
  --pn_ref_path guidance_exmaples/preprocessed_14B-low_81f_duck.mp4 --pn_task t2v_mt \
  --pn_gamma 3 --pn_alpha 4
```

I2V Motion Trasfer:
```bash
export PYTHONPATH=absolute-patto/phi-noise/Wan2.2_phi-noise
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
python -m torch.distributed.run \
  --nproc_per_node 8 --master_port 29501 Wan2.2_phi-noise/generate.py \
  --ulysses_size 8 --task t2v-A14B --size "832*480" --sample_steps 20 \
  --ckpt_dir /path/to/checkpoints --offload_model False --convert_model_dtype \
  --dit_fsdp --prompt "A yellow helicopter is flying in the beach. Camera is fixed and static. Fixed Background." \
  --pn_ref_path guidance_exmaples/preprocessed_14B-low_81f_duck.mp4 --pn_task t2v_mt \
  --pn_gamma 3 --pn_alpha 4
```

Cut n' Drag:
```bash
export PYTHONPATH=absolute-patto/phi-noise/Wan2.2_phi-noise
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
python -m torch.distributed.run \
  --nproc_per_node 8 --master_port 29501 Wan2.2_phi-noise/generate.py \
  --ulysses_size 8 --task t2v-A14B --size "832*480" --sample_steps 20 \
  --ckpt_dir /path/to/checkpoints --offload_model False --convert_model_dtype \
  --dit_fsdp --prompt "A yellow helicopter is flying in the beach. Camera is fixed and static. Fixed Background." \
  --pn_ref_path guidance_exmaples/preprocessed_14B-low_81f_duck.mp4 --pn_task t2v_mt \
  --pn_gamma 3 --pn_alpha 4
```
*Tip*: To run with multiple gamma or alpha values, pass them with `#` separators, for example: `--pn_alpha arg1#arg2#arg3`.

#### General Usage ####
As utilities in your own code (recommended):

```python
from phi_noise_utils import freq_mix_temporal, freq_mix_spatial

# freq_mix_temporal expects lists like [latents] and returns a list
latents = freq_mix_temporal(noise_list, latents_ref_list, alpha=3, gamma=30.0) # recommended range values: gamma: alpha: [3-6], gamma: [30]

# freq_mix_spatial mixes spatial phase; returns a tensor
out = freq_mix_spatial(latents_hi, latents_lo, alpha=3, gamma=4.0, dims=("h","w")) # recommended range values: gamma: alpha: [3-4], gamma: [5-10]
```


### Citation ###
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

### License ###
This project is licensed under the **Apache License 2.0**.
