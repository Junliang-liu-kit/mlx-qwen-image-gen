# 生图脚本参考（scripts/mlx_image_gen.py）

自包含脚本，仅依赖 Python 标准库（`urllib` / `json` / `base64` / `argparse`），
不依赖任何第三方包，也不需要宿主项目有 `pyproject.toml`。可直接 `python3` 运行。

## 调用方式

```bash
cd <任意工作目录>
python3 <skill>/scripts/mlx_image_gen.py -p "<英文提示词>" [参数]
```

- 进度条写在 **stderr**，成功时 **stdout** 打印 `图片已保存到：<路径>`。
- 退出码：成功 `0`，失败 `1`（错误信息在 stderr）。
- 输出目录不存在时会自动创建。

## 参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-p` / `--prompt` | 必填 | 提示词 |
| `--url` | `http://127.0.0.1:11234/v1/images/generations` | 接口地址 |
| `--model` | `ddalcu/Qwen-Image-2.1-MLX-Serve-4bit` | 模型 id |
| `--size` | `720x720` | 画布尺寸 `WxH`，**宽高须为 16 的倍数** |
| `--steps` | `30` | 采样步数 |
| `--seed` | `42` | 随机种子 |
| `--transparent` | 关闭 | 输出 RGBA PNG，仅 Qwen-Image-2.1 支持 |
| `--output` | `output/mlx_image_gen_<YYYYMMDDHHMM>.png` | 保存路径 |
| `--timeout` | `600` | 请求超时秒数 |

## 两个容易踩的坑

1. **默认文件名只精确到分钟**。同一分钟内生成多张会互相覆盖，批量时必须显式传互不相同的 `--output`。
2. **非 16 倍数尺寸会被服务端向上对齐**。实测请求 `712x712` 实际得到 `720x720`，所以直接给 16 的倍数。

## 耗时（Apple M4 / 24 GB，Qwen-Image-2.1 4bit 实测）

单张耗时 ≈ **步数 × 每步秒数**；每步秒数与像素量大致成正比，固定开销很小。

| 尺寸 | 每步 | 常用档位单张预算 |
|---|---:|---:|
| 512x512 | ~10 s | 512x512 / 12 步 → **2 分钟** |
| 720x720 | ~17~21 s | 720x720 / 30 步（默认）→ **8~9 分钟** |
| 1024x1024 | ~40 s | 1024x1024 / 30 步 → **约 20 分钟**（外推） |

换机器需重测；服务启动后第一张会更慢。客户端超时中断不会阻塞服务端，重试是安全的。

## 报错对照

| 现象 | 含义 |
|---|---|
| HTTP 400 | 参数不合法，或对非 Qwen-Image-2.1 模型使用了 `transparent: true` |
| HTTP 404 | 模型 id 不存在 |
| HTTP 502 | 本机 VPN / 反向代理拦截了本地请求 |
| HTTP 503 | 显存不足或模型未加载（常见于 OOM） |
| HTTP 413 | 请求体超过 512 MB |
| `无法连接接口` | 服务未启动 |
| 流结束但没有 complete 事件 | 服务端中途异常，看 stderr 原始响应 |

## 未暴露的接口能力

脚本只暴露上表参数。底层接口还支持 `cfg_scale` / `negative_prompt` / `lora_paths` + `lora_scales`
（最多 8 个堆叠）/ `image` + `mode: "variation"` + `strength`（图生图）/ `width` + `height`。
需要时按 [mlx-serve-api.md](mlx-serve-api.md) 扩展 `build_payload()`。
