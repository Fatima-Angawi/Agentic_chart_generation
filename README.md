# Chart Agent

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows, use `.venv\Scripts\activate` and `copy .env.example .env`.

Add your `OPENAI_API_KEY` to the `.env` file before running.

## Usage

Open `http://127.0.0.1:8000/docs` or use:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/charts \
  -F "file=@data.csv" \
  -F "instructions=Create a bar chart of average sales by region" \
  --output chart.png
```

## Tests

```bash
pytest
```
