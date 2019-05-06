# biolink-model-toolkit

A collection of useful python functions for looking up information from the biolink model (https://github.com/biolink/biolink-model).


Official source for `biolink-model.yaml`: https://biolink.github.io/biolink-model/biolink-model.yaml

### Installation

https://pypi.org/project/bmt/

`pip install bmt`

### Documentation
This is a small project, so I'll let the code speak for itself. To see documentation use pythons built in `help` method:

```
$ python
>>> import bmt
>>> help(bmt)
CLASSES
    builtins.object
        Toolkit
    
    class Toolkit(builtins.object)
     |  Provides a series of methods for performing lookups on the
     |  biolink-model.yaml file.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, schema:Union[str, TextIO, metamodel.metamodel.SchemaDefinition]='https://biolink.github.io/biolink-model/biolink-model.yaml') -> bmt.toolkit_generator.ToolkitGenerator
     |      Instantiates a Toolkit object.
     |      
     |      Parameters
     |      ----------
     |      schema : Union[str, TextIO, SchemaDefinition]
     |          The path or url to an instance of the biolink-model.yaml file.
     |  
     |  ancestors(self, name:str) -> List[str]
     |      Gets a list of names of ancestors.
     |      
     |      Parameters
     |      ----------
     |      name : str
     |          The name of an element in the biolink model.
     |      
     |      Returns
     |      -------
     |      List[str]
     |          The names of the given elements ancestors.
     ...
```

### Usage

```
>>> from bmt import Toolkit
>>> t = Toolkit()
>>> t.get_by_mapping('SEMMEDDB:CAUSES')
'causes'
>>> t.get_by_mapping('RO:0002410')
'causes'
>>> t.get_element('causes')
SlotDefinition(name='causes', singular_name=None, description='holds between two entities where the occurrence, existence, or activity of one causes the occurrence or  generation of the other', note=None, comment=None, examples=[], see_also=None, flags=[], aliases=[], mappings=['RO:0002410', 'SEMMEDDB:CAUSES', 'WD:P1542'], id_prefixes=[], in_subset=['translator_minimal'], from_schema=None, alt_descriptions=[], exact_matches=[], broader_matches=[], narrower_matches=[], close_matches=[], is_a='contributes to', mixin=False, mixins=[], abstract=False, local_names=[], union_of=[], subclass_of=None, values_from=[], symmetric=False, multivalued=False, domain='named thing', range='named thing', required=False, object_property=False, inlined=False, primary_key=False, identifier=False, definitional=False, alias=None, path=None, subproperty_of=None, inverse=None, is_class_field=False, role=None, inherited=False)
>>> t.ancestors('causes')
['contributes to', 'related to']
>>> t.descendents('related to')
['has gene product', 'produces', 'homologous to', 'expresses', 'participates in', 'has phenotype', 'has participant', 'in taxon', 'has molecular consequence', 'interacts with', 'correlated with', 'contributes to', 'model of', 'affects', 'same as', 'coexists with', 'located in', 'gene associated with condition', 'precedes', 'location of', 'derives from', 'affects risk for', 'derives into', 'occurs in', 'treated by', 'expressed in', 'overlaps', 'subclass of', 'manifestation of', 'orthologous to', 'xenologous to', 'paralogous to', 'actively involved in', 'has input', 'physically interacts with', 'genetically interacts with', 'has biomarker', 'biomarker for', 'causes', 'affects mutation rate of', 'affects stability of', 'affects expression of', 'affects degradation of', 'affects response to', 'affects synthesis of', 'affects activity of', 'disrupts', 'affects molecular modification of', 'affects transport of', 'affects uptake of', 'treats', 'affects secretion of', 'affects abundance of', 'affects localization of', 'affects splicing of', 'regulates', 'affects metabolic processing of', 'affects folding of', 'co-localizes with', 'in cell population with', 'in pathway with', 'in complex with', 'predisposes', 'prevents', 'has part', 'part of', 'capable of', 'molecularly interacts with', 'decreases mutation rate of', 'increases mutation rate of', 'increases stability of', 'decreases stability of', 'increases expression of', 'decreases expression of', 'increases degradation of', 'decreases degradation of', 'decreases response to', 'increases response to', 'decreases synthesis of', 'increases synthesis of', 'decreases activity of', 'increases activity of', 'increases molecular modification of', 'decreases molecular modification of', 'increases transport of', 'decreases transport of', 'decreases uptake of', 'increases uptake of', 'decreases secretion of', 'increases secretion of', 'decreases abundance of', 'increases abundance of', 'decreases localization of', 'increases localization of', 'increases splicing of', 'decreases splicing of', 'regulates, process to process', 'positively regulates', 'regulates, entity to entity', 'negatively regulates', 'increases metabolic processing of', 'decreases metabolic processing of', 'increases folding of', 'decreases folding of', 'positively regulates, process to process', 'negatively regulates, process to process', 'negatively regulates, entity to entity', 'positively regulates, entity to entity']
>>> t.is_category('causes')
False
>>> t.is_edgelabel('causes')
True
>>> t.is_category('gene')
True
```
