import sys
import pandas as pd
import matplotlib.pyplot as plt

def run_generated_code(code_str: str, df):
    # تعريف المساحة المحلية عشان الكود يقدر يشوف الـ df و plt
    local_vars = {"df": df, "plt": plt}

    try:
        exec(code_str, {}, local_vars)
        print("تم تنفيذ الكود وحفظ الرسمة بنجاح!")
    except Exception as e:
        print(f"حدث خطأ أثناء تنفيذ الكود: {e}")

if __name__ == "__main__":
    code_path, data_path = sys.argv[1], sys.argv[2]
    with open(code_path, encoding="utf-8") as f:
        code = f.read()
    df = pd.read_pickle(data_path)
    run_generated_code(code, df)