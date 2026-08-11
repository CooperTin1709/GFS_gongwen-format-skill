from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

from scripts.classify import classify_document
from scripts.input_adapter import adapt_source_text
from scripts.render_docx import render_document
from scripts.validate import validate_document


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".tmp" / "tests"
SOURCE_TEXT = """关于进一步加强人工智能应用管理工作的通知


一、总体要求
近年来，人工智能技术快速发展，相关工作编号为AI-001，不得修改。

（一）主要任务
各单位应严格按照相关要求开展工作。
1. 加强组织管理
本项目2026年度测试编号为001。
（1）明确责任分工
相关单位应按要求完成工作，不得改变数字、中文标点及英文ABC。


附件：1.人工智能应用管理任务表
　　　2.相关工作说明"""


def build_output(folder: Path) -> tuple[dict[str, object], Path, dict[str, object]]:
    canonical = adapt_source_text(SOURCE_TEXT)
    classified, analysis = classify_document(canonical)
    if analysis["review_count"]:
        raise AssertionError(analysis["review_items"])
    output = folder / "formatted.docx"
    render_document(classified, output)
    result = validate_document(classified, output)
    return classified, output, result


class RenderValidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    def assert_validation_failed(
        self,
        classified: dict[str, object],
        output: Path,
        expected_check: str,
    ) -> None:
        result = validate_document(classified, output)
        self.assertEqual(result["status"], "VALIDATION_FAILED")
        self.assertFalse(result["validation_passed"])
        self.assertIn(expected_check, {error["check"] for error in result["errors"]})

    def test_render_reopen_and_strict_validation(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, result = build_output(Path(directory))
            self.assertEqual(result["status"], "SUCCESS", result["errors"])
            self.assertEqual(result["verified_against"], "browser_extracted_text")
            self.assertTrue(result["validation"]["text_identical"])
            self.assertEqual(result["validation"]["blank_after_title_count"], 1)
            self.assertEqual(result["validation"]["blank_before_attachment_count"], 1)

            expected = [item["text"] for item in classified["paragraphs"]]
            reopened = Document(output)
            actual = [paragraph.text for paragraph in reopened.paragraphs if paragraph.text != ""]
            self.assertEqual(actual, expected)

            formats = result["validation"]["observed_formats"]
            for attribute in ("eastAsia", "ascii", "hAnsi", "cs"):
                self.assertEqual(formats["title"][attribute], ["方正小标宋简体"])
                self.assertEqual(formats["heading_1"][attribute], ["黑体"])
                self.assertEqual(formats["heading_2"][attribute], ["楷体_GB2312"])
                self.assertEqual(formats["heading_3"][attribute], ["仿宋_GB2312"])
                self.assertEqual(formats["heading_4"][attribute], ["仿宋_GB2312"])
                self.assertEqual(formats["body"][attribute], ["仿宋_GB2312"])
                self.assertEqual(formats["attachment"][attribute], ["仿宋_GB2312"])
            self.assertEqual(formats["title"]["size_pt"], [22.0])
            self.assertEqual(formats["title"]["alignment"], ["CENTER"])
            for paragraph_type in (
                "heading_1",
                "heading_2",
                "heading_3",
                "heading_4",
                "body",
                "attachment",
            ):
                self.assertEqual(formats[paragraph_type]["size_pt"], [16.0])
                self.assertEqual(formats[paragraph_type]["line_spacing_pt"], [30.0])

    def test_validator_rejects_text_change(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, _ = build_output(Path(directory))
            document = Document(output)
            document.paragraphs[3].runs[0].text += "篡改"
            document.save(output)
            self.assert_validation_failed(classified, output, "text_integrity")

    def test_validator_rejects_wrong_title_font(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, _ = build_output(Path(directory))
            document = Document(output)
            fonts = document.paragraphs[0].runs[0]._element.get_or_add_rPr().get_or_add_rFonts()
            for attribute in ("eastAsia", "ascii", "hAnsi", "cs"):
                fonts.set(qn(f"w:{attribute}"), "宋体")
            document.save(output)
            self.assert_validation_failed(classified, output, "font_eastAsia")

    def test_validator_rejects_multiple_line_spacing(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, _ = build_output(Path(directory))
            document = Document(output)
            document.paragraphs[3].paragraph_format.line_spacing = 1.5
            document.save(output)
            self.assert_validation_failed(classified, output, "line_spacing")

    def test_validator_rejects_deleted_required_blank(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, _ = build_output(Path(directory))
            document = Document(output)
            blank = document.paragraphs[1]._element
            blank.getparent().remove(blank)
            document.save(output)
            self.assert_validation_failed(classified, output, "blank_after_title")

    def test_validator_rejects_extra_blank(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, _ = build_output(Path(directory))
            document = Document(output)
            first_blank = document.paragraphs[1]._element
            first_blank.addnext(copy.deepcopy(first_blank))
            document.save(output)
            self.assert_validation_failed(classified, output, "blank_after_title")

    def test_validator_rejects_wrong_heading_2_size(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            classified, output, _ = build_output(Path(directory))
            document = Document(output)
            document.paragraphs[4].runs[0].font.size = Pt(15)
            document.save(output)
            self.assert_validation_failed(classified, output, "font_size")


if __name__ == "__main__":
    unittest.main()
