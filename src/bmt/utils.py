import re

import stringcase
from linkml_runtime.linkml_model.meta import (
    ClassDefinition,
    SlotDefinition,
    Element,
    ClassDefinitionName,
    SlotDefinitionName,
    ElementName,
    TypeDefinition,
)

lowercase_pattern = re.compile(r"[a-zA-Z]*[a-z][a-zA-Z]*")
underscore_pattern = re.compile(r"(?<!^)(?=[A-Z][a-z])")


def from_camel(s: str, sep: str = " ") -> str:
    underscored = underscore_pattern.sub(sep, s)
    lowercased = lowercase_pattern.sub(
        lambda match: match.group(0).lower(),
        underscored,
    )
    return lowercased


def camelcase_to_sentencecase(s: str) -> str:
    """
    Convert CamelCase to sentence case.

    Parameters
    ----------
    s: str
        Input string in CamelCase
    Returns
    -------
    str
        string in sentence case form
    """
    return from_camel(s, sep=" ")


def snakecase_to_sentencecase(s: str) -> str:
    """
    Convert snake_case to sentence case.

    Parameters
    ----------
    s: str
        Input string in snake_case
    Returns
    -------
    str
        string in sentence case form
    """
    return stringcase.sentencecase(s).lower()


def sentencecase_to_snakecase(s: str) -> str:
    """
    Convert sentence case to snake_case.

    Parameters
    ----------
    s: str
        Input string in sentence case
    Returns
    -------
    str
        string in snake_case form
    """
    return stringcase.snakecase(s).lower()


def sentencecase_to_camelcase(s: str) -> str:
    """
    Convert sentence case to CamelCase.
    Parameters
    ----------
    s: str
        Input string in sentence case
    Returns
    -------
    str
        string in CamelCase form
    """
    return re.sub(r"(?:^| )([a-zA-Z])", lambda match: match.group(1).upper(), s)


def format_element(element: Element) -> str:
    """
    Format a given element's name.

    Parameters
    ----------
    element: linkml_runtime.linkml_model.meta.Element
        An element

    Returns
    -------
    str
        A CURIE representation of an element's name

    """
    if isinstance(element, ClassDefinitionName):
        formatted = f"biolink:{sentencecase_to_camelcase(element)}"
    elif isinstance(element, ClassDefinition):
        formatted = f"biolink:{sentencecase_to_camelcase(element.name)}"
    elif isinstance(element, SlotDefinitionName):
        formatted = f"biolink:{sentencecase_to_snakecase(element)}"
    elif isinstance(element, SlotDefinition):
        formatted = f"biolink:{sentencecase_to_snakecase(element.name)}"
    elif isinstance(element, TypeDefinition):
        if element.from_schema == "https://w3id.org/linkml/types":
            formatted = f"metatype:{sentencecase_to_camelcase(element.name)}"
        else:
            formatted = f"biolink:{sentencecase_to_camelcase(element.name)}"
    else:
        if isinstance(element, ElementName):
            formatted = f"biolink:{sentencecase_to_camelcase(element)}"
        else:
            formatted = f"biolink:{sentencecase_to_camelcase(element.name)}"
    return formatted


def parse_name(name) -> str:
    """
    Parse an element name into it's proper internal representation.

    Parameters
    ----------
    name: str
        An element name

    Returns
    -------
    str
        An internal representation of the given name

    """
    actual_name = name
    if name.startswith("biolink"):
        m = re.match("biolink:(.+)", name)
        if m:
            r = m.groups()[0]
            if "_" in r:
                actual_name = snakecase_to_sentencecase(r)
            else:
                actual_name = camelcase_to_sentencecase(r)
    elif "_" in name:
        actual_name = snakecase_to_sentencecase(name)
    elif " " in name:
        actual_name = name
    else:
        actual_name = camelcase_to_sentencecase(name)
    return actual_name
