import tempfile
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from openai import OpenAIError
from app import config
from app.services.file_loader import load_file
from app.services.pipeline import create_chart

router = APIRouter(prefix="/api/v1")


@router.post("/charts")
def create_chart_endpoint(file: UploadFile = File(...), instructions: str = Form(...)):
    content = file.file.read(config.MAX_FILE_SIZE + 1)
    if len(content) > config.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="حجم الملف أكبر من الحد المسموح")

    df = load_file(file.filename, content)

    try:
        with tempfile.TemporaryDirectory() as job_dir:
            chart = create_chart(df, instructions, job_dir)
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"حدث خطأ أثناء الاتصال بالنموذج: {e}")

    return Response(content=chart, media_type="image/png")