[简体中文](README.zh-CN.md) | **English**

# Global Multilingual Content Risk Control Gateway

An open-source gateway design for reviewing user-generated text and images before they reach an international entertainment or social application.

## Local setup

1. Copy `.env.example` to `.env` and fill the Content Safety endpoint and key. `.env.example` is only a template and is never read by the service.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start the gateway: `uvicorn gateway.main:app --reload`.

## Configuration for contributors

The repository contains only an empty `.env.example` template. Copy it to `.env` and supply your own Azure AI Content Safety credentials locally. The `.env` file, virtual environments, local work folders, and test-image files are excluded from version control.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to use the browser interface. It supports text and image scans and keeps the latest 50 result records in that browser's local storage without saving raw submitted content.

## Run the credential-free demo

The demo uses a deterministic local Azure Content Safety simulator only to demonstrate the middleware flow; it is not a replacement for the Azure service in production.

```powershell
$env:PYTHONPATH = "."
python scripts/demo.py
```

It shows a safe multilingual post, a jailbreak attempt, personal-data exposure, a culture-sensitive review case, and an image-moderation decision.

## API endpoints

- `POST /v1/scan/text` accepts `{ "text": "...", "policy_id": "eu" }`.
- `POST /v1/scan/image` accepts `{ "image_base64": "...", "policy_id": "eu" }`.
- `GET /health` confirms that the service is running.

Image scanning accepts image bytes encoded as Base64. The gateway deliberately does not fetch external image URLs, avoiding server-side request forgery and unbounded third-party data transfer.

To use an Azure text blocklist, create it in Azure and add its name under `azure_blocklists` in the applicable regional policy file. A matching blocklist item becomes a hard `block` decision; the API exposes only the match count, not the matched text.

## Unified risk score

Azure returns category severities on its standard `0`, `2`, `4`, `6` scale. The gateway maps its four categories to the policy vocabulary (`hate_or_harassment`, `self_harm`, `sexual_content`, and `violence`) and calculates `risk_score` as the highest active category severity normalized to `0-100`: `0 -> 0`, `2 -> 33`, `4 -> 67`, `6 -> 100`. Local context signals use the same scale. Policy thresholds then map that risk to `allow`, `review`, or `block`; all scanner evidence remains in `provider_results`.

## Local contextual controls

The gateway detects jailbreak patterns, language hints, PII exposure, illegal-activity patterns, and region-configured cultural review terms without a generative model. See [`gateway/context.py`](gateway/context.py). A trained multilingual classifier can later be substituted behind the same output contract; the policy engine remains authoritative.

## Initial decision contract

The gateway follows [`schemas/scan-response.schema.json`](schemas/scan-response.schema.json). Provider scores inform a policy decision; they are not themselves the final moderation decision.
