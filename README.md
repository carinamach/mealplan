# Meal Plan

A beginner-friendly meal-planning web app built with Flask. It helps you browse recipes, generate weekly meal plans, and produce aggregated shopping lists.

## Quick start (local)

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app in development:

```bash
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

## Features

- Browse and filter recipes
- Save favorites in-session
- Create a daily/weekly meal plan based on simple profile targets
- Auto-generate shopping lists with aggregated ingredient quantities

## Demo steps (2–4 minutes)

1. Open the app and go to "Recipes" to browse and apply filters.
2. Visit "Profile" and enter your age/weight/height to set targets.
3. Go to "Meal Plan" and use auto-generate or manually assign meals.
4. Open "Shopping List" to view aggregated ingredients and export/print.

## Deployment (recommended: Render)

For this Flask app the simplest production deploy is a small PaaS (Render, Railway, or Heroku). Example for Render:

1. Ensure `requirements.txt` includes `flask` and add `gunicorn`.
2. Add a `Procfile` containing:

```
web: gunicorn app:app
```

3. Push your repo to GitHub and create a new Web Service on Render connected to the repo.
4. Set `SECRET_KEY` (and any env vars) in the Render dashboard and deploy.

Serverless hosts (Vercel) are possible but require adapting routes to serverless functions or using a container image.

## Tests

Run the unit tests included in the repo with:

```bash
pytest -q
```

## Next steps

- Add CI to run tests and linting on push
- Add end-to-end tests for the main flows
- Add user accounts to persist plans across sessions

If you want, I can create the `Procfile` and update `requirements.txt` now for Render deployment.
