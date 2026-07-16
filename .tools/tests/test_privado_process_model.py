import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PrivadoProcessModelTests(unittest.TestCase):
    def test_image_installs_tls_certificate_authorities(self):
        dockerfile = (ROOT / ".src" / "privado-proxy" / "Dockerfile").read_text()
        self.assertRegex(dockerfile, r"apt-get install[^\n]*\\\n(?:.*\\\n)*?\s+ca-certificates\b")

    def test_package_pins_fixed_multiarch_image(self):
        manifest = (ROOT / "umbrel-arr-privado-vpn" / "umbrel-app.yml").read_text()
        compose = (ROOT / "umbrel-arr-privado-vpn" / "docker-compose.yml").read_text()
        self.assertIn('version: "1.2.8"', manifest)
        self.assertIn("Recovers stale WireGuard routes", manifest)
        self.assertRegex(
            compose,
            r"image: ghcr\.io/umbrel-arr/privado-proxy:1\.2\.7@sha256:938168855e47c046053b95d479e696affa6b86e928dcc91c9ef95a83cbcc319e",
        )

    def test_supervisor_owns_the_dashboard_without_nested_rpc(self):
        dashboard = (
            ROOT / ".src" / "privado-proxy" / "etc" / "supervisor" / "conf.d" / "dashboard.conf"
        ).read_text()
        main = (ROOT / ".src" / "privado-proxy" / "scripts" / "main.sh").read_text()
        self.assertIn("autostart=true", dashboard)
        self.assertNotIn("supervisorctl", main)

    def test_main_execs_socks_only_after_wireguard_setup(self):
        main = (ROOT / ".src" / "privado-proxy" / "scripts" / "main.sh").read_text()
        proxy = (ROOT / ".src" / "privado-proxy" / "scripts" / "dante.sh").read_text()
        self.assertNotIn("supervisorctl", proxy)
        self.assertIn('exec /usr/bin/microsocks -i 0.0.0.0 -p "${SOCK_PORT}"', proxy)
        self.assertLess(main.index("check_connection"), main.index("start_dante"))
        self.assertFalse(
            (ROOT / ".src" / "privado-proxy" / "etc" / "supervisor" / "conf.d" / "proxy.conf").exists()
        )


if __name__ == "__main__":
    unittest.main()
