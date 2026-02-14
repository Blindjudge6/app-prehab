import ast
import re
import unittest
from pathlib import Path


UI_METHODS = {
    "title",
    "subheader",
    "header",
    "caption",
    "write",
    "error",
    "success",
    "warning",
    "info",
    "button",
    "form_submit_button",
    "slider",
}


def _extract_ui_texts(source: str) -> list[str]:
    tree = ast.parse(source)
    results = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in UI_METHODS:
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
            continue

        text = first.value.strip()
        if not text:
            continue
        if "<style>" in text or "<div" in text:
            continue

        results.append(text)

    return results


class TestUiCopyReadability(unittest.TestCase):
    def test_ui_copy_is_readable(self):
        source = Path("app.py").read_text(encoding="utf-8-sig")
        texts = _extract_ui_texts(source)

        self.assertGreater(len(texts), 10)

        for text in texts:
            words = re.findall(r"[A-Za-zÄÖÜäöüß0-9\-]+", text)
            self.assertLessEqual(len(text), 120, msg=f"UI-Text zu lang: {text}")
            self.assertLessEqual(len(words), 22, msg=f"Zu viele Wörter im UI-Text: {text}")


if __name__ == "__main__":
    unittest.main()
