# infinity-player
# ♾️ infinity-player - The Ultimate Primary Source Aggregator

[Features](#-features) • [Installation](#-installation) • [Configuration](#-configuration) • [Usage](#-usage) • [Contributing](#-contributing) • [License](#-license)

---

## 📖 Introduction

**infinity-player** is a self-hosted, intelligent media archival system designed for researchers, developers, and deep learners. In an era of algorithmic noise, infinity-player acts as your **Autonomous Research Agent**. It executes massive concurrent searches across the web, uses **Large Language Models (LLMs)** to filter out clickbait, commentary, and reaction content, and delivers a pure, ad-free stream of **Primary Sources** (Interviews, Keynotes, Lectures, and Documentaries).

---

## ✨ Features

### 🧠 AI-Powered "Truth Shield"

* The core engine can use **NVIDIA NIM (open-source models)**, **OpenAI**, or **DeepSeek** to semantically analyze video metadata.
* **Sentiment Analysis:** Instantly rejects "Reaction", "Gossip", and "Clickbait" content.
* **Source Verification:** Prioritizes official channels (e.g., Stanford, TED, YC) and primary speakers.
* **AI Insight:** Generates real-time viewing guides (Context, Key Topics, Target Audience) before you watch.

### 🌊 Massive "Funnel" Architecture

* **Wide Net:** Scans **1,000+** candidates per search session using concurrent matrix probing (Year + Topic combinations).
* **Heuristic Pre-filter:** Python-based regex engine instantly eliminates 90% of junk data (Shorts, TikToks, Gaming).
* **Deep Verification:** The top candidates are sent to the LLM for final "Quality Assurance".

### 📽️ Cinema-Grade Experience

* **System-Level Proxy:** Bypasses browser CORS and 403 restrictions for seamless playback via backend piping.
* **Floating Mini-Window:** A draggable, glass-morphism Picture-in-Picture mode for multitasking.
* **High Fidelity:** Forces **1080p MP4** streams with full seek/scrub support.
* **Direct Download:** One-click offline archiving of any video source.

### 🤖 Autonomous Persistence

* **Auto-Pilot:** Background scheduler wakes up every 24 hours to hunt for new content automatically.
* **Smart Resume:** Remembers your playback position across sessions via LocalStorage. Close the tab, come back tomorrow, and resume exactly where you left off.

---

## 🛠️ Tech Stack

| Component      |            Technology | Description                                            |
| -------------- | --------------------: | ------------------------------------------------------ |
| **Core**       |          Python 3.10+ | The brain of the operation.                            |
| **API**        |     FastAPI + Uvicorn | High-performance asynchronous backend.                 |
| **AI Engine**  |            OpenAI SDK | Compatible with NVIDIA NIM, DeepSeek, SiliconFlow.     |
| **Scraping**   |                yt-dlp | Custom configured for metadata extraction & streaming. |
| **Database**   |               SQLite3 | Zero-config persistence storage.                       |
| **Frontend**   | Vanilla JS + Tailwind | No build steps required, extremely fast.               |
| **Networking** |                 HTTPX | Advanced SOCKS/HTTP Proxy support.                     |

---

## ⚡ Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/infinity-player.git
cd infinity-player
```

### 2. Environment Setup (recommended)

Using conda (recommended):

```bash
conda create -n infinity python=3.10 -y
conda activate infinity
```

Or use virtualenv:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

From `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install fastapi uvicorn yt-dlp openai apscheduler jinja2 requests "httpx[socks]"
```

### 4. Run Application

```bash
# option 1: run the main script
python main.py

# option 2: use uvicorn for development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Access the dashboard at: `http://localhost:8000`

---

## ⚙️ Configuration

infinity-player features a built-in Graphical Setup Wizard — manual editing of config files is usually unnecessary.

1. Launch App: open `http://localhost:8000`.
2. Setup Screen: if no API key is found, you'll be redirected to the setup page.
3. Select Provider:

   * **NVIDIA NIM (recommended):** use open-source models without powerful hardware.
   * **OpenAI / DeepSeek / SiliconFlow:** fully supported via a preset dropdown.
4. Proxy Settings (important):

   * If you are behind a firewall or using a local proxy (e.g., Clash, V2Ray), enter your proxy URL in Advanced Settings (example: `http://127.0.0.1:7890`) to avoid connection errors.

---

## 🖥️ User Guide

### 🔍 Deep Search

* Type a subject (e.g., `Sam Altman`). The system initiates a massive concurrent scan and returns long-form primary-source content (preferably within the last 5 years).

### 🎞️ Cinema Mode

* **AI Insight (🧠):** Click to generate a summary and a viewing guide for the current video.
* **Download (⬇️):** One-click download of current video (1080p MP4).
* **Mini-Mode (🗗):** Detach the player into a floating window for multitasking.

### 🖱️ Drag & Drop

* In Mini-Mode, drag the top handle of the player to reposition it anywhere. The list will expand to full width for easier browsing.

---

## ⚠️ Notes & Tips

* Recommended Python: **3.10+**
* Recommended storage: keep a dedicated folder for archives if you plan to download many videos.
* Respect copyright and content licenses when archiving or redistributing media.
* For best AI performance, ensure your chosen provider's API key and quota are configured correctly.

---

## 🤝 Contributing

Contributions are welcome! Whether it's adding new AI providers, improving the UI, or optimizing the scraper.

1. Fork the project.
2. Create your feature branch:

```bash
git checkout -b feature/AmazingFeature
```

3. Commit your changes:

```bash
git add .
git commit -m "Add some AmazingFeature"
```

4. Push and open a Pull Request:

```bash
git push origin feature/AmazingFeature
# then open a PR on GitHub with a clear description of changes
```

Please follow the repository's code style and add tests where appropriate.

---

## 📝 License

MIT License


