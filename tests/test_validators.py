import pandas as pd
from app.validators.code_validator import extract_code, validate_code
from app.validators.data_validator import validate_data
from app.validators.semantic_validator import validate_semantics

OUT = "chart_v1.png"

df = pd.DataFrame({
    "year": [2024, 2024, 2025],
    "quarter": [1, 2, 1],
    "sales": [10.0, 20.0, 30.0],
    "region": ["A", "B", "A"],
})

GOOD = """
import matplotlib.pyplot as plt
d = df[df["year"] == 2024].copy()
g = d.groupby("quarter")["sales"].sum().reset_index()
fig, ax = plt.subplots()
ax.bar(g["quarter"], g["sales"])
ax.set_title("Sales")
ax.set_xlabel("Quarter")
ax.set_ylabel("Sales")
plt.savefig("chart_v1.png", dpi=300)
plt.close()
"""

INTENT = {"chart_type": "bar", "x": "quarter", "y": ["sales"], "aggregation": "sum", "filters": {"year": [2024]}}


def test_extract_code():
    assert extract_code("<execute_python>\nx=1\n</execute_python>") == "x=1"
    assert extract_code("nothing") is None


def test_good_code_passes():
    assert validate_code(GOOD, OUT)["valid"]
    assert validate_data(GOOD, df)["valid"]
    assert validate_semantics(GOOD, df, INTENT)["valid"]


def test_code_validator_blocks_imports():
    assert not validate_code("import os", OUT)["valid"]


def test_data_validator_suggests_column():
    result = validate_data("df['sale']", df)
    assert "Did you mean 'sales'" in result["errors"][0]


def test_semantic_validator_chart_type():
    result = validate_semantics(GOOD.replace("ax.bar(", "ax.scatter("), df, INTENT)
    assert not result["valid"]
