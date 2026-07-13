import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_SLUGS = (
    "prowlarr",
    "sabnzbd",
    "sonarr",
    "sonarr-4k",
    "radarr",
    "radarr-4k",
    "bazarr",
    "overseerr",
    "lidarr",
)
SERVICE_SLUGS = (
    "privado-vpn",
    "flaresolverr",
    "prowlarr",
    "qbittorrent",
    "sabnzbd",
    "sonarr",
    "sonarr-4k",
    "radarr",
    "radarr-4k",
    "bazarr",
    "overseerr",
    "profilarr",
    "lidarr",
)


class ExportTests(unittest.TestCase):
    def run_export(self, slug, directory, *, app_password=""):
        script = ROOT / f"umbrel-arr-{slug}" / "exports.sh"
        command = f'. "{script}"; env | sort'
        return subprocess.run(
            ["sh", "-c", command],
            env={
                **os.environ,
                "APP_PASSWORD": app_password,
                "EXPORTS_APP_DATA_DIR": str(directory),
            },
            text=True,
            capture_output=True,
            check=True,
        ).stdout

    def test_exports_are_read_only_for_every_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for slug in SERVICE_SLUGS:
                app_data = root / slug
                self.run_export(slug, app_data, app_password="umbrel-password")
                self.assertFalse(app_data.exists(), f"{slug} export modified its app data")

    def test_config_exports_point_to_owning_app_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for slug in CONFIG_SLUGS:
                output = self.run_export(slug, root / slug)
                var = slug.upper().replace("-", "_")
                self.assertIn(
                    f"UMBREL_ARR_{var}_CONFIG_DIR={root / slug}/config",
                    output,
                )
                self.assertNotIn(f"UMBREL_ARR_{var}_API_KEY=", output)

    def test_qbittorrent_exports_umbrel_deterministic_password(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = self.run_export(
                "qbittorrent",
                Path(temporary) / "qbittorrent",
                app_password="umbrel-deterministic-password",
            )
        self.assertIn(
            "UMBREL_ARR_QBITTORRENT_PASSWORD=umbrel-deterministic-password",
            output,
        )

    def test_generated_exports_contain_no_mutating_commands(self):
        forbidden = (
            "mkdir",
            "touch",
            "chmod",
            "chown",
            "openssl",
            "sed -i",
            "tee ",
            "printf ",
            "> $",
            '> "$',
        )
        for slug in SERVICE_SLUGS:
            content = (ROOT / f"umbrel-arr-{slug}" / "exports.sh").read_text()
            for token in forbidden:
                self.assertNotIn(token, content, f"{slug} export contains {token!r}")
            for line in content.splitlines():
                self.assertRegex(line, r'^export UMBREL_ARR_[A-Z0-9_]+="[^`]*"$')
                self.assertNotIn("$(", line)


class StatelessPackagingTests(unittest.TestCase):
    def test_umbrelarr_is_read_only_and_mounts_only_dependency_configs(self):
        compose = (ROOT / "umbrel-arr-umbrelarr" / "docker-compose.yml").read_text()
        self.assertIn("read_only: true", compose)
        self.assertNotIn("STATE_DIR", compose)
        self.assertNotIn("${APP_DATA_DIR}", compose)
        self.assertNotIn("/data", compose)
        self.assertNotIn("docker.sock", compose)
        self.assertNotIn("_API_KEY:", compose)
        for slug in CONFIG_SLUGS:
            var = slug.upper().replace("-", "_")
            self.assertIn(
                f"${{UMBREL_ARR_{var}_CONFIG_DIR}}:/managed-config/{slug}:ro",
                compose,
            )
            self.assertNotIn(f"UMBREL_ARR_{var}_CONFIG_DIR:-", compose)

    def test_umbrelarr_never_invokes_dependency_export_scripts(self):
        package = ROOT / "umbrel-arr-umbrelarr"
        self.assertFalse((package / "exports.sh").exists())
        for path in (package / "docker-compose.yml", ROOT / ".tools" / "generate-packages.py"):
            content = path.read_text()
            self.assertNotIn("/exports.sh", content)
            self.assertNotIn("source exports.sh", content)
            self.assertNotIn(". exports.sh", content)

    def test_umbrelarr_requires_all_thirteen_user_installed_apps(self):
        manifest = (ROOT / "umbrel-arr-umbrelarr" / "umbrel-app.yml").read_text()
        dependencies = [
            line.removeprefix("  - ")
            for line in manifest.splitlines()
            if line.startswith("  - umbrel-arr-")
        ]
        self.assertEqual(dependencies, [f"umbrel-arr-{slug}" for slug in SERVICE_SLUGS])
        self.assertNotIn("permissions:", manifest)

    def test_qbittorrent_enables_deterministic_password(self):
        manifest = (ROOT / "umbrel-arr-qbittorrent" / "umbrel-app.yml").read_text()
        self.assertIn("deterministicPassword: true", manifest)

    def test_changed_dependency_revisions_have_current_release_notes(self):
        versions = {
            "prowlarr": "2.3.5.5327-umbrel.3",
            "qbittorrent": "5.2.4-umbrel.3",
            "sabnzbd": "5.0.4-umbrel.3",
            "sonarr": "4.0.17.2952-umbrel.3",
            "sonarr-4k": "4.0.17.2952-umbrel.3",
            "radarr": "6.1.1.10360-umbrel.3",
            "radarr-4k": "6.1.1.10360-umbrel.3",
            "bazarr": "1.6.0-umbrel.3",
            "overseerr": "1.35.0-umbrel.3",
            "lidarr": "3.1.0.4875-umbrel.3",
        }
        for slug, version in versions.items():
            manifest = (ROOT / f"umbrel-arr-{slug}" / "umbrel-app.yml").read_text()
            self.assertIn(f'version: "{version}"', manifest)
            release_notes = re.search(
                r"releaseNotes: >-\n  (.+)\n",
                manifest,
            ).group(1)
            self.assertNotIn("opaque app icon", release_notes)

    def test_umbrelarr_release_requires_all_handoff_revisions_first(self):
        manifest = (ROOT / "umbrel-arr-umbrelarr" / "umbrel-app.yml").read_text()
        self.assertIn("Before installing 1.1, update Prowlarr", manifest)
        self.assertIn("Lidarr to their .3 handoff revisions", manifest)
        readme = (ROOT / "README.md").read_text()
        required = {
            "Prowlarr": "2.3.5.5327-umbrel.3",
            "qBittorrent": "5.2.4-umbrel.3",
            "SABnzbd": "5.0.4-umbrel.3",
            "Sonarr": "4.0.17.2952-umbrel.3",
            "Sonarr 4K": "4.0.17.2952-umbrel.3",
            "Radarr": "6.1.1.10360-umbrel.3",
            "Radarr 4K": "6.1.1.10360-umbrel.3",
            "Bazarr": "1.6.0-umbrel.3",
            "Overseerr": "1.35.0-umbrel.3",
            "Lidarr": "3.1.0.4875-umbrel.3",
        }
        for name, version in required.items():
            self.assertIn(f"| {name} | `{version}` |", readme)
        self.assertIn(
            "Only after all ten updates are installed should umbrelarr be updated to 1.1.",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
