# AI Question Bank & Quiz Tutor - Frontend

The frontend client for the AI Question Bank & Quiz Tutor platform. Built with **React 18**, **TypeScript**, and **Vite**, featuring an interactive AI Master Tutor with Server-Sent Events (SSE) streaming, quiz generator, interactive quiz player, and dataset ingestion.

---

## 🚀 Features

- **🧠 AI Master Tutor Chat**:
  - Full-featured chat interface with real-time SSE token streaming and typing animation.
  - Context-aware doubt resolution with dynamic answer modes (`SHORT`, `MEDIUM`, `DETAILED`, `PROBLEM_SOLVING`).
  - Seamless pronoun and follow-up handling (`"Explain in the large way"`, `"Tell me more about him"`, `"Give an example"`).
  - Context-bound **"Practice [Topic]"** action card to test concept understanding immediately.
- **⚡ Interactive Quiz Generator**:
  - Natural language prompt-based quiz creation (e.g., *"Give me 5 hard Physics questions"*).
  - Explicit subject and difficulty selection.
  - Previous Year Questions (PYQ) toggle for competitive exams.
- **🎮 Quiz Player**:
  - Live timer, progress tracking, and instant answer validation (Green / Red feedback).
  - Review mode with comprehensive question explanations and Gemini deep breakdowns.
  - Score calculations and summary cards.
- **📊 Dashboard & Overview**:
  - Instant view of system status, database health, total questions, and available subjects.
- **📥 Question Bank Import**:
  - Batch JSON question upload directly into PostgreSQL with automatic embedding computation.

---

## 🛠️ Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite 5
- **Icons**: Lucide React
- **HTTP Client**: Axios & Fetch API (for SSE Streams)
- **Styling**: Vanilla CSS (Tailored Design System with Dark/Light glassmorphism & responsive layouts)

---

## 📁 Project Structure

```text
frontend/
├── public/                 # Static assets
├── src/
│   ├── api/                # API client integration modules
│   │   ├── aiApi.ts        # AI Tutor chat SSE streaming & Gemini explanations
│   │   ├── healthApi.ts    # Backend & PostgreSQL health checks
│   │   ├── questionApi.ts  # Question listing & subject filters
│   │   └── quizApi.ts      # Quiz generation, submission & scoring
│   ├── components/         # Modular React UI components
│   │   ├── AITutorChat.tsx         # Full-screen AI Master Tutor Chat with SSE
│   │   ├── AITutorDrawer.tsx       # Slide-out AI Tutor chat drawer
│   │   ├── Dashboard.tsx           # Main navigation & health cards
│   │   ├── QuestionBankImport.tsx  # JSON dataset upload interface
│   │   ├── QuizGeneratorChat.tsx   # Natural language quiz creator
│   │   └── QuizPlayer.tsx          # Interactive quiz engine & score screen
│   ├── App.tsx             # Root application component & view routing
│   ├── index.css           # Global styles, variables, and animations
│   ├── main.tsx            # React application entry point
│   └── vite-env.d.ts       # Vite environment typings
├── .env                    # Environment variables (API base URL)
├── package.json            # Node.js dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite build configuration
```

---

## ⚙️ Environment Configuration

Create or update `.env` in the `frontend/` folder:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 📦 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
The app will be live at **[http://localhost:5173/](http://localhost:5173/)**

### 3. Build for Production
```bash
npm run build
```

---

## 🔗 Connected Backend Endpoints

| Frontend Service | API Route | Description |
| :--- | :--- | :--- |
| `aiApi.ts` | `POST /api/ai/chat/stream` | Real-time SSE streaming for AI Tutor Chat |
| `aiApi.ts` | `POST /api/ai/chat/create-quiz` | Generate 5-question quiz from learning context |
| `aiApi.ts` | `POST /api/ai/explain` | Request Gemini AI deep concept explanation |
| `healthApi.ts` | `GET /health`, `GET /health/postgres` | System & PostgreSQL status |
| `questionApi.ts` | `GET /api/questions/subjects` | Fetch unique available subjects |
| `quizApi.ts` | `POST /api/quizzes/generate` | Generate quiz session |
| `quizApi.ts` | `POST /api/quizzes/{id}/answers` | Submit answer & retrieve validation |
| `quizApi.ts` | `GET /api/quizzes/{id}/summary` | Retrieve final quiz scorecard |
| `questionApi.ts` | `POST /api/questions/import` | Ingest batch question JSON |
