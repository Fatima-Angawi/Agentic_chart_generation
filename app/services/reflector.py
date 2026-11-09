import base64
import json
import re
import os
from openai import OpenAI

def encode_image_to_b64_local(image_path: str) -> tuple[str, str]:
    """Encodes an image file into base64."""
    # Determine media type based on file extension
    ext = image_path.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg']:
        media_type = 'image/jpeg'
    elif ext == 'png':
        media_type = 'image/png'
    else:
        media_type = f'image/{ext}'

    with open(image_path, "rb") as image_file:
        b64_string = base64.b64encode(image_file.read()).decode('utf-8')

    return media_type, b64_string

def reflect_on_image_and_regenerate(
    chart_path: str,
    instruction: str,
    model_name: str,
    out_path_v2: str,
    code_v1: str,
) -> tuple[str, str]:
    """
    Critique the chart IMAGE and the original code against the instruction,
    then return refined matplotlib code using the configured OpenAI client directly.
    Returns (feedback, refined_code_with_tags).
    """
    media_type, b64 = encode_image_to_b64_local(chart_path)

    prompt = f"""
    You are a data visualization expert.
    Your task: critique the attached chart and the original code against the given instruction,
    then return improved matplotlib code.

    Original code (for context):
    {code_v1}

    OUTPUT FORMAT (STRICT):
    1) First line: a valid JSON object with ONLY the "feedback" field.
    Example: {{\"feedback\": \"The legend is unclear and the axis labels overlap.\"}}

    2) After a newline, output ONLY the refined Python code wrapped in:
    <execute_python>
    ...
    </execute_python>

    3) Import all necessary libraries in the code. Don\'t assume any imports from the original code.

    HARD CONSTRAINTS:
    - Do NOT include Markdown, backticks, or any extra prose outside the two parts above.
    - Use pandas/matplotlib only (no seaborn).
    - Assume df already exists; do not read from files.
    - Save to \'{out_path_v2}\' with dpi=300.
    - Always call plt.close() at the end (no plt.show()).
    - Include all necessary import statements.
    - Do NOT use ax.bar_label / plt.bar_label. If you want value labels, use ax.text with f-strings.
    - Only use plain format strings such as f\"{{v:,.0f}}\" (no spaces inside the format specifier).
    - Stick to basic, widely supported matplotlib functions.

    Instruction:
    {instruction}
    """

    # Call OpenAI API directly
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content

    # --- Parse ONLY the first JSON line (feedback) ---
    lines = content.strip().splitlines()
    json_line = lines[0].strip() if lines else ""

    try:
        obj = json.loads(json_line)
    except Exception as e:
        # Fallback: try to capture the first {...} in all the content
        m_json = re.search(r"\{.*?\}", content, flags=re.DOTALL)
        if m_json:
            try:
                obj = json.loads(m_json.group(0))
            except Exception as e2:
                obj = {"feedback": f"Failed to parse JSON: {e2}", "refined_code": ""}
        else:
            obj = {"feedback": f"Failed to find JSON: {e}", "refined_code": ""}

    # --- Extract refined code from <execute_python>...</execute_python> ---
    m_code = re.search(r"<execute_python>([\s\S]*?)</execute_python>", content)
    refined_code_body = m_code.group(1).strip() if m_code else ""
    refined_code = f"<execute_python>\n{refined_code_body}\n</execute_python>"

    feedback = str(obj.get("feedback", "")).strip()
    return feedback, refined_code
