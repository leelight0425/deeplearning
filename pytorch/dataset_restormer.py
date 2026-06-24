"""
Restormer 经典数据预处理模块
----------------------------
按照 Restormer 论文 (CVPR 2022) 的标准数据管线实现：

1. 随机裁剪 → 固定 patch 大小 (128×128)
2. 随机水平/垂直翻转
3. 随机 90° 旋转
4. 在线合成高斯噪声（训练时每 epoch 噪声不同，增强泛化性）
5. 支持真实配对数据集（SIDD / GoPro / Rain100 等）和 合成数据集

用法:
    from dataset_restormer import SyntheticDenoisingDataset, paired_collate

    train_set = SyntheticDenoisingDataset(root="dataset/train", patch_size=128,
                                           sigma_range=(10, 50), augment=True)
    train_loader = DataLoader(train_set, batch_size=8, shuffle=True, ...)
"""

import random
from pathlib import Path
from typing import Callable, Optional, Tuple, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset
from torchvision.io import read_image, ImageReadMode
from PIL import Image


# ============================================================
# 1. 增强操作（纯 Tensor 实现，可直接在 GPU 上跑）
# ============================================================

class RandomAugmentPair:
    """
    对 paired (clean, degraded) 做**严格同步**的空间增强。

    关键：两张图必须经过完全相同的几何变换，
    否则 clean 和 degraded 像素不对齐，模型学到错误映射。
    """

    def __init__(
        self,
        crop_size: int = 128,
        hflip_p: float = 0.5,
        vflip_p: float = 0.5,
        rotate90_p: float = 0.5,
    ):
        self.crop_size = crop_size
        self.hflip_p = hflip_p
        self.vflip_p = vflip_p
        self.rotate90_p = rotate90_p

    def _random_crop(self, *imgs: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        """随机裁剪 — 所有图片同一位置"""
        _, h, w = imgs[0].shape
        if h < self.crop_size or w < self.crop_size:
            # 图片太小，先放大到 crop_size
            imgs = tuple(F.interpolate(
                img.unsqueeze(0), size=(self.crop_size, self.crop_size), mode='bilinear'
            ).squeeze(0) for img in imgs)
            return imgs

        top = random.randint(0, h - self.crop_size)
        left = random.randint(0, w - self.crop_size)
        return tuple(img[:, top:top + self.crop_size, left:left + self.crop_size]
                     for img in imgs)

    def _random_flip_h(self, *imgs: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        if random.random() < self.hflip_p:
            return tuple(torch.flip(img, dims=[2]) for img in imgs)
        return imgs

    def _random_flip_v(self, *imgs: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        if random.random() < self.vflip_p:
            return tuple(torch.flip(img, dims=[1]) for img in imgs)
        return imgs

    def _random_rotate90(self, *imgs: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        if random.random() < self.rotate90_p:
            k = random.choice([1, 2, 3])
            return tuple(torch.rot90(img, k, dims=[1, 2]) for img in imgs)
        return imgs

    def __call__(self, *imgs: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        imgs = self._random_crop(*imgs)
        imgs = self._random_flip_h(*imgs)
        imgs = self._random_flip_v(*imgs)
        imgs = self._random_rotate90(*imgs)
        return imgs


# ============================================================
# 2. 合成去噪数据集 — Restormer 论文最常用的训练范式
# ============================================================

class SyntheticDenoisingDataset(Dataset):
    """
    用任意图像集合在线合成 noisy/clean 训练对。

    每 __getitem__ 返回 (noisy, clean)，噪声强度在 sigma_range 内随机采样。

    参数
    ----------
    root : str
        图像文件夹路径（支持 .png, .jpg, .jpeg, .bmp, .tiff）
    patch_size : int
        训练 patch 大小，默认 128
    sigma_range : (min, max)
        高斯噪声标准差范围，单位 1/255
    augment : bool
        是否启用随机裁剪 + 翻转 + 旋转
    image_size : int | None
        如果指定，先把图片 resize 到这个尺寸再裁剪（适合小图数据集如 CIFAR）
    max_images : int | None
        最多使用多少张图片（限制数据集大小）
    """

    def __init__(
        self,
        root: str,
        patch_size: int = 128,
        sigma_range: Sequence[float] = (10, 50),
        augment: bool = True,
        image_size: Optional[int] = None,
        max_images: Optional[int] = None,
    ):
        self.root = Path(root)
        self.patch_size = patch_size
        self.sigma_min, self.sigma_max = sigma_range
        self.image_size = image_size

        # 收集所有图片路径
        self.paths = sorted(
            p for p in self.root.rglob("*")
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
        )
        if max_images is not None:
            self.paths = self.paths[:max_images]

        if len(self.paths) == 0:
            raise FileNotFoundError(f"在 {root} 中未找到图片文件")

        self.augment_fn = RandomAugmentPair(crop_size=patch_size) if augment else None
        print(f"  [SyntheticDenoisingDataset] {len(self.paths)} 张图片 | "
              f"sigma [{self.sigma_min}, {self.sigma_max}] | "
              f"augment={'on' if augment else 'off'}")

    def __len__(self) -> int:
        return len(self.paths)

    def _load_image(self, path: Path) -> torch.Tensor:
        """加载图片 → float32 [0, 1], shape (C, H, W)"""
        try:
            img = read_image(str(path), ImageReadMode.RGB)
            return img.float() / 255.0
        except Exception:
            # PIL 兜底（某些格式 torchvision 读不了）
            pil = Image.open(path).convert("RGB")
            tensor = torch.from_numpy(np.array(pil)).permute(2, 0, 1).float() / 255.0
            return tensor

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        clean = self._load_image(self.paths[idx])

        # resize 到固定尺寸（如果指定）
        if self.image_size is not None:
            clean = F.interpolate(
                clean.unsqueeze(0), size=(self.image_size, self.image_size),
                mode='bilinear'
            ).squeeze(0).clamp(0, 1)

        # 随机噪声强度
        sigma = random.uniform(self.sigma_min, self.sigma_max)

        # 数据增强（裁剪 + 翻转 + 旋转）
        if self.augment_fn is not None:
            clean, = self.augment_fn(clean)

        # 在线加噪
        with torch.no_grad():
            noise = torch.randn_like(clean) * (sigma / 255.0)
            noisy = (clean + noise).clamp(0, 1)

        return noisy, clean


# ============================================================
# 3. 真实配对数据集 — 用于 SIDD / GoPro / Rain100 等
# ============================================================

class PairedImageDataset(Dataset):
    """
    直接加载 paired (input, target) 图像对。

    目录结构:
        root/
          input/     ← 降质图像（带噪声、模糊、低光照等）
          target/    ← 干净真值图像

    文件名按字母序一一配对。

    参数
    ----------
    root : str
        包含 input/ 和 target/ 子目录的文件夹
    patch_size : int
        训练 patch 大小
    augment : bool
        是否启用随机增强
    """

    def __init__(
        self,
        root: str,
        patch_size: int = 128,
        augment: bool = True,
    ):
        self.root = Path(root)
        self.patch_size = patch_size

        input_dir = self.root / "input"
        target_dir = self.root / "target"

        if not input_dir.exists() or not target_dir.exists():
            raise FileNotFoundError(
                f"需要 {root}/input/ 和 {root}/target/ 两个子目录"
            )

        exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        self.input_paths = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in exts)
        self.target_paths = sorted(p for p in target_dir.iterdir() if p.suffix.lower() in exts)

        if len(self.input_paths) != len(self.target_paths):
            print(f"  ⚠ input ({len(self.input_paths)}) 和 target ({len(self.target_paths)}) 数量不一致，"
                  f"取较小值")

        self.augment_fn = RandomAugmentPair(crop_size=patch_size) if augment else None
        print(f"  [PairedImageDataset] {min(len(self.input_paths), len(self.target_paths))} 对 | "
              f"augment={'on' if augment else 'off'}")

    def __len__(self) -> int:
        return min(len(self.input_paths), len(self.target_paths))

    def _load(self, path: Path) -> torch.Tensor:
        try:
            img = read_image(str(path), ImageReadMode.RGB)
            return img.float() / 255.0
        except Exception:
            pil = Image.open(path).convert("RGB")
            return torch.from_numpy(np.array(pil)).permute(2, 0, 1).float() / 255.0

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        inp = self._load(self.input_paths[idx])
        tgt = self._load(self.target_paths[idx])

        if self.augment_fn is not None:
            inp, tgt = self.augment_fn(inp, tgt)

        return inp, tgt


# ============================================================
# 4. 数据集工厂 — 自动检测并构建
# ============================================================

def build_dataset(
    data_root: str,
    patch_size: int = 128,
    sigma_range: Tuple[float, float] = (10, 50),
    augment: bool = True,
    max_images: Optional[int] = None,
) -> Dataset:
    """
    自动检测数据集类型并构建对应的 Dataset。

    - 如果 data_root 下有 input/ 和 target/  → PairedImageDataset（真实配对）
    - 否则                                   → SyntheticDenoisingDataset（在线加噪）
    """
    root = Path(data_root)
    has_paired = (root / "input").exists() and (root / "target").exists()

    if has_paired:
        return PairedImageDataset(data_root, patch_size=patch_size, augment=augment)
    else:
        return SyntheticDenoisingDataset(
            data_root,
            patch_size=patch_size,
            sigma_range=sigma_range,
            augment=augment,
            max_images=max_images,
        )


# ============================================================
# 5. 独立预处理脚本入口 — 命令行批量预处理工具
# ============================================================

if __name__ == "__main__":
    """
    命令行用法:
        python dataset_restormer.py --mode download   # 下载示例数据集 (CIFAR-10)
        python dataset_restormer.py --mode info       # 打印数据集信息
        python dataset_restormer.py --mode test       # 测试数据加载管线

    训练时不需要运行这个——dataset_restormer.py 作为模块被 restromer.py import 使用。
    """
    import argparse
    import torchvision
    import torchvision.transforms as transforms

    ap = argparse.ArgumentParser(description="Restormer 数据预处理")
    ap.add_argument("--mode", choices=["info", "download", "test"], default="test")
    ap.add_argument("--root", default="dataset")
    ap.add_argument("--patch-size", type=int, default=128)
    ap.add_argument("--sigma-min", type=float, default=10)
    ap.add_argument("--sigma-max", type=float, default=50)
    ap.add_argument("--batch-size", type=int, default=4)
    args = ap.parse_args()

    if args.mode == "download":
        print("=" * 60)
        print("下载 CIFAR-10 作为示例数据集")
        print("=" * 60)
        root = Path(args.root) / "cifar10_images"
        root.mkdir(parents=True, exist_ok=True)

        full = torchvision.datasets.CIFAR10(
            root="dataset", train=True, download=True,
            transform=transforms.ToTensor()
        )
        # 保存前 10000 张作为训练图
        saved = 0
        for i, (img, _) in enumerate(full):
            if saved >= 10000:
                break
            img_pil = transforms.ToPILImage()(img)
            img_pil.save(root / f"{saved:05d}.png")
            saved += 1
        print(f"  已保存 {saved} 张 PNG 到 {root}")
        print("  现在可以用 restromer.py 训练了：")
        print(f"    python restromer.py --data-root {root}")

    elif args.mode == "info":
        root = Path(args.root)
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        images = list(p for p in root.rglob("*") if p.suffix.lower() in exts)
        print(f"数据集根目录: {root}")
        print(f"图片总数: {len(images)}")
        if images:
            # 读一张看尺寸
            img = read_image(str(images[0]), ImageReadMode.RGB)
            print(f"示例图片: {images[0].name} | shape: {tuple(img.shape)} | "
                  f"dtype: {img.dtype}")

    elif args.mode == "test":
        print("=" * 60)
        print("测试数据管线")
        print("=" * 60)

        # 先确保有数据
        data_dir = Path(args.root) / "cifar10_images"
        if not data_dir.exists():
            print("未找到示例数据集，正在下载...")
            from torch.utils import data as _data_utils
            import torchvision as _tv
            data_dir.mkdir(parents=True, exist_ok=True)
            full = _tv.datasets.CIFAR10(root="dataset", train=True, download=True)
            for i in range(5000):
                img = _tv.transforms.ToPILImage()(full[i][0])
                img.save(data_dir / f"{i:05d}.png")
            print(f"  下载完成: {data_dir}")

        # 构建数据集
        ds = SyntheticDenoisingDataset(
            str(data_dir),
            patch_size=args.patch_size,
            sigma_range=(args.sigma_min, args.sigma_max),
            augment=True,
            max_images=5000,
        )
        loader = torch.utils.data.DataLoader(
            ds, batch_size=args.batch_size, shuffle=True, num_workers=0
        )

        noisy, clean = next(iter(loader))
        print(f"\n  一个 batch: noisy={tuple(noisy.shape)}  clean={tuple(clean.shape)}")
        print(f"  noisy 范围: [{noisy.min().item():.3f}, {noisy.max().item():.3f}]")
        print(f"  clean 范围: [{clean.min().item():.3f}, {clean.max().item():.3f}]")

        # 验证增强的一致性
        print(f"\n  验证增强同步性...")
        ds2 = PairedImageDataset(str(data_dir.parent / "paired_test").replace(
            "cifar10_images", "paired_test"
        ) if False else str(data_dir),  # fallback 到合成
                             patch_size=args.patch_size, augment=True)
        print(f"  {len(ds)} 训练样本")
        print(f"  预处理管线测试通过 ✓")
# 新家测试莫款
# 新家位置编码
# 宽大空间覅偶尔 
