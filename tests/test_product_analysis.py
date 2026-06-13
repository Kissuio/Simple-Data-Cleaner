import unittest

import pandas as pd

from analyzer.product_analysis import get_product_count, get_top_quantity, get_top_revenue


class ProductAnalysisTests(unittest.TestCase):
    """验证实名商品和匿名 SKU 都能生成商品排行。"""

    def test_stock_code_is_used_when_description_is_absent(self):
        frame = pd.DataFrame(
            {
                "StockCode": ["sku-a", "sku-b", "sku-a"],
                "Quantity": [2, 5, 4],
                "TotalPrice": [20.0, 25.0, 40.0],
            }
        )

        quantity = get_top_quantity(frame)
        revenue = get_top_revenue(frame)

        self.assertEqual(quantity.index.tolist(), ["sku-a", "sku-b"])
        self.assertEqual(revenue.index.tolist(), ["sku-a", "sku-b"])

    def test_description_is_preferred_when_available(self):
        frame = pd.DataFrame(
            {
                "StockCode": ["sku-a", "sku-a", "sku-b"],
                "Description": ["商品甲", "商品甲", "商品乙"],
                "Quantity": [1, 2, 1],
                "TotalPrice": [10.0, 20.0, 40.0],
            }
        )

        self.assertEqual(get_top_quantity(frame).index[0], "商品甲")
        self.assertEqual(get_top_revenue(frame).index[0], "商品乙")

    def test_description_can_be_used_without_stock_code(self):
        frame = pd.DataFrame(
            {
                "Description": ["商品甲", "商品乙", "商品甲"],
                "Quantity": [2, 5, 4],
                "TotalPrice": [20.0, 25.0, 40.0],
            }
        )

        self.assertEqual(get_product_count(frame), 2)
        self.assertEqual(get_top_quantity(frame).index.tolist(), ["商品甲", "商品乙"])
        self.assertEqual(get_top_revenue(frame).index.tolist(), ["商品甲", "商品乙"])


if __name__ == "__main__":
    unittest.main()
