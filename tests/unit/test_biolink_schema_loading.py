"""
Tests for biolink schema loading functionality in validate_biolink_kgx.py
TODO: does this code belong in bmt.pydantic?
"""

import pytest
from importlib.resources import files
from linkml_runtime.utils.schemaview import SchemaView

from bmt.pydantic import get_biolink_schema


@pytest.fixture(autouse=True)
def clear_lru_cache():
    """Clear the LRU cache before each test."""
    get_biolink_schema.cache_clear()
    yield
    get_biolink_schema.cache_clear()

def test_can_import_biolink_model():
    """Test that we can access biolink_model resources with importlib."""
    with files("biolink_model.schema").joinpath("biolink_model.yaml") as schema_file:
        assert schema_file.exists()


def test_can_load_schema_from_local_biolink_model():
    """Test that we can load biolink schema from a local biolink_model import."""
    with files("biolink_model.schema").joinpath("biolink_model.yaml") as schema_file:
        schema_view = SchemaView(str(schema_file))
        assert schema_view is not None
        assert hasattr(schema_view, 'schema')
        assert schema_view.schema is not None

        # Verify this is actually a biolink schema
        assert schema_view.get_class("named thing") is not None
        assert schema_view.get_slot("related to") is not None

def test_can_load_schema_from_url():
    """Test that we can load biolink schema from the official URL."""
    schema_view = SchemaView("https://w3id.org/biolink/biolink-model.yaml")
    assert schema_view is not None
    assert hasattr(schema_view, 'schema')
