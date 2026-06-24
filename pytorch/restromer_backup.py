"""
Restormer: Efficient Transformer for High-Resolution Image Restoration
论文: https://arxiv.org/abs/2111.09881

适用于图像去噪、去模糊、去雨、低光照增强等恢复任务。
输入输出均为 (B, C, H, W) 的图像张量。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# 1. 基础组件
# ============================================================

class LayerNorm(nn.Module):
    """Layer Normalization for 4D tensors (B, C, H, W) — 沿通道维度做归一化"""
    def __init__(self, dim):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.bias = nn.Parameter(torch.zeros(dim))

    def forward(self, x):
        # x: (B, C, H, W) → permute → (B, H, W, C) → norm → permute back
        x = x.permute(0, 2, 3, 1).contiguous()
        x = F.layer_norm(x, (x.shape[-1],), self.weight, self.bias)
        return x.permute(0, 3, 1, 2).contiguous()


class MDTA(nn.Module):
    """
    Multi-Dconv Head Transposed Attention
    在通道维度上做自注意力，配合 3×3 深度可分离卷积增强局部上下文。
    输入/输出形状: (B, C, H, W)
    """
    def __init__(self, channels, num_heads=4):
        super().__init__()
        self.channels = channels
        self.num_heads = num_heads
        self.head_dim = channels // num_heads
        self.scale = self.head_dim ** -0.5

        # 生成 Q/K/V 的 1×1 卷积 + 3×3 逐通道卷积
        self.qkv = nn.Conv2d(channels, channels * 3, kernel_size=1, bias=False)
        self.qkv_dwconv = nn.Conv2d(
            channels * 3, channels * 3,
            kernel_size=3, padding=1, groups=channels * 3, bias=False
        )
        # 输出投影
        self.proj = nn.Conv2d(channels, channels, kernel_size=1, bias=False)

    def forward(self, x):
        B, C, H, W = x.shape

        # QKV 投影 + 深度卷积增强
        qkv = self.qkv_dwconv(self.qkv(x))          # (B, 3C, H, W)
        q, k, v = qkv.chunk(3, dim=1)               # 各 (B, C, H, W)

        # 重塑为多头格式: (B, heads, head_dim, H*W)
        q = q.reshape(B, self.num_heads, self.head_dim, H * W)
        k = k.reshape(B, self.num_heads, self.head_dim, H * W)
        v = v.reshape(B, self.num_heads, self.head_dim, H * W)

        # 转置注意力: Q @ K^T，在通道维度算注意力
        q = q * self.scale
        attn = torch.matmul(q, k.transpose(-2, -1))      # (B, heads, head_dim, head_dim)
        attn = F.softmax(attn, dim=-1)
        out = torch.matmul(attn, v)                       # (B, heads, head_dim, H*W)

        # 恢复为原始形状
        out = out.reshape(B, C, H, W)
        out = self.proj(out)
        return out


class GDFN(nn.Module):
    """
    Gated-Dconv Feed-forward Network
    使用门控机制 + 深度卷积，增强局部信息提取。
    """
    def __init__(self, channels, expansion_factor=2.66):
        super().__init__()
        hidden = int(channels * expansion_factor)

        self.dwconv1 = nn.Conv2d(hidden, hidden, kernel_size=3, padding=1, groups=hidden, bias=False)
        self.dwconv2 = nn.Conv2d(hidden, hidden, kernel_size=3, padding=1, groups=hidden, bias=False)

        self.proj_in = nn.Conv2d(channels, hidden * 2, kernel_size=1, bias=False)
        self.proj_out = nn.Conv2d(hidden, channels, kernel_size=1, bias=False)

    def forward(self, x):
        x = self.proj_in(x)                # (B, 2*hidden, H, W)
        x1, x2 = x.chunk(2, dim=1)         # 各 (B, hidden, H, W)

        # 门控：一条分支激活，另一条做线性变换后相乘
        x1 = self.dwconv1(x1)
        x2 = self.dwconv2(x2)
        x = F.gelu(x1) * x2

        x = self.proj_out(x)
        return x


class TransformerBlock(nn.Module):
    """Restormer 基础 Transformer Block: MDTA + GDFN"""
    def __init__(self, channels, num_heads=4):
        super().__init__()
        self.norm1 = LayerNorm(channels)
        self.attn = MDTA(channels, num_heads)
        self.norm2 = LayerNorm(channels)
        self.ffn = GDFN(channels)

    def forward(self, x):
        x = x + self.attn(self.norm1(x))    # 残差 + 注意力
        x = x + self.ffn(self.norm2(x))     # 残差 + 前馈
        return x


# ============================================================
# 2. Encoder / Decoder
# ============================================================

class DownSample(nn.Module):
    """下采样：卷积 stride=2 + PixelUnshuffle（可选）"""
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=2, padding=1, bias=False)

    def forward(self, x):
        return self.conv(x)


class UpSample(nn.Module):
    """上采样：PixelShuffle 或最近邻插值 + 卷积"""
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.up = nn.Sequential(
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False),
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False)
        )

    def forward(self, x):
        return self.up(x)


# ============================================================
# 3. Restormer 整体结构
# ============================================================

class Restormer(nn.Module):
    """
    Restormer 网络

    参数
    ----------
    inp_channels : int      输入通道数（RGB=3，灰度=1）
    out_channels : int      输出通道数（通常与输入相同）
    dim : int               初始特征维度
    num_blocks : list       每层的 Transformer Block 数量
    num_heads : int         注意力头数
    """
    def __init__(
        self,
        inp_channels=3,
        out_channels=3,
        dim=48,
        num_blocks=(4, 6, 6, 8),
        num_heads=4,
    ):
        super().__init__()

        # ---- 浅层特征提取 ----
        self.shallow_conv = nn.Conv2d(inp_channels, dim, kernel_size=3, padding=1, bias=False)

        # ---- Encoder ----
        self.encoder_level1 = nn.Sequential(*[TransformerBlock(dim * 1, num_heads) for _ in range(num_blocks[0])])
        self.down1 = DownSample(dim * 1, dim * 2)

        self.encoder_level2 = nn.Sequential(*[TransformerBlock(dim * 2, num_heads) for _ in range(num_blocks[1])])
        self.down2 = DownSample(dim * 2, dim * 4)

        self.encoder_level3 = nn.Sequential(*[TransformerBlock(dim * 4, num_heads) for _ in range(num_blocks[2])])
        self.down3 = DownSample(dim * 4, dim * 8)

        # ---- Bottleneck ----
        self.bottleneck = nn.Sequential(*[TransformerBlock(dim * 8, num_heads) for _ in range(num_blocks[3])])

        # ---- Decoder ----
        self.up3 = UpSample(dim * 8, dim * 4)
        self.reduce3 = nn.Conv2d(dim * 8, dim * 4, kernel_size=1, bias=False)
        self.decoder_level3 = nn.Sequential(*[TransformerBlock(dim * 4, num_heads) for _ in range(num_blocks[2])])

        self.up2 = UpSample(dim * 4, dim * 2)
        self.reduce2 = nn.Conv2d(dim * 4, dim * 2, kernel_size=1, bias=False)
        self.decoder_level2 = nn.Sequential(*[TransformerBlock(dim * 2, num_heads) for _ in range(num_blocks[1])])

        self.up1 = UpSample(dim * 2, dim * 1)
        self.reduce1 = nn.Conv2d(dim * 2, dim * 1, kernel_size=1, bias=False)
        self.decoder_level1 = nn.Sequential(*[TransformerBlock(dim * 1, num_heads) for _ in range(num_blocks[0])])

        # ---- 输出 ----
        self.output_conv = nn.Conv2d(dim, out_channels, kernel_size=3, padding=1, bias=False)

    def forward(self, x):
        # 浅层特征
        feat = self.shallow_conv(x)

        # Encoder
        enc1 = self.encoder_level1(feat)                     # (B, dim,   H,   W)
        enc2 = self.encoder_level2(self.down1(enc1))         # (B, dim*2, H/2, W/2)
        enc3 = self.encoder_level3(self.down2(enc2))         # (B, dim*4, H/4, W/4)

        # Bottleneck
        bottleneck = self.bottleneck(self.down3(enc3))       # (B, dim*8, H/8, W/8)

        # Decoder + skip connection
        dec3 = self.up3(bottleneck)                           # (B, dim*4, H/4, W/4)
        dec3 = self.reduce3(torch.cat([dec3, enc3], dim=1))  # concat → (B, dim*8) → (B, dim*4)
        dec3 = self.decoder_level3(dec3)

        dec2 = self.up2(dec3)                                 # (B, dim*2, H/2, W/2)
        dec2 = self.reduce2(torch.cat([dec2, enc2], dim=1))
        dec2 = self.decoder_level2(dec2)

        dec1 = self.up1(dec2)                                 # (B, dim, H, W)
        dec1 = self.reduce1(torch.cat([dec1, enc1], dim=1))
        dec1 = self.decoder_level1(dec1)

        # 输出
        out = self.output_conv(dec1) + x                     # 残差连接
        return out


# ============================================================
# 4. 图像退化操作（模拟真实降质）
# ============================================================

def add_gaussian_noise(images, sigma=25.0):
    """给干净图像加高斯噪声，返回 noisy + clean 对"""
    noise = torch.randn_like(images) * (sigma / 255.0)
    noisy = images + noise
    return noisy.clamp(0, 1)


# ============================================================
# 5. PSNR 评估指标
# ============================================================

def compute_psnr(pred, target):
    """计算 PSNR（峰值信噪比），值越大越好"""
    mse = F.mse_loss(pred, target, reduction='mean')
    if mse == 0:
        return float('inf')
    return 20 * torch.log10(1.0 / torch.sqrt(mse)).item()
# 逐样本 PSNR 的正确实现
# mse_per_sample = F.mse_loss(pred, target, reduction='none')
# mse_per_sample = mse_per_sample.view(pred.size(0), -1).mean(dim=1)
# psnr_per_sample = 20 * torch.log10(1.0 / torch.sqrt(mse_per_sample + 1e-10))
# return psnr_per_sample.mean().item()

# ============================================================
# 6. 硬件监控
# ============================================================

class HardwareMonitor:
    """监控 GPU 显存、利用率和 CPU/内存使用情况"""

    def __init__(self, device):
        self.device = device
        self.has_gpu = device.type == "cuda"
        if self.has_gpu:
            import pynvml
            pynvml.nvmlInit()
            self._pynvml = pynvml
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        import psutil
        self._psutil = psutil

    def snapshot(self):
        """采集当前硬件状态，返回字典"""
        info = {}

        # GPU 显存
        if self.has_gpu:
            alloc = torch.cuda.memory_allocated(self.device) / 1024 ** 3
            reserved = torch.cuda.memory_reserved(self.device) / 1024 ** 3
            info["GPU_alloc_GB"] = alloc
            info["GPU_reserved_GB"] = reserved

            # GPU 利用率
            try:
                util = self._pynvml.nvmlDeviceGetUtilizationRates(self._handle)
                info["GPU_util_%"] = util.gpu
                info["GPU_mem_util_%"] = util.memory
            except Exception:
                pass

            # GPU 温度
            try:
                info["GPU_temp_C"] = self._pynvml.nvmlDeviceGetTemperature(
                    self._handle, self._pynvml.NVML_TEMPERATURE_GPU
                )
            except Exception:
                pass

        # CPU
        info["CPU_%"] = self._psutil.cpu_percent()
        info["RAM_GB"] = self._psutil.virtual_memory().used / 1024 ** 3

        return info

    def summary(self):
        """返回一行简洁的硬件状态字符串"""
        s = self.snapshot()
        parts = []
        if s.get("GPU_alloc_GB") is not None:
            parts.append(f"GPU: {s['GPU_alloc_GB']:.2f}/{s['GPU_reserved_GB']:.2f} GB")
        if s.get("GPU_util_%") is not None:
            parts.append(f"util: {s['GPU_util_%']}%")
        if s.get("GPU_temp_C") is not None:
            parts.append(f"temp: {s['GPU_temp_C']}°C")
        parts.append(f"CPU: {s['CPU_%']}%  RAM: {s['RAM_GB']:.1f} GB")
        return " | ".join(parts)

    def close(self):
        if self.has_gpu:
            self._pynvml.nvmlShutdown()


# ============================================================
# 7. 训练入口
# ============================================================
if __name__ == "__main__":
    import time
    import torchvision
    import torchvision.transforms as transforms
    from torch.utils.data import DataLoader, random_split
    from torch.utils.tensorboard import SummaryWriter

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"设备: {device}")

    # 开启 TF32 加速（Ampere+ GPU 支持，速度更快，精度几乎无损失）
    torch.backends.cuda.matmul.allow_tf32 = True   # 矩阵乘法用 TF32
    torch.backends.cudnn.allow_tf32 = True         # 卷积用 TF32

    # ---- 数据准备 ----
    # 使用 CIFAR-10 构建合成去噪任务: 输入 = 干净图 + 高斯噪声, 目标 = 干净图
    transform = transforms.Compose([
        transforms.Resize(128),
        transforms.ToTensor(),
    ])

    full_set = torchvision.datasets.CIFAR10(
        root="dataset", train=True, download=True, transform=transform
    )

    train_size = int(0.8 * len(full_set))
    val_size = len(full_set) - train_size
    train_set, val_set = random_split(full_set, [train_size, val_size])

    batch_size = 8
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader   = DataLoader(val_set,   batch_size=batch_size, shuffle=False, drop_last=True)

    print(f"训练集: {train_size}  验证集: {val_size}  batch_size: {batch_size}")

    # ---- 模型 ----
    model = Restormer(
        inp_channels=3, out_channels=3,
        dim=32,
        num_blocks=(2, 3, 3, 4),
        num_heads=4,
    ).to(device)

    params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {params:,}")

    # ---- 优化器 & 损失 ----
    loss_fn = nn.L1Loss()                                  # L1 损失，对图像恢复比 L2 更鲁棒
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50, eta_min=1e-6)

    writer = SummaryWriter("logs_restormer")
    best_psnr = 0.0
    noise_sigma = 25.0                                     # 噪声强度

    # 硬件监控
    hw = HardwareMonitor(device)
    print(f"  初始状态: {hw.summary()}")

    # ---- 训练循环 ----
    total_step = 0
    train_start = time.time()
    for epoch in range(50):
        epoch_start = time.time()

        # ====== 训练 ======
        model.train()
        running_loss = 0.0
        for clean_imgs, _ in train_loader:
            clean_imgs = clean_imgs.to(device)
            noisy_imgs = add_gaussian_noise(clean_imgs, sigma=noise_sigma)

            restored = model(noisy_imgs)
            loss = loss_fn(restored, clean_imgs)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            writer.add_scalar("Loss/train", loss.item(), total_step)
            running_loss += loss.item()

            # 每 50 个 batch 采样一次硬件状态（训练过程中，不影响性能）
            if total_step % 50 == 0:
                hw_snap = hw.snapshot()
                if hw_snap.get("GPU_alloc_GB") is not None:
                    writer.add_scalar("Hardware/GPU_alloc_GB", hw_snap["GPU_alloc_GB"], total_step)
                if hw_snap.get("GPU_util_%") is not None:
                    writer.add_scalar("Hardware/GPU_util_%", hw_snap["GPU_util_%"], total_step)
                if hw_snap.get("GPU_temp_C") is not None:
                    writer.add_scalar("Hardware/GPU_temp_C", hw_snap["GPU_temp_C"], total_step)
                writer.add_scalar("Hardware/CPU_%", hw_snap["CPU_%"], total_step)
                writer.add_scalar("Hardware/RAM_GB", hw_snap["RAM_GB"], total_step)
                print(f"  [step {total_step:5d}] {hw.summary()}")

            total_step += 1

        avg_loss = running_loss / len(train_loader)
        scheduler.step()

        # ====== 验证 ======
        model.eval()
        val_loss, val_psnr = 0.0, 0.0
        with torch.no_grad():
            for clean_imgs, _ in val_loader:
                clean_imgs = clean_imgs.to(device)
                noisy_imgs = add_gaussian_noise(clean_imgs, sigma=noise_sigma)
                restored = model(noisy_imgs)

                val_loss += loss_fn(restored, clean_imgs).item()
                val_psnr += compute_psnr(restored, clean_imgs)

        val_loss /= len(val_loader)
        val_psnr /= len(val_loader)

        writer.add_scalar("Loss/val", val_loss, epoch)
        writer.add_scalar("PSNR/val", val_psnr, epoch)

        # ====== 保存最佳模型 ======
        if val_psnr > best_psnr:
            best_psnr = val_psnr
            torch.save(model.state_dict(), "restormer_best.pth")
            save_flag = " [保存]"
        else:
            save_flag = ""

        epoch_time = time.time() - epoch_start
        writer.add_scalar("Time/epoch_sec", epoch_time, epoch)

        # 预估剩余时间
        avg_epoch_time = (time.time() - train_start) / (epoch + 1)
        remaining_sec = avg_epoch_time * (50 - epoch - 1)
        remaining_min = remaining_sec / 60

        print(f"Epoch {epoch:2d} | train_loss: {avg_loss:.5f} | val_loss: {val_loss:.5f} | "
              f"val_psnr: {val_psnr:.2f} dB | lr: {scheduler.get_last_lr()[0]:.2e} | "
              f"耗时: {epoch_time:.1f}s | 预计剩余: {remaining_min:.1f}min{save_flag}")
        print(f"        {hw.summary()}")

        model.train()

    total_time = time.time() - train_start
    print(f"\n训练完成！最佳 PSNR: {best_psnr:.2f} dB | 总耗时: {total_time/60:.1f} 分钟")
    hw.close()
    writer.close()
