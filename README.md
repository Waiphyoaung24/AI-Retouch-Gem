# Retouch Gem

A jewellery virtual try-on application using Google Gemini AI.

## Prerequisites

- Node.js 18+
- Python 3.11+
- Google Gemini API Key

## Setup

1.  **Backend**
    ```bash
    cd backend
    pip install -r requirements.txt
    # Create .env and set GOOGLE_API_KEY
    cp .env.example .env
    uvicorn app.main:app --reload
    ```

2.  **Frontend**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Admin Access

-   URL: `http://localhost:3000/admin`
-   Key: `secret123` (or set in `.env`)

## Usage

1.  Go to `http://localhost:3000/admin` and login.
2.  Upload some jewellery products.
3.  Upload some hand model photos.
4.  Go to `http://localhost:3000` or `http://localhost:3000/try-on`.
5.  Select a product and a hand model, then click "Try On".

## Exposing to the Internet

To expose both the frontend and backend using ngrok:

1.  Ensure `ngrok` is installed.
2.  Run the following command from the project root:
    ```bash
    ngrok start --all --config=ngrok.yml
    ```
3.  **Important:** If you access the frontend via its public ngrok URL, you must update the `NEXT_PUBLIC_API_URL` environment variable in `frontend/.env.local` to point to the *backend's* public ngrok URL. Otherwise, the frontend will try to connect to `localhost:8000` which won't work from other devices.

## Architecture

-   **Frontend:** Next.js, Tailwind CSS
-   **Backend:** FastAPI, Python, Google Gen AI SDK
-   **Storage:** Local filesystem (uploads/) and JSON files (data/)
