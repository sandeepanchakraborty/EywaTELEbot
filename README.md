# 🎥 YouTube AI Telegram Bot

A smart Telegram bot that summarizes YouTube videos and answers questions about them — powered by a **dual AI fallback system**: OpenClaw local gateway (primary) and Groq cloud API (fallback). Supports English, Hindi, Kannada, Tamil, Telugu, and Marathi.

---

## 📸 Example Screenshots

> _(Add screenshots here after running the bot)_

---

## ✨ Features

| Feature           | Description                                                 |
| ----------------- | ----------------------------------------------------------- |
| 📺 Auto Summary   | Sends a structured summary when you paste a YouTube URL     |
| 📌 Key Points     | Extracts 5 key points from any video                        |
| ⏱ Timestamps      | Highlights important moments                                |
| 🧠 Core Takeaway  | Distills the single most important insight                  |
| 💬 Q&A            | Ask unlimited follow-up questions about the video           |
| 🌐 Multi-language | Responds in English, Hindi, Kannada, Tamil, Telugu, Marathi |
| ♻️ Smart Cache    | Avoids re-fetching transcripts for the same video           |
| 👥 Multi-user     | Each user has an independent session                        |
| 🔬 Deep Dive      | In-depth thematic and analytical breakdown                  |
| ✅ Action Points  | Extracts actionable items from the video                    |

---

## 🚀 Setup Guide

### Prerequisites

- Python 3.10 or higher
- A Telegram account
- A [Groq](https://console.groq.com) account (free tier available)
- *(Optional)* [OpenClaw](https://openclaw.ai) local gateway running on your machine — used as the primary AI endpoint. If not set up, the bot falls back to Groq automatically.

---

### Step 1 — Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts — choose a name and username
4. Copy the **bot token** (looks like `123456:ABCdef...`)

---

### Step 2 — Get Groq API Key

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign in / create a free account
3. Go to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_...`)

---

### Step 2b — (Optional) Set Up OpenClaw Local Gateway

OpenClaw is a local AI gateway that proxies requests to Groq internally. It is the **primary** AI provider. Groq direct is used only as a fallback.

1. Install and run the OpenClaw gateway on your machine — it listens on `http://127.0.0.1:18789/v1` by default
2. Get your OpenClaw API key from your OpenClaw dashboard
3. If OpenClaw is **not** set up, the bot works fine — it will use Groq directly

> **How the fallback works:**
> 1. Bot sends request to OpenClaw gateway first
> 2. If OpenClaw is unreachable, rate-limited, or returns an error → automatically retries up to 3 times
> 3. If still failing → silently switches to Groq direct
> 4. Users never see an error — the switch is completely transparent

---

### Step 3 — Clone & Configure

```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-ai-bot.git
cd youtube-ai-bot

# Create .env file from example
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenClaw local gateway (primary — optional but recommended)
OPENCLAW_BASE_URL=http://127.0.0.1:18789/v1
OPENCLAW_API_KEY=your_openclaw_api_key_here
OPENCLAW_MODEL=openclaw

# Groq direct (fallback — required)
GROQ_API_KEY=your_gsk_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Note:** `OPENCLAW_API_KEY` is optional. If left empty, the bot skips OpenClaw entirely and uses Groq directly. `GROQ_API_KEY` is always required as the fallback.

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Run the Bot

```bash
python main.py
```

You should see:

```
INFO | __main__ | Starting YouTube AI Telegram Bot...
INFO | __main__ | Bot is running in polling mode. Press Ctrl+C to stop.
```

Open Telegram, find your bot, and send a YouTube URL!

---

## 💬 Usage

### Send a YouTube URL

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Bot responds with:**

```
🎥 VIDEO OVERVIEW
...

📌 5 KEY POINTS
1. ...
2. ...

⏱ IMPORTANT TIMESTAMPS
...

🧠 CORE TAKEAWAY
...
```

### Ask Questions

```
What did he say about pricing?
Who is the target audience?
Can you explain the main concept?
```

### Switch Language

```
Summarize in Hindi
Explain in Kannada
/language telugu
```

---

## 🤖 Bot Commands

| Command            | Description                            |
| ------------------ | -------------------------------------- |
| `/start`           | Welcome message and instructions       |
| `/help`            | Full help guide                        |
| `/summary`         | Regenerate video summary               |
| `/deepdive`        | In-depth analysis of the video         |
| `/actionpoints`    | Extract actionable items               |
| `/language [lang]` | Set language (e.g., `/language hindi`) |
| `/reset`           | Clear current video and start fresh    |
| `/status`          | Show session info and cache stats      |

---

## 🌐 Supported Languages

| Language        | Command                       |
| --------------- | ----------------------------- |
| English         | `/language english` (default) |
| Hindi (हिंदी)   | `/language hindi`             |
| Kannada (ಕನ್ನಡ) | `/language kannada`           |
| Tamil (தமிழ்)   | `/language tamil`             |
| Telugu (తెలుగు) | `/language telugu`            |
| Marathi (मराठी) | `/language marathi`           |

You can also say naturally: _"Summarize in Hindi"_ or _"Explain in Kannada"_

---

## 🏗️ Architecture

```
bot/
├── main.py                     # Entry point, bot setup, polling
├── config.py                   # Environment variables, constants
├── requirements.txt
├── .env.example
├── services/
│   ├── transcript.py           # YouTube transcript fetching & chunking
│   └── gemini_service.py       # Groq AI — summary, Q&A, deep dive, actions
├── handlers/
│   ├── commands.py             # /start, /help, /summary, /deepdive, etc.
│   ├── messages.py             # URL detection, Q&A routing, language switching
│   └── utils.py                # Language detection, message formatting
├── session/
│   └── manager.py              # Per-user session state management
└── cache/
    └── transcript_cache.py     # LRU + TTL cache for transcripts
```

### AI Request Flow

```
User Message
     │
     ▼
┌─────────────────────┐
│  OpenClaw Gateway   │  ← Primary (local, http://127.0.0.1:18789/v1)
│  (up to 3 retries)  │
└─────────────────────┘
     │ failure / rate-limit
     ▼
┌─────────────────────┐
│    Groq Direct      │  ← Fallback (cloud, api.groq.com)
│  (up to 3 retries)  │
└─────────────────────┘
     │
     ▼
  Response sent to user
```

### Architectural Decisions

#### 1. In-Memory Session Management

Each user gets a `UserSession` object stored in a dictionary keyed by `user_id`. This ensures:

- Complete isolation between users
- O(1) session lookup
- Automatic expiry after 60 minutes of inactivity

**Trade-off:** Sessions are lost on bot restart. For production, use Redis or a database.

#### 2. LRU Cache with TTL

Transcripts are cached using an `OrderedDict`-based LRU cache with a 24-hour TTL. This:

- Eliminates redundant YouTube API calls
- Reduces Groq API token usage
- Handles up to 50 videos concurrently

**Trade-off:** Memory-only. In production, persist to disk or Redis.

#### 3. Transcript Chunking

Long transcripts (>15,000 characters) are truncated for the model's context window. For very long videos, the first 15K characters are used for summary generation. Chunks overlap by 500 characters to maintain continuity.

**Trade-off:** The tail of very long videos may not be summarized. A future improvement would be map-reduce summarization across all chunks.

#### 4. Dual LLM Fallback — OpenClaw + Groq

**OpenClaw (Primary):**
- Runs locally at `http://127.0.0.1:18789/v1`
- Acts as a gateway/proxy — routes to Groq internally via its own config
- Adds a local caching/routing layer on top of Groq
- Uses the `openclaw` model identifier
- Completely optional — if `OPENCLAW_API_KEY` is not set, it is skipped

**Groq (Fallback):**
- Cloud API at `https://api.groq.com/openai/v1`
- Free tier with fast inference
- OpenAI-compatible API (no vendor lock-in)
- Multilingual capability via `llama-3.3-70b-versatile`
- Always required as the safety net

**Retry logic (in `services/gemini_service.py`):**
- OpenClaw: up to 3 attempts with 3s / 6s backoff
- Also detects rate-limit signals *inside* the response body (not just HTTP status codes)
- Groq: same retry logic independently
- Both clients use the `openai` Python SDK since both are OpenAI-API-compatible

#### 5. Grounded Q&A

The transcript is always passed in the prompt. The model is explicitly instructed to only answer from transcript content and respond with a standard "not covered" message if the information isn't present. This prevents hallucinations.

#### 6. Polling Mode

The bot uses long-polling (not webhooks) for local deployment. To switch to webhooks for production deployment, change `application.run_polling()` to `application.run_webhook()`.

---

## ☁️ Web Deployment (Railway / Render)

To deploy publicly (so the bot runs 24/7):

### Railway (Recommended)

1. Push code to GitHub
2. Go to [https://railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables in the Railway dashboard
4. Add a `Procfile`:
   ```
   worker: python main.py
   ```
5. Deploy — Railway will keep the bot running

### Render

1. Create a new **Background Worker** service
2. Connect your GitHub repo
3. Set environment variables
4. Build command: `pip install -r requirements.txt`
5. Start command: `python main.py`

---

## ⚠️ Edge Cases Handled

| Edge Case                       | Handling                                           |
| ------------------------------- | -------------------------------------------------- |
| Invalid YouTube URL             | Regex validation with clear error message          |
| Video unavailable/private       | `VideoUnavailable` exception caught                |
| No transcript/captions disabled | `TranscriptsDisabled` / `NoTranscriptFound` caught |
| Non-English transcript          | Auto-translated to English via API if possible     |
| Very long video                 | Truncated to 30K chars with user notification      |
| Q&A with no video loaded        | Prompts user to send a URL first                   |
| OpenClaw unavailable            | Automatically falls back to Groq direct            |
| Groq API failure                | Graceful error with retry suggestion after 3 attempts |
| Multiple users simultaneously   | Independent sessions via `user_id` key             |

---

## 🔧 Configuration

| Variable                  | Default                          | Required | Description                                                  |
| ------------------------- | -------------------------------- | -------- | ------------------------------------------------------------ |
| `TELEGRAM_BOT_TOKEN`      | —                                | ✅ Yes   | From BotFather on Telegram                                   |
| `OPENCLAW_BASE_URL`       | `http://127.0.0.1:18789/v1`      | ❌ No    | OpenClaw local gateway URL                                   |
| `OPENCLAW_API_KEY`        | —                                | ❌ No    | OpenClaw API key — if empty, OpenClaw is skipped entirely    |
| `OPENCLAW_MODEL`          | `openclaw`                       | ❌ No    | Model name for the OpenClaw gateway                          |
| `GROQ_API_KEY`            | —                                | ✅ Yes   | From console.groq.com — used as fallback (and primary if no OpenClaw) |
| `GROQ_BASE_URL`           | `https://api.groq.com/openai/v1` | ❌ No    | Groq API endpoint                                            |
| `GROQ_MODEL`              | `llama-3.3-70b-versatile`        | ❌ No    | Groq model to use                                            |
| `CACHE_MAX_SIZE`          | `50`                             | ❌ No    | Max number of cached transcripts                             |
| `CACHE_TTL_HOURS`         | `24`                             | ❌ No    | Hours before cache entry expires                             |
| `SESSION_TIMEOUT_MINUTES` | `60`                             | ❌ No    | Minutes before inactive session expires                      |

---

## 📝 License

MIT License — free to use and modify.
