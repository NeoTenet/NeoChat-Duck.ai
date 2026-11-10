"""Regression checks for the download-on-first-run portable launcher."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LightweightPortableTests(unittest.TestCase):
    def test_launcher_uses_embedded_python_and_sha256_verification(self):
        code = (ROOT / "neo_portable_launcher.cs").read_text(encoding="utf-8")
        self.assertIn("python-3.13.17-embeddable-amd64.zip", code)
        self.assertIn("PythonSha256", code)
        self.assertIn("SHA256.Create()", code)
        self.assertIn("ConfigureEmbeddedPython", code)
        self.assertNotIn("EnsurePythonPackages", code)
        self.assertIn('updated.Add("import site")', code)

    def test_launcher_discovers_official_node_lts_and_checksum(self):
        code = (ROOT / "neo_portable_launcher.cs").read_text(encoding="utf-8")
        self.assertIn("https://nodejs.org/dist/index.json", code)
        self.assertIn("SHASUMS256.txt", code)
        self.assertIn('record["lts"] is string', code)
        self.assertIn("DownloadFile(baseUrl + fileName, archive, expectedHash", code)
        self.assertNotIn("baseUrl + \"win-x64/\" + fileName", code)

    def test_launcher_installs_python_and_npm_dependencies_once(self):
        code = (ROOT / "neo_portable_launcher.cs").read_text(encoding="utf-8")
        self.assertIn("requirements-portable.txt", code)
        self.assertIn("npm-cli.js", code)
        self.assertIn("jsdom", code)
        self.assertIn("vazir-font", code)
        self.assertIn("node-packages.sha256", code)

    def test_duck_engine_uses_downloaded_runtime_node_path(self):
        code = (ROOT / "duck_cli.py").read_text(encoding="utf-8")
        self.assertIn('os.path.join(APP_DIR, "runtime", "node", "node.exe")', code)
        self.assertIn('os.path.join(APP_DIR, "runtime", "node", "node_modules")', code)

    def test_build_package_excludes_generated_test_images(self):
        script = (ROOT / "build_lightweight_portable.bat").read_text(encoding="utf-8")
        self.assertIn('mkdir "%APP_DIR%\\generated"', script)
        self.assertNotIn('robocopy "generated"', script)

    def test_build_script_does_not_require_python_or_node_on_builder(self):
        script = (ROOT / "build_lightweight_portable.bat").read_text(encoding="utf-8")
        self.assertIn("neo_portable_launcher.cs", script)
        self.assertIn("NeoAI-Terminal-Lightweight-Portable-Windows.zip", script)
        self.assertNotIn("where python", script.lower())
        self.assertNotIn("where node", script.lower())

    def test_requirements_are_lean_and_do_not_include_build_tools(self):
        reqs = (ROOT / "requirements-portable.txt").read_text(encoding="utf-8").lower()
        self.assertIn("fastapi", reqs)
        self.assertIn("uvicorn", reqs)
        self.assertIn("pillow", reqs)
        self.assertNotIn("pyinstaller", reqs)
        self.assertNotIn("keyring", reqs)

    def test_bootstrap_window_uses_persian_rtl_copy(self):
        code = (ROOT / "neo_portable_launcher.cs").read_text(encoding="utf-8")
        self.assertIn("RightToLeft = RightToLeft.Yes", code)
        self.assertIn("در حال نصب وابستگی‌های Python", code)
        self.assertIn("تلاش دوباره", code)

    def test_server_is_detached_and_logs_survive_launcher_exit(self):
        code = (ROOT / "neo_portable_launcher.cs").read_text(encoding="utf-8")
        self.assertIn("Start-Process -FilePath", code)
        self.assertIn("-RedirectStandardOutput", code)
        self.assertIn("-RedirectStandardError", code)
        self.assertIn("server.stderr.log", code)

    def test_launcher_suppresses_duplicate_browser_open(self):
        code = (ROOT / "neo_launcher.py").read_text(encoding="utf-8")
        self.assertIn('NEO_SKIP_AUTO_OPEN', code)


if __name__ == "__main__":
    unittest.main()
