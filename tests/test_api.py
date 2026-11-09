import json
import types
import pytest
from fastapi.testclient import TestClient
from app import config
from app.execution.runner import run_code
from app.main import app

PNG = b"\x89PNG"

CSV = b"region,sales\nA,10\nB,20\nA,30\n"

INTENT = {"chart_type": "bar", "x": "region", "y": ["sales"], "aggregation": "sum", "filters": None}


def chart_code(out_path, title="Sales"):
    return f"""<execute_python>
import matplotlib.pyplot as plt
g = df.groupby("region")["sales"].sum().reset_index()
fig, ax = plt.subplots()
ax.bar(g["region"], g["sales"])
ax.set_title("{title}")
ax.set_xlabel("Region")
ax.set_ylabel("Sales")
plt.savefig("{out_path}", dpi=300)
plt.close()
</execute_python>"""


class FakeLLM:
    def __init__(self, codes, reflection):
        self.codes = list(codes)
        self.reflection = reflection
        self.prompts = []

    def create(self, **kw):
        if "response_format" in kw:
            text = json.dumps(INTENT)
        elif isinstance(kw["messages"][0]["content"], list):
            text = self.reflection
        else:
            self.prompts.append(kw["messages"][1]["content"])
            text = self.codes.pop(0) if len(self.codes) > 1 else self.codes[0]
        message = types.SimpleNamespace(content=text)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def install(monkeypatch, fake):
    client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=fake))
    for module in ["code_generator", "reflector", "llm_client"]:
        monkeypatch.setattr(f"app.services.{module}.OpenAI", lambda api_key=None: client)


def post(content=CSV, name="a.csv"):
    return TestClient(app).post(
        "/api/v1/charts",
        files={"file": (name, content)},
        data={"instructions": "bar chart of total sales by region"},
    )


def reflection(body):
    return '{"feedback": "ok"}\n' + body


def test_returns_v2_chart(monkeypatch):
    install(monkeypatch, FakeLLM([chart_code("chart_v1.png")], reflection(chart_code("chart_v2.png", "Better"))))
    response = post()
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(PNG)


def test_falls_back_to_v1(monkeypatch):
    bad = reflection("<execute_python>\nimport os\n</execute_python>")
    install(monkeypatch, FakeLLM([chart_code("chart_v1.png")], bad))
    response = post()
    assert response.status_code == 200
    assert response.content.startswith(PNG)


def test_retry_sends_errors_to_model(monkeypatch):
    fake = FakeLLM(["<execute_python>\nimport os\n</execute_python>", chart_code("chart_v1.png")], reflection(chart_code("chart_v2.png")))
    install(monkeypatch, fake)
    assert post().status_code == 200
    assert len(fake.prompts) == 2
    assert "import 'os' is not allowed" in fake.prompts[1]


def test_runtime_error_is_retried_then_422(monkeypatch):
    failing = chart_code("chart_v1.png").replace('g = df', 'x = 1 / 0\ng = df')
    fake = FakeLLM([failing], reflection(""))
    install(monkeypatch, fake)
    response = post()
    assert response.status_code == 422
    assert len(fake.prompts) == config.MAX_RETRIES + 1
    assert "division" in response.json()["detail"]["errors"][0]


def test_rejects_large_file(monkeypatch):
    monkeypatch.setattr(config, "MAX_FILE_SIZE", 5)
    assert post().status_code == 413


def test_rejects_bad_type():
    assert post(name="a.txt").status_code == 400


def test_worker_has_no_api_key(tmp_path, monkeypatch):
    import pandas as pd
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    data = tmp_path / "d.pkl"
    pd.DataFrame({"a": [1]}).to_pickle(data)
    code = "import os\nopen('out.txt', 'w').write(os.environ.get('OPENAI_API_KEY', 'none'))"
    assert run_code(code, str(data), str(tmp_path), "out.txt")["success"]
    assert (tmp_path / "out.txt").read_text() == "none"


def test_timeout(tmp_path, monkeypatch):
    import pandas as pd
    monkeypatch.setattr(config, "EXECUTION_TIMEOUT", 3)
    data = tmp_path / "d.pkl"
    pd.DataFrame({"a": [1]}).to_pickle(data)
    assert not run_code("while True:\n    pass", str(data), str(tmp_path), "out.png")["success"]
