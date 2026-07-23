from io import StringIO
from unittest.mock import Mock

import pytest
import requests
import yaml
from linkml_runtime.linkml_model.meta import SchemaDefinition

from bmt import Toolkit

PREDICATE_MAP = {
    "predicate mappings": [
        {
            "mapped predicate": "augments",
            "predicate": "affects",
        }
    ]
}


@pytest.fixture
def schema():
    return SchemaDefinition(
        id="https://example.org/test-schema",
        name="test-schema",
    )


def test_loads_predicate_map_from_mapping_without_network(schema, monkeypatch):
    get = Mock(side_effect=AssertionError("network access was not expected"))
    monkeypatch.setattr("bmt.toolkit.requests.get", get)

    toolkit = Toolkit(schema, PREDICATE_MAP)

    assert toolkit.pmap == PREDICATE_MAP
    get.assert_not_called()


def test_loads_predicate_map_from_file_object_without_network(schema, monkeypatch):
    get = Mock(side_effect=AssertionError("network access was not expected"))
    monkeypatch.setattr("bmt.toolkit.requests.get", get)
    stream = StringIO(yaml.safe_dump(PREDICATE_MAP))

    toolkit = Toolkit(schema, stream)

    assert toolkit.pmap == PREDICATE_MAP
    get.assert_not_called()


@pytest.mark.parametrize("use_path_object", [False, True])
def test_loads_predicate_map_from_local_path_without_network(
    schema,
    monkeypatch,
    tmp_path,
    use_path_object,
):
    get = Mock(side_effect=AssertionError("network access was not expected"))
    monkeypatch.setattr("bmt.toolkit.requests.get", get)
    predicate_map_path = tmp_path / "predicate_mapping.yaml"
    predicate_map_path.write_text(yaml.safe_dump(PREDICATE_MAP), encoding="utf-8")
    source = predicate_map_path if use_path_object else str(predicate_map_path)

    toolkit = Toolkit(schema, source)

    assert toolkit.pmap == PREDICATE_MAP
    get.assert_not_called()


def test_uses_pathlike_filesystem_representation(schema, tmp_path):
    predicate_map_path = tmp_path / "predicate_mapping.yaml"
    predicate_map_path.write_text(yaml.safe_dump(PREDICATE_MAP), encoding="utf-8")

    class PredicateMapPath:
        def __fspath__(self):
            return str(predicate_map_path)

        def __str__(self):
            return "not-the-filesystem-path"

    toolkit = Toolkit(schema, PredicateMapPath())

    assert toolkit.pmap == PREDICATE_MAP


def test_loads_predicate_map_from_url_with_timeout_and_status_check(schema, monkeypatch):
    response = Mock(text=yaml.safe_dump(PREDICATE_MAP))
    get = Mock(return_value=response)
    monkeypatch.setattr("bmt.toolkit.requests.get", get)
    predicate_map_url = "https://example.org/predicate_mapping.yaml"

    toolkit = Toolkit(
        schema,
        predicate_map_url,
        predicate_map_timeout=(2.0, 5.0),
    )

    assert toolkit.pmap == PREDICATE_MAP
    get.assert_called_once_with(predicate_map_url, timeout=(2.0, 5.0))
    response.raise_for_status.assert_called_once_with()


def test_propagates_predicate_map_http_errors(schema, monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("503 Service Unavailable")
    monkeypatch.setattr("bmt.toolkit.requests.get", Mock(return_value=response))

    with pytest.raises(requests.HTTPError, match="503 Service Unavailable"):
        Toolkit(schema, "https://example.org/predicate_mapping.yaml")


def test_propagates_predicate_map_timeouts(schema, monkeypatch):
    get = Mock(side_effect=requests.Timeout("request timed out"))
    monkeypatch.setattr("bmt.toolkit.requests.get", get)

    with pytest.raises(requests.Timeout, match="request timed out"):
        Toolkit(
            schema,
            "https://example.org/predicate_mapping.yaml",
            predicate_map_timeout=1.0,
        )


def test_rejects_invalid_predicate_map_yaml_from_url(schema, monkeypatch):
    response = Mock(text="predicate mappings: [")
    monkeypatch.setattr("bmt.toolkit.requests.get", Mock(return_value=response))

    with pytest.raises(yaml.YAMLError):
        Toolkit(schema, "https://example.org/predicate_mapping.yaml")


@pytest.mark.parametrize(
    "predicate_map",
    [
        {},
        {"predicate mappings": {}},
        {"predicate mappings": ["not a mapping"]},
    ],
)
def test_rejects_invalid_predicate_map_structures(schema, predicate_map):
    with pytest.raises(ValueError, match="Predicate map"):
        Toolkit(schema, predicate_map)


def test_rejects_unsupported_predicate_map_source(schema):
    with pytest.raises(TypeError, match="Predicate map source"):
        Toolkit(schema, [])
