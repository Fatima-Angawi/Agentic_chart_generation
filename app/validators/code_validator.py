import ast
import re

ALLOWED_IMPORTS = {"pandas", "numpy", "matplotlib", "datetime", "math", "calendar"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "input", "getattr", "setattr", "delattr", "globals", "locals", "vars", "breakpoint"}
FORBIDDEN_ATTRS = {
    "show", "bar_label", "load", "save", "savetxt",
    "read_csv", "read_excel", "read_json", "read_sql", "read_parquet", "read_pickle", "read_html",
    "to_csv", "to_excel", "to_json", "to_sql", "to_parquet", "to_pickle", "to_html",
}


def extract_code(response):
    match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", response or "")
    return match.group(1).strip() if match else None


def validate_code(code, out_path):
    if not code:
        return ["No code was found in the model response"]

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"SyntaxError at line {e.lineno}: {e.msg}"]

    errors = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]

        for name in names:
            if name.split(".")[0] not in ALLOWED_IMPORTS:
                errors.append(f"import '{name}' is not allowed")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            errors.append(f"call to '{node.func.id}' is not allowed")
        if isinstance(node, ast.Attribute) and (node.attr in FORBIDDEN_ATTRS or node.attr.startswith("__")):
            errors.append(f"attribute '{node.attr}' is not allowed")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            errors.append(f"name '{node.id}' is not allowed")

    if re.search(r"\bdf\s*=\s*pd\.DataFrame", code):
        errors.append("do not create a new df, use the existing one")
    if out_path not in code:
        errors.append(f"the chart must be saved to '{out_path}'")

    return errors