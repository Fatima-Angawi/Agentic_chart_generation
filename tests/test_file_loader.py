import io
import pandas as pd
import pytest
from fastapi import HTTPException
from app.services.file_loader import load_file


def test_csv_utf8():
    df = load_file("a.csv", " name ,sales\nأحمد,1\n".encode("utf-8-sig"))
    assert df.columns.tolist() == ["name", "sales"]
    assert df["name"][0] == "أحمد"


def test_csv_cp1256():
    df = load_file("a.csv", "name,sales\nأحمد,1\n".encode("cp1256"))
    assert df["name"][0] == "أحمد"


def test_xlsx():
    buffer = io.BytesIO()
    pd.DataFrame({"a": [1, 2]}).to_excel(buffer, index=False)
    assert len(load_file("a.xlsx", buffer.getvalue())) == 2


@pytest.mark.parametrize("name,content", [
    ("a.txt", b"a,b\n1,2\n"),
    ("a.csv", b""),
    ("a.csv", b"a,b\n"),
    ("a.xlsx", b"not excel"),
    (None, b"a\n1\n"),
])
def test_rejected_files(name, content):
    with pytest.raises(HTTPException) as e:
        load_file(name, content)
    assert e.value.status_code == 400
