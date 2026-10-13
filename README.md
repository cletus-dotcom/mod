# Motorela Operator and Driver Registry

Municipal desk for the Municipality of Jagna, Province of Bohol. Staff search and update the motorela roll, and print identification cards from the official template.

## Run locally

1. Install Docker, then start Postgres:

```bash
docker compose up -d
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy the environment file and set a secret key:

```bash
copy .env.example .env
```

4. Place the source workbook at `data/motorela-source.xlsx`. The first start imports it when the registry is empty. The ID artwork ships at `data/motorela_id.pdf`.

5. Start the app:

```bash
python run.py
```

Open `http://127.0.0.1:8036`.

On a new database, the first administrator and staff passwords are written to `data/initial_accounts.txt`. Sign-in requires a new password before the desk opens. Set `ADMIN_PASSWORD` and `STAFF_PASSWORD` in `.env` before that first start if you want to choose them.

## What stays off GitHub

`.env`, uploaded ID photos, `data/initial_accounts.txt`, and the Excel workbook are ignored. The workbook contains personal records. Do not remove those lines from `.gitignore`.
