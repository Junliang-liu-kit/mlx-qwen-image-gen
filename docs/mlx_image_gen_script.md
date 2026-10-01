# MLX 本地图像生成脚本（src/mlx_image_gen.py）

面向 mlx-serve 的本地生图命令行脚本，封装 `POST /v1/images/generations` 的 SSE 流式调用，
在终端展示进度条，并把结果 PNG 落盘。

- 脚本路径：`src/mlx_image_gen.py`
- 依赖：仅 Python 标准库（`urllib` / `json` / `base64`），无需额外安装
- 接口细节依据：[MLXServe_API_docs.md](MLXServe_API_docs.md)

---

## 1. 前置条件

1. 本地 mlx-serve 已启动，图像模型已加载：

   ```bash
   curl -s http://127.0.0.1:11234/v1/models
   ```

2. 默认模型为 `ddalcu/Qwen-Image-2.1-MLX-Serve-4bit`，`capabilities` 需包含 `image`。
   换模型时用 `--model` 覆盖，同时注意下面的 `--transparent` 限制。

---

## 2. 快速使用

```bash
# 默认 720x720、30 步、seed 42，自动按时间戳命名到 output/mlx_image_gen_<YYYYMMDDHHMM>.png
uv run python src/mlx_image_gen.py -p "a red apple on a wooden table, studio light"

# 指定输出路径
uv run python src/mlx_image_gen.py -p "a futuristic router product poster" \
    --output output/router.png

# 生成带透明通道的贴纸
uv run python src/mlx_image_gen.py \
    -p "a cute cartoon dragon sticker, transparent background" \
    --transparent --output output/dragon.png
```

终端进度输出示例（写到 stderr）：

```
Encoding prompt  [----------------------------] 0/4
Generating       [=======---------------------] 1/4
Generating       [============================] 4/4
Decoding image   [============================] 4/4
图片已保存到：output/dragon.png
```

---

## 3. 参数说明

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-p` / `--prompt` | 必填 | 图片描述（提示词） |
| `--url` | `http://127.0.0.1:11234/v1/images/generations` | 图片生成接口地址 |
| `--model` | `ddalcu/Qwen-Image-2.1-MLX-Serve-4bit` | 模型名称 |
| `--size` | `720x720` | 图片尺寸，格式 `WxH`（建议用 16 的倍数） |
| `--steps` | `30` | 采样 / 去噪步数 |
| `--seed` | `42` | 随机种子，便于复现 |
| `--transparent` | 关闭 | 输出带 alpha 通道的 PNG，仅 Qwen-Image-2.1 支持 |
| `--output` | `output/mlx_image_gen_<YYYYMMDDHHMM>.png` | 保存路径；不传时按分钟级时间戳自动命名以防覆盖，父目录不存在时自动创建 |
| `--timeout` | `600` | 请求超时秒数 |

退出码：成功 `0`，失败 `1`（错误信息打印到 stderr）。

---

## 4. 内部实现要点

| 环节 | 做法 |
|---|---|
| 请求体 | `build_payload()` 固定带 `stream: true`，以便拿到进度事件 |
| 默认命名 | `parse_args()` 在未传 `--output` 时用 `datetime.now()` 生成分钟级时间戳文件名 |
| 流解析 | `consume_stream()` 逐行读取 SSE，只处理 `data:` 行，跳过空行与 `: ping` 心跳 |
| 进度条 | `render_progress()` 用 `stage / step / total` 在 stderr 原地刷新单行进度条 |
| 取图 | 从 `complete` 事件取 `data[0].b64_json`，base64 解码后写入文件 |
| 错误处理 | HTTP 错误、连接失败、`error` 事件、流结束仍无 `complete`、字段缺失，统一转成 `RuntimeError` |

SSE 事件形态（实测）：

```
data: {"type":"progress","stage":"Encoding prompt","step":0,"total":30}
data: {"type":"progress","stage":"Generating","step":1,"total":30}
data: {"type":"progress","stage":"Decoding image","step":30,"total":30}
data: {"type":"complete","data":[{"b64_json":"iVBORw0KGgo..."}]}
```

---

## 5. 实测记录与注意事项

1. **默认尺寸 720x720 是 16 的倍数**
   服务端会把画布向上对齐到 16 的倍数（实测请求 `712x712` 实际返回 720x720），
   因此默认值直接取 720，避免二次对齐；若想精确控制尺寸，也请传 16 的倍数。

2. **默认文件名是分钟级时间戳，同一分钟内多次生成会互相覆盖**
   默认命名形如 `mlx_image_gen_202610012216.png`（精确到分钟）。
   若需要连续批量生成不覆盖，请显式传 `--output` 或串行等待跨分钟。

2. **`--transparent` 确实生效，但需要提示词配合**
   实测同一提示词下：不带该参数时 PNG color type 为 `2`（RGB），带 `--transparent` 时为 `6`（RGBA）。
   该参数只是保留模型输出的透明通道，不会自动抠图，提示词里要明确写出透明背景。

3. **`--transparent` 只适用于 Qwen-Image-2.1**
   其他图像后端收到 `transparent: true` 会返回 HTTP 400。

4. **HTTP 502 不一定代表服务挂了**
   如果本机开了 VPN / 反向代理，本地请求也可能被代理拦成 502，关闭后重试即可（详见 API 文档第 6 节）。

---

## 6. 性能实测

测试环境：Apple M4（10 核 CPU）/ 24 GB 统一内存 / macOS，模型 `ddalcu/Qwen-Image-2.1-MLX-Serve-4bit`（4bit，约 10.7 GB 常驻）。

| 尺寸 | 步数 | 实测单张耗时 | 平均每步 |
|---|---:|---:|---:|
| 512x512 | 3 | 29 s | ~10 s |
| 512x512 | 12 | 120 s | ~10 s |
| 720x720 | 5 | 103 s | ~21 s |
| 720x720 | 30 | 504 s | ~17 s |
| 1024x1024 | 5 | 200 s | ~40 s |

规律：**单张耗时 ≈ 步数 × 每步秒数**，而每步秒数与像素量大致成正比（512² → 10 s，720² → 17~21 s，1024² → 40 s）。固定开销很小，所以降步数和降尺寸都能线性提速。

常用档位的预算：

| 档位 | 参数 | 单张预算 | 来源 |
|---|---|---:|---|
| 默认 | 720x720 / 30 步 | **8~9 分钟** | 实测 504 s |
| 草稿 | 512x512 / 12 步 | **2 分钟** | 实测 120 s |
| 高质量 | 1024x1024 / 30 步 | **约 20 分钟** | 按 40 s/步 外推 |

两个额外验证结果：

- 两张 512x512 / 3 步 串行生成实测 29 s + 30 s，进度与耗时不受串行影响。
- 客户端主动断开（`curl -m 3`）后，服务端立即回到 `state: ready`，紧接着的小请求 37 s 正常完成 —— **超时中断不会阻塞后续请求，重试是安全的**。

注意：以上数字强依赖机器与内存带宽，换设备需重测；模型首次加载（服务启动后第一张）会更慢。

---

## 7. 后续可扩展方向

以下字段 API 支持但脚本暂未暴露，需要时再加：

- `cfg_scale` / `negative_prompt`：控制引导强度与负向提示词
- `lora_paths` + `lora_scales`：最多 8 个堆叠 LoRA
- `image` + `mode: "variation"` + `strength`：图生图 / 变体生成
- `width` + `height`：作为 `size` 的替代写法
