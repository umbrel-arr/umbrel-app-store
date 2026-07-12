import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".src" / "privado-proxy" / "scripts" / "dashboard.py"
SPEC = importlib.util.spec_from_file_location("privado_dashboard", MODULE_PATH)
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


class PrivadoDashboardTests(unittest.TestCase):
    def test_credentials_configured_reads_persisted_login(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "privado.env"
            config_file.write_text(
                "PRIVADO_USERNAME='user name'\nPRIVADO_PASSWORD='secret value'\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "CONFIG_FILE": str(config_file),
                    "PRIVADO_USERNAME": "",
                    "PRIVADO_PASSWORD": "",
                },
                clear=False,
            ):
                self.assertTrue(dashboard.credentials_configured())

    def test_credentials_configured_requires_both_values(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "privado.env"
            config_file.write_text("PRIVADO_USERNAME=user\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "CONFIG_FILE": str(config_file),
                    "PRIVADO_USERNAME": "",
                    "PRIVADO_PASSWORD": "",
                },
                clear=False,
            ):
                self.assertFalse(dashboard.credentials_configured())

    def test_restart_starts_an_exited_main_process(self):
        with patch.object(dashboard, "supervisor_state", return_value="exited"), patch.object(
            dashboard, "run", return_value=("main: started", "", 0)
        ) as run:
            self.assertTrue(dashboard.restart_main())
            run.assert_called_once_with(["supervisorctl", "start", "main"], timeout=30)

    def test_restart_reports_supervisor_failure(self):
        with patch.object(dashboard, "supervisor_state", return_value="running"), patch.object(
            dashboard, "run", return_value=("", "main: ERROR", 1)
        ) as run:
            self.assertFalse(dashboard.restart_main())
            run.assert_called_once_with(["supervisorctl", "restart", "main"], timeout=30)


if __name__ == "__main__":
    unittest.main()
