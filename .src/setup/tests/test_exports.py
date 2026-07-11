import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ExportTests(unittest.TestCase):
    def run_export(self, slug, directory):
        script = ROOT / f"umbrel-arr-{slug}" / "exports.sh"
        command = f'. "{script}"; env | sort'
        return subprocess.run(
            ["sh", "-c", command],
            env={**os.environ, "EXPORTS_APP_DATA_DIR": str(directory)},
            text=True,
            capture_output=True,
            check=True,
        ).stdout

    def test_generated_api_key_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            first = self.run_export("sonarr", directory)
            second = self.run_export("sonarr", directory)
            self.assertEqual(first, second)
            key = (Path(directory) / ".api-key").read_text().strip()
            self.assertEqual(len(key), 32)
            self.assertIn(f"UMBREL_ARR_SONARR_API_KEY={key}", first)

    def test_overseerr_preseeds_its_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.run_export("overseerr", directory)
            key = (Path(directory) / ".api-key").read_text().strip()
            settings = (Path(directory) / "data/config/settings.json").read_text()
            self.assertIn(key, settings)
            self.assertIn("UMBREL_ARR_OVERSEERR_URL=http://umbrel-arr-overseerr_server_1:5055", output)

    def test_bazarr_preseeds_its_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_export("bazarr", directory)
            key = (Path(directory) / ".api-key").read_text().strip()
            config = (Path(directory) / "data/config/config.yaml").read_text()
            self.assertIn(f"apikey: {key}", config)


if __name__ == "__main__":
    unittest.main()
