import unittest

import pandas as pd

from data_handlers.field_mapping import (
    apply_field_mapping,
    guess_mapping,
    missing_required_fields,
)


class ApplyFieldMappingTests(unittest.TestCase):
    """验证字段映射不会产生重复列或污染原始数据。"""

    def test_selected_source_overrides_existing_standard_column(self):
        """用户选择的来源应覆盖同名标准列，并用于派生销售额。"""
        source = pd.DataFrame(
            {
                "Quantity": [999],
                "qty": [2],
                "price": [3],
                "TotalPrice": [999],
            }
        )

        result = apply_field_mapping(
            source,
            {"Quantity": "qty", "UnitPrice": "price"},
        )

        self.assertTrue(result.columns.is_unique)
        self.assertEqual(result.loc[0, "Quantity"], 2)
        self.assertEqual(result.loc[0, "UnitPrice"], 3)
        self.assertEqual(result.loc[0, "TotalPrice"], 6)
        self.assertNotIn("qty", result.columns)
        self.assertNotIn("price", result.columns)
        self.assertEqual(source.loc[0, "Quantity"], 999)
        self.assertIn("qty", source.columns)

    def test_explicit_total_price_mapping_is_not_recalculated(self):
        """显式映射的销售额应优先于数量乘单价。"""
        source = pd.DataFrame(
            {"qty": [2], "price": [3], "amount": [100]}
        )

        result = apply_field_mapping(
            source,
            {
                "Quantity": "qty",
                "UnitPrice": "price",
                "TotalPrice": "amount",
            },
        )

        self.assertEqual(result.loc[0, "TotalPrice"], 100)

    def test_cross_mapping_reads_each_value_from_original_dataframe(self):
        """字段互换时不能让前一次赋值影响后一次取值。"""
        source = pd.DataFrame({"Quantity": [2], "UnitPrice": [7]})

        result = apply_field_mapping(
            source,
            {"Quantity": "UnitPrice", "UnitPrice": "Quantity"},
        )

        self.assertEqual(result.loc[0, "Quantity"], 7)
        self.assertEqual(result.loc[0, "UnitPrice"], 2)
        self.assertEqual(result.loc[0, "TotalPrice"], 14)
        self.assertTrue(result.columns.is_unique)

    def test_same_source_cannot_feed_multiple_standard_fields(self):
        """同一实际列映射到多个标准字段时应明确拒绝。"""
        source = pd.DataFrame({"value": [1]})

        with self.assertRaisesRegex(ValueError, "不能映射到多个标准字段"):
            apply_field_mapping(
                source,
                {"Quantity": "value", "UnitPrice": "value"},
            )

    def test_duplicate_input_column_names_are_rejected(self):
        """原始重复列名无法可靠选列，应在映射前明确报错。"""
        source = pd.DataFrame([[1, 2]], columns=["value", "value"])

        with self.assertRaisesRegex(ValueError, "重复列名"):
            apply_field_mapping(source, {"Quantity": "value"})

    def test_common_date_export_names_are_guessed(self):
        """常见第三方日期列名应自动建议为 InvoiceDate。"""
        self.assertEqual(
            guess_mapping(["ORDERDATE"])["InvoiceDate"],
            "ORDERDATE",
        )
        self.assertEqual(
            guess_mapping(["update_time"])["InvoiceDate"],
            "update_time",
        )

    def test_jd_style_underscored_columns_are_guessed(self):
        """大型平台常见的下划线字段应直接匹配到标准销售字段。"""
        columns = [
            "order_ID",
            "user_ID",
            "sku_ID",
            "order_time",
            "quantity",
            "final_unit_price",
        ]

        self.assertEqual(
            guess_mapping(columns),
            {
                "CustomerID": "user_ID",
                "InvoiceNo": "order_ID",
                "InvoiceDate": "order_time",
                "Quantity": "quantity",
                "UnitPrice": "final_unit_price",
                "Description": None,
                "StockCode": "sku_ID",
                "Country": None,
                "TotalPrice": None,
            },
        )

    def test_precise_order_time_is_preferred_over_order_date(self):
        """同时存在日期和时间时，应优先保留小时分钟信息。"""
        self.assertEqual(
            guess_mapping(["order_date", "order_time"])["InvoiceDate"],
            "order_time",
        )

    def test_anonymized_products_do_not_require_description(self):
        """有稳定 SKU 编码时，匿名数据不应因缺商品名称而被拦截。"""
        columns = [
            "CustomerID",
            "InvoiceNo",
            "InvoiceDate",
            "Quantity",
            "UnitPrice",
            "StockCode",
            "TotalPrice",
        ]

        self.assertEqual(missing_required_fields(columns, "product"), [])
        self.assertEqual(missing_required_fields(columns, "overview"), [])

    def test_named_products_do_not_require_stock_code(self):
        """只有商品名称、没有 SKU 编码时，也应允许进入商品分析。"""
        columns = [
            "CustomerID",
            "InvoiceNo",
            "InvoiceDate",
            "Quantity",
            "UnitPrice",
            "Description",
            "TotalPrice",
        ]

        self.assertEqual(missing_required_fields(columns, "product"), [])
        self.assertEqual(missing_required_fields(columns, "overview"), [])

    def test_missing_product_identity_uses_alternative_hint(self):
        """编码和名称都缺时，提示应表达“二选一”而不是写死编码。"""
        columns = [
            "CustomerID",
            "InvoiceNo",
            "InvoiceDate",
            "Quantity",
            "UnitPrice",
            "TotalPrice",
        ]

        self.assertEqual(
            missing_required_fields(columns, "product"),
            ["StockCode|Description"],
        )


if __name__ == "__main__":
    unittest.main()
