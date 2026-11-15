"""고정 클릭 시나리오의 전하 효과 바이트와 CPU 비용을 변경 전후 비교한다."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from statistics import median, quantiles
from time import perf_counter_ns
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pico2d.pico2d as pico

from game import charge, scene, teleport_link


TARGETS = (2, 4, 1, 0, 1, 4, 2, 3, 2, 4, 1, 0, 1, 4)
FRAME_COUNT = 180


def baseline_art(revision):
    commit = subprocess.check_output(
        ['git', 'rev-parse', '--verify', '--end-of-options', f'{revision}^{{commit}}'],
        cwd=ROOT, encoding='ascii').strip()
    source = subprocess.check_output(['git', 'show', f'{commit}:game/charge.py'], cwd=ROOT)
    namespace = {'__file__': charge.__file__}
    exec(compile(source, f'{commit}:game/charge.py', 'exec'), namespace)
    return namespace['ChargeArt']


def run_scenario(art_class):
    width, height = scene.DEFAULT_SIZE
    surface = pico.SDL_CreateRGBSurfaceWithFormat(0, width, height, 32, pico.SDL_PIXELFORMAT_RGBA32)
    if not surface:
        raise RuntimeError(pico.SDL_GetError())
    renderer = None
    try:
        renderer = pico.SDL_CreateSoftwareRenderer(surface)
        if not renderer:
            raise RuntimeError(pico.SDL_GetError())
        return run_frames(art_class, renderer, width, height)
    finally:
        if renderer:
            pico.SDL_DestroyRenderer(renderer)
        pico.SDL_FreeSurface(surface)


def run_frames(art_class, renderer, width, height):
    app = SimpleNamespace(viewport=(0, 0, width, height), output_valid=True, reset_generation=0,
                          event_to_output=lambda event: (event.x, event.y))
    pixels_ns = 0

    def time_pixels(function):
        def measured(*args):
            nonlocal pixels_ns
            started = perf_counter_ns()
            result = function(*args)
            pixels_ns += perf_counter_ns() - started
            return result
        return measured

    with (patch.object(pico, 'renderer', renderer, create=True),
          patch.object(pico, 'window', None, create=True),
          patch.object(pico, 'canvas_height', height, create=True),
          patch.object(pico, 'SDL_SetWindowTitle'),
          patch.object(scene, 'ChargeArt', art_class),
          patch.object(art_class, 'frame', time_pixels(art_class.frame)),
          patch.object(teleport_link, 'render_link_frame',
                       time_pixels(teleport_link.render_link_frame))):
        level_scene = scene.CharacterScene()
        try:
            level_scene.enter(app)
            clicks = dict(zip(range(18, FRAME_COUNT, 12), TARGETS, strict=True))
            times = []
            teleports = 0
            for index in range(FRAME_COUNT):
                if index in clicks:
                    target = level_scene.level.charges[clicks[index]]
                    x, y = level_scene.transform.point(*target.position)
                    level_scene.handle_event(SimpleNamespace(type=pico.SDL_MOUSEBUTTONDOWN,
                                                            button=pico.SDL_BUTTON_LEFT,
                                                            x=round(x), y=round(y)))
                    teleports += level_scene.level.mode.teleport_link is not None
                pico.SDL_RenderClear(renderer)
                pixels_ns = 0
                started = perf_counter_ns()
                level_scene.update(1 / 60)
                level_scene.draw()
                pico.SDL_RenderPresent(renderer)
                times.append((pixels_ns / 1e6, (perf_counter_ns() - started) / 1e6))
            return times, teleports
        finally:
            level_scene.exit()


def upload_digest(art_class):
    digest = hashlib.sha256()
    uploads = 0
    update = pico.SDL_UpdateTexture

    def capture(texture, rect, rgba, pitch):
        nonlocal uploads
        digest.update(rgba)
        uploads += 1
        return update(texture, rect, rgba, pitch)

    with patch.object(pico, 'SDL_UpdateTexture', capture):
        _, teleports = run_scenario(art_class)
    return digest.hexdigest(), uploads, teleports


def report(label, runs):
    print(label)
    for title, values in zip(('픽셀 CPU', 'update+draw+software present'), zip(*runs)):
        p95 = median(quantiles(samples, n=20, method='inclusive')[18] for samples in values)
        max_ms = max(map(max, values))
        over = sum(value > 1000 / 60 for samples in values for value in samples)
        print(f'  {title} p95(실행별 중앙값)={p95:.3f}ms, 최대={max_ms:.3f}ms, 16.67ms 초과={over}프레임')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', help='비교할 기준 Git 리비전. 생략하면 합성 기준 리비전을 사용한다.')
    parser.add_argument('--repeats', type=int, default=5, help='전후 교대 측정 쌍 수 (기본값 5).')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats는 1 이상이어야 합니다.')
    reference = json.loads((ROOT / 'tests/fixtures/charge_composition.json').read_text(encoding='utf-8'))
    revision = args.baseline or reference['baseline']
    print(f'비교 기준 {revision}')
    variants = (baseline_art(revision), charge.ChargeArt)
    first, second = map(upload_digest, variants)
    if first != second or not first[2]:
        raise SystemExit(f'RGBA 업로드 또는 순간이동 횟수가 다릅니다. 변경 전={first}, 변경 후={second}')
    digest, uploads, teleports = first
    print(f'180프레임, 순간이동 {teleports}회, RGBA 업로드 {uploads}개 동일 SHA-256 {digest}')
    runs = ([], [])
    for repeat in range(args.repeats):
        for index in (range(2) if repeat % 2 == 0 else reversed(range(2))):
            times, _ = run_scenario(variants[index])
            runs[index].append(tuple(zip(*times)))
    for label, group in zip(('변경 전', '변경 후'), runs):
        report(label, group)


if __name__ == '__main__':
    main()
