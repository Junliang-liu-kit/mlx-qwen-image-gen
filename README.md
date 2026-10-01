# 基于 MLXServe 的 Qwen Image 2.1 本地图像生成

在 Apple Silicon Mac 上通过 [mlx-serve](https://github.com/ml-explore/mlx-serve) 本地部署 Qwen-Image-2.1（4bit 量化），可以用skill或直接用命令行脚本调用其 SSE 流式图像生成接口，实时展示进度并保存 PNG。

## 前置条件

1. 本地已启动 mlx-serve 并加载图像模型，默认监听 `http://127.0.0.1:11234`：

   ```bash
   curl -s http://127.0.0.1:11234/v1/models
   ```

2. 默认模型 `ddalcu/Qwen-Image-2.1-MLX-Serve-4bit`，`capabilities` 需包含 `image`。
3. Python 3.12+，使用 [uv](https://docs.astral.sh/uv/) 管理依赖（`.venv` 已初始化）。核心脚本仅依赖 Python 标准库，无需额外安装。

## 快速使用

```bash
# 默认 720x720 / 30 步 / seed 42，自动按时间戳命名到 output/
uv run python src/mlx_image_gen.py -p "a red apple on a wooden table, studio light"

# 指定输出路径
uv run python src/mlx_image_gen.py -p "a futuristic router product poster" \
    --output output/router.png

# 生成带透明通道的贴纸（仅 Qwen-Image-2.1 支持）
uv run python src/mlx_image_gen.py \
    -p "a cute cartoon dragon sticker, transparent background" \
    --transparent --output output/dragon.png
```

终端会在 stderr 实时刷新进度条，成功后打印保存路径。完整参数说明见 [docs/mlx_image_gen_script.md](docs/mlx_image_gen_script.md)。

## 项目结构

```
llm_image_gen/
├── src/
│   └── mlx_image_gen.py        # 核心脚本：SSE 流式生图 + 进度条 + 落盘
├── test/
│   └── mlx_image_gen.py        # 早期非流式接口测试脚本
├── docs/
│   ├── Introduction of Qwen Image 2.1.md   # 模型发布介绍
│   ├── MLXServe_API_docs.md               # mlx-serve 图像接口文档
│   ├── mlx_image_gen_script.md            # 核心脚本完整文档（参数/实现/性能实测）
│   ├── AGENTS.override.md                 # docs 目录结构索引
│   └── temp/                              # 临时笔记（gitignore）
├── config/                     # 配置文件（预留，当前为空）
├── data/                       # 测试数据（提示词等）
├── logs/                       # 日志输出（预留，当前为空）
├── output/                     # 生成图片输出目录
├── .claude/ .codex/ .pi/       # 各 AI 助手本地配置
├── .venv/                      # uv 虚拟环境
├── pyproject.toml              # 项目配置（仍为模板状态，待更新）
├── AGENTS.md                   # AI 代理行为规范
└── README.md
```

## 文档索引

| 文档 | 内容 |
|---|---|
| [docs/mlx_image_gen_script.md](docs/mlx_image_gen_script.md) | 核心脚本的参数表、实现要点、实测注意事项与性能数据 |
| [docs/MLXServe_API_docs.md](docs/MLXServe_API_docs.md) | mlx-serve `POST /v1/images/generations` 接口字段与 SSE 事件格式 |
| [docs/Introduction of Qwen Image 2.1.md](docs/Introduction%20of%20Qwen%20Image%202.1.md) | Qwen Image 2.1 模型能力介绍（原生 RGBA、图编辑等） |

## 当前进度

- **已完成**：核心生图脚本 `src/mlx_image_gen.py`（SSE 流式、进度条、透明通道、自动命名），配套完整文档与性能实测。
- **进行中 / 待办**：
  - API 已支持但脚本暂未暴露的参数：`cfg_scale`、`negative_prompt`、LoRA 堆叠、图生图（`image` + `mode: variation`）。
- **性能参考**（Apple M4 / 24GB，4bit 模型）：720x720 / 30 步约 8~9 分钟/张；512x512 / 12 步约 2 分钟/张。详见脚本文档第 6 节。

## 注意事项

- 默认文件名精确到分钟，同一分钟内多次运行会互相覆盖，批量生成请显式传 `--output`。
- 图片尺寸建议用 16 的倍数（默认 720x720），否则服务端会向上对齐。
- `--transparent` 仅适用于 Qwen-Image-2.1，其他后端会返回 HTTP 400；且该参数只保留透明通道，提示词仍需明确写出透明背景。
- 本机若开了 VPN / 反向代理，本地请求可能被拦成 502，关闭后重试。
