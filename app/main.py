from fastapi import FastAPI
from app.api.charts import router

app = FastAPI(title="Chart Agent")
app.include_router(router)