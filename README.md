### An official implementation of the paper: ###

<div align="center">
  <h1>&phi;-Noise:<br>Training-Free Temporal Video Conditioning via Phase-Based Noise Manipulation</h1>

  <img src="docs/static/logos/lab_logo.svg" alt="Lab Logo" width="25%" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="docs/static/logos/uni_logo.png" alt="University Logo" width="20%" />

  <br><br>

  <a href="https://arxiv.org/abs/2605.24509">
    <img src="https://img.shields.io/badge/arXiv-paper-b31b1b?style=flat-square&logo=arxiv&logoColor=white" alt="arXiv" />
  </a>
  &nbsp;
  <a href="https://ofirabramovich.github.io/phi-noise/">
    <img src="https://img.shields.io/badge/Web-page-1f77b4?style=flat-square&logo=github&logoColor=white" alt="Web page" />
  </a>
  &nbsp;
  <a href="https://arxiv.org/pdf/2605.24509">
    <img src="https://img.shields.io/badge/PDF-download-0066cc?style=flat-square&logo=adobeacrobatreader&logoColor=white" alt="PDF" />
  </a>
</div>

<br>

*Φ-Noise* enables motion and structure conditioning for diffusion-based video generation. By utilizing low-frequency components in either the spatial or temporal dimensions, it facilitates precise motion transfer and supports three key applications:
- Image-to-video motion Transfer
- Text-to-video Motion Transfer
- Cut-n-Drag (interactive user control over object trajectories and spatial placement)

| **I2V Motion Transfer** | **T2V Motion Transfer** | **Cut n' Drag** |
| :---: | :---: | :---: |
| <img src="docs/static/media/results/i2v.gif" alt="I2V Motion Transfer" width="100%"> | <img src="docs/static/media/results/t2v.gif" alt="T2V Motion Transfer" width="100%"> | <img src="docs/static/media/results/cnd.gif" alt="Cut n' Drag" width="100%"> |

### Contents ###
- `phi_noise_utils.py`: core frequency-mixing utilities.
- `video_processing_utils.py`: Video utilities: preprocessing and adjusting sizes/lengths.
- `Wan2.2_phi-noise/`: A fork of [Wan2.2 official GitHub](https://github.com/Wan-Video/Wan2.2) with small adjustments for the integration of our method.

### Highlights ###
- *Φ-Noise* is **training-free** temporal conditioning via phase/magnitude mixing in frequency domain.
- This code (`freq_mix_temporal` and `freq_mix_spatial` in [phi_noise_utils.py](phi_noise_utils.py#L1-L220)) can be integrated easily with any diffusion-based video model.
- We supply an example integration for Wan2.2 model: [Wan2.2_phi-noise/generate.py](Wan2.2_phi-noise/generate.py#L1-L520).

### Installation ###
*Φ-Noise* uses [PyTorch](https://pytorch.org/) for frequency decomposition (`torch.fft` module). <br>
For installation instructions of Wan2.2, please refer to [Wan2.2/INSTALL.md](https://github.com/Wan-Video/Wan2.2/blob/main/INSTALL.md).

### Usage ###

#### Φ-Noise + Wan2.2 ####
 
For a new input video, first preprocess it with `video_processing_utils.py` so the FPS, frame size, and clip length match the model requirements. This saves the preprocessed video in addition to the first frame (for I2V Motion Transfer).

Run the Wan example script (multi-GPU via torch.distributed.run). Make sure both the workspace root and the Wan folder are on `PYTHONPATH` so `phi_noise_utils` and `wan` import correctly. Example commands (adjust `--nproc_per_node`, `CUDA_VISIBLE_DEVICES`, and `--ckpt_dir`):

**T2V Motion Transfer:**
```bash
export PYTHONPATH=/absolute-path-to/phi-noise/Wan2.2_phi-noise
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
python -m torch.distributed.run \
  --nproc_per_node 8 --master_port 29501 Wan2.2_phi-noise/generate.py \
  --ulysses_size 8 --task t2v-A14B --size "832*480" --sample_steps 20 \
  --ckpt_dir /path/to/checkpoints --offload_model False --convert_model_dtype \
  --dit_fsdp --prompt "A yellow helicopter is flying in the beach. Camera is fixed and static. Fixed Background." \
  --pn_ref_path guidance_examples/preprocessed_14B-low_81f_duck.mp4 --pn_task t2v_mt \
  --pn_gamma 3 --pn_alpha 4