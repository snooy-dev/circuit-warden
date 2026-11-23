"""고정 클릭 시나리오의 PNG 재생 시간·업로드·자산 크기를 Git 기준과 교대 비교한다."""

import argparse
from contextlib import ExitStack
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

from game import charge, mode, scene, teleport_link


TARGETS = (2, 4, 1, 0, 1, 4, 2, 3, 2, 4, 1, 0, 1, 4)
POSITIONS = ((-320, -80), (-160, 70), (140, -50), (320, 140), (0, 200))
FRAME_COUNT = 180


def baseline_art(revision):
    commit = subprocess.check_output(
        ['git', 'rev-parse', '--verify', '--end-of-options', f'{revision}^{{commit}}'],
        cwd=ROOT, encoding='ascii').strip()
    result = []
    for module in (charge, teleport_link):
        path = f'game/{Path(module.__file__).name}'
        source = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT)
        namespace = {'__file__': module.__file__}
        exec(compile(source, f'{commit}:{path}', 'exec'), namespace)
        result.append(SimpleNamespace(**namespace))
    return result


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
    uploads = 0
    update_texture = pico.SDL_UpdateTexture

    def count_uploads(*args):
        nonlocal uploads
        uploads += 1
        return update_texture(*args)

    with ExitStack() as stack:
        for name, value in (('renderer', renderer), ('window', None), ('canvas_height', height)):
            stack.enter_context(patch.object(pico, name, value, create=True))
        stack.enter_context(patch.object(pico, 'SDL_SetWindowTitle'))
        stack.enter_context(patch.object(pico, 'SDL_UpdateTexture', count_uploads))
        if art_class:
            old_charge, old_link = art_class
            stack.enter_context(patch.object(scene, 'ChargeArt', lambda images: old_charge.ChargeArt()))
            stack.enter_context(patch.object(scene, 'Charge', old_charge.Charge))
            stack.enter_context(patch.object(mode, 'TeleportLink',
                                            lambda start, end, *args: old_link.TeleportLink(start, end)))
            if hasattr(scene, 'LinkArt'):
                stack.enter_context(patch.object(scene, 'LinkArt', lambda images: None))
        else:
            stack.enter_context(patch.object(mode, 'TeleportLink',
                                            lambda start, end, art, _: teleport_link.TeleportLink(start, end, art)))
        # 재사용 전하의 과거 클릭 부하를 CPU와 PNG에 동일하게 재현한다.
        stack.enter_context(patch.object(scene.Charge, 'spend', lambda _: None, create=True))
        stack.enter_context(patch.object(scene.GameplayLevel, '_update_environment'))
        level_scene = scene.CharacterScene()
        try:
            started = perf_counter_ns()
            level_scene.enter(app)
            load_ms = (perf_counter_ns() - started) / 1e6
            level_scene.level.enemy.destroy()
            for target, position in zip(level_scene.level.charges, POSITIONS, strict=True):
                target.position = position
            image_bytes = sum(image.width * image.height * 4
                              for path, image in level_scene.images._images.items() if 'baked' in path.parts)
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
                started = perf_counter_ns()
                level_scene.update(1 / 60)
                level_scene.draw()
                pico.SDL_RenderPresent(renderer)
                times.append((perf_counter_ns() - started) / 1e6)
            return dict(times=times, teleports=teleports, uploads=uploads, load_ms=load_ms, image_bytes=image_bytes)
        finally:
            level_scene.exit()


def report(label, runs):
    p95 = median(quantiles(run['times'], n=20, method='inclusive')[18] for run in runs)
    maximum = max(max(run['times']) for run in runs)
    over = sum(t > 1000 / 60 for run in runs for t in run['times'])
    print(f'{label}: p95={p95:.3f}ms, 최대={maximum:.3f}ms, 예산초과={over}, '
          f"장면로딩중앙값={median(run['load_ms'] for run in runs):.1f}ms, "
          f"업로드/실행={runs[0]['uploads']}, baked RGBA={runs[0]['image_bytes']/2**20:.2f}MiB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='eb082e5', help='비교할 CPU 효과 Git 리비전.')
    parser.add_argument('--repeats', type=int, default=5, help='전후 교대 측정 쌍 수 (기본값 5).')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats는 1 이상이어야 합니다.')
    revision = args.baseline
    print(f'비교 기준 {revision}, 각{args.repeats*FRAME_COUNT}프레임, SDL 소프트웨어')
    try:
        variants = (baseline_art(revision), None)
    except ModuleNotFoundError as error:
        if error.name != 'numpy':
            raise
        raise SystemExit('이전 구현 비교에만 numpy==2.5.4가 필요합니다. tests/README.md의 성능 검사 환경을 참고하세요.') from error
    warmups = [run_scenario(variant) for variant in variants]
    assert warmups[0]['teleports'] == warmups[1]['teleports'] == 12
    assert warmups[1]['uploads'] == 0, 'PNG 재생 중 업로드 발생'
    runs = ([], [])
    for repeat in range(args.repeats):
        for index in (range(2) if repeat % 2 == 0 else reversed(range(2))):
            runs[index].append(run_scenario(variants[index]))
    for label, group in zip(('변경 전', '변경 후'), runs):
        report(label, group)


if __name__ == '__main__':
    main()
