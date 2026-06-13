"""Tests for per-dataset chart output folder names."""

from pathlib import Path
import unittest

from gui.output_paths import dataset_output_folder_name, dataset_output_picture_dir


class OutputPathTests(unittest.TestCase):
    """Verify generated chart folders are separated by dataset name."""

    def test_online_retail_folder_name(self):
        """English dataset names should be preserved and normalized with underscores."""
        self.assertEqual(
            dataset_output_folder_name("data/online_retail/Online Retail.csv"),
            "Online_Retail_output_picture",
        )

    def test_symbols_are_collapsed_to_underscores(self):
        """Spaces and punctuation should not leak into the output folder name."""
        self.assertEqual(
            dataset_output_folder_name("sales-data sample.xlsx"),
            "sales_data_sample_output_picture",
        )

    def test_non_ascii_name_gets_stable_english_fallback(self):
        """A non-English filename should still produce an ASCII-only folder."""
        folder = dataset_output_folder_name("用户购买记录.csv")
        self.assertRegex(folder, r"^dataset_[0-9a-f]{8}_output_picture$")
        self.assertTrue(folder.isascii())

    def test_output_dir_uses_requested_base_dir(self):
        """The folder should be created under the project-controlled base directory."""
        self.assertEqual(
            dataset_output_picture_dir("Online Retail.csv", base_dir=Path("reports")),
            Path("reports") / "Online_Retail_output_picture",
        )

    def test_default_output_dir_stays_under_output(self):
        """All chart routes should share output as their top-level directory."""
        self.assertEqual(
            dataset_output_picture_dir("Online Retail.csv"),
            Path("output") / "Online_Retail_output_picture",
        )


if __name__ == "__main__":
    unittest.main()
