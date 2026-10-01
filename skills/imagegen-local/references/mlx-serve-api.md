# mlx-serve 生图接口事实

用于扩展脚本或排查接口层问题。接口细节的完整版见宿主项目的 `docs/MLXServe_API_docs.md`（若存在）。

## 端点

```http
POST http://localhost:11234/v1/images/generations
Content-Type: application/json
```

同一服务默认端口 `11234`。另有 `POST /v1/images/edits`（按指令编辑、multipart、多张参考图），
`GET /v1/models` 用于确认模型是否 `loaded` 且 `capabilities` 含 `image`。

## 请求字段

| 字段 | 类型 | 脚本已实现 | 说明 |
|---|---|---|---|
| `prompt` | string | 是 | 必填 |
| `size` | string | 是 | `"WxH"`；宽高建议为 16 的倍数 |
| `width` / `height` | int | 否 | 与 `size` 二选一的写法 |
| `steps` | int | 是 | 采样步数 |
| `seed` | int | 是 | 复现用 |
| `stream` | bool | 是（固定 true） | SSE 流式，最后发 `complete` 事件 |
| `transparent` | bool | 是 | **仅 Qwen-Image-2.1**；其他后端传 `true` 返回 400。只保留模型生成的 alpha 通道，不会替你抠图 |
| `cfg` / `cfg_scale` | number | 否 | guidance scale，优先用 `cfg_scale` |
| `negative_prompt` | string | 否 | 负向提示词 |
| `image` + `mode: "variation"` + `strength` | string/string/number | 否 | 图生图 / 变体 |
| `lora_paths` / `lora_scales` | string[] / number[] | 否 | 官方统一写法，最多 8 个堆叠。注意 `zig-ai` 文档写的是单数 `lora_path`，直接调 mlx-serve 时用复数 |

## SSE 事件形态（实测）

```
data: {"type":"progress","stage":"Encoding prompt","step":0,"total":30}
data: {"type":"progress","stage":"Generating","step":1,"total":30}
data: {"type":"progress","stage":"Decoding image","step":30,"total":30}
data: {"type":"complete","data":[{"b64_json":"iVBORw0KGgo..."}]}
```

- `progress` 的 `total` 等于 `steps`，`stage` 依次为 `Encoding prompt` → `Generating` → `Decoding image`。
- `complete` 事件的 `data[0].b64_json` 就是最终 PNG 的 base64。
- 非流式调用返回体形如 `{"created":0,"data":[{"b64_json":"..."}]}`。
- 未知 `type` 应忽略，不要当成错误。

## 状态码

| 码 | 含义 |
|---|---|
| 400 | 请求不合法；非 Qwen-Image-2.1 用 `transparent: true`；模型能力不匹配 |
| 401 | 服务开了 `--api-key` 但未提供 key |
| 403 | LAN Sharing 权限限制 |
| 404 | 模型 id 不存在（`model_not_found`） |
| 413 | media endpoint 单请求上限 512 MB |
| 500 | 服务端生成失败（模型文件损坏、推理异常等） |
| 502 | LAN peer 连不上；本地场景常见于 VPN / 反向代理拦截 |
| 503 | 最常见是显存不足 / OOM，也可能是模型未加载、Scheduler 未就绪 |

## 扩展脚本时

在 `build_payload()` 里加字段即可，SSE 与取图逻辑无需改动。加 `negative_prompt` / `cfg_scale`
这类可选字段时，注意别设成会改变默认出图行为的非空默认值。
