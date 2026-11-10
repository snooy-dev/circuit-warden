"""엔진의 게임 독립성과 중립 렌더 실행 계약."""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

import engine
from engine.loop import Engine
from engine.scene import Scene
from engine.rendering.renderer import execute


class EnginePackageTests(unittest.TestCase):
    def test_public_imports_and_engine_only_dependency_direction(self):
        self.assertIs(engine.Engine, Engine)
        self.assertIs(engine.Scene, Scene)
        root = Path(__file__).resolve().parents[2]
        for path in (root / 'engine').rglob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                names = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                         [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
                self.assertFalse(any(name.split('.')[0] in ('game_framework', 'demos')
                                     for name in names), path)
        result = subprocess.run(
            [sys.executable, '-c',
             "import sys; import engine.rendering.drawing; import engine.rendering.renderer; "
             "assert not any(n == 'game_framework' or n.startswith('game_framework.') for n in sys.modules)"],
            cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_neutral_execution_is_stable_and_propagates_failure(self):
        items = [(2, 'back'), (1, 'first'), (1, 'second')]
        drawn = []
        execute(items, drawn.append, key=lambda item: item[0])
        self.assertEqual(drawn, [(1, 'first'), (1, 'second'), (2, 'back')])
        self.assertEqual(items, drawn)
        drawn.clear()
        execute(items, drawn.append)
        self.assertEqual(items, drawn)
        def fail(item):
            raise ValueError('draw')
        with self.assertRaisesRegex(ValueError, 'draw'):
            execute(items, fail)
