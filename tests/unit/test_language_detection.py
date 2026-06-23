"""Tests for language detection and stall detection."""

import pytest

from semar.agents.judge_agent import JudgeAgent


@pytest.fixture
def judge():
    return JudgeAgent()


def test_detect_python(judge):
    diff = "+import os\n+def main():\n+    pass"
    langs = judge._detect_languages(diff, {})
    assert "python" in langs


def test_detect_javascript(judge):
    diff = "+const x = 1;\n+function hello() {}"
    langs = judge._detect_languages(diff, {})
    assert "javascript" in langs


def test_detect_typescript(judge):
    diff = "+const x: number = 1;\n+function hello(): void {}"
    langs = judge._detect_languages(diff, {})
    assert "typescript" in langs


def test_detect_go(judge):
    diff = '+package main\n+import "fmt"\n+func main() {}'
    langs = judge._detect_languages(diff, {})
    assert "go" in langs


def test_detect_java(judge):
    diff = "+public class Main {\n+    public static void main(String[] args) {}"
    langs = judge._detect_languages(diff, {})
    assert "java" in langs


def test_detect_rust(judge):
    diff = '+fn main() {\n+    println!("hello");\n+}'
    langs = judge._detect_languages(diff, {})
    assert "rust" in langs


def test_detect_cpp(judge):
    diff = "+#include <iostream>\n+int main() {\n+    return 0;\n+}"
    langs = judge._detect_languages(diff, {})
    assert "cpp" in langs


def test_detect_multiple_languages(judge):
    diff = """
+import os
+const x = 1;
+fn main() {}
+package main
"""
    langs = judge._detect_languages(diff, {})
    assert len(langs) >= 2


def test_detect_uses_metadata_files(judge):
    diff = ""
    metadata = {"files": ["app.py", "utils.py"]}
    langs = judge._detect_languages(diff, metadata)
    assert "python" in langs


def test_detect_empty_diff(judge):
    langs = judge._detect_languages("", {})
    assert isinstance(langs, list)


def test_stall_detection(judge):
    assert hasattr(judge, "_check_stall")
    result = judge._check_stall({"improvement": 0.0, "accuracy": 0.5})
    assert isinstance(result, bool)


def test_stall_detection_no_stall(judge):
    result = judge._check_stall({"improvement": 0.1, "accuracy": 0.6})
    assert result is False
