import unittest

from services.product_import import (
    build_template_xlsx,
    infer_import_category,
    parse_jsonl_rows,
    parse_xlsx_rows,
)


class ProductImportTests(unittest.TestCase):
    def test_template_can_roundtrip_for_racket(self):
        rows = parse_xlsx_rows(build_template_xlsx(1))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "YONEX 天斧 77 Pro（示例）")
        self.assertIn("AX77PRO", rows[0]["model_aliases"])
        self.assertEqual(rows[0]["source_confidence"], "中高")
        self.assertIn("实时价格", rows[0]["unverified_fields"])

    def test_category_can_be_inferred_from_headers(self):
        rows = parse_xlsx_rows(build_template_xlsx(4))
        category_id = infer_import_category(rows[0].keys())

        self.assertEqual(category_id, 4)

    def test_v4_jsonl_record_is_normalized_for_racket_import(self):
        raw = (
            '{"model_display":"YONEX ASTROX 77 PRO","brand":"YONEX","series":"ASTROX 天斧",'
            '"model_aliases":["AX77PRO","天斧77PRO"],"price_ref":"¥1100",'
            '"specs_summary":"重量规格=4U；平衡点=头重；中杆硬度=中；最高建议穿线磅数=28 lbs；适合水平=新手/进阶；打法定位=进攻/均衡",'
            '"source_confidence":"中高","caution_notes":"部分参数建议以品牌官方页为准"}\n'
        ).encode("utf-8")

        rows = parse_jsonl_rows(raw)

        self.assertEqual(rows[0]["name"], "YONEX ASTROX 77 PRO")
        self.assertEqual(rows[0]["price"], "1100")
        self.assertEqual(rows[0]["weight_class"], "4U")
        self.assertEqual(rows[0]["balance"], "head-heavy")
        self.assertEqual(rows[0]["shaft_flex"], "medium")
        self.assertEqual(rows[0]["source_confidence"], "中高")


if __name__ == "__main__":
    unittest.main()
