import logging
import torch


__all__ = ["freq_mix_temporal", "freq_mix_spatial"]


def _real_fft_energy(t_fft: torch.Tensor, band_end: int | None = None) -> torch.Tensor:
    """Return the energy of a real FFT tensor, accounting for mirrored bins."""

    if band_end is not None:
        t_fft = t_fft[:, :band_end, ...]

    dc_energy = t_fft[:, 0, ...].norm() ** 2
    mirrored_energy = t_fft[:, 1:, ...].norm() ** 2
    return dc_energy + 2 * mirrored_energy


def _temporal_high_band_scale(mixed_t: torch.Tensor, alpha: int, gamma: float) -> torch.Tensor:
    total_energy = _real_fft_energy(mixed_t)
    low_energy = _real_fft_energy(mixed_t, band_end=alpha)
    high_energy = torch.clamp(total_energy - low_energy, min=1e-8)
    target_high_energy = total_energy - (low_energy / (gamma**2))
    return torch.sqrt(torch.clamp(target_high_energy / high_energy, min=0.0))


def _frequency_radius_grid(latents: torch.Tensor, fft_dims: tuple[int, ...]) -> torch.Tensor:
    grids = [torch.linspace(-1, 1, latents.shape[d], device=latents.device) for d in fft_dims]
    mesh = torch.meshgrid(*grids, indexing="ij")

    rr = torch.zeros_like(mesh[0])
    for grid in mesh:
        rr = rr + grid**2
    return torch.sqrt(rr)


def freq_mix_temporal(l1, l2, gamma=30.0, alpha=3, **kwargs):
    """Mix temporal frequency magnitude from ``l1`` with phase from ``l2``."""

    l1, l2 = l1[0], l2[0]
    l1_f, l2_f = l1.float(), l2.float()

    fft1_t = torch.fft.rfft(l1_f, dim=1, norm='ortho')
    fft2_t = torch.fft.rfft(l2_f, dim=1, norm='ortho')

    magnitude1_t = torch.abs(fft1_t)
    phase2_t = torch.angle(fft2_t)

    if alpha > 0:
        alpha = int(alpha)
        mixed_t = torch.polar(magnitude1_t, phase2_t)

        mixed_t[:, alpha:] = fft1_t[:, alpha:]

        high_band_scale = _temporal_high_band_scale(mixed_t, alpha, gamma)
        temporal_scale = torch.empty(mixed_t.shape[1], device=mixed_t.device, dtype=mixed_t.real.dtype)
        temporal_scale[:alpha] = 1.0 / gamma
        temporal_scale[alpha:] = high_band_scale
        mixed_t_final = mixed_t * temporal_scale[None, :, None, None]
        logging.info("beta term: %f", high_band_scale)
        logging.info(f'l1_f norm: {l1_f.norm()}\t{l1.norm()}')

    else:
        mixed_t_final = fft1_t.clone()

    combined_latents_t = torch.fft.irfft(mixed_t_final, dim=1, n=l1_f.shape[1], norm='ortho')

    return [combined_latents_t.to(l1.dtype)]


def freq_mix_spatial(latents_hi, latents_lo, alpha, gamma, dims=("t", "h", "w"), **kwargs):
    """
    Replace LOW-FREQUENCY PHASE of latents_hi with latents_lo
    """

    assert latents_hi.shape == latents_lo.shape
    device = latents_hi.device

    dim_map = {
        "t": 1,
        "h": 2,
        "w": 3,
    }
    fft_dims = tuple(dim_map[d] for d in dims)

    fft_hi = torch.fft.fftn(latents_hi, dim=fft_dims, norm='ortho')
    fft_lo = torch.fft.fftn(latents_lo, dim=fft_dims, norm='ortho')

    fft_hi = torch.fft.fftshift(fft_hi, dim=fft_dims)
    fft_lo = torch.fft.fftshift(fft_lo, dim=fft_dims)

    # frequency grid
    rr = _frequency_radius_grid(latents_hi, fft_dims)

    cutoff = rr.max() / (2 ** alpha)

    low_mask = (rr < cutoff).float()
    high_mask = 1.0 - low_mask

    shape = [1] * latents_hi.ndim
    for i, d in enumerate(fft_dims):
        shape[d] = low_mask.shape[i]

    low_mask = low_mask.reshape(shape)
    high_mask = high_mask.reshape(shape)

    mag_hi = torch.abs(fft_hi)
    phase_hi = torch.angle(fft_hi)

    mag_lo = torch.abs(fft_lo)
    phase_lo = torch.angle(fft_lo)

    # swap phase only
    phase_mix = phase_lo * low_mask + phase_hi * high_mask

    fft_mix = mag_hi * torch.exp(1j * phase_mix)

    # energy over 2D spatial freq bins
    power = (torch.abs(fft_mix) ** 2)
    total_energy = power.sum()
    low_energy = (power * low_mask).sum()
    high_energy = (power * high_mask).sum().clamp(min=1e-12)

    high_band_scale = torch.sqrt((total_energy - (low_energy / (gamma ** 2))) / high_energy)
    scale = (low_mask / gamma) + (high_mask * high_band_scale)

    fft_mix = fft_mix * scale
    fft_mix = torch.fft.ifftshift(fft_mix, dim=fft_dims)
    out = torch.fft.ifftn(fft_mix, dim=fft_dims, norm='ortho').real

    return out
