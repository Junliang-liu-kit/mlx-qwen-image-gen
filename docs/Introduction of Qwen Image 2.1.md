---
title: "Qwen Image 2.1 发布：7B 模型、原生 RGBA 透明图、10 图编辑与 ComfyUI"
source: "https://qwenimages.com/zh/blog/qwen-image-2-1-release"
author:
  - "[[QwenImages Editorial Team]]"
published: 2026-09-20
created: 2026-10-01
description: "Qwen-Image-2.1 是新的 7B 图像生成与编辑模型，支持原生 RGBA 透明通道、最多 10 张参考图、2K 输出，以及 Day-0 ComfyUI。本文整理功能、架构、许可证，以及它和 Qwen Image 2.0、3.0 的区别。"
tags:
  - "clippings"
---
![QwenImages Editorial Team](https://qwenimages.com/_next/image?url=%2Flogo.png&w=96&q=75)

QwenImages Editorial Team

独立编辑团队

[在线体验 Qwen-Image-2.1](https://aiimageedit.ai/qwen-image-2-1?utm_source=qwenimages) 前往 AI Image Edit · 新窗口打开

阿里巴巴通义千问团队于 **2026 年 9 月 20 日发布 Qwen-Image-2.1** ，推出一款把文生图和图像编辑放进同一条流水线的轻量图像模型。官方权重可在 [Hugging Face](https://huggingface.co/Qwen/Qwen-Image-2.1) 和 [ModelScope](https://modelscope.cn/models/Qwen/Qwen-Image-2.1) 下载，代码与示例见 [Qwen-Image-2.1 GitHub 仓库](https://github.com/QwenLM/Qwen-Image-2.1) 。也可以先在 [AI Image Edit 在线体验 Qwen-Image-2.1](https://aiimageedit.ai/qwen-image-2-1) ，无需本地部署。

这次发布聚焦四件事：更低的推理成本、原生透明图生成、更灵活的多图编辑，以及更好的视觉质量。其视觉生成组件包含 **70 亿参数、32 层 Single-Stream DiT** ，文本指令和条件图则由 Qwen3-VL 8B 编码。这里的 7B 明确指视觉生成组件，不是整条工作流里所有模型的总和。

最醒目的能力可能是原生透明通道。Qwen-Image-2.1 可以直接生成和编辑带 **真实 alpha 通道的 RGBA 图像** ，而不必在出图后再跑一遍抠图。它还支持 **最多 10 张参考图** ，可用圆圈、涂抹标注或单独 mask 做局部编辑，并原生输出 2K 分辨率。

对开发者来说，这次上线相当完整：Diffusers、ComfyUI、vLLM-Omni、SGLang 和 LightX2V 都宣布了 Day-0 支持。

## Qwen-Image-2.1 一览

| 特性 | Qwen-Image-2.1 |
| --- | --- |
| 视觉生成组件 | 7B 参数 |
| Transformer | 32 层 Single-Stream DiT |
| 文本/图像编码器 | Qwen3-VL 8B |
| VAE | 64 通道 RGBA VAE |
| 空间压缩 | 16× |
| 文生图 | 支持 |
| 图像编辑 | 支持 |
| 原生透明 | 支持，RGBA |
| 参考图 | 最多 10 张 |
| 局部编辑 | 圆圈、涂抹标注、单独 mask |
| 原生输出 | 2K |
| 默认推理步数 | 40 |
| Diffusers | Day-0 支持 |
| ComfyUI | Day-0 支持 |
| 许可证 | Qwen Research License |

模型使用 64 通道 RGBA 自编码器、16× 空间压缩和 Flow Matching 调度器。官方实现默认 40 步去噪，方形图输出 2048 × 2048。

## Qwen Image 2.1 新在哪里？

Qwen-Image-2.1 不只是又一次画质升级。它的几项新能力会改变开发者围绕模型搭建的工作流。

### 1\. 原生透明 RGBA 图像生成

最有辨识度的新增能力是 **原生 alpha 通道** 。

大多数“透明背景”工作流其实分两步：

```
先生成 RGB 图
↓
再做分割或抠图
↓
导出透明 PNG
```

Qwen-Image-2.1 把透明度直接放进图像表示里。RGBA VAE 让模型生成的图本身就带透明信息。官方说明同一套模型可以生成透明素材、编辑透明图层，也能从照片里提取主体。

![Qwen Image 2.1 native transparent RGBA image generation examples](https://qwenimages.com/images/blog/qwen-image-2-1-rgba.webp)

*官方 Qwen-Image-2.1 透明素材示例。图中铺了棋盘格，方便看清 alpha 通道。*

这让它特别适合：

- 贴纸和 emoji 素材
- 商品抠图
- 游戏素材
- 图标
- 演示文稿图形
- 合成与叠图
- 电商产品图
- 之后要叠到其他背景上的设计元素

官方仓库建议在提示词里明确写出 RGBA：

```
This is an RGBA image with transparency.
A cute cartoon dragon sticker.
The image has alpha channel and the background is transparent.
```

这比再加一个抠图功能更重要：透明度现在属于生成模型本身。

### 2\. 最多 10 张参考图

Qwen-Image-2.1 在一次编辑任务里最多接受 **10 张参考图** 。

这比传统的单参考图图生图能做更复杂的组合。

例如可以分别提供：

```
人物
+ 外套
+ 鞋子
+ 手袋
+ 帽子
→ 完整穿搭图
```

或者：

```
沙发
+ 椅子
+ 桌子
+ 灯
+ 房间参考
→ 室内设计组合
```

官方演示包括用多张肖像合成合影，以及用分开的单品参考拼出一套穿搭。模型被设计成在组合这些参考时，尽量保住人物身份和商品特征。

![Qwen Image 2.1 multi-reference image editing using multiple input images](https://qwenimages.com/images/blog/qwen-image-2-1-multi-ref.webp)

*官方演示：用六张单独肖像参考合成一张合影。*

![Qwen Image 2.1 outfit assembled from separate clothing, shoes, bag and hat references](https://qwenimages.com/images/blog/qwen-image-2-1-outfit.webp)

*官方演示：用人物、外套、鞋子、包和帽子的分开参考拼出一套完整穿搭。*

对电商、角色设计和广告工作流来说，这可能比文生图画质再提升一点更有用。

### 3\. 更精确的局部图像编辑

Qwen-Image-2.1 还提供了几种告诉模型 **编辑应该发生在哪里** 的方式。

用户可以用以下方式标出编辑区域：

- 圆圈
- 涂抹标注
- 单独的 mask 图

例如一张图里可以有多个标记区域，分别对应去掉手表、改发色或换衣服，同时尽量不动照片其余部分。

![Qwen Image 2.1 local editing before and after using circled and painted regions](https://qwenimages.com/images/blog/qwen-image-2-1-local-edit.webp)

*官方示例：左侧是标记区域，右侧是编辑结果。手表被去掉，发色改变，衣服被替换。*

单独 mask 对生产流程尤其有用，因为原图不必被永久画上标记。

概念上的流程变成：

```
原图
+
Mask 图
+
自然语言指令
↓
编辑后的图
```

这给开发者提供了一条接近 Photoshop 式 AI 编辑界面的路径，而不必让用户把所有空间细节都写进文字。

### 4\. 原生 2K 图像生成

Qwen-Image-2.1 原生支持 2K 出图。

官方仓库推荐分辨率如下：

| 宽高比 | 分辨率 |
| --- | --- |
| 1:1 | 2048 × 2048 |
| 4:3 | 2400 × 1792 |
| 3:4 | 1792 × 2400 |
| 3:2 | 2528 × 1696 |
| 2:3 | 1696 × 2528 |
| 16:9 | 2752 × 1536 |
| 9:16 | 1536 × 2752 |

默认方形输出是 **2048 × 2048** ，推理步数 40。

因此 2752 像素指的是部分宽高比的长边，而不是默认输出 2752 × 2752。

官方示例还包括这些原生分辨率下的宽幅全景和多格分镜。

![Qwen Image 2.1 panoramic 2K image generated from a selfie reference](https://qwenimages.com/images/blog/qwen-image-2-1-panorama.webp)

*官方演示：由一张自拍生成的全景图。*

![Qwen Image 2.1 multi-frame storyboard with consistent character identity](https://qwenimages.com/images/blog/qwen-image-2-1-storyboard.webp)

*官方演示：六格分镜，同一角色在不同场景和光线下保持一致。*

## Qwen-Image-2.1 如何提高推理效率

如果每张输入图都要在每一步去噪里重复处理，支持 10 张参考图会非常昂贵。

Qwen 的做法是 **混合粒度注意力和 prefix KV cache 复用** 。

![Qwen Image 2.1 prefix KV cache diagram for static text and reference-image context](https://qwenimages.com/images/blog/qwen-image-2-1-kv-cache.webp)

*官方架构图：文本和参考图只计算一次，后续去噪步复用；每一步重新计算的是目标图。*

生成过程中，文本指令和参考图保持不变。因此 Qwen-Image-2.1 可以先处理这段静态条件上下文，并在后续去噪步里复用缓存，而不是每一步都从头计算。

这对多参考图编辑尤其关键，因为条件数据里可能包含多张高分辨率图。

官方 Diffusers 实现会在模型的因果条件选项开启时自动使用这种 prefix caching。

## Qwen-Image-2.1 架构

模型由几个主要组件构成。

### 7B Single-Stream DiT

视觉生成组件包含：

```
7B 参数
32 层 Single-Stream DiT
```

这个区分很重要。 **7B 明确指视觉生成组件** ，不是完整 Qwen-Image-2.1 工作流里的全部模型。部分发布报道在把 Qwen3-VL 编码器也算进去后，会给出更大的总参数量。官方 GitHub README 对 7B / 32 层视觉栈的表述是清楚的。

### Qwen3-VL 8B

Qwen3-VL 8B 作为视觉语言模型编码器，同时处理：

- 文本指令
- 条件图像

这样文本和参考图信息可以在生成前被放到一起表示。

### 64 通道 RGBA VAE

VAE 具备：

```
64 通道
16× 空间压缩
RGBA 支持
```

带 alpha 的 VAE 才是原生透明图生成的关键，而不是先出 RGB 再做后处理透明。

## Qwen-Image-2.1 效果如何？

Qwen 也用自己的 **[Qwen-Image-Bench](https://github.com/QwenLM/Qwen-Image-Bench)** 公布了 Qwen-Image-2.1 成绩。

发布相关报道给出的综合分是 **60.28** 。同一套厂商对比里，Nano Banana 2.0 为 59.82，GPT Image 1.5 为 59.65。 [PC Watch 的报道](https://pc.watch.impress.co.jp/docs/news/2142515.html) 还把 Qwen-Image-2.1 放在 GPT Image 2.5 Sunburst（67.01）之下、FLUX 2 Max（55.33）之上。

![Qwen-Image-Bench vendor-reported scores highlighting Qwen-Image-2.1 at 60.28](https://qwenimages.com/images/blog/qwen-image-2-1-bench.webp)

*以上为 Qwen 团队公布的 Qwen-Image-Bench 结果。这是厂商自报基准，而不是独立第三方评测。*

这个数字需要谨慎解读。

Qwen-Image-Bench 由 Qwen 团队开发，不是独立第三方榜单。基准包含 1000 条提示词，从五个高层类别评估生成图：

- Quality
- Aesthetics
- Alignment
- Real-world Fidelity
- Creative Generation

这些类别再拆成 23 项子能力和 56 个细粒度评估面。打分使用基于 Qwen3.6-27B 的 Q-Judger。

因此这个分数适合理解 Qwen 如何定位这款模型，但不应被当成 Qwen-Image-2.1 在所有真实工作流里都会超过其他模型的证据。

## Qwen Image 2.1 有了专用 Prompt Enhancer

Qwen 还为 Qwen-Image-2.1 发布了专用提示词改写模型：

```
Qwen-Image-2.1-PE-T2I
Qwen-Image-2.1-PE-I2I
```

两者都是微调后的 **Qwen3.5-VL 9B** 检查点。一个用于文生图提示词，一个用于图像编辑。权重分别发布在 [Qwen-Image-2.1-PE-T2I](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-T2I) 和 [Qwen-Image-2.1-PE-I2I](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I) 。

思路很简单。

用户可能只写：

```
a corgi playing guitar in the rain
```

Prompt enhancer 可以把这条短请求扩成更详细的生成提示词，并建议宽高比。

图像编辑时，类似：

```
make the sky sunset
```

这样的指令可以被扩成更明确的编辑说明，同时尽量保住原图里需要保留的内容。

这意味着提示词增强是一层可选能力，而不是强迫每个用户都手写超详细提示词。

## 如何用 Diffusers 运行 Qwen Image 2.1

Qwen-Image-2.1 通过 `QwenImage21Pipeline` 获得了 Day-0 Diffusers 支持。

官方安装要求包括：

```bash
pip install torch>=2.4.0
pip install transformers>=5.17
pip install git+https://github.com/huggingface/diffusers
pip install accelerate
pip install pillow
```

最小生成示例如下：

```python
import torch
from diffusers import QwenImage21Pipeline

pipe = QwenImage21Pipeline.from_pretrained(
    "Qwen/Qwen-Image-2.1",
    torch_dtype=torch.bfloat16
).to("cuda")
image = pipe(
    prompt="A neon shop sign that reads "QWEN IMAGE 2.1", rainy night, reflections on wet pavement",
    num_inference_steps=40,
    generator=torch.Generator("cuda").manual_seed(42)
).images[0]
image.save("qwen-image-2-1.png")
```

同一条 pipeline 也接受用于编辑的源图，以及用于多参考生成的图像列表。

显存较小的机器可以使用官方示例里的 CPU offload：

```python
pipe.enable_model_cpu_offload()
```

## 在 ComfyUI 中使用 Qwen Image 2.1

ComfyUI 也在发布当天加入了原生 Qwen-Image-2.1 支持。

[Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) 目前把扩散模型、文本编码器和 VAE 分成独立文件。

扩散模型选项包括：

```
qwen_image_2.1_bf16.safetensors
qwen_image_2.1_int8_convrot.safetensors
```

BF16 扩散模型大约 **14.2 GB** ，INT8 版本大约 **7.26 GB** 。

文本编码器提供 BF16、INT8 和 W4A8 变体，并配有专用的 Qwen-Image-2.1 VAE。官方工作流模板已覆盖 [文生图](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_2_1_t2i.json) 和 [图像编辑](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_2_1_image_edit.json) 。

如果新的 Qwen-Image-2.1 节点或模板找不到，先把 ComfyUI 更新到最新构建，再排查工作流本身。

完整安装流程会另写一篇 Qwen Image 2.1 ComfyUI 指南。

## Qwen Image 2.1 vs Qwen Image 2.0

相比 [原版 Qwen-Image](https://qwenimages.com/zh/blog/qwen-image-release) ， [Qwen-Image-2.0](https://qwenimages.com/zh/blog/qwen-image-2-release) 已经把生成架构做得更紧凑，并引入了原生 2K 输出。

Qwen-Image-2.1 则把这条线继续推向更实用的图像编辑。

| 特性 | Qwen Image 2.0 | Qwen Image 2.1 |
| --- | --- | --- |
| 生成 + 编辑 | 支持 | 支持 |
| 原生 2K | 支持 | 支持 |
| 原生 RGBA 透明 | — | **支持** |
| 最多 10 张参考图 | — | **支持** |
| 圆圈/mask 编辑 | 更有限 | **支持** |
| Prefix KV cache 重点 | — | **支持** |
| 专用 prompt enhancer | — | **支持** |
| Day-0 ComfyUI | — | **支持** |

因此关心 2.1 的最大理由，不只是“图更好看”，而是它补上了 **透明素材、多参考工作流和更可控的编辑** 。

上一世代的背景见 [Qwen Image 2.0 指南](https://qwenimages.com/zh/blog/qwen-image-2-release) 。

## Qwen Image 2.1 vs Qwen Image 3.0

版本号一开始可能让人困惑，因为 **[Qwen Image 3.0](https://qwenimages.com/zh/blog/qwen-image-3-release) 在 2026 年 7 月 21 日发布，而 Qwen-Image-2.1 更晚，是 2026 年 9 月 20 日** 。

两款产品强调的方向不同，并不是一条简单的时间线升级。

Qwen Image 3.0 更侧重高信息密度生成。官方描述支持最长约 4.5K token 的提示词、约 10px 小字、12 种语言，以及报纸、分镜和界面设计这类复杂版式。

Qwen-Image-2.1 则更适合本地和开发者工作流：

| Qwen Image 2.1 | Qwen Image 3.0 |
| --- | --- |
| 可下载模型权重 | 更偏云端产品定位 |
| 7B 视觉生成器 | 产品定位不同 |
| 原生 RGBA | 高信息密度版式 |
| 最多 10 张参考图 | 最长约 4.5K token 提示词 |
| Mask / 局部编辑 | 复杂内容生成 |
| ComfyUI + Diffusers | 更强的多语言版式 |
| 可自托管工作流 | 约 10px 文字渲染 |

我们会另发一篇带实际例子的 Qwen Image 2.1 vs Qwen Image 3.0 对比。眼下可先看 [Qwen Image 3.0 发布说明](https://qwenimages.com/zh/blog/qwen-image-3-release) 和 [Qwen Image 3.0 专题页](https://qwenimages.com/zh/qwen-image-3) 。

## Qwen Image 2.1 可以商用吗？

这是这次发布最需要先看清的细节。

Qwen-Image-2.1 使用的是 **[Qwen Research License Agreement](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE)** ，不是 Apache 2.0 这类宽松许可证。

许可证把允许的非商用用途定义为 **仅限研究或评估** ，并写明商用需要向 Qwen 另行取得商业许可。

因此要分清：

```
可以下载权重？                 可以
可以研究/评估模型？             可以
可以出于研究目的自托管？         可以
公开许可证是否自动授予商用权利？ 否
```

如果计划把 Qwen-Image-2.1 接入商业产品，应直接阅读官方许可证，而不是默认沿用此前 Qwen 版本的授权条款。

这对给客户生成素材、或把模型嵌进付费服务的公司尤其重要。

## Qwen-Image-2.1 适合谁？

这些新能力让 Qwen-Image-2.1 对几类工作流特别有吸引力。

**设计师** 可以直接生成能立刻放进更大构图里的透明素材。

**电商团队** 可以把商品、模特、服装和配饰参考组进新场景。

![Qwen Image 2.1 product photograph with bilingual packaging text](https://qwenimages.com/images/blog/qwen-image-2-1-product.webp)

*官方示例：带中英包装文字的商品特写。*

**AI 图像编辑产品** 可以提供基于 mask 的自然语言改图。

![Qwen Image 2.1 portrait example showing identity and lighting detail](https://qwenimages.com/images/blog/qwen-image-2-1-portrait.webp)

*官方示例：用来说明身份保持和光线细节的肖像。*

**游戏和贴纸创作者** 可以生成带 alpha 通道的角色和物体。

**研究者和开发者** 可以通过 Diffusers、ComfyUI、vLLM-Omni 或 SGLang 在本地运行可下载权重。

而正在做多参考工作流的开发者，现在有了一款被设计成一次处理最多十张条件图的模型。

## FAQ

### Qwen-Image-2.1 是什么？

Qwen-Image-2.1 是 Qwen 于 2026 年 9 月 20 日发布的统一图像生成与编辑模型。其视觉生成组件包含 7B 参数和 32 层 Single-Stream DiT。

### Qwen Image 2.1 是开源的吗？

Qwen 将 Qwen-Image-2.1 描述为开源，并公布了可下载的模型权重和代码。但权重受 Qwen Research License 约束，默认授权仅限非商用研究与评估。对许可敏感的场景，用 “open-weight” 来区分会更准确。

### Qwen Image 2.1 能生成透明 PNG 吗？

可以。模型使用支持 RGBA 的 VAE，能原生生成带 alpha 通道的图像，包括透明背景素材。

### Qwen Image 2.1 支持多少张参考图？

在多参考图像编辑或组合工作流中，最多支持 **10 张参考图** 。

### Qwen Image 2.1 支持什么分辨率？

官方将 Qwen-Image-2.1 描述为支持原生 2K 输出。默认方形分辨率是 2048 × 2048；16:9 和 9:16 推荐预设的长边可到 2752 像素。

### Qwen Image 2.1 能在 ComfyUI 里用吗？

可以。ComfyUI 在发布当天提供了原生支持，并配套 BF16 / INT8 模型文件以及生成和编辑工作流模板。

### 我可以商用 Qwen Image 2.1 吗？

在默认的 Qwen Research License 下不行。公开许可证把授权限制在非商用研究/评估，并写明商用用户需要另行取得商业许可。

### Qwen Image 2.1 比 Qwen Image 3.0 更新吗？

是。Qwen Image 3.0 于 2026 年 7 月 21 日发布，Qwen-Image-2.1 于 2026 年 9 月 20 日发布。因此不能只按版本号理解发布时间顺序。

## 立即体验 Qwen-Image-2.1

体验 Qwen-Image-2.1 的原生 RGBA 生成、多参考图编辑和 2K 输出：

- **在 AI Image Edit 在线体验 Qwen-Image-2.1** ： [https://aiimageedit.ai/qwen-image-2-1](https://aiimageedit.ai/qwen-image-2-1)
- **Hugging Face Demo** ： [https://huggingface.co/spaces/Qwen/Qwen-Image-2.1](https://huggingface.co/spaces/Qwen/Qwen-Image-2.1)
- **GitHub 仓库** ： [https://github.com/QwenLM/Qwen-Image-2.1](https://github.com/QwenLM/Qwen-Image-2.1)

## 结论

Qwen-Image-2.1 之所以特别，是因为它最值得关注的改进并不只停留在画质。

**7B 视觉生成组件** 、原生 RGBA 透明、最多 **10 张参考图** 、可控局部编辑、2K 输出，以及 Diffusers 和 ComfyUI 的即时接入，让它特别适合搭建实用的图像生成和编辑工作流。

原生透明可能会尤其重要。模型内部直接生成可用的 alpha 通道，等于从很多素材流水线里拿掉整段分割或抠图步骤。

部署前最需要先理解的限制是许可证。Qwen-Image-2.1 的可下载权重适用 Qwen Research License，商用部署需要额外许可，而不是由公开模型许可证自动授予。

我们会继续测试 Qwen-Image-2.1，并陆续发布 **ComfyUI 安装、透明 PNG 生成、提示词，以及与 Qwen Image 3.0 的对比** 专题。

---

**更多资源：**

- [在 AI Image Edit 在线体验 Qwen-Image-2.1](https://aiimageedit.ai/qwen-image-2-1)
- [Qwen-Image-2.1 官方公告](https://qwen.ai/blog?id=qwen-image-2.1)
- [GitHub 仓库](https://github.com/QwenLM/Qwen-Image-2.1)
- [Hugging Face 权重](https://huggingface.co/Qwen/Qwen-Image-2.1)
- [Hugging Face Demo](https://huggingface.co/spaces/Qwen/Qwen-Image-2.1)
- [ComfyUI 权重](https://huggingface.co/Comfy-Org/Qwen-Image-2.1)
- [Qwen Research License](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE)
- [Qwen Image 2.0 指南](https://qwenimages.com/zh/blog/qwen-image-2-release)
- [Qwen Image 3.0 指南](https://qwenimages.com/zh/blog/qwen-image-3-release)

Qwen Image 2.1

原生 RGBA

ComfyUI

图像编辑

Qwen Research License

分享这篇文章

![QwenImages Editorial Team](https://qwenimages.com/_next/image?url=%2Flogo.png&w=128&q=75)

### QwenImages Editorial Team

独立编辑团队

QwenImages 独立编辑团队优先核对一手来源，并明确区分厂商主张与本站实测。