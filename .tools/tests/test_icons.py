import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / ".tools" / "generate-icons.py"
SPEC = importlib.util.spec_from_file_location("icon_generator", GENERATOR_PATH)
icon_generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(icon_generator)


class IconTests(unittest.TestCase):
    def test_every_package_has_a_generated_icon(self):
        expected = set(icon_generator.expected_icons())
        packages = {
            path.name.removeprefix("umbrel-arr-")
            for path in ROOT.glob("umbrel-arr-*")
            if path.is_dir()
        }
        self.assertEqual(expected, packages)

    def test_icons_are_square_with_an_opaque_canvas(self):
        for name, content in icon_generator.expected_icons().items():
            with self.subTest(icon=name):
                root = ET.fromstring(content)
                self.assertEqual(root.attrib.get("viewBox"), "0 0 256 256")
                self.assertTrue(
                    '<rect width="256" height="256"' in content
                    or 'd="M256 0H0V256H256V0Z"' in content,
                    f"{name} has no full-canvas background",
                )

    def test_4k_variants_are_visibly_distinct(self):
        icons = icon_generator.expected_icons()
        self.assertIn('aria-label="4K edition"', icons["radarr-4k"])
        self.assertIn('aria-label="4K edition"', icons["sonarr-4k"])
        self.assertNotEqual(icons["radarr"], icons["radarr-4k"])
        self.assertNotEqual(icons["sonarr"], icons["sonarr-4k"])


if __name__ == "__main__":
    unittest.main()
