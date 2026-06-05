# Sentilytics

AI-powered YouTube sentiment and engagement analysis.

Sentilytics is a web app that analyzes YouTube videos by combining live comment sentiment scoring, engagement metrics, and AI content verification. The frontend is built with React, Tailwind, and TanStack Router, while the backend uses Flask plus the YouTube Data API and optional Gemini AI verification.

## Features

- Analyze YouTube video sentiment from comments
- Display estimated positive / neutral / negative sentiment ratios
- Show engagement, likes, views, and AI-powered content verdicts
- Built with a modern React + Vite frontend
- Flask backend for YouTube API access, comment analysis, and transcript / AI verification

## Tech stack

- Frontend
  - React 19
  - Vite
  - TanStack Router
  - TanStack React Query
  - Tailwind CSS
  - Radix UI primitives
  - Lucide icons
- Backend
  - Python 3
  - Flask
  - Flask-CORS
  - vaderSentiment
  - google-api-python-client
  - youtube-transcript-api
  - dotenv
  - google-generative-ai (Gemini)

## Getting started

### Prerequisites

- Node.js 20+ and npm / pnpm
- Python 3.11+ or compatible Python 3 runtime
- YouTube Data API key
- Optional: Google Gemini API key for AI verification

### Setup

1. Install frontend dependencies:

   ```bash
   npm install
   ```

2. Create a Python virtual environment and install backend dependencies:

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file at the project root with the following values:

   ```env
   YOUTUBE_API_KEY=your_youtube_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

   - `GEMINI_API_KEY` is optional. If missing, the app will still analyze comments but will skip AI verification.

### Running locally

Start the backend Flask server:

```bash
python app.py
```

Then start the frontend development server:

```bash
npm run dev
```

Open the Vite URL shown in the terminal, and use the app to analyze YouTube video URLs.

## Scripts

- `npm run dev` — start the frontend development server
- `npm run build` — build the frontend for production
- `npm run preview` — preview the built frontend
- `npm run lint` — run ESLint
- `npm run format` — format files with Prettier

## Environment variables

- `YOUTUBE_API_KEY` — required to fetch video metadata and comments from the YouTube Data API
- `GEMINI_API_KEY` — optional AI key used for transcript-based content verification

## Project structure

- `app.py` — Flask backend entrypoint and analysis API
- `src/` — React frontend source code
- `src/routes/` — app routes and page components
- `src/styles.css` — app styling and Tailwind imports
- `package.json` — frontend dependencies and scripts
- `bunfig.toml` — package manager install guard configuration

## Notes

- The frontend calls `/analyze?url=...` on the backend, so both servers should be running concurrently in development.
- If comments are unavailable or disabled for a video, the backend returns a fallback response.
- AI verification will only run if `GEMINI_API_KEY` is configured.

## License

This repository currently does not specify a license. Add a `LICENSE` file if you want to make this project open source.
