# 💎 Retouch Gem

> ✨ AI-powered virtual jewelry try-on — see any gemstone come to life on your hand, ear, or neck in seconds.

Retouch Gem uses **Google Gemini AI** to generate stunning, photorealistic jewelry previews. Upload a loose gemstone, pick your dream setting, and watch it transform into a wearable piece — powered by a sophisticated two-pass AI pipeline.

![Next.js](https://img.shields.io/badge/Next.js-black?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=flat-square&logo=google&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

---

## 🚀 How It Works

```
📸 Upload Gem Photo  →  🔍 AI Analyzes Gem  →  💍 Pick Your Setting  →  🖼️ Photorealistic Preview
```

1. **🔬 Pass 1 — Gem Analysis** → `gemini-2.5-flash` extracts the gem's color, cut, facets, brilliance, and unique features as structured text.
2. **🎨 Pass 2 — Jewelry Rendering** → `gemini-3-pro-image-preview` composes a photorealistic preview using 3 reference images:
   - 💎 Gem product photo (color & brilliance reference)
   - 🤚 Gem context photo on a real hand (size ground truth)
   - 📷 Customer/model body photo (base image to edit)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| 🖥️ **Frontend** | Next.js 15 · React 19 · TypeScript · Tailwind CSS v4 |
| ⚡ **Backend** | FastAPI · Python 3.11+ · Pydantic v2 |
| 🧠 **AI Engine** | Google Gemini API (`gemini-2.5-flash` + `gemini-3-pro-image-preview`) |
| 🗄️ **Database** | Supabase (PostgreSQL) |
| 📦 **Storage** | Supabase Storage |

---

## 📋 Prerequisites

- 🟢 **Node.js** 18+
- 🐍 **Python** 3.11+
- 🔑 **Google Gemini API Key** — [Get one here](https://aistudio.google.com/apikey)
- 🟩 **Supabase Project** — [Create one here](https://supabase.com)

---

## ⚙️ Setup

### 1️⃣ Clone & Install

```bash
git clone https://github.com/Waiphyoaung24/AI-Retouch-Gem.git
cd AI-Retouch-Gem
```

### 2️⃣ Backend

```bash
cd backend
pip install -e .
```

Create a `.env` file:

```env
GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
ADMIN_PASSWORD=your_secret_password
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8001
```

### 3️⃣ Frontend

```bash
cd frontend
npm install
```

Create a `.env` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001/api
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Start the dev server:

```bash
npm run dev -- -p 3001
```

### 4️⃣ Database

Run the migration files in your **Supabase SQL Editor** (in order):

```
backend/migrations/001_gem_preview_schema.sql
backend/migrations/002_seed_prompt_templates.sql
backend/migrations/003_add_gem_dimensions.sql
```

---

## 🎮 Usage

### 👑 Admin Panel

1. Navigate to `http://localhost:3001/admin/login`
2. Enter your admin password
3. **Upload gems** — product photo + context photo (gem on hand for size reference)
4. **Add model photos** — hand/ear/neck photos for customers to try on
5. **Manage settings** — categories, metals, and styles

### 💍 Customer Experience

1. Share a gem link with your customer: `http://localhost:3001/gem/{gem_id}`
2. Customer selects their preferred **category** (Ring, Earring, Pendant)
3. Picks a **metal** (Gold, White Gold, Rose Gold, Silver, Platinum)
4. Chooses a **style** (Solitaire, Halo, Three-Stone, Pavé, and more)
5. Uses a model photo or uploads their own
6. 🪄 AI generates a photorealistic jewelry preview in seconds!

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   🖥️ Frontend                       │
│            Next.js 15 · Port 3001                   │
│                                                     │
│  /gem/[id]        → Customer preview page           │
│  /admin/gems      → Gem management                  │
│  /admin/model-photos → Model photo management       │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                   ⚡ Backend                         │
│             FastAPI · Port 8001                      │
│                                                     │
│  Pass 1: gemini-2.5-flash (TEXT)                    │
│    → Analyze gem characteristics                    │
│                                                     │
│  Pass 2: gemini-3-pro-image-preview (IMAGE)         │
│    → 3-image composition → photorealistic preview   │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │     🗄️ Supabase         │
          │  PostgreSQL + Storage   │
          └─────────────────────────┘
```

---

## 📁 Project Structure

```
retouch-gem/
├── 🖥️ frontend/
│   ├── src/app/
│   │   ├── gem/[id]/       # 💍 Customer gem preview page
│   │   ├── admin/gems/     # 💎 Gem management
│   │   ├── admin/model-photos/  # 📸 Model photo management
│   │   └── admin/login/    # 🔐 Admin authentication
│   └── src/lib/api.ts      # 🔌 API client
│
├── ⚡ backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── try_on.py   # 🧠 Prompt engineering & generation endpoint
│   │   │   ├── gems.py     # 💎 Gem CRUD
│   │   │   ├── model_photos.py  # 📸 Model photo CRUD
│   │   │   └── settings.py # ⚙️ Settings (categories, metals, styles)
│   │   ├── services/
│   │   │   └── gemini_service.py  # 🤖 Gemini AI integration
│   │   └── models/schemas.py     # 📐 Pydantic models
│   └── migrations/         # 🗄️ SQL migration files
│
└── 📄 docs/plans/          # 📝 Architecture & design documents
```

---

## 🌟 Key Features

- 🎯 **Accurate Gem Sizing** — Context photo provides visual ground truth for real-world proportions
- 🔮 **Two-Pass AI Pipeline** — Analysis pass extracts gem identity, generation pass creates the preview
- 💎 **Multi-Category Support** — Rings, earrings, and pendants with category-specific styles
- 🪞 **5 Metal Options** — Gold, White Gold, Rose Gold, Silver, and Platinum
- 📱 **Customer-Facing Links** — Share gem links directly with customers
- 🖼️ **2K Resolution Output** — High-resolution previews for professional use
- 🔐 **Admin Dashboard** — Full CRUD for gems, model photos, and settings

---

## 📜 License

MIT

---

<p align="center">
  Made with 💎 and 🤖 by <a href="https://github.com/Waiphyoaung24">Wai Phyo Aung</a>
</p>
