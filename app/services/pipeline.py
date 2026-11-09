import os
from fastapi import HTTPException
from openai import OpenAIError
from app import config
from app.execution.runner import run_code
from app.services.code_generator import generate_chart_code
from app.services.reflector import reflect_on_image_and_regenerate
from app.validators.code_validator import extract_code, validate_code
from app.validators.data_validator import validate_data
from app.validators.semantic_validator import validate_semantics


def validate_all(code, df, out_path):
    return validate_code(code, out_path) or validate_data(code, df) or validate_semantics(code)


def build_chart_v1(df, user_instructions, data_path, job_dir):
    instructions = user_instructions
    errors = []

    for attempt in range(config.MAX_RETRIES + 1):
        code_v1 = generate_chart_code(config.MODEL, df, instructions, config.OUT_PATH_V1)
        code = extract_code(code_v1)
        errors = validate_all(code, df, config.OUT_PATH_V1)

        if not errors:
            run = run_code(code, data_path, job_dir, config.OUT_PATH_V1)
            if run["success"]:
                return code_v1
            errors = [run["error"]]

        instructions = user_instructions + "\n\nThe previous code failed with these errors, fix them:\n" + "\n".join(errors)

    raise HTTPException(status_code=422, detail={"message": "تعذر إنشاء الرسمة", "errors": errors})


def build_chart_v2(df, user_instructions, data_path, job_dir, code_v1):
    try:
        feedback, code_v2 = reflect_on_image_and_regenerate(
            chart_path=os.path.join(job_dir, config.OUT_PATH_V1),
            instruction=user_instructions,
            model_name=config.MODEL,
            out_path_v2=config.OUT_PATH_V2,
            code_v1=code_v1,
        )
    except OpenAIError:
        return False

    code = extract_code(code_v2)
    if validate_all(code, df, config.OUT_PATH_V2):
        return False
    return run_code(code, data_path, job_dir, config.OUT_PATH_V2)["success"]


def create_chart(df, user_instructions, job_dir):
    data_path = os.path.join(job_dir, "data.pkl")
    df.to_pickle(data_path)

    code_v1 = build_chart_v1(df, user_instructions, data_path, job_dir)
    improved = build_chart_v2(df, user_instructions, data_path, job_dir, code_v1)
    out_path = config.OUT_PATH_V2 if improved else config.OUT_PATH_V1

    with open(os.path.join(job_dir, out_path), "rb") as f:
        return f.read()