<div align="center">

  <h1>ZenXYT</h1>
  
  <p>
    <strong>Automated Metadata Optimization Engine for YouTube</strong><br>
    <em>High-Performance Concurrent LLM Analysis (Gemini 1.5 Pro & NVIDIA Nemotron)</em>
  </p>

  <p>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
    <a href="https://github.com/sponsors/atomicdhruba"><img src="https://img.shields.io/badge/sponsor-30363D?style=flat&logo=GitHub-Sponsors&logoColor=#EA4AAA" alt="Sponsor"></a>
  </p>

</div>

---

> ZenXYT is a highly optimized, local desktop client designed to automate YouTube metadata generation. The pipeline uses a custom "Debate Engine" architecture where two distinct LLM models evaluate the same video context independently, before a synthesis prompt generates the ultimate metadata payload designed for maximum CTR and algorithmic reach.

## Core Architecture

The system utilizes a multi-agent pipeline to process raw video files into highly optimized YouTube metadata.

```text
 [ RAW VIDEO ] ───▶ ( yt-dlp ) ───▶ [ MULTIMODAL PARSING ]
                                             │
                                             ▼
                                   [ CONTEXT CACHE ]
                                             │
                ┌────────────────────────────┼────────────────────────────┐
                ▼                            ▼                            ▼
       [ NVIDIA MODE ]                [ DEBATE MODE ]              [ GEMINI MODE ]
    (Nemotron Inference)        (Concurrent Multi-Agent)         (Gemini Inference)
                │                            │                            │
                └────────────────────────────┼────────────────────────────┘
                                             ▼
                                 [ SYNTHESIS & SEO GRADING ]
                                             │
                                             ▼
                                   [ YOUTUBE DATA API ]
```

## Features

| System Component | Description |
| :--- | :--- |
| **Vision Extraction** | Frame-by-frame multimodal parsing to build a persistent context cache, avoiding redundant API calls. |
| **Debate Pipeline** | Multi-agent drafting where distinct LLMs generate competing metadata, followed by strict synthesis evaluation. |
| **Execution Modes** | Toggle between isolated models (`nvidia`, `gemini`) or the concurrent `debate` synthesizer via the UI. |
| **Heuristic Scoring** | Built-in SEO grading algorithm (0–100) evaluating title CTR potential, tag relevance, and algorithmic hook. |
| **Asynchronous UI** | CustomTkinter dark-mode desktop interface running completely decoupled from background API threads. |

## Quick Start

To run this project locally, provision external API keys for the inference models and Google services.

- **Environment:** `Python 3.10+`
- **System Binaries:** `FFmpeg` must be in your system PATH.
- **API Keys:** You will need keys for YouTube Data API v3, NVIDIA Developer (Nemotron), and Google AI Studio (Gemini).

```bash
git clone https://github.com/atomicdhruba/ZenXYT.git
cd ZenXYT
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with your API keys:
```ini
NVIDIA_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GENERATION_MODE=debate
```

### YouTube OAuth Configuration (BYOK)

To avoid standard Google App Verification overhead, this repository uses a "Bring Your Own Key" (BYOK) model for YouTube authentication. Your tokens remain strictly local.

1. Create a project in the Google Cloud Console.
2. Enable the **YouTube Data API v3**.
3. Configure the **OAuth Consent Screen** (External, add `.../auth/youtube.force-ssl` scope, and add your email as a Test User).
4. Create **OAuth client ID** credentials (Desktop app).
5. Download the JSON credential file, rename it to `client_secrets.json`, and place it in the root of the repository.

*On initial execution, a local server will spawn to handle the OAuth callback, generating a `token.pickle` file for subsequent headless runs.*

## Execution

Initialize the desktop GUI dashboard:
```bash
python bot.py
```

Execute in headless CLI mode for server environments:
```bash
python bot.py --cli
```

## Security

**Never commit your secrets.**  
The provided `.gitignore` explicitly blocks `.env`, `client_secrets.json`, `cookies.txt`, and `token.pickle`. Do not override these rules.

## Support the Project

If ZenXYT optimizes your workflow, consider supporting its continued development.

<div align="center">
  <a href="https://ko-fi.com/atomicdhruba"><img src="https://ko-fi.com/img/githubbutton_sm.svg" width="400" alt="Buy Me a Coffee at ko-fi.com" /></a><br>
  <a href="https://patreon.com/c/AtomicDhruba"><img src="https://img.shields.io/badge/BECOME_A_PATRON-000000?style=for-the-badge&logo=patreon&logoColor=white" width="400" alt="Become a Patron" /></a>
</div>
