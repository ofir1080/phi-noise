import sys
import os
import torch
import cv2
import numpy as np
import imageio
from torchvision.transforms import Grayscale, functional as TF

NUM_FRAMES_5B = 121
NUM_FRAMES_14B = 81

STRIDE = 8

def load_video(path, target_size=(1280, 704),
               ret_motion_video=False,
               frame_limit=None,
               stride=(4, 16, 16)):
               
    cap = cv2.VideoCapture(path)
    frames = []
    motion_frames = []
    i = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, target_size)
        frames.append(frame_rgb)

        frame_gs = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if ret_motion_video:
            if i == 0:
                prev_frame_gs = frame_gs
            motion_frame = cv2.absdiff(frame_gs, prev_frame_gs)
            # mask if larger than threshold, binary
            motion_frame = cv2.threshold(motion_frame, 10, 255, cv2.THRESH_BINARY)[1]
            # resize using nearatse neighbor
            motion_frame = cv2.resize(motion_frame, (target_size[0] // stride[-2], target_size[1] // stride[-1]), interpolation=cv2.INTER_NEAREST)
            motion_frames.append(motion_frame)
            prev_frame_gs = frame_gs
        # print(f"Loaded frame {len(frames)} at {cap.get(cv2.CAP_PROP_FPS):.2f} FPS")
        i += 1
    cap.release()
    
    # Shape: [F, H, W, C] -> [C, F, H, W]
    vid = np.array(frames).transpose(3, 0, 1, 2)
    vid = (vid / 127.5) - 1.0  # Normalize to [-1, 1]
    if frame_limit is not None:
        vid = vid[:, :frame_limit]
    if ret_motion_video:
        motion_frames.append(motion_frame)
        motion_mask = np.array(motion_frames)[::STRIDE][None]
        # motion_vid = motion_vid / motion_vid.max()
        if frame_limit is not None:
            motion_mask = motion_mask[:, :frame_limit] 
    return (torch.from_numpy(vid).float(), torch.from_numpy(motion_mask)) if ret_motion_video else torch.from_numpy(vid).float()


def get_video_fps(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return fps


def load_motion_video(path, target_size=(1280, 704)):
    cap = cv2.VideoCapture(path)
    prev_frame = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY)
    motion_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_frame, frame)
        diff = cv2.resize(diff, target_size)
        diff[diff < 25] = 0
        # _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_frames.append(diff)
        prev_frame = frame
        # print frame rate
        # print(f"Loaded frame {len(frames)} at {cap.get(cv2.CAP_PROP_FPS):.2f} FPS")
    cap.release()
    
    # Shape: [F, H, W, C] -> [C, F, H, W]
    vid = np.array(motion_frames)[None, ::4, ...] # .repeat(3, axis=0)  # [1, F, H, W] -> [3, F, H, W]
    # vid = (vid / 127.5) - 1.0  # Normalize to [-1, 1]
    return torch.from_numpy(vid).float()


def save_video(frames, path, fps, save_first_frame=False, gs=False):
    if isinstance(frames, (list, tuple)):
        frames = torch.cat(frames, dim=0)

    if isinstance(frames, torch.Tensor):
        frames = frames.detach().float().cpu()

        # Support [1, 3, F, H, W], [3, F, H, W], or [F, H, W, 3].
        if frames.ndim == 5 and frames.shape[0] == 1:
            frames = frames[0]
        if frames.ndim == 4 and frames.shape[0] == 3:
            frames = frames.permute(1, 2, 3, 0)  # [3, F, H, W] -> [F, H, W, 3]
        # if grayscale, convert to RGB by repeating channels
        if frames.ndim == 4 and frames.shape[0] == 1:
            frames = frames.repeat(3, 1, 1, 1).permute(1, 2, 3, 0)  # [1, F, H, W] -> [F, H, W, 3]
        elif frames.ndim != 4 or frames.shape[-1] != 3:
            raise ValueError(f"Unsupported frame tensor shape: {tuple(frames.shape)}")
        
        # VAE output is typically in [-1, 1]. Convert to [0, 255] uint8.
        if frames.min() < 0 and frames.max() < 1.1:
            frames = ((frames + 1.0) * 127.5).clamp(0, 255)
        else:
            frames *= 255.0
            frames = frames.clamp(0, 255)
        frames = frames.to(torch.uint8).numpy()
    else:
        frames = np.asarray(frames)
        if frames.ndim != 4 or frames.shape[-1] != 3:
            raise ValueError(f"Expected numpy frames with shape [F, H, W, 3], got {frames.shape}")
        if frames.dtype != np.uint8:
            frames = np.clip(frames, 0, 255).astype(np.uint8)

    if gs:
        transform = Grayscale(num_output_channels=3)
        frames = transform(torch.from_numpy(frames).float().permute(0, 3, 1, 2)).permute(0, 2, 3, 1).byte().numpy()
    # height, width = frames.shape[1], frames.shape[2]
    # save first frame
    if save_first_frame:
        imageio.imwrite(f"{path[:-4]}_ff.png", frames[0])
    imageio.mimwrite(path, frames, fps=fps, codec='libx264', quality=8)


def decode_video(latents, save_path="reconstructed_video.mp4", fps=24.0):
    with torch.no_grad():
        video_recon = vae.decode(latents)
        if save_path:
            save_video(video_recon, save_path, fps=fps)
        return video_recon


def encode_video(video_path, target_size=(1280, 704), frame_limit=None, vae_enc=None, ret_motion_mask=False, stride=(4, 16, 16)):
    vae_enc = vae_enc if vae_enc is not None else vae
    # target_size
    out = load_video(video_path, target_size=target_size, ret_motion_video=ret_motion_mask, frame_limit=frame_limit, stride=stride)
    if ret_motion_mask:
        video_tensor, motion_mask = out
        video_tensor = video_tensor.to(vae_enc.device, dtype=vae_enc.dtype)
        motion_mask = motion_mask.to(vae_enc.device, dtype=vae_enc.dtype)
    else:
        video_tensor = out
    input_tensor = video_tensor.unsqueeze(0).to(vae_enc.device, dtype=vae_enc.dtype)
    with torch.no_grad():
        latents = vae_enc.encode([input_tensor[0]])
    if ret_motion_mask:
        return latents, motion_mask.bool()
    return latents, None # [1, latent_dim, F//16, H//16, W//16]


def noise_up(latents,
             x,
             noise=None,
             num_train_timesteps=1000,
             x_is_timestep=True,
             clamp_sigma=True,
             return_noise=False,
             generator=None):
    """
    Create WAN flow-matching noisy latent Z_x from clean latent and Gaussian noise.

    WAN schedulers use:
        alpha_x = 1 - sigma_x
        Z_x = alpha_x * z0 + sigma_x * eps

    Args:
        latents: Tensor shaped [C, F, H, W] or list/tuple with a single tensor.
        x: Noise level selector. If x_is_timestep=True, interpreted in [0, num_train_timesteps].
           Otherwise interpreted directly as sigma in [0, 1].
        noise: Optional epsilon tensor with same shape as latent.
        num_train_timesteps: Training timestep count (WAN default: 1000).
        x_is_timestep: Whether x is a timestep value rather than direct sigma.
        clamp_sigma: Clamp sigma to [0, 1].
        return_noise: If True, also return the sampled/used epsilon tensor.
        generator: Optional torch.Generator used when sampling noise.

    Returns:
        Same container type as latents (tensor or single-item list), optionally with noise.
    """
    is_sequence = isinstance(latents, (list, tuple))
    latent = latents[0] if is_sequence else latents

    if x_is_timestep:
        sigma = torch.as_tensor(
            x, device=latent.device, dtype=torch.float32) / float(num_train_timesteps)
    else:
        sigma = torch.as_tensor(x, device=latent.device, dtype=torch.float32)

    if clamp_sigma:
        sigma = sigma.clamp(0.0, 1.0)

    while sigma.ndim < latent.ndim:
        sigma = sigma.unsqueeze(-1)

    alpha = 1.0 - sigma

    if noise is None:
        noise = torch.randn(
            latent.shape,
            device=latent.device,
            dtype=torch.float32,
            generator=generator)
    else:
        noise = noise.to(device=latent.device, dtype=torch.float32)

    zx = alpha * latent.to(torch.float32) + sigma * noise
    zx = zx.to(latent.dtype)

    if is_sequence:
        zx_out = [zx]
    else:
        zx_out = zx

    if return_noise:
        return zx_out, noise
    return zx_out


def preprocess_guidance(video_path, model_type='5B', fps=None, gs=False):
    if model_type == '5B':
        num_frames = 121
        target_size = (1280, 704)
        fps = 24.0
    elif model_type == '14B-low':
        num_frames= 81 # 121 # -> default is 81
        target_size= (832, 464) # (832, 480) -> WRONG!
        fps = 16.0
    elif model_type == '14B-high':
        num_frames= 81
        target_size= (1280, 720)
        fps = 16.0
    fn = video_path.split("/")[-1].split(".")[0]
    video_tensor = load_video(video_path, target_size=target_size)
    orig_num_frames = video_tensor.shape[1]
    new_frame_indices = np.round(np.linspace(0, orig_num_frames - 1, num_frames)).astype(int)
    adjusted_video_tensor = video_tensor[:, new_frame_indices]
    # adjust fps
    new_fps = int(get_video_fps(video_path) / (round(get_video_fps(video_path) / fps))) if fps is None else fps
    assert adjusted_video_tensor.shape[1] == num_frames, f"Expected {num_frames} frames after preprocessing, but got {adjusted_video_tensor.shape[1]}"
    print(f'removing {orig_num_frames - adjusted_video_tensor.shape[1]} frames')
    output_path = f"{os.path.dirname(video_path)}/preprocessed_{model_type}_{num_frames}f{'_gs' if gs else ''}_{fn}.mp4"
    save_video(adjusted_video_tensor, output_path, fps=new_fps, save_first_frame=True)
    print(f'Saved in {output_path}')
    return output_path


def preprocess_guidance_ttm(video_path, model_type='5B'):
    if model_type == '5B':
        num_frames = 121
        target_size = (1280, 704)
        fps = 24.0
    elif model_type == '14B-low':
        num_frames= 81
        target_size= (832, 464) # (832, 480) -> WRONG!
        fps = 16.0
    elif model_type == '14B-high':
        num_frames= 81
        target_size= (1280, 720)
        fps = 16.0
    fn = video_path.split("/")[-1].split(".")[0]
    video_tensor = load_video(video_path, target_size=target_size)
    adjusted_num_frames = video_tensor.shape[1]
    skip_frame = int(adjusted_num_frames / num_frames)
    print(f'sub-sampleing rate: {skip_frame}')
    video_tensor = video_tensor[:, ::skip_frame]
    print(f'removing {adjusted_num_frames - video_tensor.shape[1]}')
    video_tensor = video_tensor[:, :num_frames]
    save_video(video_tensor, f"{os.path.dirname(video_path)}/preprocessed_{model_type}_{fn}_{num_frames}f.mp4", fps=fps, save_first_frame=True, gs=False)
    print(['Done.'])


def image_motion_mix(vid_path, img_path, model_type):
    assert model_type in vid_path
    if model_type == '5B':
        target_size = (1280, 704)
        fps = 24.0
    elif model_type == '14B-low':
        target_size= (832, 464) # (832, 480) -> WRONG!
        fps = 16.0
    elif model_type == '14B-high':
        target_size= (1280, 720)
        fps = 16.0

    cap = cv2.VideoCapture(vid_path)
    frames = []
    i = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, target_size)
        frames.append(frame)

    frames = np.stack(frames, axis=0)
    ref_img = cv2.imread(img_path)
    ref_img = cv2.cvtColor(ref_img, cv2.COLOR_BGR2RGB)
    ref_img = cv2.resize(ref_img, target_size)

    frames_diff = [ref_img]
    for i in range(1, len(frames)):
        diff = frames[i-1] - frames[i]
        fused_frame = frames_diff[0] + np.stack([diff, diff, diff], axis=-1)
        frames_diff.append(fused_frame)
    imageio.mimwrite(f'{vid_path[:-4]}_x_{os.path.basename(img_path)[:-4]}_diff.mp4', frames_diff, fps=fps, codec='libx264', quality=8)
    print('save', f'{vid_path[:-4]}_x_{os.path.basename(img_path)[:-4]}_diff.mp4')


def decode_latent_img(latent, save_path='./latent.png'):
    with torch.no_grad():
        img_recon = vae.decode([latent])[0]
        # cnvert to scale [0, 255] and save
        np.save(save_path.replace('.png', '.npy'), latent.cpu().numpy())
        img_recon = (img_recon + 1) / 2 * 255
        imageio.imwrite(save_path, img_recon.permute(1, 2, 3, 0)[0].float().byte().cpu())
        return img_recon


if __name__ == "__main__":
    VID_TO_PROCESS = 'guidance_exmaples/mt-it2m/woman_turning.mp4'
    # for I2V motion transfer
    # IMG_SOURCE = 'guidance_exmaples/i2v-mt/rock.png'
    
    output_path_5b = preprocess_guidance(VID_TO_PROCESS, model_type='5B')
    output_path_14bl = preprocess_guidance(VID_TO_PROCESS, model_type='14B-low')

    # for motion mix (for moore stable I2V MT)
    # image_motion_mix(output_path_14bl, IMG_SOURCE, model_type='14B-low')
