"""Layout helper tests for cleaning toolbox dialogs."""

import unittest

from gui.clean_dialog import (
    CATEGORIES,
    CLEAN_DIALOG_DELETE_ROW_MAX_HEIGHT,
    clean_dialog_height,
    steps_in_category,
)


class CleanDialogLayoutTests(unittest.TestCase):
    """Verify cleaning toolbox dialog sizing remains comfortable."""

    def test_delete_row_toolbox_opens_shorter(self):
        """The first toolbox should no longer open as a very tall dialog."""
        category = next(cat for cat in CATEGORIES if cat["name"] == "删除行")
        height = clean_dialog_height(steps_in_category(category), category["name"])
        self.assertEqual(height, CLEAN_DIALOG_DELETE_ROW_MAX_HEIGHT)
        self.assertLess(height, 840)


if __name__ == "__main__":
    unittest.main()
