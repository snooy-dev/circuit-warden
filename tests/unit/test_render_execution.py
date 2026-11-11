"""렌더 실행의 안정 정렬과 오류 전달."""

import unittest

from engine.rendering.renderer import execute


class RenderExecutionTests(unittest.TestCase):
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
