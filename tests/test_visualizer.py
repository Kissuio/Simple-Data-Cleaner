import unittest
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")

from visualization.visualizer import Visualizer


class VisualizerTests(unittest.TestCase):
    """验证真实交易中的边界金额不会阻断图表生成。"""

    def test_rfm_scatter_accepts_negative_monetary_values(self):
        rfm = pd.DataFrame(
            {
                "Recency": [1, 2],
                "Frequency": [1, 3],
                "Monetary": [-10.0, 100.0],
                "Label": ["一般挽留客户", "重要价值客户"],
            }
        )

        directory = Path("output/test_visualizer")
        path = Visualizer(directory).plot_rfm_scatter(rfm)
        self.assertGreater(Path(path).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
