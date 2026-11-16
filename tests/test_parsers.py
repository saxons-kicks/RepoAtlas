import json
import tempfile
import unittest
from pathlib import Path

from repoatlas.parsers import load_bookmarks


class ParserTests(unittest.TestCase):
    def test_nested_netscape_html_paths(self):
        source = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
        <DL><p><DT><H3>Barra de favoritos</H3><DL><p>
        <DT><H3>Tecnologia</H3><DL><p>
        <DT><H3>QA &amp; Testes</H3><DL><p>
        <DT><A HREF="https://github.com/example/tool" ADD_DATE="123">Example Tool</A>
        </DL><p></DL><p></DL><p></DL><p>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.html"
            path.write_text(source, encoding="utf-8")
            items = load_bookmarks(path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].folder_path, ["Tecnologia", "QA & Testes"])
        self.assertEqual(items[0].title, "Example Tool")

    def test_repoatlas_json(self):
        source = {"bookmarks": [{"title": "Work repo", "url": "https://github.com/acme/app", "organized_path": ["Trabalho", "Projetos"]}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            items = load_bookmarks(path)
        self.assertTrue(items[0].private_context)


    def test_frameworks_folder_is_not_mistaken_for_private_work_context(self):
        source = {
            "bookmarks": [{
                "title": "Frameworks & Agents",
                "url": "https://github.com/example/frameworks",
                "organized_path": ["Tecnologia", "Frameworks & Agentes"],
            }]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            items = load_bookmarks(path)
        self.assertFalse(items[0].private_context)

    def test_work_folder_is_marked_private_as_a_whole_word(self):
        source = {
            "bookmarks": [{
                "title": "Work repository",
                "url": "https://github.com/example/work-repo",
                "organized_path": ["My Work", "Projects"],
            }]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            items = load_bookmarks(path)
        self.assertTrue(items[0].private_context)


if __name__ == "__main__":
    unittest.main()
