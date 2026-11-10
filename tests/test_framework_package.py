"""패키지 분리 후 공개 API와 독립 import 계약."""

import importlib
import subprocess
import sys
import unittest
from pathlib import Path

import game_framework


class FrameworkPackageTests(unittest.TestCase):
    def test_public_exports_are_the_original_objects(self):
        exports = {
            'core': ('GameObject', 'GameMode', 'Level'),
            'transforms': ('WorldTransform', 'UITransform'),
            'ui': ('Canvas', 'UIElement'),
            'rendering': ('RenderItem', 'Renderer'),
            'drawing': ('draw_rect', 'draw_image'),
            'scene': ('LevelScene',),
        }
        self.assertEqual(set(game_framework.__all__),
                         {name for names in exports.values() for name in names})
        for module, names in exports.items():
            implementation = importlib.import_module(f'game_framework.{module}')
            for name in names:
                with self.subTest(name=name):
                    self.assertIs(getattr(game_framework, name), getattr(implementation, name))

    def test_submodules_import_in_fresh_processes(self):
        for module in ('core', 'transforms', 'ui', 'rendering', 'drawing', 'scene', '_validation'):
            with self.subTest(module=module):
                result = subprocess.run(
                    [sys.executable, '-c', f'import game_framework.{module}'],
                    cwd=Path(__file__).resolve().parents[1],
                    capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
