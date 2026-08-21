**简体中文** | [English](README.md)

# 全球多语言内容风险控制网关

一个开源网关设计，用于在用户生成的文本和图片进入国际娱乐或社交应用之前对其进行审核。

## 本地设置

1. 将 `.env.example` 复制为 `.env`，并填写 Content Safety 终结点和密钥。`.env.example` 仅为模板，服务不会读取它。
2. 安装依赖：`pip install -r requirements.txt`。
3. 启动网关：`uvicorn gateway.main:app --reload`。

## 贡献者配置

仓库仅包含一个空的 `.env.example` 模板。请将其复制为 `.env`，然后在本地填入自己的 Azure AI Content Safety 凭据。`.env` 文件、虚拟环境、本地工作文件夹和测试图片文件均已排除在版本控制之外。

打开 [http://127.0.0.1:8000](http://127.0.0.1:8000) 使用浏览器界面。它支持文本和图片扫描，并在当前浏览器的本地存储中保留最近 50 条结果记录，不会保存提交内容的原始文本或图片。

## 运行无需凭据的演示

此演示仅使用确定性的本地 Azure Content Safety 模拟器来展示中间件流程；它不能替代生产环境中的 Azure 服务。

```powershell
$env:PYTHONPATH = "."
python scripts/demo.py
```

演示将展示一条安全的多语言帖子、一次越狱提示尝试、个人数据泄露、一个文化敏感性审核案例，以及一项图片审核决策。

## API 端点

- `POST /v1/scan/text` 接受 `{ "text": "...", "policy_id": "eu" }`。
- `POST /v1/scan/image` 接受 `{ "image_base64": "...", "policy_id": "eu" }`。
- `GET /health` 用于确认服务正在运行。

图片扫描接受采用 Base64 编码的图片字节。网关刻意不会获取外部图片 URL，以避免服务器端请求伪造以及无边界的第三方数据传输。

若要使用 Azure 文本屏蔽列表，请先在 Azure 中创建该列表，再将其名称添加到适用地区策略文件中的 `azure_blocklists` 下。与屏蔽列表项目匹配时会直接产生 `block` 决策；API 仅公开匹配数量，不会公开匹配到的文本。

## 统一风险评分

Azure 按标准的 `0`、`2`、`4`、`6` 等级返回类别严重程度。网关将四个类别映射到策略词汇（`hate_or_harassment`、`self_harm`、`sexual_content` 和 `violence`），并将当前活跃类别中的最高严重程度归一化为 `0-100` 的 `risk_score`：`0 -> 0`、`2 -> 33`、`4 -> 67`、`6 -> 100`。本地上下文信号使用相同的评分尺度。随后，策略阈值会将该风险映射为 `allow`、`review` 或 `block`；所有扫描器证据都会保留在 `provider_results` 中。

## 本地上下文控制

网关无需生成式模型即可检测越狱模式、语言提示、个人身份信息泄露、违法活动模式，以及按地区配置的文化审核词。请参阅 [`gateway/context.py`](gateway/context.py)。后续可在相同的输出契约下替换为经过训练的多语言分类器；策略引擎仍然是最终决策依据。

## 初始决策契约

网关遵循 [`schemas/scan-response.schema.json`](schemas/scan-response.schema.json)。供应商评分用于辅助策略决策，但它们本身并不是最终的内容审核决策。
