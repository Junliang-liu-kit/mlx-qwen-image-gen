"""基于 mlx-serve 的本地图像生成脚本。

调用 `POST /v1/images/generations`（SSE 流式），在终端展示生成进度，
并把返回的 base64 图片保存到本地。

用法示例：

    uv run python src/mlx_image_gen.py -p "a cute cartoon dragon sticker" \\
        --output output/dragon.png
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "http://127.0.0.1:11234/v1/images/generations"
DEFAULT_MODEL = "ddalcu/Qwen-Image-2.1-MLX-Serve-4bit"
# 720x720 是 16 的倍数，服务端不会二次对齐；比 1024x1024 生成更快，画质损失有限。
DEFAULT_SIZE = "720x720"
DEFAULT_STEPS = 30
DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = Path("output")
OUTPUT_FILENAME_PREFIX = "mlx_image_gen"
PROGRESS_BAR_WIDTH = 28


def parse_args() -> argparse.Namespace:
    """解析接口地址、生成参数与输出路径。

    Returns:
        argparse.Namespace: 命令行参数。
    """
    parser = argparse.ArgumentParser(description="调用 mlx-serve 生成图片")
    parser.add_argument("-p", "--prompt", required=True, help="图片描述（提示词）")
    parser.add_argument("--url", default=DEFAULT_URL, help="图片生成接口地址")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument("--size", default=DEFAULT_SIZE, help="图片尺寸，格式 WxH")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="生成步数")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="随机种子")
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="输出带 alpha 通道的 PNG（仅 Qwen-Image-2.1 支持）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "生成图片的保存路径，默认按时间戳自动命名："
            f"{DEFAULT_OUTPUT_DIR}/{OUTPUT_FILENAME_PREFIX}_<YYYYMMDDHHMM>.png"
        ),
    )
    parser.add_argument("--timeout", type=float, default=600, help="请求超时秒数")
    args = parser.parse_args()
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        args.output = DEFAULT_OUTPUT_DIR / f"{OUTPUT_FILENAME_PREFIX}_{timestamp}.png"
    return args


def build_payload(args: argparse.Namespace) -> dict:
    """根据命令行参数构造请求体。

    Args:
        args (argparse.Namespace): 命令行参数。

    Returns:
        dict: 接口请求体，固定开启 stream 以获取进度事件。
    """
    return {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "steps": args.steps,
        "seed": args.seed,
        "stream": True,
        "transparent": args.transparent,
    }


def render_progress(stage: str, step: int, total: int) -> None:
    """在 stderr 上原地刷新一行进度条。

    Args:
        stage (str): 当前阶段名称，例如 "Generating"。
        step (int): 已完成步数。
        total (int): 总步数。
    """
    ratio = step / total if total > 0 else 1.0
    ratio = min(max(ratio, 0.0), 1.0)
    filled = int(ratio * PROGRESS_BAR_WIDTH)
    bar = "=" * filled + "-" * (PROGRESS_BAR_WIDTH - filled)
    sys.stderr.write(f"\r{stage:<16} [{bar}] {step}/{total}")
    sys.stderr.flush()


def consume_stream(response) -> dict:
    """解析 SSE 流，渲染进度并返回 complete 事件。

    Args:
        response: urlopen 返回的流式响应对象。

    Returns:
        dict: 类型为 complete 的最终事件。

    Raises:
        RuntimeError: 流中出现 error 事件，或流结束时没有 complete 事件。
    """
    for raw_line in response:
        line = raw_line.decode("utf-8").strip()
        if not line.startswith("data:"):
            continue  # 跳过空行与 SSE 注释（如心跳 ": ping"）
        body = line[len("data:") :].strip()
        if not body or body == "[DONE]":
            continue
        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            continue  # 容忍非 JSON 的心跳内容

        event_type = event.get("type")
        if event_type == "progress":
            render_progress(
                event.get("stage", ""),
                int(event.get("step", 0)),
                int(event.get("total", 0)),
            )
        elif event_type == "error":
            raise RuntimeError(f"生成失败：{event.get('message') or event}")
        elif event_type == "complete":
            sys.stderr.write("\n")
            sys.stderr.flush()
            return event

    raise RuntimeError("流式响应结束，但没有收到 complete 事件")


def generate_image(args: argparse.Namespace) -> Path:
    """调用接口生成图片并写入磁盘。

    Args:
        args (argparse.Namespace): 接口请求及文件保存参数。

    Returns:
        Path: 已保存图片的路径。

    Raises:
        RuntimeError: 请求失败或响应中缺少有效图片数据时抛出。
    """
    request = Request(
        args.url,
        data=json.dumps(build_payload(args)).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=args.timeout) as response:
            event = consume_stream(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"接口返回 HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"无法连接接口 {args.url}: {error.reason}") from error

    try:
        image_bytes = base64.b64decode(event["data"][0]["b64_json"], validate=True)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise RuntimeError(
            f"complete 事件中没有有效的 data[0].b64_json：{event}"
        ) from error

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image_bytes)
    return args.output


def main() -> int:
    """解析参数、生成图片并打印结果。

    Returns:
        int: 成功时返回 0，失败时返回 1。
    """
    args = parse_args()
    try:
        output_path = generate_image(args)
    except (OSError, RuntimeError) as error:
        sys.stderr.write("\n")
        print(f"图片生成失败：{error}", file=sys.stderr)
        return 1

    print(f"图片已保存到：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
