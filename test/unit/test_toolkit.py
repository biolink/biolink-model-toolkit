from bmt import Toolkit


def test_get_element():
    toolkit = Toolkit()
    gene = toolkit.get_element('gene')
    locus = toolkit.get_element('locus')
    assert gene == locus


def test_predicate():
    toolkit = Toolkit()
    assert not toolkit.is_predicate('named thing')
    assert not toolkit.is_predicate('gene')
    assert toolkit.is_predicate('causes')


def test_category():
    toolkit = Toolkit()
    assert toolkit.is_category('named thing')
    assert toolkit.is_category('gene')
    assert not toolkit.is_category('causes')
    assert not toolkit.is_category('affects')


def test_ancestors():
    toolkit = Toolkit()
    assert 'related to' in toolkit.get_ancestors('causes')
    assert 'named thing' in toolkit.get_ancestors('gene')


def test_descendants():
    toolkit = Toolkit()
    assert 'causes' in toolkit.get_descendants('related to')
    assert 'interacts with' in toolkit.get_descendants('related to')
    assert 'gene' in toolkit.get_descendants('named thing')
    assert 'phenotypic feature' in toolkit.get_descendants('named thing')


def test_children():
    toolkit = Toolkit()
    assert 'causes' in toolkit.get_children('contributes to')
    assert 'physically interacts with' in toolkit.get_children('interacts with')
    assert 'gene' in toolkit.get_children('gene or gene product')


def test_parent():
    toolkit = Toolkit()
    assert 'contributes to' in toolkit.get_parent('causes')
    assert 'interacts with' in toolkit.get_parent('physically interacts with')
    assert 'gene or gene product' in toolkit.get_parent('gene')


def test_mapping():
    toolkit = Toolkit()
    assert len(toolkit.get_all_elements_by_mapping('SO:0000704')) == 1
    assert 'gene' in toolkit.get_all_elements_by_mapping('SO:0000704')

    assert len(toolkit.get_all_elements_by_mapping('MONDO:0000001')) == 1
    assert 'disease' in toolkit.get_all_elements_by_mapping('MONDO:0000001')

    assert len(toolkit.get_all_elements_by_mapping('UPHENO:0000001')) == 1
    assert 'affects' in toolkit.get_all_elements_by_mapping('UPHENO:0000001')

    assert len(toolkit.get_all_elements_by_mapping('RO:0004033')) == 1
    assert 'negatively regulates' in toolkit.get_all_elements_by_mapping('RO:0004033')

