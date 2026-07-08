import unittest

from services.product_import import (
    build_template_xlsx,
    infer_import_category,
    parse_xlsx_rows,
)


class ProductImportTests(unittest.TestCase):
    def test_template_can_roundtrip_for_racket(self):
        rows = parse_xlsx_rows(build_template_xlsx(1))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "YONEX 天斧 77 Pro（示例）")
        self.assertIn("AX77PRO", rows[0]["model_aliases"])

    def test_category_can_be_inferred_from_headers(self):
        rows = parse_xlsx_rows(build_template_xlsx(4))
        category_id = infer_import_category(rows[0].keys())

        self.assertEqual(category_id, 4)


if __name__ == "__main__":
    unittest.main()
