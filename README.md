# LandChain (KhestraBlocks HackIndia MVP)

A demo blockchain-based property registry platform for hackathon judging.

## Features
- Demo Google login flow.
- Identity verification upload (Aadhaar / Government ID / Property docs).
- Wallet generation (public/private key and wallet address).
- Property marketplace with filters (city, zone, price, size).
- Property details and ownership transfer flow.
- Fake blockchain block creation using SHA-256 hashing.
- Public blockchain explorer.
- Government authority dashboard for Proof-of-Authority style approvals.

## Tech Stack
- Frontend: HTML, CSS, JavaScript-ready templates with glassmorphism style.
- Backend: Python + Flask.
- Database: SQLite.
- Blockchain simulation: Python module.

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Deploy on Vercel
This repo is now configured for Vercel using:
- `api/index.py` as the Vercel Python entrypoint.
- `vercel.json` to route all traffic to Flask.

### 1) Push your code to GitHub
```bash
git add .
git commit -m "Prepare Vercel deployment"
git push origin <your-branch>
```

### 2) Import project in Vercel
1. Go to [vercel.com](https://vercel.com).
2. Click **Add New Project**.
3. Import your GitHub repository.
4. Framework preset: **Other** (or let Vercel auto-detect Python).
5. Deploy.

### 3) Set environment variables (recommended)
In Vercel Project Settings → Environment Variables, add:
- `SECRET_KEY`: a random secure string.

### 4) Redeploy
Trigger redeploy after adding env vars.

### Important note about SQLite on Vercel
Vercel serverless filesystem is ephemeral, so `landchain.db` is not durable across cold starts/deployments.

For hackathon demo this is usually fine. For persistent production-style data, switch to a hosted DB (e.g., Neon/Postgres, Supabase, PlanetScale, or Turso).

## Demo Flow
1. Login with Google (demo form).
2. Upload identity documents.
3. Generate wallet.
4. Register / browse properties in marketplace.
5. Transfer ownership from property detail page.
6. View generated block in Blockchain Explorer.
7. Review pending approvals in Government Node dashboard.
