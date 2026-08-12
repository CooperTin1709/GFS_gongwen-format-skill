from __future__ import annotations

import unittest

from scripts.input_adapter import adapt_source_text
from scripts.utils import PipelineError


class InputAdapterTests(unittest.TestCase):
    def test_lf_and_crlf_produce_the_same_paragraphs(self) -> None:
        lf = adapt_source_text("甲\n乙\n")
        crlf = adapt_source_text("甲\r\n乙\r\n")
        self.assertEqual(lf["paragraphs"], crlf["paragraphs"])

    def test_cr_newlines_are_supported(self) -> None:
        data = adapt_source_text("甲\r乙")
        self.assertEqual([item["text"] for item in data["paragraphs"]], ["甲", "乙"])

    def test_leading_trailing_and_repeated_blank_lines_are_ignored(self) -> None:
        data = adapt_source_text("\n\n标题\n\n\n正文\n\n")
        self.assertEqual([item["text"] for item in data["paragraphs"]], ["标题", "正文"])

    def test_original_nonblank_text_is_not_stripped(self) -> None:
        original = "  中文ABC 001：50%．  "
        item = adapt_source_text(original)["paragraphs"][0]
        self.assertEqual(item["text"], original)
        self.assertEqual(item["analysis_text"], "中文ABC 001：50%．")

    def test_fullwidth_spaces_and_symbols_are_preserved(self) -> None:
        original = "　　　2.第二个附件（ABC-001）：100%"
        item = adapt_source_text(original)["paragraphs"][0]
        self.assertEqual(item["text"], original)
        self.assertEqual(item["analysis_text"], original)

    def test_canonical_ids_and_indexes_are_contiguous(self) -> None:
        paragraphs = adapt_source_text("甲\n\n乙") ["paragraphs"]
        self.assertEqual([item["id"] for item in paragraphs], ["p0001", "p0002"])
        self.assertEqual([item["index"] for item in paragraphs], [0, 1])

    def test_blank_only_input_is_invalid(self) -> None:
        with self.assertRaises(PipelineError) as context:
            adapt_source_text("\n \t\n")
        self.assertEqual(context.exception.code, "INVALID_INPUT")

    def test_non_string_input_is_invalid(self) -> None:
        with self.assertRaises(PipelineError) as context:
            adapt_source_text(None)  # type: ignore[arg-type]
        self.assertEqual(context.exception.code, "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
