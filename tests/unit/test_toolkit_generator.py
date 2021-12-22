import pytest
from bmt import ToolkitGenerator

REMOTE_PATH = (
    "https://raw.githubusercontent.com/biolink/biolink-model/2.2.12/biolink-model.yaml"
)

def test_get_generator():
    gen = ToolkitGenerator(REMOTE_PATH)
    tk = gen.serialize()
    print(tk)
