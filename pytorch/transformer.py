"""
Vanilla Transformer — "Attention Is All You Need" (Vaswani et al., 2017)

纯 PyTorch 实现，带详细注释。支持:
  - 文本分类 / 序列到序列 (翻译、摘要)
  - 断点续训
  - TensorBoard 可视化
"""

import math
import os as _os
import torch
import torch.nn as nn
import torch.nn.functional as F


# ================================================================
# 1. 位置编码 — 正弦/余弦
# ================================================================

class PositionalEncoding(nn.Module):
    """正弦-余弦位置编码 (Sinusoidal Positional Encoding)"""
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # (max_len, d_model)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(max_len, dtype=torch.float).unsqueeze(1)   # (max_len, 1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float)
            * (-math.log(10000.0) / d_model)
        )                                                                  # (d_model // 2,)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(1)  # (max_len, 1, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x):
        # x: (seq_len, batch, d_model)
        return self.dropout(x + self.pe[: x.size(0)])


# ================================================================
# 2. 注意力机制
# ================================================================

class MultiHeadAttention(nn.Module):
    """
    缩放点积多头注意力
    """
    def __init__(self, d_model: int, nhead: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % nhead == 0
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        self.scale = math.sqrt(self.head_dim)

        self.w_q = nn.Linear(d_model, d_model, bias=False)
        self.w_k = nn.Linear(d_model, d_model, bias=False)
        self.w_v = nn.Linear(d_model, d_model, bias=False)
        self.w_o = nn.Linear(d_model, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)
 
    def forward(self, query, key, value, mask=None):
        """
        query, key, value: (seq_len, batch, d_model)
        mask: True=遮挡. 支持 (B, S) padding mask 或 (T, T) causal mask.
        """
        T_q, B, _ = query.shape
        T_k = key.shape[0]

        def project_and_reshape(x, w):
            out = w(x).reshape(-1, B, self.nhead, self.head_dim)
            return out.permute(1, 2, 0, 3).reshape(B * self.nhead, -1, self.head_dim)

        Q = project_and_reshape(query, self.w_q)   # (B*nh, T_q, hd)
        K = project_and_reshape(key,   self.w_k)   # (B*nh, T_k, hd)
        V = project_and_reshape(value, self.w_v)   # (B*nh, T_k, hd)

        attn_scores = torch.bmm(Q, K.transpose(1, 2)) / self.scale   # (B*nh, T_q, T_k)

        if mask is not None:
            # 统一到可 broadcast 的 3D 形状
            if mask.dim() == 2 and mask.shape[0] != mask.shape[1]:
                # (B, S) padding mask → 作用在 key 维度 (dim=-1)
                # (B, S) → (B, 1, S) → (B*nh, 1, S)
                mask = mask.unsqueeze(1).expand(B, self.nhead, T_k)
                mask = mask.reshape(B * self.nhead, 1, T_k)
            elif mask.dim() == 2:
                # (T, T) causal → 每个 sample 共享
                mask = mask.unsqueeze(0).expand(B * self.nhead, -1, -1)
            else:
                # (B, T_q, T_k) → add head dim
                mask = mask.unsqueeze(1).expand(B, self.nhead, T_q, T_k)
                mask = mask.reshape(B * self.nhead, T_q, T_k)
            attn_scores = attn_scores.masked_fill(mask, float("-inf"))

        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        out = torch.bmm(attn_weights, V)

        out = out.reshape(B, self.nhead, T_q, self.head_dim)
        out = out.permute(0, 2, 1, 3).reshape(T_q, B, self.d_model)
        return self.w_o(out)


# ================================================================
# 3. 前馈网络
# ================================================================

class FeedForward(nn.Module):
    """Position-wise Feed-Forward Network"""
    def __init__(self, d_model: int, d_ff: int = 2048, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


# ================================================================
# 4. Encoder / Decoder Layer
# ================================================================

class EncoderLayer(nn.Module):
    def __init__(self, d_model: int, nhead: int, d_ff: int = 2048, dropout: float = 0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, nhead, dropout)
        self.ffn = FeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, src_mask=None):
        # Self-Attention + Residual + Norm
        x = self.norm1(x + self.dropout(self.self_attn(x, x, x, src_mask)))
        # FFN + Residual + Norm
        x = self.norm2(x + self.ffn(x))
        return x


class DecoderLayer(nn.Module):
    def __init__(self, d_model: int, nhead: int, d_ff: int = 2048, dropout: float = 0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, nhead, dropout)
        self.cross_attn = MultiHeadAttention(d_model, nhead, dropout)
        self.ffn = FeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, memory, src_mask=None, tgt_mask=None):
        # Masked Self-Attention
        x = self.norm1(x + self.dropout(self.self_attn(x, x, x, tgt_mask)))
        # Cross-Attention (Q=decoder, K/V=encoder output)
        x = self.norm2(x + self.dropout(self.cross_attn(x, memory, memory, src_mask)))
        # FFN
        x = self.norm3(x + self.ffn(x))
        return x


# ================================================================
# 5. Transformer 整体结构
# ================================================================

class Transformer(nn.Module):
    """
    经典 Transformer 编码器-解码器

    参数
    ----------
    vocab_size : int      词表大小
    d_model : int         模型维度 (默认 512)
    nhead : int           注意力头数 (默认 8)
    num_encoder_layers : int  编码器层数 (默认 6)
    num_decoder_layers : int  解码器层数 (默认 6)
    d_ff : int            前馈网络隐藏维度 (默认 2048)
    max_len : int         最大序列长度
    dropout : float       Dropout 概率
    """
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 512,
        nhead: int = 8,
        num_encoder_layers: int = 6,
        num_decoder_layers: int = 6,
        d_ff: int = 2048,
        max_len: int = 5000,
        dropout: float = 0.1,
        pad_idx: int = 0,
    ):
        super().__init__()
        self.d_model = d_model
        self.pad_idx = pad_idx

        # Embedding
        self.src_embed = nn.Embedding(vocab_size, d_model, padding_idx=pad_idx)
        self.tgt_embed = nn.Embedding(vocab_size, d_model, padding_idx=pad_idx)
        self.scale_embed = math.sqrt(d_model)

        # Positional Encoding (共享)
        self.pos_encoder = PositionalEncoding(d_model, max_len, dropout)

        # Encoder / Decoder stacks
        self.encoder_layers = nn.ModuleList([
            EncoderLayer(d_model, nhead, d_ff, dropout)
            for _ in range(num_encoder_layers)
        ])
        self.decoder_layers = nn.ModuleList([
            DecoderLayer(d_model, nhead, d_ff, dropout)
            for _ in range(num_decoder_layers)
        ])

        # 输出投影
        self.output_proj = nn.Linear(d_model, vocab_size)

        # 初始化
        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def _make_src_mask(self, src):
        """源序列 padding mask — True = 遮挡"""
        # src: (seq_len, batch) → mask: (batch, 1, 1, seq_len)
        return (src == self.pad_idx).transpose(0, 1)  # (batch, seq_len)

    def _make_tgt_mask(self, tgt):
        """目标序列因果 mask (causal) + padding mask"""
        T = tgt.shape[0]
        # 下三角 causal mask
        causal = torch.triu(torch.ones(T, T, device=tgt.device), diagonal=1).bool()
        return causal  # (T, T), True=遮挡

    def encode(self, src, src_mask=None):
        """编码器前向传播"""
        x = self.pos_encoder(self.src_embed(src) * self.scale_embed)
        for layer in self.encoder_layers:
            x = layer(x, src_mask)
        return x  # memory

    def decode(self, tgt, memory, src_mask=None, tgt_mask=None):
        """解码器前向传播"""
        x = self.pos_encoder(self.tgt_embed(tgt) * self.scale_embed)
        for layer in self.decoder_layers:
            x = layer(x, memory, src_mask, tgt_mask)
        return x

    def forward(self, src, tgt, src_mask=None, tgt_mask=None):
        """
        src: (src_len, batch)  源序列 token IDs
        tgt: (tgt_len, batch)  目标序列 token IDs (训练时右移一位, 预测前一位置)
        """
        if src_mask is None:
            src_mask = self._make_src_mask(src)
        if tgt_mask is None:
            tgt_mask = self._make_tgt_mask(tgt)

        memory = self.encode(src, src_mask)
        output = self.decode(tgt, memory, src_mask, tgt_mask)
        return self.output_proj(output)  # (tgt_len, batch, vocab_size)

    @torch.no_grad()
    def generate(self, src, start_token: int, end_token: int, max_len: int = 100):
        """
        自回归生成

        参数
        ----------
        src : (src_len, 1)  源序列 (单样本, batch=1)
        start_token : int   起始符 ID (如 <bos>)
        end_token : int     结束符 ID (如 <eos>)
        max_len : int       最大生成长度
        """
        self.eval()
        src_mask = self._make_src_mask(src)

        memory = self.encode(src, src_mask)
        generated = [start_token]

        for _ in range(max_len - 1):
            tgt = torch.tensor(generated, device=src.device).unsqueeze(1)  # (len, 1)
            tgt_mask = self._make_tgt_mask(tgt)

            out = self.decode(tgt, memory, src_mask, tgt_mask)
            logits = self.output_proj(out)                     # (len, 1, vocab)
            next_token = logits[-1, 0, :].argmax(dim=-1).item()  # greedy
            generated.append(next_token)
            if next_token == end_token:
                break

        return generated


# ================================================================
# 6. Mask 生成工具
# ================================================================

def generate_square_subsequent_mask(sz: int, device="cpu") -> torch.Tensor:
    """生成因果 mask — True = 不可见"""
    return torch.triu(torch.ones(sz, sz, device=device), diagonal=1).bool()


def create_padding_mask(seq: torch.Tensor, pad_idx: int = 0) -> torch.Tensor:
    """padding mask — (batch, seq_len), True = 遮挡"""
    return (seq == pad_idx).transpose(0, 1)


# ================================================================
# 7. 训练入口
# ================================================================
if __name__ == "__main__":
    import time
    import argparse
    from torch.utils.data import DataLoader, TensorDataset
    from torch.utils.tensorboard import SummaryWriter

    # ---- 参数 ----
    ap = argparse.ArgumentParser(description="Vanilla Transformer 训练")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--d-model", type=int, default=256)
    ap.add_argument("--nhead", type=int, default=4)
    ap.add_argument("--num-layers", type=int, default=3)
    ap.add_argument("--d-ff", type=int, default=512)
    ap.add_argument("--dropout", type=float, default=0.1)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"设备: {device}")

    # ---- 合成数据: 学习 "反转序列" 任务 ----
    # 这是一个经典的 seq2seq 验证任务: 输入 [1,2,3,4,5] → 输出 [5,4,3,2,1]
    VOCAB_SIZE = 128
    PAD, BOS, EOS = 0, 1, 2
    SEQ_LEN = 10

    def make_data(num_samples=5000):
        """生成随机序列对 (src → reversed tgt)"""
        src = torch.randint(3, VOCAB_SIZE, (num_samples, SEQ_LEN))
        tgt = torch.flip(src, dims=[1])  # 反转

        # 添加 BOS/EOS
        bos = torch.full((num_samples, 1), BOS, dtype=torch.long)
        eos = torch.full((num_samples, 1), EOS, dtype=torch.long)
        tgt_in = torch.cat([bos, tgt], dim=1)          # 解码器输入
        tgt_out = torch.cat([tgt, eos], dim=1)          # 解码器目标

        return src, tgt_in, tgt_out

    print(f"生成合成数据: 反转序列任务 (vocab={VOCAB_SIZE}, seq_len={SEQ_LEN})")
    src_train, tgt_in_train, tgt_out_train = make_data(5000)
    src_val, tgt_in_val, tgt_out_val = make_data(500)

    train_loader = DataLoader(
        TensorDataset(src_train, tgt_in_train, tgt_out_train),
        batch_size=args.batch_size, shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(src_val, tgt_in_val, tgt_out_val),
        batch_size=args.batch_size, shuffle=False,
    )

    # ---- 模型 ----
    model = Transformer(
        vocab_size=VOCAB_SIZE,
        d_model=args.d_model,
        nhead=args.nhead,
        num_encoder_layers=args.num_layers,
        num_decoder_layers=args.num_layers,
        d_ff=args.d_ff,
        dropout=args.dropout,
        max_len=SEQ_LEN + 2,
        pad_idx=PAD,
    ).to(device)

    params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {params:,}")

    # ---- 优化器 ----
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.98))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2
    )

    # ---- 断点续训 ----
    CKPT = "transformer_checkpoint.pt"
    start_epoch, best_loss = 0, float("inf")

    if _os.path.exists(CKPT):
        print(f"\n>>> 恢复断点: {CKPT}")
        ck = torch.load(CKPT, map_location=device, weights_only=False)
        model.load_state_dict(ck["model"])
        optimizer.load_state_dict(ck["optimizer"])
        start_epoch = ck["epoch"] + 1
        best_loss = ck["best_loss"]
        print(f"  已恢复: epoch={start_epoch}  best_loss={best_loss:.4f}\n")

    writer = SummaryWriter("logs_transformer")

    # ---- 训练循环 ----
    train_start = time.time()
    for epoch in range(start_epoch, args.epochs):
        model.train()
        total_loss, total_tokens = 0.0, 0

        for src, tgt_in, tgt_out in train_loader:
            src = src.transpose(0, 1).to(device)          # (seq_len, batch)
            tgt_in = tgt_in.transpose(0, 1).to(device)
            tgt_out = tgt_out.transpose(0, 1).to(device)  # (tgt_len, batch)

            pred = model(src, tgt_in)                     # (tgt_len, batch, vocab)
            loss = loss_fn(
                pred.reshape(-1, VOCAB_SIZE),
                tgt_out.reshape(-1)
            )

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            n_tokens = (tgt_out != PAD).sum().item()
            total_loss += loss.item() * n_tokens
            total_tokens += n_tokens

        avg_train_loss = total_loss / total_tokens

        # ---- 验证 ----
        model.eval()
        val_loss, val_tokens = 0.0, 0
        with torch.no_grad():
            for src, tgt_in, tgt_out in val_loader:
                src = src.transpose(0, 1).to(device)
                tgt_in = tgt_in.transpose(0, 1).to(device)
                tgt_out = tgt_out.transpose(0, 1).to(device)

                pred = model(src, tgt_in)
                loss = loss_fn(pred.reshape(-1, VOCAB_SIZE), tgt_out.reshape(-1))
                n_tok = (tgt_out != PAD).sum().item()
                val_loss += loss.item() * n_tok
                val_tokens += n_tok

        avg_val_loss = val_loss / val_tokens
        scheduler.step(avg_val_loss)

        # ---- 保存断点 ----
        torch.save({
            "epoch": epoch,
            "best_loss": best_loss,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
        }, CKPT)

        if avg_val_loss < best_loss:
            best_loss = avg_val_loss
            torch.save(model.state_dict(), "transformer_best.pth")
            flag = " [保存]"
        else:
            flag = ""

        epoch_t = time.time() - (train_start if epoch == start_epoch else 0)
        # 简单估时
        elapsed = time.time() - train_start
        eta = (elapsed / (epoch - start_epoch + 1)) * (args.epochs - epoch - 1) / 60

        writer.add_scalar("Loss/train", avg_train_loss, epoch)
        writer.add_scalar("Loss/val",   avg_val_loss,   epoch)

        print(f"Epoch {epoch:2d} | train_loss: {avg_train_loss:.4f} | "
              f"val_loss: {avg_val_loss:.4f} | lr: {optimizer.param_groups[0]['lr']:.2e} | "
              f"预计剩余: {eta:.1f}min{flag}")

        # ---- 每 5 个 epoch 做一次生成测试 ----
        if epoch % 5 == 0 or epoch == start_epoch:
            test_src = torch.randint(3, VOCAB_SIZE, (SEQ_LEN, 1), device=device)
            result = model.generate(test_src, BOS, EOS, max_len=SEQ_LEN + 5)
            print(f"  测试生成 | 输入: {test_src.squeeze(1).tolist()}")
            print(f"           | 输出: {result}")

    # ---- 最终测试 ----
    print(f"\n{'='*60}")
    print("最终生成测试:")
    test_src = torch.randint(3, VOCAB_SIZE, (SEQ_LEN, 1), device=device)
    result = model.generate(test_src, BOS, EOS, max_len=SEQ_LEN + 5)
    print(f"  输入: {test_src.squeeze(1).tolist()}")
    print(f"  输出: {result}")
    print(f"  期望: 反转序列 + {EOS}")
    print(f"  最佳 val_loss: {best_loss:.4f}")
    writer.close()
