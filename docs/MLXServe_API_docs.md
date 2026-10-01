---
title: mlx-serve 图像生成 API 文档
tags:
  - mlx-serve
  - api
  - image-generation
---
# mlx-serve 图像生成 API 文档
mlx-serve 图像生成 / 编辑接口的调用参考：请求字段、响应格式、SSE 事件与错误码。
> [!info] 服务信息
> - Base URL：`http://127.0.0.1:11234`（等价于 `http://localhost:11234`）
> - 鉴权：默认无。服务端以 `--api-key` / `--api-key-strict` 启动后，请求需带 `Authorization: Bearer <API_KEY>`
> - 本地默认模型：`ddalcu/Qwen-Image-2.1-MLX-Serve-4bit`（4bit），其 `capabilities` 需包含 `image`
> - 相关文档：[[mlx_image_gen_script]]、[[Qwen Image 2.1 部署与实践]]
## 接口一览
| 接口 | 用途 | Content-Type |
|---|---|---|
| `POST /v1/images/generations` | 文生图；配合 `image` + `mode:"variation"` + `strength` 也可做变体 / 图生图 | `application/json` |

## POST /v1/images/generations
```http
POST http://127.0.0.1:11234/v1/images/generations
Content-Type: application/json
```
### 基础参数
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `prompt` | `string` | 是 | 生成提示词 |
| `model` | `string` | 否 | 模型 ID，本地默认 `ddalcu/Qwen-Image-2.1-MLX-Serve-4bit` |
| `negative_prompt` | `string` | 否 | 负向提示词 |
| `stream` | `boolean` | 否 | 开启 SSE 流式输出。所有 media endpoint 都支持 `stream:true`，最终以一个包含 base64 结果的 `complete` 事件结束 |
### 尺寸参数
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `size` | `string` | 否 | 画布尺寸，格式 `"WxH"`，例如 `"1024x1024"` |
| `width` | `integer` | 否 | 可替代 `size`，与 `height` 配对使用 |
| `height` | `integer` | 否 | 可替代 `size`，与 `width` 配对使用 |
> [!warning] 尺寸会被对齐到 16 的倍数
> 服务端会把画布向上对齐（实测请求 `712x712`，实际返回 `720x720`）。建议直接传 16 的倍数，避免尺寸与预期不符。
### 采样参数
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `steps` | `integer` | 否 | 采样 / 去噪步数 |
| `seed` | `integer` | 否 | 随机种子，用于复现结果 |
| `cfg_scale` | `number` | 否 | guidance scale，**推荐优先使用这个名字**。FLUX 类模型会结合 guidance scale 与 negative prompt 一起生效 |
| `cfg` | `number` | 否 | guidance scale 的别名（文档写作 `cfg` / `cfg_scale`），与 `cfg_scale` 二选一 |
### 图生图 / 变体参数
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `image` | `string` | 否 | base64 编码的源图，用于图生图 / 变体生成 |
| `mode` | `string` | 否 | 与 `image` 配合使用，文档显式列出 `mode:"variation"`，即把 `generations` 端点用于变体 / 图生图 |
| `strength` | `number` | 否 | 与 `image` + `mode:"variation"` 搭配，控制保留原图的程度 / 改动强度 |
### 后端能力与 LoRA
| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `transparent` | `boolean` | 否 | **仅 Qwen-Image-2.1 支持**。`true` 时返回带 alpha 通道的 PNG，其他图像后端会返回 HTTP 400 |
| `lora_paths` | `string[]` | 否 | media LoRA 统一语法，与 `lora_scales` 配对，**最多 8 个，堆叠生效** |
| `lora_scales` | `number[]` | 否 | 与 `lora_paths` 一一对应的权重 |
> [!warning] `transparent` 不会替你抠图
> 它只保留模型自己生成出的透明通道，不会自动去背或改写提示词。想让背景真的透明，提示词里要明确写出「透明背景 / RGBA」。
### 请求示例
最小可跑通（文生图，非流式）：
```bash
curl http://127.0.0.1:11234/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ddalcu/Qwen-Image-2.1-MLX-Serve-4bit",
    "prompt": "a red apple on a wooden table, studio light",
    "size": "1024x1024",
    "steps": 30,
    "seed": 42
  }'
```
覆盖常用字段（含 LoRA）：
```json
{
  "prompt": "A futuristic product poster of a precision instrument, clean white background, blue accents, high detail",
  "size": "1024x1024",
  "steps": 30,
  "seed": 42,
  "cfg_scale": 4.5,
  "negative_prompt": "blurry, low quality, distorted text",
  "stream": false,
  "transparent": false,
  "lora_paths": ["/absolute/path/to/style.safetensors"],
  "lora_scales": [0.8]
}
```
变体 / 图生图时追加：
```json
{
  "image": "<base64-source-image>",
  "mode": "variation",
  "strength": 0.45
}
```
### 非流式响应
`stream` 未开启时，返回体结构如下：
```json
{
  "created": 0,
  "data": [
    {
      "b64_json": "<png-base64>"
    }
  ]
}
```
### 流式响应（`stream: true`）
开启后走 SSE：所有 media endpoint 都支持 `stream:true`，服务端持续推送 `progress` 事件，最后以包含 base64 结果的 `complete` 事件结束。
```json
{
  "prompt": "A clean UI dashboard illustration",
  "size": "1024x1024",
  "stream": true
}
```
事件形态（本地实测）：
```text
data: {"type":"progress","stage":"Encoding prompt","step":0,"total":30}
data: {"type":"progress","stage":"Generating","step":1,"total":30}
data: {"type":"progress","stage":"Decoding image","step":30,"total":30}
data: {"type":"complete","data":[{"b64_json":"iVBORw0KGgo..."}]}
```
| 字段 | 说明 |
|---|---|
| `type` | 事件类型：`progress` / `complete` / `error` |
| `stage` | 当前阶段，如 `Encoding prompt`、`Generating`、`Decoding image` |
| `step` / `total` | 当前进度与总步数，可用于渲染进度条 |
| `data[0].b64_json` | `complete` 事件中的 PNG base64，解码后即为图片 |
解析时的容错约定：只处理 `data:` 前缀的行，跳过空行与 `: ping` 心跳；`error` 事件视为失败；流结束仍未收到 `complete` 也视为失败。
## LoRA 字段名：`lora_path` 还是 `lora_paths`？
> [!danger] 直接用复数
> 同作者的 `zig-ai` README 写的是单数 `lora_path` + `lora_scale`，而 **mlx-serve 官方 API 文档**明确规定统一语法为 **`lora_paths` + `lora_scales`**（最多 8 个 stacked）。
> 直接调用 mlx-serve 时请使用复数形式：
> ```json
> {
>   "prompt": "A product poster of a futuristic router",
>   "size": "1024x1024",
>   "lora_paths": ["/path/to/style1.safetensors"],
>   "lora_scales": [0.8]
> }
> ```
## HTTP 状态码
| 状态码 | 含义 | 常见原因 |
|---|---|---|
| **400 Bad Request** | 请求本身不合法 | JSON 格式错误、参数类型错误、目标模型不是图像模型，或参数当前后端不支持（例如非 Qwen-Image-2.1 传 `transparent:true`）。图像模型能力不匹配同样返回 400 |
| **401 Unauthorized** | 鉴权失败 | 服务端开启了 `--api-key` / `--api-key-strict`，但请求未提供正确的 API Key |
| **403 Forbidden** | 服务存在，但当前请求不被允许 | 主要与 LAN Sharing 权限限制有关，例如访问了未允许共享的模型或接口；普通本机调用一般不涉及 |
| **404 Not Found** | 模型或接口不存在 | 模型 ID 不存在、绝对模型路径未注册、LAN peer 已离线，或 URL 写错。源码对未知模型会返回 `model_not_found` |
| **413 Payload Too Large** | 请求体过大 | `/v1/images/*` 属于 media endpoint，单次请求上限 **512 MB**，常见于传入大量 base64 图片 |
| **500 Internal Server Error** | 生成或模型加载失败 | 模型文件损坏 / 缺失、配置解析失败、tokenizer 缺失、MLX / Metal 推理异常，或 image job 本身失败。源码会记录 `[gen] image job failed: ...` |
| **502 Bad Gateway** | 上游 / 远端连接失败 | LAN peer 已找到但连不上，或 provider 上游不响应。本地生图模型出现 502 常见于本机第三方反向代理拦截，关闭 VPN 后重试 |
| **503 Service Unavailable** | 服务暂时无法执行任务 | 最常见是**加载模型的内存不足（OOM）**，本地实测报错 `Not enough free memory to load model`，关闭占内存的大程序后重试；其他原因包括模型未加载、无默认模型、Scheduler 未就绪、服务正在关闭 |
