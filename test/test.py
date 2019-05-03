import unittest
from bmt import Toolkit

from inspect import signature

class TestBiolinkModelToolkit(unittest.TestCase):

    def test_get_element(self):
        toolkit = Toolkit.build_locally()

        gene = toolkit.get_element('gene')
        locus = toolkit.get_element('locus')

        self.assertEqual(gene, locus)
        self.assertTrue(gene is not None)

    def test_edgelabel(self):
        toolkit = Toolkit.build_locally()
        self.assertEqual(toolkit.is_edgelabel('named thing'), False)
        self.assertEqual(toolkit.is_edgelabel('gene'), False)
        self.assertEqual(toolkit.is_edgelabel('causes'), True)

    def test_category(self):
        toolkit = Toolkit.build_locally()
        self.assertTrue(toolkit.is_category('named thing'))
        self.assertTrue(toolkit.is_category('gene'))
        self.assertFalse(toolkit.is_category('causes'))

    def test_ancestors(self):
        toolkit = Toolkit.build_locally()
        self.assertTrue('related to' in toolkit.ancestors('causes'))
        self.assertTrue('named thing' in toolkit.ancestors('gene'))

    def test_descendents(self):
        toolkit = Toolkit.build_locally()
        self.assertTrue('causes' in toolkit.descendents('related to'))
        self.assertTrue('gene' in toolkit.descendents('named thing'))

    def test_children(self):
        toolkit = Toolkit.build_locally()
        self.assertTrue('causes' in toolkit.children('contributes to'))

    def test_parent(self):
        toolkit = Toolkit.build_locally()
        self.assertTrue('contributes to' == toolkit.parent('causes'))

    def test_mapping(self):
        toolkit = Toolkit.build_locally()
        self.assertEqual(toolkit.get_by_mapping('RO:0002410'), 'causes')
        self.assertEqual(toolkit.get_by_mapping('UMLSSG:GENE'), 'genomic entity')
        self.assertTrue('gene' in toolkit.get_all_by_mapping('UMLSSG:GENE'))
        self.assertTrue('genomic entity' in toolkit.get_all_by_mapping('UMLSSG:GENE'))

        try:
            toolkit.get_by_mapping('SEMMEDDB:ASSOCIATED_WITH')
            toolkit.get_by_mapping('SEMMEDDB:CAUSES')
        except:
            self.fail()

    def test_inputs(self):
        """
        All methods in toolkit.ToolKit take a single string as an input. This test
        checks that they still work for invalid inputs and return None.
        """
        tk = Toolkit.build_locally()

        for name in dir(tk):
            if name.startswith('_'):
                continue
            method = getattr(tk, name)
            if hasattr(method, '__call__'):
                sig = signature(method)
                if len(sig.parameters) == 1:
                    # Testing the standard lookup methods
                    method(None)
                    method(3)
                    method('invalid')
                    method(0.25)
                else:
                    method(*sig.parameters.keys())

if __name__ == '__main__':
    unittest.main()
