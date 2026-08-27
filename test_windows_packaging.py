from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class WindowsPackagingTest(unittest.TestCase):
    def test_windows_installer_workflow_template_builds_installer_exe_and_portable_zip(self):
        workflow = (ROOT / "packaging" / "build-windows-installer-workflow.yml").read_text(encoding="utf-8")

        self.assertIn("windows-latest", workflow)
        self.assertIn("packaging\\build_windows_exe.ps1", workflow)
        self.assertIn("packaging\\build_windows_installer.ps1", workflow)
        self.assertIn("小红书笔记截图工具_Windows安装包.exe", workflow)
        self.assertIn("小红书笔记截图工具_Windows便携版.zip", workflow)

    def test_existing_windows_workflow_still_builds_portable_exe_zip(self):
        workflow = (ROOT / ".github" / "workflows" / "build-windows-exe.yml").read_text(encoding="utf-8")

        self.assertIn("windows-latest", workflow)
        self.assertIn("packaging\\build_windows_exe.ps1", workflow)
        self.assertIn("小红书笔记截图工具_Windows版.zip", workflow)

    def test_windows_installer_script_uses_built_exe_folder(self):
        script = (ROOT / "packaging" / "build_windows_installer.ps1").read_text(encoding="utf-8")

        self.assertIn("iscc", script.lower())
        self.assertIn('Join-Path $ProjectDir "dist\\$Name"', script)
        self.assertIn('${Name}_Windows安装包', script)


if __name__ == "__main__":
    unittest.main()
