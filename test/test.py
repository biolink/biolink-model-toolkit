import bmt, unittest

class TestBiolinkModelToolkit(unittest.TestCase):

    def test_edgelabel(self):
        self.assertEqual(bmt.is_edgelabel('named thing'), False)
        self.assertEqual(bmt.is_edgelabel('gene'), False)
        self.assertEqual(bmt.is_edgelabel('causes'), True)

    def test_predicate(self):
        self.assertEqual(bmt.is_predicate('named thing'), False)
        self.assertEqual(bmt.is_predicate('gene'), False)
        self.assertEqual(bmt.is_predicate('related to'), True)
        self.assertEqual(bmt.is_predicate('causes'), True)

    def test_category(self):
        self.assertTrue(bmt.is_category('named thing'))
        self.assertTrue(bmt.is_category('gene'))
        self.assertFalse(bmt.is_category('causes'))

    def test_ancestors(self):
        self.assertTrue('related to' in bmt.ancestors('causes'))
        self.assertTrue('named thing' in bmt.ancestors('gene'))

    def test_descendents(self):
        self.assertTrue('causes' in bmt.descendents('related to'))
        self.assertTrue('gene' in bmt.descendents('named thing'))

    def test_children(self):
        self.assertTrue('causes' in bmt.children('contributes to'))

    def test_parent(self):
        self.assertTrue('contributes to' == bmt.parent('causes'))

    def test_mapping(self):
        self.assertEqual(bmt.get_by_mapping('RO:0002410'), 'causes')
        self.assertEqual(bmt.get_by_mapping('UMLSSG:GENE'), 'genomic entity')
        self.assertTrue('gene' in bmt.get_all_by_mapping('UMLSSG:GENE'))
        self.assertTrue('genomic entity' in bmt.get_all_by_mapping('UMLSSG:GENE'))

        try:
            bmt.get_by_mapping('SEMMEDDB:ASSOCIATED_WITH')
            bmt.get_by_mapping('SEMMEDDB:CAUSES')
        except:
            self.fail()

    def test_get_class(self):
        p1 = bmt.get_class('phenotype')
        p2 = bmt.get_class('phenotypic feature')
        self.assertTrue(p1.name == p2.name == 'phenotypic feature')
        self.assertEqual(bmt.get_class('causes'), None)

    def test_get_predicate(self):
        p1 = bmt.get_predicate('is substance that treats')
        p2 = bmt.get_predicate('treats')
        self.assertTrue(p1.name == p2.name == 'treats')
        self.assertEqual(bmt.get_predicate('gene'), None)

if __name__ == '__main__':
    unittest.main()
