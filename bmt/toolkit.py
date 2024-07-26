import logging
import yaml
import deprecation
import requests
from functools import lru_cache, reduce

from typing import List, Union, TextIO, Optional, Dict

from linkml_runtime.linkml_model import PermissibleValueText
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model.meta import (
    SchemaDefinition,
    Element,
    ElementName,
    Definition,
    ClassDefinition,
    SlotDefinition,
)
from bmt.utils import format_element, parse_name

Url = str
Path = str

LATEST_BIOLINK_RELEASE = "4.2.2"

REMOTE_PATH = f"https://raw.githubusercontent.com/biolink/biolink-model/v{LATEST_BIOLINK_RELEASE}/biolink-model.yaml"
PREDICATE_MAP = f"https://raw.githubusercontent.com/biolink/biolink-model/v{LATEST_BIOLINK_RELEASE}/predicate_mapping.yaml"


NODE_PROPERTY = "node property"
ASSOCIATION_SLOT = "association slot"
RELATED_TO = "related to"

CACHE_SIZE = 1024

logger = logging.getLogger(__name__)


class Toolkit(object):
    """
    Provides a series of methods for performing lookups on the Biolink Model

    Parameters
    ----------
    schema: Union[str, TextIO, SchemaDefinition]
        The path or url to an instance of the biolink-model.yaml file.

    """

    def __init__(
            self, schema: Union[Url, Path, TextIO, SchemaDefinition] = REMOTE_PATH,
            predicate_map: Url = PREDICATE_MAP
    ) -> None:
        self.view = SchemaView(schema)
        r = requests.get(predicate_map)
        self.pmap = yaml.safe_load(r.text)

    @lru_cache(CACHE_SIZE)
    def get_all_elements(self, formatted: bool = False) -> List[str]:
        """
        Get all elements from Biolink Model.

        This method returns a list containing all
        classes, slots, and types defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        classes = self.get_all_classes(formatted)
        slots = self.get_all_slots(formatted)
        types = self.get_all_types(formatted)
        all_elements = classes + slots + types
        return all_elements

    @lru_cache(CACHE_SIZE)
    def get_all_classes(self, formatted: bool = False) -> List[str]:
        """
        Get all classes from Biolink Model.

        This method returns a list containing all the
        classes defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        classes = []
        for x in self.view.schema.classes:
            classes.append(x)
        filtered_classes = self._filter_secondary(classes)
        return self._format_all_elements(filtered_classes, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_slots(self, formatted: bool = False) -> List[str]:
        """
        Get all slots from Biolink Model.

        This method returns a list containing all the
        slots defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        slots = []
        for x in self.view.schema.slots:
            slots.append(x)
        filtered_slots = self._filter_secondary(slots)
        return self._format_all_elements(filtered_slots, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_types(self, formatted: bool = False) -> List[str]:
        """
        Get all types from Biolink Model.

        This method returns a list containing all the
        built-in and defined types in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        types = []
        for x in self.view.all_types():
            types.append(x)
        return self._format_all_elements(types, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_entities(self, formatted: bool = False) -> List[str]:
        """
        Get all entities from Biolink Model.

        This method returns a list containing all the classes
        that are descendants of the class ``named thing``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants("named thing")
        return self._format_all_elements(elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_associations(self, formatted: bool = False) -> List[str]:
        """
        Get all associations from Biolink Model.

        This method returns a list of names or (optionally) curies
        designating classes that are descendants of the class ``association``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        return self.get_descendants("association", formatted=formatted)

    def filter_values_on_slot(
            self,
            slot_values: List[str],
            definition: SlotDefinition,
            field: str,
            formatted: bool = True
    ) -> bool:
        """

        Parameters
        ----------
        slot_values: List[str]
            List of (Biolink CURIE) slot values to be matched against target slot field values.
        definition: SlotDefinition
            Slot definition containing the embedded target field.
        field: str
            Name of embedded (slot) field rooting the tree of elements
            against which the slot_values are to be matched.
        formatted: bool = True
            Use of Biolink CURIE identifiers assumed when True (default: True)

        Returns
        -------
        bool
           Returns 'True' if any match is found for at least
           one entry in the slot_values, against the target field values.

        """
        if field in definition:
            value = definition[field]
            if value:
                value_set = self.get_descendants(value, formatted=formatted)
                return any([entry in slot_values for entry in value_set])
        if "description" in definition and definition["description"] is not None:
            # In the case where the target 'field' is missing target details but the definition
            # still has a 'description' field, we deflect responsibility for vetting the slot_values
            # to the caller of the function (this is effectively saying 'all slot values are acceptable'
            # in this position (although the description itself may informally constrain them otherwise)
            return True
        return False

    @staticmethod
    def get_local_slot_usage(element: Element, slot: str) -> Optional[SlotDefinition]:
        """
        Retrieve the definition of a specified slot from the 'slot_usage'
        defined locally within the class model of the specified Element.

        Parameters
        ----------
        element:
            Element defining the specified 'slot' in its local 'slot_usage'.
        slot: str
            Name of the slot whose definition is to be retrieved.

        Returns
        -------
        Optional[SlotDefinition]
            None, if not available.

        """
        slot_definition: Optional[SlotDefinition] = None
        if "slot_usage" in element:
            slot_usage = element["slot_usage"]
            if slot_usage and slot in slot_usage:
                slot_definition = slot_usage[slot]
        return slot_definition

    def get_slot_usage(self, element: Element, slot: str) -> Optional[SlotDefinition]:
        """
        Get the definition of a specified slot from the 'slot_usage' of a specified Element.
        A relatively deep search is made within the Element context - local class, parent class
        and associated mixins - to discover an available 'slot_usage' definition for the slot.

        Parameters
        ----------
        element:
            Element defining the specified 'slot' in 'slot_usage'.
        slot: str
            Name of the slot whose definition is to be retrieved.

        Returns
        -------
        Optional[SlotDefinition]
            None, if not available.

        """
        # Check first for local referencing of the slot
        slot_definition: Optional[SlotDefinition] = self.get_local_slot_usage(element, slot)

        # shallow (immediate parent) check up the class hierarchy...
        # Note: we don't attempt a recursive search through ancestors for now
        if slot_definition is None and "is_a" in element and element["is_a"]:
            parent_name: str = element["is_a"]
            parent: Element = self.get_element(parent_name)
            slot_definition = self.get_local_slot_usage(parent, slot)

        # if still empty-handed at this point follow the mixins
        if slot_definition is None and "mixins" in element and element["mixins"]:
            # 'slot_usage' for some fields may be inherited from the association mixins. For example:
            #
            #     druggable gene to disease association
            #         mixins:
            #         - entity to disease association mixin
            #         - gene to entity association mixin
            #
            # the mixins would have a 'subject' slot_usage for Gene and 'object' usage for Disease
            for mixin_name in element["mixins"]:
                mixin: Element = self.get_element(mixin_name)
                slot_definition = self.get_local_slot_usage(mixin, slot)
                if slot_definition:
                    break

        return slot_definition

    def match_slot_usage(
            self,
            element,
            slot: str,
            slot_values: List[str],
            formatted: bool = True
    ) -> bool:
        """
        Match slot_values against expected slot_usage for
        specified slot in specified (association) element.

        Parameters
        ----------
        element: Element
            Target element against which slot_usage is being assessed.
        slot: str
            Name of target slot in given element, against which slot_usage is being assessed.
        slot_values: List[str]
            List of slot value (strings) e.g. categories, predicates, etc. - being assessed against slot_usage
        formatted: bool = True
            Use of Biolink CURIE identifiers in slot_values assumed when True (default: True)

        Returns
        -------
        bool
            Returns 'True' if slot exists and slot_values are compatible with slot usage
            within the given element (or its immediate parent or mixins); False otherwise

        """
        # scope of method sanity check for now
        assert slot in ["subject", "object", "predicate"]

        slot_definition: Optional[SlotDefinition] = self.get_slot_usage(element, slot)

        # assess "slot_values" for "subject", "object"
        # or "predicate" against stipulated constraints
        if slot_definition:
            if slot == "predicate":
                # check for a non-null "subproperty_of" constraint on a "predicate" slot_value
                return self.filter_values_on_slot(slot_values, slot_definition, "subproperty_of", formatted=formatted)
            else:
                # check for a non-null "range" constraint on a "subject" or "object" slot_value
                return self.filter_values_on_slot(slot_values, slot_definition, "range", formatted=formatted)
        elif slot == "predicate":
            # the default here if no 'predicate' slot_usage constraint is defined in the model,
            # is to assume that any and all predicates are allowed for this specified subclass
            # of biolink:Association. This is functionally identical to the 'description' property
            # only slot definition (which doesn't computationally restrict things either).
            return True

        return False

    def match_association(
            self,
            assoc: Element,
            subj_cats: List[str],
            predicates: List[str],
            obj_cats: List[str],
            formatted: bool = True
    ) -> bool:
        """
        Match a specified element (assumed to be a child of biolink:Association) to a given set of
        Subject category -- Predicate -> Object category name constraints.

        Parameters
        ----------
        assoc: Element
            Subclass of biolink:Association to be matched.
        subj_cats: List[str]
            List of Biolink CURIEs of subject categories.
        predicates: List[str]
            List of Biolink CURIEs of predicates.
        obj_cats: List[str]
            List of Biolink CURIEs of object categories.
        formatted: bool = True
            Use of Biolink CURIE identifiers in 'subj_cats', 'preds' and 'obj_cats' assumed when True (default: True)

        Returns
        -------
        bool:
           True if all constraints match the slot_usage of the Association components.

        """
        if subj_cats and not self.match_slot_usage(assoc, "subject", subj_cats, formatted=formatted):
            return False
        if predicates and not self.match_slot_usage(assoc, "predicate", predicates, formatted=formatted):
            return False
        if obj_cats and not self.match_slot_usage(assoc, "object", obj_cats, formatted=formatted):
            return False
        return True

    def get_associations(
            self,
            subject_categories: Optional[List[str]] = None,
            predicates: Optional[List[str]] = None,
            object_categories: Optional[List[str]] = None,
            match_inverses: bool = True,
            formatted: bool = False
    ) -> List[str]:
        """
        Get associations from Biolink Model constrained by target
        list of subject categories, predicates and/or object categories.

        Note: to get matches to most specific associations, it is
        recommended that the subject_categories and object_categories
        lists be limited to the most specific node categories of interest.

        This method returns a list of names or (optionally formatted) curies
        designating classes that are descendants of the class biolink:Association.

        Note that the method does not attempt to continue matching input constraints
        if any category or predicate is deemed unknown to the current Biolink Model:
        The caller should know well enough to check these, *before* calling this method!
        But log warnings are issued as a courtesys to inform them!

        Parameters
        ----------
        subject_categories: Optional[List[str]]
            List of node categories (as CURIES) that the associations must match for the subject node; default: None
        predicates: Optional[List[str]]
            List of edge predicates (as CURIES) that the associations allowed for matching associations; default: None
        object_categories: Optional[List[str]]
            List of node categories (as CURIES) that the associations must match for the object node; default: None
        match_inverses: bool
            Whether to also return associations with swapped subject and object with inverted qualifiers
            (as applicable) plus inverse predicates; default: rue
        formatted: bool
            Whether to format element names as CURIEs; default: False

        Returns
        -------
        List[str]
            A list of elements

        """

        filtered_elements: List[str] = []
        inverse_predicates: Optional[List[str]] = None
        subject_categories_formatted = []
        object_categories_formatted = []
        predicates_formatted = []
        association_elements = self.get_descendants("association")

        if subject_categories:
            for sc in subject_categories:
                sc_elem = self.get_element(sc)
                if not sc_elem:
                    logger.warning(
                        f"get_associations(): could not find subject category " +
                        f"element '{str(sc)}' in current Biolink Model release?"
                    )
                    return []
                sc_formatted = format_element(sc_elem)
                subject_categories_formatted.append(sc_formatted)

        if object_categories:
            for oc in object_categories:
                oc_elem = self.get_element(oc)
                if not oc_elem:
                    logger.warning(
                        f"get_associations(): could not find object category " +
                        f"element '{str(oc)}' in current Biolink Model release?"
                    )
                    return []
                oc_formatted = format_element(oc_elem)
                object_categories_formatted.append(oc_formatted)

        if predicates:
            for pred in predicates:
                p_elem = self.get_element(pred)
                if not p_elem:
                    logger.warning(
                        f"get_associations(): could not find predicate " +
                        f"element '{str(pred)}' in current Biolink Model release?"
                    )
                    return []
                pred_formatted = format_element(p_elem)
                predicates_formatted.append(pred_formatted)

            inverse_predicates = list()
            for pred_curie in predicates_formatted:
                p_elem = self.get_element(pred_curie)
                if not p_elem:
                    # Not too worried here about predictes missing
                    # their inverse, so we just skip them
                    continue
                inverse_p = self.get_inverse(p_elem.name)
                if inverse_p:
                    # TODO: unsure that this test is needed, if the
                    #       existence of 'p_elem' is vetted above, since
                    #       all predicates in the model ought to have names?
                    logger.warning(
                        f"get_associations(): inverse predicate name '{str(p_elem.name)}' " +
                        f"does not match any element in the current Biolink Model release?"
                    )
                    inverse_predicates.append(inverse_p)
            inverse_predicates = self._format_all_elements(elements=inverse_predicates, formatted=True)

        if subject_categories_formatted or predicates_formatted or object_categories_formatted:
            # This feels like a bit of a brute force approach as an implementation,
            # but we just use the list of all association names to retrieve each
            # association record for filtering against the constraints?
            for name in association_elements:

                # although get_element() is Optional[Element],
                # the association_elements all come from
                # get_descendants(), hence are assumed to be extant
                association: Element = self.get_element(name)
                if not association:
                    # TODO: unsure that this test is needed, since all
                    #       known association classes ought to have names?
                    logger.warning(
                        f"get_associations(): association name '{str(name)}' " +
                        f"does not match any element in the current Biolink Model release?"
                    )
                    continue

                # sanity checks, probably not necessary
                # assert association, f"'{name}' not a Biolink Element?"
                # assert isinstance(association, ClassDefinition), f"'{name}' not a ClassDefinition?"

                # Try to match associations in the forward direction
                if not (
                    self.match_association(
                        association,
                        subject_categories_formatted,
                        predicates_formatted,
                        object_categories_formatted
                    ) or
                    (
                        match_inverses and
                        self.match_association(
                            association,
                            object_categories,
                            inverse_predicates,
                            subject_categories_formatted
                        )
                    )
                ):
                    continue

                # this association is assumed to pass stipulated constraints
                filtered_elements.append(association.name)
        else:
            # no filtering equivalent to get_all_associations()
            filtered_elements = association_elements

        return self._format_all_elements(filtered_elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_node_properties(self, formatted: bool = False) -> List[str]:
        """
        Get all node properties from Biolink Model.

        This method returns a list containing all the slots
        that are descendants of the slot ``node property``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_all_slots_with_class_domain("entity")
        elements += self.get_descendants("node property")
        filtered_elements = self._filter_secondary(elements)
        return self._format_all_elements(filtered_elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_edge_properties(self, formatted: bool = False) -> List[str]:
        """
        Get all edge properties from Biolink Model.

        This method returns a list containing all the slots
        that are descendants of the slot ``association slot``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_all_slots_with_class_domain("entity")
        elements += self.get_descendants("association slot")
        filtered_elements = self._filter_secondary(elements)
        return self._format_all_elements(filtered_elements, formatted)

    def _filter_secondary(self, elements: List[str]) -> List[str]:
        """
        From a given list of elements, remove elements that are not proper slots.

        This method removes spurious slots like ``gene_to_gene_association_subject``
        that are artifact of domain/range constraints and not actual slots.

        Parameters
        ----------
        elements: List[str]
            List of elements

        Returns
        -------
        List[str]
            A filtered list of elements

        """
        filtered_elements = []
        for e in elements:
            eo = self.view.get_element(e)
            if isinstance(eo, SlotDefinition):
                if not eo.alias:
                    filtered_elements.append(e)
            else:
                filtered_elements.append(e)
        return filtered_elements

    @lru_cache(CACHE_SIZE)
    def get_permissible_value_ancestors(
            self, permissible_value: str,
            enum_name: str,
            formatted: bool = False
    ) -> List[str]:
        """
        Get ancestors of a permissible value.

        This method returns a list containing all the ancestors of a
        permissible value of a given enum.

        Parameters
        ----------
        enum_name: str
            The name of the enum
        permissible_value: str
            The name of the permissible value
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        ancestors = self.view.permissible_value_ancestors(permissible_value, enum_name)
        if formatted:
            return self._format_all_elements(ancestors)
        return ancestors

    @lru_cache(CACHE_SIZE)
    def get_permissible_value_descendants(
            self, permissible_value: str,
            enum_name: str,
            formatted: bool = False
    ) -> List[str]:
        """
        Get descendants of a permissible value.

        This method returns a list containing all the descendants of a
        permissible value of a given enum.

        Parameters
        ----------
        enum_name: str
            The name of the enum
        permissible_value: str
            The name of the permissible value
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        descendants = self.view.permissible_value_descendants(permissible_value, enum_name)
        if formatted:
            return self._format_all_elements(descendants)
        return descendants

    @lru_cache(CACHE_SIZE)
    def get_predicate_mapping(self, mapped_predicate: str) -> Dict[str, str]:
        """
        Get the predicates that map to a given predicate.

        This method returns a list containing all the predicates that map to
        a given predicate.

        Parameters
        ----------
        mapped_predicate: str
            The name of the mapped predicate

        Returns
        -------
        List[str]
            A list of elements

        """
        association = {}

        for mp in self.pmap.values():
            for item in mp:
                if item['mapped predicate'] == mapped_predicate:
                    for k, v in item.items():
                        association[format_element(self.get_element(k))] = v
        return association

    @lru_cache(CACHE_SIZE)
    def get_permissible_value_parent(self, permissible_value: str, enum_name: str) -> str:
        """
        Get parent of a permissible value.

        This method returns a list containing all the parent of a
        permissible value of a given enum.

        Parameters
        ----------
        enum_name: str
            The name of the enum
        permissible_value: str
            The name of the permissible value

        Returns
        -------
        List[str]
            A list of elements

        """
        parent = self.view.permissible_value_parent(permissible_value, enum_name)
        return parent

    @lru_cache(CACHE_SIZE)
    def get_permissible_value_children(self, permissible_value: str, enum_name: str) -> Union[
        str, PermissibleValueText, None]:
        """
        Gets the children of a permissible value in an enumeration.

        :param permissible_value: The permissible value to check.
        :param enum_name: The name of the enumeration.
        :return: The children of the permissible value.
        :raises ValueError: If the permissible value or enum is not valid.
        """

        children = self.view.permissible_value_children(permissible_value, enum_name)
        return children

    @lru_cache(CACHE_SIZE)
    def get_ancestors(
            self,
            name: str,
            reflexive: bool = True,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Gets a list of names of ancestors.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        reflexive: bool
            Whether to include the query element in the list of ancestors
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The names of the given elements ancestors

        """
        element = self.get_element(name)
        ancs = []
        if isinstance(element, ClassDefinition):
            ancs = self.view.class_ancestors(element.name, mixins=mixin, reflexive=reflexive)
        if isinstance(element, SlotDefinition):
            ancs = self.view.slot_ancestors(element.name, mixins=mixin, reflexive=reflexive)
            filtered_ancs = self._filter_secondary(ancs)
        else:
            filtered_ancs = ancs
        return self._format_all_elements(filtered_ancs, formatted)

    def _get_mixin_descendants(self, ancestors: List[ElementName]) -> List[ElementName]:
        mixins_parents = []
        for ancestor in ancestors:
            a_element = self.get_element(ancestor)
            if a_element.mixins:
                for mixin in a_element.mixins:
                    mixin_element = self.get_element(mixin)
                    mixin_parents = self.view.ancestors(mixin_element)
                    mixins_parents = mixins_parents + mixin_parents
        return mixins_parents

    @lru_cache(CACHE_SIZE)
    def get_descendants(
            self,
            name: str,
            reflexive: bool = True,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Gets a list of names of descendants.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        reflexive: bool
            Whether to include the query element in the list of descendants
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin descendants as well as is_a ancestors

        Returns
        -------
        List[str]
            The names of the given element's descendants

        """
        desc = []
        filtered_desc = []
        element = self.get_element(name)

        if element:
            if isinstance(element, ClassDefinition):
                desc = self.view.class_descendants(element.name, mixins=mixin, reflexive=reflexive)
            if isinstance(element, SlotDefinition):
                desc = self.view.slot_descendants(element.name, mixins=mixin, reflexive=reflexive)
                filtered_desc = self._filter_secondary(desc)
            else:
                filtered_desc = desc
        else:
            raise ValueError("not a valid biolink component")

        return self._format_all_elements(filtered_desc, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_multivalued_slots(self) -> List[str]:
        """
        Gets a list of names of all multivalued slots.

        Returns
        -------
        List[str]
            The names of all multivalued slots

        """
        multivalued_slots = []
        slots = self.view.all_slots()
        for slot_name, slot_def in slots.items():
            if self.view.is_multivalued(slot_name):
                multivalued_slots.append(slot_name)
        return multivalued_slots

    @lru_cache(CACHE_SIZE)
    def get_children(
            self, name: str, formatted: bool = False, mixin: bool = True
    ) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The names of the given elements children

        """
        children = []
        element = self.get_element(name)
        if element:
            children = self.view.get_children(element.name, mixin)
        return self._format_all_elements(children, formatted)

    @lru_cache(CACHE_SIZE)
    def get_parent(self, name: str, formatted: bool = False) -> Optional[str]:
        """
        Gets the name of the parent.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        Optional[str]
            The name of the given elements parent

        """
        parent = None
        element = self.get_element(name)
        if element:
            p = element.is_a if isinstance(element, Definition) else None
            if p and formatted:
                parent = format_element(p)
            else:
                parent = p
        return parent

    @lru_cache(CACHE_SIZE)
    def get_element(self, name: str) -> Optional[Element]:
        """
        Gets an element that is identified by the given name, either as its name
        or as one of its aliases.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        Element
            The element identified by the given name

        """
        parsed_name = parse_name(name)
        logger.debug(parsed_name)
        element = self.view.get_element(parsed_name)
        if element is None and self.view.all_aliases() is not None:
            if parsed_name.startswith("biolink:"):
                parsed_name = parsed_name.replace("biolink:", "")
                parsed_name = parsed_name.replace("_", " ")
            for e in self.view.all_aliases():
                if name in self.view.all_aliases()[e] or parsed_name in self.view.all_aliases()[e]:
                    element = self.view.get_element(e)
        if element is None and "_" in name:
            element = self.get_element(name.replace("_", " "))
        if element is None:
            for e, el in self.view.all_elements().items():
                if el.name.lower() == name.lower():
                    element = el

        if type(element) == ClassDefinition and element.class_uri is None:
            element.class_uri = format_element(element)
        if type(element) == SlotDefinition and element.slot_uri is None:
            element.slot_uri = format_element(element)
        return element

    def get_slot_domain(
            self,
            slot_name,
            include_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Get the domain for a given slot.

        Parameters
        ----------
        slot_name: str
            The name or alias of a slot in the Biolink Model
        include_ancestors: bool
            Whether or not to include ancestors of the domain class
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The domain for a given slot

        """
        slot_domain = []
        slot_domain_desc = []
        element = self.get_element(slot_name)
        if element:
            if element.domain:
                slot_domain.append(element.domain)
            else:
                if include_ancestors:
                    for element in self.get_ancestors(element.name):
                        tk_element = self.get_element(element)
                        if tk_element and tk_element.domain:
                            slot_domain.append(tk_element.domain)
            if slot_domain:
                for domain in slot_domain:
                    slot_domain_desc = self.get_descendants(domain, reflexive=True, mixin=mixin)
                slot_domain.extend(slot_domain_desc)
        return self._format_all_elements(slot_domain, formatted)

    def get_slot_range(
            self,
            slot_name,
            include_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Get the range for a given slot.

        Parameters
        ----------
        slot_name: str
            The name or alias of a slot in the Biolink Model
        include_ancestors: bool
            Whether or not to include ancestors of the range class
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors


        Returns
        -------
        List[str]
            The range for a given slot

        """
        slot_range = []
        slot_range_desc = []
        element = self.get_element(slot_name)
        if element:
            if element.range:
                slot_range.append(element.range)
            else:
                if include_ancestors:
                    for element in self.get_ancestors(element.name):
                        tk_element = self.get_element(element)
                        if tk_element and tk_element.range:
                            slot_range.append(tk_element.range)
            if slot_range:
                for range in slot_range:
                    slot_range_desc = self.get_descendants(range, reflexive=True, mixin=mixin)
                slot_range.extend(slot_range_desc)
        return self._format_all_elements(slot_range, formatted)

    def validate_edge(self, subject: str, predicate: str, p_object: str, ancestors: bool = True) -> bool:
        """
        Validates an edge.

        Parameters
        ----------
        subject: str
            The name or alias of a subject in the Biolink Model
        predicate: str
            The name or alias of a predicate in the Biolink Model
        p_object: str
            The name or alias of an object in the Biolink Model
        ancestors: bool
            Whether to include ancestors of the domain and range classes

        Returns
        -------
        bool
            Whether or not the given edge is valid

        """
        if self.is_predicate(predicate):
            predicate_domains = self.get_slot_domain(predicate, include_ancestors=True, mixin=True, formatted=True)
            predicate_ranges = self.get_slot_range(predicate, include_ancestors=True, mixin=True, formatted=True)

            if subject in predicate_domains and p_object in predicate_ranges:
                return True
            else:
                subject_entity = self.get_element(subject)
                object_entity = self.get_element(p_object)

                if subject_entity and object_entity:
                    subject_ancestors = self.get_ancestors(subject_entity.name, formatted=True, mixin=True)
                    object_ancestors = self.get_ancestors(object_entity.name, formatted=True, mixin=True)
                    # this is kind of hacky, the issue is that mixins don't descend from any shared class
                    # like NamedThing.
                    if self.is_mixin(subject_entity.name):
                        subject_ancestors.append("biolink:NamedThing")
                    if self.is_mixin(object_entity.name):
                        object_ancestors.append("biolink:NamedThing")
                    subject_in_domain = False
                    object_in_range = False
                    for subject_ancestor in subject_ancestors:
                        if subject_ancestor in predicate_domains:
                            subject_in_domain = True
                    for object_ancestor in object_ancestors:
                        if object_ancestor in predicate_ranges:
                            object_in_range = True
                    if subject_in_domain and object_in_range:
                        return True
                else:
                    return False

        return False

    def is_subproperty_of(self, predicate: str, name: str, formatted: bool = False) -> bool:
        """
        Checks if a given name is a 'subproperty_of' a given predicate.
        Note: unsure if this method yet captures the full subtlety of 'subproperty_of'.

        Parameters
        ----------
        predicate: str
            Target predicate against which a given name is to be searched as a subproperty
        name: str
            Name to be searched
        formatted: bool = False
            Input name assumed to be a CURIE

        Returns
        -------
            True if the name is observed to be equivalent to,
            or a 'subproperty' descendant of, the given predicate.

        """
        return name in self.get_descendants(predicate, formatted=formatted)

    def validate_qualifier(
            self,
            qualifier_type_id: str,
            qualifier_value: str,
            associations: Optional[List[str]] = None
    ) -> bool:
        """
        Validates a qualifier.

        Parameters
        ----------
        qualifier_type_id: str
            The name or alias of a qualifier in the Biolink Model
        qualifier_value: str
            The value of the qualifier
        associations: Optional[List[str]] = None
            Optional list of possible biolink:Association subclass (CURIEs)
            which could resolve the context for qualifier_value validation.

        Returns
        -------
        bool
            Whether or not the given qualifier is valid

        """
        if qualifier_type_id and qualifier_value and self.is_qualifier(qualifier_type_id):
            qualifier_type_name = parse_name(qualifier_type_id)
            qualifier_slot = self.view.get_slot(parse_name(qualifier_type_id))
            # qualifier slot may be undefined in the current model
            if qualifier_slot:
                value_range: Optional[str] = None
                if "range" in qualifier_slot and qualifier_slot.range:
                    value_range = qualifier_slot.range

                # Perhaps the qualifier value range is defined
                # within a biolink:Association subclass?
                elif associations:
                    for association in associations:
                        association_element = self.get_element(association)
                        if "slot_usage" in association_element and \
                                qualifier_type_name in association_element["slot_usage"]:
                            qualifier_type = association_element["slot_usage"][qualifier_type_name]
                            if qualifier_type_name == "qualified predicate" and \
                                    "subproperty_of" in qualifier_type and qualifier_type.subproperty_of:
                                value_range = qualifier_type.subproperty_of

                            elif "range" in qualifier_type and qualifier_type.range:
                                value_range = qualifier_type.range
                                break

                # Else: the range may be missing from a particular model
                # or the range will be None for abstract/mixin qualifiers?

                if value_range:
                    if qualifier_type_name == "qualified predicate":
                        return self.is_subproperty_of(predicate=value_range, name=qualifier_value)
                    elif self.is_enum(value_range):
                        enum = self.view.get_enum(value_range)
                        return self.is_permissible_value_of_enum(enum.name, qualifier_value)
                    else:
                        # The value range possibly may be a Biolink categorical qualifier
                        categories = self.get_element_by_prefix(qualifier_value)
                        return bool(categories and value_range in categories)

        return False

    def get_all_slots_with_class_domain(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all the slots where the class is the domain.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        element = self.get_element(class_name)
        slots = self._get_all_slots_with_class_domain(element, check_ancestors, mixin)
        slot_names = [x.name for x in slots]
        return self._format_all_elements(slot_names, formatted)

    def get_all_slots_with_class_range(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all the slots where the class is the range.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        element = self.get_element(class_name)
        slots = self._get_all_slots_with_class_range(element, check_ancestors, mixin)
        slot_names = [x.name for x in slots]
        return self._format_all_elements(slot_names, formatted)

    def get_all_predicates_with_class_domain(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all Biolink predicates where the class is the domain.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_domain(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_all_predicates_with_class_range(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ):
        """
        Given a class, get all Biolink predicates where the class is the range.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_range(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_all_properties_with_class_domain(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all Biolink properties where the class is the domain.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_domain(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO not in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_all_properties_with_class_range(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all Biolink properties where the class is the range.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_range(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO not in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_value_type_for_slot(self, slot_name, formatted: bool = False) -> str:
        """
        Get the value type for a given slot.

        Parameters
        ----------
        slot_name: str
            The name or alias of a slot in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        str
            The slot type

        """
        element_type = None
        element = self.get_element(slot_name)
        if element:
            types = self.get_all_types()
            if element.range is None and self.view.schema.default_range:
                element.range = self.view.schema.default_range
            if element.range in types:
                et = element.range
            else:
                et = "uriorcurie"
            if formatted:
                element_type = format_element(self.view.get_element(et))
            else:
                element_type = et
        return element_type

    def _get_all_slots_with_class_domain(
            self, element: Element, check_ancestors: bool, mixin: bool = True
    ) -> List[Element]:
        """
        Given a class, get all the slots where the class is the domain.

        Parameters
        ----------
        element: linkml_model.meta.Element
            An element
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        mixin:
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[linkml_model.meta.Element]
            A list of slots

        """
        slots = []
        for k, v in self.view.schema.slots.items():
            if check_ancestors:
                if (v.domain == element.name or v.domain in self.get_ancestors(element.name, mixin)
                        or element.name in v.domain_of
                        or any(v.domain_of) in self.get_ancestors(element.name, mixin)):
                    slots.append(v)
            else:
                if element.name == v.domain or element.name in v.domain_of:
                    slots.append(v)
        return slots

    def _get_all_slots_with_class_range(
            self, element: Element, check_ancestors: bool, mixin: bool = True
    ) -> List[Element]:
        """
        Given a class, get all the slots where the class is the range.

        Parameters
        ----------
        element: linkml_model.meta.Element
            An element
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[linkml_model.meta.Element]
            A list of slots

        """
        slots = []
        for k, v in self.view.schema.slots.items():
            if check_ancestors:
                if v.range == element.name or v.range in self.get_ancestors(
                        element.name, mixin
                ):
                    slots.append(v)
            else:
                if v.range and element.name == v.range:
                    slots.append(v)
        return slots

    @lru_cache(CACHE_SIZE)
    def is_node_property(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a node property
        in the Biolink Model. An element is a node property if it descends from
        `NODE_PROPERTY`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid node property in Biolink Model
        """
        return NODE_PROPERTY in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_association_slot(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of an association slot
        in the Biolink Model. An element is an association slot if it descends from
        `ASSOCIATION_SLOT`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid an association slot in Biolink Model
        """
        return ASSOCIATION_SLOT in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_predicate(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a relation/predicate
        in the Biolink Model. An element is a predicate if it descends from
        `RELATED_TO`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid relation/predicate in Biolink Model
        """
        return RELATED_TO in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def get_denormalized_association_slots(self, formatted) -> List[Element]:
        """
        Gets all association slots that are denormalized

        Returns
        -------
        List[linkml_model.meta.Element]
            A list of association slots

        """
        slots = []
        for k, v in self.view.schema.slots.items():
            if v.annotations and "denormalized" in v.annotations:
                if formatted:
                    slots.append(format_element(v))
                else:
                    slots.append(k)
        return slots

    @lru_cache(CACHE_SIZE)
    def is_translator_canonical_predicate(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a canonical relation/predicate
        in the Biolink Model. An element is a canonical predicate if it descends from
        `RELATED_TO` and is tagged with the annotation 'biolink:canonical_predicate'

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid translator canonical prediacte in Biolink Model
        """
        element = self.get_element(name)
        annotation_tags = []
        if element:
            for annotation in element.annotations:
                annotation_tags.append(annotation)
        is_canonical = (
            True
            if element is not None and "canonical_predicate" in annotation_tags
            else False
        )
        return (
            True
            if RELATED_TO in self.get_ancestors(name, mixin) and is_canonical
            else False
        )

    @lru_cache(CACHE_SIZE)
    def is_mixin(self, name: str) -> bool:
        """
        Determines whether the given name is the name of a mixin
        in the Biolink Model. An element is a mixin if one of its properties is "is_mixin:true"

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid mixin in Biolink Model
        """
        element = self.get_element(name)
        is_mixin = element.mixin if isinstance(element, Definition) else False
        return is_mixin

    def is_symmetric(self, name: str) -> bool:
        """
        Checks if a given element identified by name, is a symmetric (predicate) slot.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is tagged as symmetric: true in Biolink Model
        """
        if not name:
            return False
        element: Optional[Element] = self.get_element(name)
        if element is not None and element['symmetric']:
            return True
        else:
            return False

    @lru_cache(CACHE_SIZE)
    def get_inverse(self, slot_name: str):
        return self.view.inverse(slot_name)

    @lru_cache(CACHE_SIZE)
    def get_inverse_predicate(
            self, predicate: Optional[str],
            formatted: bool = False
    ) -> Optional[str]:
        """
        Utility wrapper of logic to robustly test if a predicate exists and has an inverse.

        Parameters
        ----------
        predicate: Optional[str]
            CURIE or string name of predicate in the Biolink Model, for which the inverse is sought
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        Optional[str]
            CURIE string of inverse predicate, if it exists; None otherwise
        """
        if predicate and self.is_predicate(predicate):
            predicate_name = parse_name(predicate)
            inverse_predicate_name = self.get_inverse(predicate_name)
            if not inverse_predicate_name:
                if self.is_symmetric(predicate_name):
                    inverse_predicate_name = predicate_name
                else:
                    inverse_predicate_name = None
            if inverse_predicate_name:
                ip = self.get_element(inverse_predicate_name)
                return format_element(ip) if formatted else str(ip.name)
        return None

    @lru_cache(CACHE_SIZE)
    def has_inverse(self, name: str) -> bool:
        """
        Determines whether the given name exists and has an inverse defined in the Biolink Model.
        An element is a predicate if it descends from `RELATED_TO` but this is
        not directly tested here (use the method 'is_predicate()' to be sure).

        Parameters
        ----------
        name: str
            The name or alias of an slot element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a slot element with an inverse in the Biolink Model
        """
        element = self.get_element(name)
        has_inverse = element.inverse if isinstance(element, SlotDefinition) else False
        return bool(has_inverse)

    @lru_cache(CACHE_SIZE)
    def in_subset(self, name: str, subset: str) -> bool:
        """
        Determines whether the given name is in a given subset
        in the Biolink Model.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model.
        subset: str
            The name of the subset

        Returns
        -------
        bool
            That the named element is part of a given subset in Biolink Model

        """
        parsed_name = parse_name(name)
        element = self.view.get_element(parsed_name)
        return subset in element.in_subset

    @lru_cache(CACHE_SIZE)
    def is_category(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a category in the
        Biolink Model. An element is a category if it descends from
        `named thing`

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid category in Biolink Model
        """
        return "named thing" in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_qualifier(self, name: str) -> bool:
        """
        Predicate to test (by name) if a given Biolink Model element is an Edge Qualifier.

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid edge qualifier in the Biolink Model
        """

        if self.view.get_slot(parse_name(name)) and "qualifier" in self.view.slot_ancestors(parse_name(name)):
            return True
        else:
            return False

    @lru_cache(CACHE_SIZE)
    def is_enum(self, name: str) -> bool:
        """
        Predicate to test (by name) if a given Biolink Model element is an Enum.

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid enum in the Biolink Model
        """
        if ":" in name:
            enum = self.view.get_enum(name.split(":")[1])
        else:
            enum = self.view.get_enum(name)
        if not enum:
            return False
        return True

    @lru_cache(CACHE_SIZE)
    def is_permissible_value_of_enum(self, enum_name: str, value) -> bool:
        """
        method to test (by name) if a candidate
        'permissible value' is associated with the given Enum

        Parameters
        ----------
        enum_name : str
            The name or alias of an Enum in the Biolink Model
        value : Any
            The name or alias of the candidate 'permissible value' associated with the given Enum

        Returns
        -------
        bool
            That the named element is in the set of 'permissible values' of the Enum
        """

        if ":" in enum_name:
            enum = self.view.get_enum(enum_name.split(":")[1])
        else:
            enum = self.view.get_enum(enum_name, strict=True)
        if enum and value in enum.permissible_values:
            return True
        else:
            return False

    @lru_cache(CACHE_SIZE)
    def get_element_by_prefix(
            self,
            identifier: str
    ) -> List[str]:
        """
        Get a Biolink Model element by prefix.

        Parameters
        ----------
        identifier: str
            The identifier as a CURIE

        Returns
        -------
        Optional[str]
                The Biolink element corresponding to the given URI/CURIE as available via
                the id_prefixes mapped to that element.

        """
        categories = []
        if ":" in identifier:
            id_components = identifier.split(":")
            prefix = id_components[0]
            elements = self.get_all_elements()
            for category in elements:
                element = self.get_element(category)
                if hasattr(element, 'id_prefixes') and prefix in element.id_prefixes:
                    categories.append(element.name)
        if len(categories) == 0:
            logger.warning("no biolink class found for the given curie: %s, try get_element_by_mapping?", identifier)

        return categories

    @lru_cache(CACHE_SIZE)
    def get_element_by_mapping(
            self,
            identifier: str,
            most_specific: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> Optional[str]:
        """
        Get a Biolink Model element by mapping.
        This method return the common ancestor of the set of elements referenced by uriorcurie.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        most_specific: bool
            Whether or not to get the first available mapping in the order of specificity
            or to get all mappings of varying specificity
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        Optional[str]
            The Biolink element (or the common ancestor) corresponding to the given URI/CURIE

        """
        if most_specific:
            mappings = self._get_element_by_mapping(identifier)
        else:
            mappings = self.get_all_elements_by_mapping(identifier)
        if mappings:
            ancestors: List[List[str]] = []
            for m in mappings:
                ancestors.append(
                    [x for x in self.get_ancestors(m, mixin)[::-1] if x in mappings]
                )
                logger.debug(ancestors)
            without_empty_lists = list(filter(None, ancestors))
            common_ancestors = reduce(
                lambda s, l: s.intersection(set(l)), without_empty_lists[1:], set(without_empty_lists[0])
            )
            logger.debug("common_ancestors")
            logger.debug(common_ancestors)
            for a in without_empty_lists[0]:
                logger.debug("ancestors[0]")
                logger.debug(a)
                if a in common_ancestors:
                    if formatted:
                        element = format_element(self.view.get_element(a))
                    else:
                        element = a
                    return element

    @lru_cache(CACHE_SIZE)
    def _get_element_by_mapping(self, identifier: str) -> List[str]:
        """
        Get the most specific mapping corresponding to a given identifier.
        This method first checks for general mappings. If it can't find any then
        it starts looking for exact_mappings, close_mappings, related_mappings,
        narrow_mappings and finally broad_mappings. It will stop if it finds a
        mapping at first occurrence.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = set(self.view.get_element_by_mapping(identifier))
        if not mappings:
            exact = set(self.get_element_by_exact_mapping(identifier))
            mappings.update(exact)
        if not mappings:
            close = set(self.get_element_by_close_mapping(identifier))
            mappings.update(close)
        if not mappings:
            related = set(self.get_element_by_related_mapping(identifier))
            mappings.update(related)
        if not mappings:
            narrow = set(self.get_element_by_narrow_mapping(identifier))
            mappings.update(narrow)
        if not mappings:
            broad = set(self.get_element_by_broad_mapping(identifier))
            mappings.update(broad)
        return mappings

    @lru_cache(CACHE_SIZE)
    def get_element_by_exact_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its exact_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mapping_index = self.view.get_mapping_index()
        elements = self.view.get_element_by_mapping(identifier)
        if elements:
            for element in elements:
                if mapping_index.get(identifier)[0] == 'exact' and mapping_index.get(identifier)[1] == element:
                    formatted_element = format_element(element)
                    return [formatted_element]
                else:
                    return []
        else:
            return []

    @lru_cache(CACHE_SIZE)
    def get_element_by_close_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its close_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mapping_index = self.view.get_mapping_index()
        elements = self.view.get_element_by_mapping(identifier)
        if elements:
            for element in elements:
                if mapping_index.get(identifier)[0] == 'close' and mapping_index.get(identifier)[1] == element:
                    formatted_element = format_element(element)
                    return [formatted_element]
                else:
                    return []
        else:
            return []

    @lru_cache(CACHE_SIZE)
    def get_element_by_related_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its related_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mapping_index = self.view.get_mapping_index()
        elements = self.view.get_element_by_mapping(identifier)
        if elements:
            for element in elements:
                if mapping_index.get(identifier)[0] == 'related' and mapping_index.get(identifier)[1] == element:
                    formatted_element = format_element(element)
                    return [formatted_element]
                else:
                    return []
        else:
            return []

    @lru_cache(CACHE_SIZE)
    def get_element_by_narrow_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its narrow_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mapping_index = self.view.get_mapping_index()
        elements = self.view.get_element_by_mapping(identifier)
        if elements:
            for element in elements:
                if mapping_index.get(identifier)[0] == 'narrow' and mapping_index.get(identifier)[1] == element:
                    formatted_element = format_element(element)
                    return [formatted_element]
                else:
                    return []
        else:
            return []

    @lru_cache(CACHE_SIZE)
    def get_element_by_broad_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its broad_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mapping_index = self.view.get_mapping_index()
        elements = self.view.get_element_by_mapping(identifier)
        if elements:
            for element in elements:
                if mapping_index.get(identifier)[0] == 'broad' and mapping_index.get(identifier)[1] == element:
                    formatted_element = format_element(element)
                    return [formatted_element]
                else:
                    return []
        else:
            return []

    @lru_cache(CACHE_SIZE)
    def get_all_elements_by_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find all Biolink elements that correspond
        to the given identifier as part of its mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.get_element_by_mapping(identifier)
        return self._format_all_elements(mappings, formatted)

    def _format_all_elements(
            self, elements: List[str], formatted: bool = False
    ) -> List[str]:
        """
        Format all the elements in a given list.

        Parameters
        ----------
        elements: str
            A list of elements
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            The formatted list of elements

        """
        if formatted:
            formatted_elements = [
                format_element(self.view.get_element(x)) for x in elements
            ]
        else:
            formatted_elements = elements
        return formatted_elements

    @lru_cache(CACHE_SIZE)
    def get_model_version(self) -> str:
        """
        Return the version of the biolink-model in use.

        Returns
        -------
        str
            The biolink-model version

        """
        return self.view.schema.version

    @deprecation.deprecated(
        deprecated_in="0.3.0",
        removed_in="1.0",
        details="Use get_all_elements method instead",
    )
    def names(self, formatted: bool = False) -> List[str]:
        return self.get_all_elements(formatted)

    @deprecation.deprecated(
        deprecated_in="0.2.0",
        removed_in="1.0",
        details="Use get_descendants method instead",
    )
    def descendents(self, name: str, mixin: bool = True) -> List[str]:
        return self.get_descendants(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.2.0",
        removed_in="1.0",
        details="Use get_ancestors method instead",
    )
    def ancestors(self, name: str, mixin: bool = True) -> List[str]:
        return self.get_ancestors(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.2.0",
        removed_in="1.0",
        details="Use get_children method instead",
    )
    def children(self, name: str, mixin: bool = True) -> List[str]:
        return self.get_children(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.2.0", removed_in="1.0", details="Use get_parent method instead"
    )
    def parent(self, name: str, mixin: bool = True) -> Optional[str]:
        return self.get_parent(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.1.1",
        removed_in="1.0",
        details="Use is_predicate method instead",
    )
    def is_edgelabel(self, name: str, mixin: bool = True) -> bool:
        return self.is_predicate(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.1.1",
        removed_in="1.0",
        details="Use get_all_elements_by_mapping method instead",
    )
    def get_all_by_mapping(self, uriorcurie: str) -> List[str]:
        return self.get_all_elements_by_mapping(uriorcurie)

    @deprecation.deprecated(
        deprecated_in="0.1.1",
        removed_in="1.0",
        details="Use get_element_by_mapping method instead",
    )
    def get_by_mapping(self, uriorcurie: str) -> Optional[str]:
        return self.get_element_by_mapping(uriorcurie)
