import unittest
from bmt import Toolkit

from inspect import signature


class TestBiolinkModelToolkit(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.toolkit = Toolkit.build_locally()

    def test_get_element(self):

        gene = self.toolkit.get_element('gene')
        locus = self.toolkit.get_element('locus')

        self.assertEqual(gene, locus)
        self.assertTrue(gene is not None)

    def test_edgelabel(self):
        self.assertEqual(self.toolkit.is_edgelabel('named thing'), False)
        self.assertEqual(self.toolkit.is_edgelabel('gene'), False)
        self.assertEqual(self.toolkit.is_edgelabel('causes'), True)

    def test_category(self):
        self.assertTrue(self.toolkit.is_category('named thing'))
        self.assertTrue(self.toolkit.is_category('gene'))
        self.assertFalse(self.toolkit.is_category('causes'))

    def test_ancestors(self):
        self.assertTrue('related to' in self.toolkit.ancestors('causes'))
        self.assertTrue('named thing' in self.toolkit.ancestors('gene'))

    def test_descendents(self):
        self.assertTrue('causes' in self.toolkit.descendents('related to'))
        self.assertTrue('gene' in self.toolkit.descendents('named thing'))

    def test_children(self):
        self.assertTrue('causes' in self.toolkit.children('contributes to'))

    def test_parent(self):
        self.assertEqual('contributes to', self.toolkit.parent('causes'))

    def test_mapping(self):
        # probe0 has no mappings
        self.assertEqual({}, self.toolkit.get_all_by_mapping('biolink:probe0'))
        self.assertIsNone(self.toolkit.get_by_mapping('biolink:probe0'))

        # probe1 has exactly one mapping
        self.assertEqual({'affects'}, self.toolkit.get_all_by_mapping('biolink:probe1'))
        self.assertEqual('affects', self.toolkit.get_by_mapping('biolink:probe1'))

        # The following tests apply to the two ancestor paths:
        #    Path 1:
        #    'negatively regulates, process to process'    probe2   probe3  probe4
        #        'regulates, process to process'                    probe3  probe4
        #            'regulates'
        #                'affects'              probe1     probe2           probe4
        #                    'related to'
        #    Path 2:
        #    'negatively regulates, entity to entity'               probe3
        #        'regulates, entity to entity'                      probe3  probe4
        #            'regulates'
        #                'affects'              probe1     probe2           probe4
        #                    'related to'
        #
        #  probe1 should return 'affects'
        self.assertEqual({'affects'}, self.toolkit.get_all_by_mapping('biolink:probe1'))
        self.assertEqual('affects', self.toolkit.get_by_mapping('biolink:probe1'))
        #  probe2 should return 'affects'
        self.assertEqual({'negatively regulates, process to process', 'affects'},
                         self.toolkit.get_all_by_mapping('biolink:probe2'))
        self.assertEqual('affects', self.toolkit.get_by_mapping('biolink:probe2'))
        #  probe3 should return None
        self.assertEqual({'negatively regulates, process to process', 'regulates, process to process',
                          'positively regulates, entity to entity', 'regulates, entity to entity'},
                         self.toolkit.get_all_by_mapping('biolink:probe3'))
        self.assertIsNone(self.toolkit.get_by_mapping('biolink:probe3'))
        #  probe4 should return 'affects
        self.assertEqual({'negatively regulates, process to process', 'regulates, process to process',
                          'positively regulates, entity to entity', 'regulates, entity to entity',
                          'affects'},
                         self.toolkit.get_all_by_mapping('biolink:probe4'))
        self.assertEqual('affects', self.toolkit.get_by_mapping('biolink:probe2'))
        try:
            self.toolkit.get_by_mapping('SEMMEDDB:ASSOCIATED_WITH')
            self.toolkit.get_by_mapping('SEMMEDDB:CAUSES')
        except:
            self.fail()

    def test_inputs(self):
        """
        All methods in toolkit.ToolKit take a single string as an input. This test
        checks that they still work for invalid inputs and return None.
        """

        for name in dir(self.toolkit):
            if name.startswith('_'):
                continue
            method = getattr(self.toolkit, name)
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
