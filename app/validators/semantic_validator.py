import ast

CHART_METHODS = {
    "plot", "bar", "barh", "scatter", "pie", "hist", "boxplot", "box", "line", "area",
    "imshow", "matshow", "pcolormesh", "violinplot", "stackplot", "errorbar", "step", "hexbin",
}


def validate_semantics(code):
    calls = {
        node.func.attr for node in ast.walk(ast.parse(code))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    errors = []
    if not calls & CHART_METHODS:
        errors.append("The code does not draw any chart")
    if "title" not in code:
        errors.append("Chart title is missing")

    return errors