import unittest
from types import SimpleNamespace

import pandas as pd

from gui.guided_tour import GuidedTour, build_tour_steps


class GuidedTourStepTests(unittest.TestCase):
    """带练步骤表结构校验（不建 GUI，直接验证数据、辅助动作与检验分发）。"""

    def test_steps_cover_full_pipeline_in_order(self):
        """带练必须按主线顺序覆盖：加载→清洗→映射→RFM→销售→商品→总览。"""
        keys = [step["key"] for step in build_tour_steps()]
        self.assertEqual(
            keys,
            [
                "welcome", "load", "dup", "range", "date", "derive", "clean_done",
                "mapping", "rfm", "sales", "product", "overview", "done",
            ],
        )

    def test_each_step_has_required_fields(self):
        """每一步都应有标题与正文，便于教练浮窗渲染。"""
        for step in build_tour_steps():
            for field in ("key", "page", "title", "body"):
                self.assertIn(field, step)
            self.assertTrue(step["title"])
            self.assertTrue(step["body"])

    def test_every_assist_and_verify_token_has_handler(self):
        """每个 assist / verify token 都必须有对应处理方法（防止拼写错导致点不动/检验崩）。"""
        for step in build_tour_steps():
            assist = step.get("assist")
            if assist is not None:
                self.assertTrue(
                    hasattr(GuidedTour, f"_assist_{assist}"),
                    f"步骤 {step['key']} 缺少 _assist_{assist}",
                )
                self.assertIn("assist_text", step)
            verify = step.get("verify")
            if verify is not None:
                self.assertTrue(
                    hasattr(GuidedTour, f"_verify_{verify}"),
                    f"步骤 {step['key']} 缺少 _verify_{verify}",
                )
                self.assertIn("verify_hint", step)

    def test_mapping_step_is_deferred_to_rfm_not_cleaner_page(self):
        """字段映射步应停留当前页（page=None）、靠按钮前往 RFM 才弹映射，而非作为清洗页的步。"""
        steps = {s["key"]: s for s in build_tour_steps()}
        mapping = steps["mapping"]
        self.assertIsNone(mapping["page"])
        self.assertEqual(mapping.get("assist"), "goto_mapping")

    def test_cleaning_steps_require_hands_on_verification(self):
        """每个清洗步都要有 verify（学生亲手做、教练事后检验），不再代劳执行。"""
        steps = {s["key"]: s for s in build_tour_steps()}
        for key in ("dup", "range", "date", "derive"):
            self.assertIn("verify", steps[key], f"{key} 缺少检验")
            self.assertNotIn("assist", steps[key], f"{key} 不该有代劳按钮")

    def test_verify_dedup_reflects_real_duplicates(self):
        """删重复的检验应真实反映数据里是否还有完全重复行。"""
        tour = GuidedTour.__new__(GuidedTour)  # 不建 GUI
        dup_df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
        tour.app = SimpleNamespace(cleaner=SimpleNamespace(df=dup_df))
        self.assertFalse(tour._verify_dedup())

        tour.app = SimpleNamespace(cleaner=SimpleNamespace(df=dup_df.drop_duplicates()))
        self.assertTrue(tour._verify_dedup())

    def test_verify_price_positive_reflects_nonpositive_rows(self):
        """单价≤0 的检验应真实反映是否还有 final_unit_price ≤ 0 的行。"""
        tour = GuidedTour.__new__(GuidedTour)
        df = pd.DataFrame({"final_unit_price": [10.0, 0.0, -3.0, 5.0]})
        tour.app = SimpleNamespace(cleaner=SimpleNamespace(df=df))
        self.assertFalse(tour._verify_price_positive())

        tour.app = SimpleNamespace(cleaner=SimpleNamespace(df=df[df["final_unit_price"] > 0]))
        self.assertTrue(tour._verify_price_positive())

    def test_verify_derived_detects_new_column(self):
        """派生新列的检验应在出现 TotalPrice / 新增列时通过。"""
        tour = GuidedTour.__new__(GuidedTour)
        tour._raw_cols = {"quantity", "final_unit_price"}
        before = pd.DataFrame({"quantity": [2], "final_unit_price": [5.0]})
        tour.app = SimpleNamespace(cleaner=SimpleNamespace(df=before))
        self.assertFalse(tour._verify_derived())

        after = before.assign(TotalPrice=[10.0])
        tour.app = SimpleNamespace(cleaner=SimpleNamespace(df=after))
        self.assertTrue(tour._verify_derived())


if __name__ == "__main__":
    unittest.main()
