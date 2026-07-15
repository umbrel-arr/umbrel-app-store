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

    def run_umbrelarr_export(
        self, directory, *, derived_password="derived-password", legacy_password=""
    ):
        script = ROOT / "umbrel-arr-umbrelarr" / "exports.sh"
        command = (
            "derive_entropy() { "
            'case "$1" in '
            '"app-umbrel-arr-qbittorrent-seed-APP_PASSWORD") printf %s "$DERIVED_PASSWORD" ;; '
            '"app-umbrel-arr-umbrelarr-seed-APP_PASSWORD") printf %s "$LEGACY_PASSWORD" ;; '
            "*) return 1 ;; "
            "esac; }; "
            f'. "{script}"; env | sort'
        )
        return subprocess.run(
            ["sh", "-c", command],
            env={
                **os.environ,
                "APP_PASSWORD": "wrong-context-password",
                "DERIVED_PASSWORD": derived_password,
                "LEGACY_PASSWORD": legacy_password,
                "EXPORTS_APP_DIR": str(directory),
                "EXPORTS_APP_DATA_DIR": str(directory / "data"),
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

    def test_umbrelarr_discovers_only_existing_optional_config_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            app_root = Path(temporary) / "app-data"
            manager = app_root / "umbrel-arr-umbrelarr"
            selected = ("prowlarr", "sonarr", "radarr-4k")
            for slug in selected:
                (app_root / f"umbrel-arr-{slug}" / "data" / "config").mkdir(parents=True)
            before = sorted(path.relative_to(app_root) for path in app_root.rglob("*"))

            output = self.run_umbrelarr_export(manager)

            after = sorted(path.relative_to(app_root) for path in app_root.rglob("*"))
            self.assertEqual(after, before)
            for slug in selected:
                var = slug.upper().replace("-", "_")
                expected = app_root / f"umbrel-arr-{slug}" / "data" / "config"
                self.assertIn(f"UMBREL_ARR_{var}_CONFIG_DIR={expected}", output)
            self.assertNotIn("UMBREL_ARR_SABNZBD_CONFIG_DIR=", output)

    def test_umbrelarr_derives_qbittorrent_password_only_when_installed(self):
        with tempfile.TemporaryDirectory() as temporary:
            app_root = Path(temporary) / "app-data"
            manager = app_root / "umbrel-arr-umbrelarr"
            without_qbittorrent = self.run_umbrelarr_export(manager)
            (app_root / "umbrel-arr-qbittorrent").mkdir(parents=True)
            with_qbittorrent = self.run_umbrelarr_export(
                manager,
                derived_password="fixture-qbittorrent-password",
                legacy_password="fixture-manager-password",
            )
        self.assertNotIn("UMBREL_ARR_QBITTORRENT_PASSWORD=", without_qbittorrent)
        self.assertNotIn("UMBREL_ARR_QBITTORRENT_LEGACY_PASSWORD=", without_qbittorrent)
        self.assertIn(
            "UMBREL_ARR_QBITTORRENT_PASSWORD=fixture-qbittorrent-password",
            with_qbittorrent,
        )
        self.assertIn(
            "UMBREL_ARR_QBITTORRENT_LEGACY_PASSWORD=fixture-manager-password",
            with_qbittorrent,
        )


class StatelessPackagingTests(unittest.TestCase):
    def test_umbrelarr_is_read_only_and_mounts_optional_installed_configs(self):
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
                f"${{UMBREL_ARR_{var}_CONFIG_DIR:-/dev/null}}:/managed-config/{slug}:ro",
                compose,
            )
        self.assertIn("UMBREL_ARR_SOCKS5_HOST: ${UMBREL_ARR_SOCKS5_HOST:-}", compose)

    def test_umbrelarr_uses_its_own_read_only_discovery_export(self):
        package = ROOT / "umbrel-arr-umbrelarr"
        export = package / "exports.sh"
        self.assertTrue(export.exists())
        content = export.read_text()
        self.assertIn('umbrel_arr_apps_root="${EXPORTS_APP_DIR%/*}"', content)
        self.assertNotIn("mkdir", content)
        self.assertNotIn("touch", content)
        for path in (package / "docker-compose.yml", ROOT / ".tools" / "generate-packages.py"):
            content = path.read_text()
            self.assertNotIn("/exports.sh", content)
            self.assertNotIn("source exports.sh", content)
            self.assertNotIn(". exports.sh", content)

    def test_umbrelarr_requires_only_the_prowlarr_core_dependency(self):
        manifest = (ROOT / "umbrel-arr-umbrelarr" / "umbrel-app.yml").read_text()
        dependencies = [
            line.removeprefix("  - ")
            for line in manifest.splitlines()
            if line.startswith("  - umbrel-arr-")
        ]
        self.assertEqual(dependencies, ["umbrel-arr-prowlarr"])
        self.assertNotIn("dependencies: []", manifest)
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

    def test_umbrelarr_release_describes_modular_installation(self):
        manifest = (ROOT / "umbrel-arr-umbrelarr" / "umbrel-app.yml").read_text()
        compose = (ROOT / "umbrel-arr-umbrelarr" / "docker-compose.yml").read_text()
        self.assertIn('version: "1.2.5"', manifest)
        self.assertIn("Reports Privado's selected VPN server", manifest)
        self.assertIn("healthy routing status accurate", manifest)
        self.assertRegex(
            compose,
            r"image: ghcr\.io/umbrel-arr/umbrelarr:1\.2\.5@sha256:[0-9a-f]{64}",
        )
        readme = (ROOT / "README.md").read_text()
        self.assertIn("never forced as dependencies", readme)
        self.assertIn("/dev/null", readme)


if __name__ == "__main__":
    unittest.main()
