import io
import os
import pandas as pd
from fastapi import HTTPException


def read_csv_file(content):
    try:
        return pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(io.BytesIO(content), encoding="cp1256")


def convert_date_columns(df):
    for col in df.columns:
        if ("date" in col.lower() or "تاريخ" in col) and not pd.api.types.is_numeric_dtype(df[col]):
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notna().mean() > 0.9:
                df[col] = converted
    return df


def load_file(filename, content):
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in [".csv", ".xlsx"]:
        raise HTTPException(status_code=400, detail="الملفات المدعومة هي csv و xlsx فقط")

    try:
        df = read_csv_file(content) if ext == ".csv" else pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"تعذر قراءة الملف: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="الملف لا يحتوي على بيانات")

    df.columns = df.columns.astype(str).str.strip()
    return convert_date_columns(df)