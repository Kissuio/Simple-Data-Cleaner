import unittest

import pandas as pd

from analyzer.sales_trend import get_monthly_sales


class MonthlySalesTests(unittest.TestCase):
    """验证月度汇总忠实保留当前筛选范围内的全部月份。"""

    def test_last_month_is_not_dropped(self):
        """最后一个月是否完整应由用户筛选决定，聚合层不得自行删除。"""
        frame = pd.DataFrame(
            {
                "InvoiceDate": pd.to_datetime(
                    ["2026-01-01", "2026-02-01", "2026-03-01"]
                ),
                "TotalPrice": [10, 20, 30],
            }
        )

        monthly = get_monthly_sales(frame)

        self.assertEqual(monthly.index.tolist(), ["2026-01", "2026-02", "2026-03"])
        self.assertEqual(monthly.iloc[-1], 30)


if __name__ == "__main__":
    unittest.main()
