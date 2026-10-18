import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("speech_check", ROOT / "scripts/speech_check.py")
speech = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speech)


class SpeechChecks(unittest.TestCase):
    def test_stage_time_and_spoken_numerals_remain_distinct(self):
        result = speech.inspect("正面有97次。[停顿 2秒]\n[画面：显示200个点]\n再看A组。[演示 10秒]", cpm=60)
        self.assertEqual(result["fixed_cue_seconds"], 12)
        self.assertEqual(result["digits"], 2)
        self.assertEqual(result["latin_letters"], 1)
        self.assertEqual(result["time_estimate"]["total_seconds"], result["spoken_characters"] + 12)

    def test_notes_tables_and_code_do_not_enter_selected_speech(self):
        text = "# 稿件\n## 讲稿正文\n甲。\n### 图表\n乙。\n```md\n## 不应结束章节\n代码\n```\n| 内部 | 表格 |\n## 来源\n附注内容。"
        result = speech.inspect(text, section="讲稿正文")
        self.assertEqual(result["han_characters"], 2)
        self.assertNotIn("time_estimate", result)

    def test_links_keep_spoken_labels_without_url_or_image(self):
        result = speech.inspect("看[甲](https://example.org/long)和![图](image.png)中的乙。")
        self.assertEqual(result["latin_letters"], 0)
        self.assertEqual(result["han_characters"], 6)

    def test_constraints_are_user_selected_with_original_line_numbers(self):
        text = "# 题目\n## 正文\n需要核对。\n必要限定保留。\n## 注释\n核对。"
        result = speech.inspect(text, "正文", forbid=("核对",))
        self.assertEqual([hit["line"] for hit in result["user_constraint_hits"]], [3])
        self.assertEqual(speech.inspect("没有出现效果。")['user_constraint_hits'], [])

    def test_frontmatter_and_foreign_fence_markers_stay_offstage(self):
        text = "---\ntitle: 标题\n---\n~~~python\n```\n隐藏\n~~~\n正文。"
        self.assertEqual(speech.inspect(text)["han_characters"], 2)

    def test_missing_section_and_invalid_speed_fail(self):
        with self.assertRaises(ValueError):
            speech.inspect("正文", section="不存在")
        for speed in (0, -1, float("nan"), float("inf"), -float("inf")):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                speech.inspect("正文", cpm=speed)

    def test_long_fence_requires_matching_length_and_empty_closing_suffix(self):
        text = "## 正文\n甲。\n````md\n```\n## 假标题\n隐藏\n```` trailing\n继续隐藏\n`````\n乙。\n## 附录\n附录。"
        self.assertEqual(speech.inspect(text, "正文")["han_characters"], 2)
        self.assertEqual(speech.inspect(text)["han_characters"], 4)

    def test_editorial_comments_and_footnotes_keep_constraint_line_numbers(self):
        text = "## 正文\n甲[^ref]。<!-- 不读 [停顿 90秒]\n## 假标题\n-->\n乙。\n[^ref]: 来源内容\n    续注\n\n丙需核对。\n## 附录\n隐藏。"
        result = speech.inspect(text, "正文", forbid=("核对",))
        self.assertEqual(result["han_characters"], 6)
        self.assertEqual(result["fixed_cue_seconds"], 0)
        self.assertEqual(result["user_constraint_hits"][0]["line"], 9)


if __name__ == "__main__":
    unittest.main()
