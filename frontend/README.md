# Aether Ledger — Frontend Web Application

A modern, responsive, role-based single-page application built with **HTML5**, **Vanilla CSS**, and **ES Modules (Vite)** providing an interactive interface for the Transaction Ledger API.

---

## 🌟 Key Features

1. **Role-Based Architecture**:
   - **Admin Console (Super Admin Treasury)**: System-wide financial metrics, treasury balance oversight, account creation modal, global ledger journal, direct deposit/withdrawal adjustments, and inter-account fund transfers.
   - **Account Holder Portal (Customer View)**: Virtual holographic debit card with live balance, quick actions (Send Money, Add Funds, Withdraw), real-time transaction activity feed with credit/debit filter chips and search.
2. **Real-Time Synchronisation**:
   - Live updates against the FastAPI backend REST API (`http://127.0.0.1:8000`).
   - Built-in API configuration modal to dynamically reconfigure the backend endpoint.
3. **Optimized User Experience**:
   - Glassmorphism design system with modern typography (`Outfit` and `JetBrains Mono`).
   - Dynamic toasts, balance counters, transaction validation hints, and smooth micro-interactions.

---

## 🚀 Running Frontend Locally

### 1. Prerequisites
- Node.js 18+
- npm / pnpm / yarn

### 2. Install & Start
```bash
# Navigate to the frontend directory
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```

The application will be served at `http://localhost:5173/`.

### 3. Build for Production
```bash
npm run build
npm run preview
```

---

## 📁 Frontend Directory Structure

```
frontend/
├── index.html         # Application shell with dual-view layout (Admin & Customer)
├── package.json       # Vite dev server configuration
├── vite.config.js     # Dev server port & host configuration
├── src/
│   ├── api.js         # REST client communicating with FastAPI backend
│   ├── state.js       # Reactive client-side state store & event dispatcher
│   ├── main.js        # UI controller, event listeners, view switcher & rendering
│   └── style.css      # Custom design tokens, glassmorphic themes, animations
└── README.md          # Frontend documentation
```
