import ast
import difflib
import re


def string_values(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.List):
        return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def validate_data(code, df):
    if re.search(r"\bdf\s*=[^=]|inplace\s*=\s*True", code):
        return []

    known = set(df.columns)
    used = []

    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "df":
            if isinstance(node.ctx, ast.Store):
                known.update(string_values(node.slice))
            else:
                used += string_values(node.slice)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "groupby":
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "df" and node.args:
                used += string_values(node.args[0])

    errors = []
    for col in used:
        if col not in known:
            close = difflib.get_close_matches(col, known, n=1)
            hint = f" Did you mean '{close[0]}'?" if close else ""
            errors.append(f"column '{col}' does not exist.{hint}")

    return list(dict.fromkeys(errors))