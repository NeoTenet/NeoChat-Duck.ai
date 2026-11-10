"""Regression tests for the lean portable Windows build layout."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowsBuildLayoutTests(unittest.TestCase):
    def test_spec_uses_onedir_not_onefile(self):
        spec = (ROOT / "NeoAITerminal.spec").read_text(encoding="utf-8")
        self.assertIn("exclude_binaries=True", spec)
        self.assertIn("COLLECT(", spec)
        self.assertNotIn("node_modules.rglob", spec)
        self.assertNotIn("collect_all", spec)

    def test_build_script_places_node_outside_exe(self):
        script = (ROOT / "build_windows_exe.bat").read_text(encoding="utf-8")
        self.assertIn('"%APP_DIR%\\node\\node.exe"', script)
        self.assertIn('"%APP_DIR%\\node_modules"', script)
        self.assertIn("NeoAI-Terminal-Portable-Windows.zip", script)

    def test_duck_client_resolves_adjacent_node_runtime_and_modules(self):
        code = (ROOT / "duck_cli.py").read_text(encoding="utf-8")
        self.assertIn('os.path.join(APP_DIR, "node", "node.exe")', code)
        self.assertIn('os.path.join(APP_DIR, "node_modules")', code)
        self.assertIn('node_env["NODE_PATH"]', code)

    def test_font_assets_are_loaded_from_portable_app_folder(self):
        code = (ROOT / "web_app.py").read_text(encoding="utf-8")
        self.assertIn('VAZIR_DIR = APP_DIR / "node_modules" / "vazir-font" / "dist"', code)

    def test_windows_build_uses_lean_requirements(self):
        reqs = (ROOT / "requirements-windows-exe.txt").read_text(encoding="utf-8")
        self.assertIn("uvicorn", reqs)
        self.assertNotIn("uvicorn[standard]", reqs)
        self.assertNotIn("keyring", reqs)


if __name__ == "__main__":
    unittest.main()
