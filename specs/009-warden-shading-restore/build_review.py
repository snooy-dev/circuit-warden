from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys
import types

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, label, map_coordinates

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/warden'
OUT = ART / 'shading-restore'
MASTER = ART / 'walk-hibit/master-v1/master_rgba.png'
EDIT = OUT / 'edited-v1.png'
RESTORED = OUT / 'master-restored-v1.png'
REVIEW = OUT / 'review-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rig(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def restore_master():
    original = np.array(Image.open(MASTER).convert('RGBA'))
    edited = np.array(Image.open(EDIT).convert('RGBA'))
    labels, _ = label(edited[:, :, 3] > 127)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    component = labels == sizes.argmax()
    ey, ex = np.where(component)
    oy, ox = np.where(original[:, :, 3] > 127)
    y, x = np.mgrid[:1024, :1024]
    sx = ex.min() + (x - ox.min()) * (ex.max() + 1 - ex.min()) / (ox.max() + 1 - ox.min())
    sy = ey.min() + (y - oy.min()) * (ey.max() + 1 - ey.min()) / (oy.max() + 1 - oy.min())
    aligned = np.stack([map_coordinates(edited[:, :, c].astype(float), [sy, sx], order=1, mode='nearest') for c in range(4)], -1).clip(0, 255).astype('uint8')
    old_eyes = (original[:, :, :3].max(2) < 60) & (original[:, :, 3] > 128)
    new_eyes = (aligned[:, :, :3].max(2) < 60) & (aligned[:, :, 3] > 128)
    # Preserve exact eye placement and silhouette, including the original antialiased edge.
    donors = (aligned[:, :, 3] > 240) & ~new_eyes
    _, nearest = distance_transform_edt(~donors, return_indices=True)
    replace = ((aligned[:, :, 3] < 240) | (new_eyes & ~old_eyes)) & (original[:, :, 3] > 0)
    aligned[replace, :3] = aligned[nearest[0][replace], nearest[1][replace], :3]
    aligned[old_eyes, :3] = original[old_eyes, :3]
    aligned[:, :, 3] = original[:, :, 3]
    aligned[aligned[:, :, 3] == 0] = 0
    assert np.array_equal(aligned[:, :, 3], original[:, :, 3])
    assert np.array_equal(aligned[old_eyes, :3], original[old_eyes, :3])
    Image.fromarray(aligned).save(RESTORED)
    return {'sourceAlphaExact': True, 'sourceEyesExact': True, 'originalBounds': [int(ox.min()), int(oy.min()), int(ox.max()+1), int(oy.max()+1)], 'editedBounds': [int(ex.min()), int(ey.min()), int(ex.max()+1), int(ey.max()+1)], 'edgeFilledPixels': int(replace.sum())}


def inject(rig, phases):
    old = rig.BASE.copy()
    current = rig.current_layer
    frozen_current = types.FunctionType(current.__code__, dict(current.__globals__, BASE=old), current.__name__, current.__defaults__)
    before = [current(p) for p in phases]
    rig.SOURCE = RESTORED
    fresh = rig.prepare()
    region = Image.new('L', (rig.W*rig.S, rig.H*rig.S))
    draw = ImageDraw.Draw(region)
    for _, _, xy, _, _ in rig.CURVES:
        draw.line([tuple(p*rig.S) for p in xy], fill=255, width=round(3.2*rig.S))
    # Only remove pale static current inside the established paths, not cyan rim lighting elsewhere.
    remove = (np.array(region) > 0) & (fresh[:, :, 0] > 70) & (fresh[:, :, 1] > 210) & (fresh[:, :, 3] > 128)
    donors = (fresh[:, :, 3] > 200) & (fresh[:, :, 0] < 65) & (fresh[:, :, 1] > 65) & ~remove
    _, nearest = distance_transform_edt(~donors, return_indices=True)
    fresh[remove, :3] = fresh[nearest[0][remove], nearest[1][remove], :3]
    assert np.array_equal(fresh[:, :, 3], old[:, :, 3])
    rig.BASE = fresh
    rig.current_layer = frozen_current
    assert all(np.array_equal(a, rig.current_layer(p)) for a, p in zip(before, phases))
    return {'currentLayersExact': True, 'preparedAlphaExact': True, 'staticCurrentRemovedPixels': int(remove.sum())}


def save_clip(name, frames, previous):
    width, height = frames[0].shape[1], frames[0].shape[0]
    report = {'frames': len(frames), 'alphaExact': True, 'paletteExact': True}
    for direction in ('right', 'left'):
        folder = REVIEW / name / f'{name}_{direction}'; folder.mkdir(parents=True)
        old_folder = previous / f'{name}_{direction}'
        manifest = json.loads((old_folder / 'animation.json').read_text(encoding='utf-8'))
        manifest['status'] = 'review-only'
        durations = manifest.get('previewDurationsMs', manifest['durationsMs'])
        # GIF duration uses 10ms units; retain the original preview's duration sequence.
        old_gif = Image.open(old_folder / 'preview.gif')
        durations = []
        for i in range(old_gif.n_frames):
            old_gif.seek(i); durations.append(old_gif.info['duration'])
        sheet = Image.new('RGBA', (width*8, height*((len(frames)+7)//8)))
        gifs = []
        for i, f in enumerate(frames):
            a = f if direction == 'right' else f[:, ::-1].copy()
            old = np.array(Image.open(old_folder / f'frame_{i:02d}.png').convert('RGBA'))
            assert np.array_equal(a[:, :, 3], old[:, :, 3]), (name, direction, i, 'alpha')
            assert set(np.unique(a[:, :, 3])) <= {0, 255}
            assert set(map(tuple, a[a[:, :, 3] > 0, :3])) <= PALETTE
            image = Image.fromarray(a); image.save(folder / f'frame_{i:02d}.png')
            sheet.alpha_composite(image, ((i % 8)*width, (i // 8)*height))
            bg = Image.new('RGBA', (width, height), '#151e30'); bg.alpha_composite(image)
            gifs.append(bg.convert('RGB').resize((width*4, height*4), Image.Resampling.NEAREST))
        sheet.save(folder / 'sheet.png')
        bg = Image.new('RGBA', sheet.size, '#eeeae0'); bg.alpha_composite(sheet)
        bg.convert('RGB').resize((sheet.width*2, sheet.height*2), Image.Resampling.NEAREST).save(folder / 'review.png')
        gifs[0].save(folder / 'preview.gif', save_all=True, append_images=gifs[1:], duration=durations, disposal=2, loop=0)
        (folder / 'animation.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        report['runtimeMs'] = sum(manifest['durationsMs'])
        report['previewMs'] = sum(durations)
    preserved = []
    for name_meta in ('physics.json', 'gait.json', 'poses.json', 'current-paths.json'):
        p = previous / name_meta
        if p.exists():
            shutil.copyfile(p, REVIEW / name / name_meta)
            assert sha(p) == sha(REVIEW / name / name_meta)
            preserved.append(name_meta)
    report['unchangedMetadata'] = preserved
    return report


def comparison(name, previous):
    frames = sorted((REVIEW / name / f'{name}_right').glob('frame_*.png'))
    reference = Image.open(ART / 'provisional-approved/idle-unarmed-v7/unarmed/frame_00.png').convert('RGBA')
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
    gifs = []
    for i, path in enumerate(frames):
        images = [reference, Image.open(previous / f'{name}_right/frame_{i:02d}.png').convert('RGBA'), Image.open(path).convert('RGBA')]
        board = Image.new('RGBA', (1152, 370), '#eeeae0')
        for j, (im, title) in enumerate(zip(images, ['기준 idle', '기존 '+name, '명암 복원 '+name])):
            ImageDraw.Draw(board).text((j*384+20, 12), title, font=font, fill='#142030')
            board.alpha_composite(im.resize((im.width*3, im.height*3), Image.Resampling.NEAREST), (j*384+(384-im.width*3)//2, 40))
        gifs.append(board.convert('RGB'))
    source_gif = Image.open(previous / f'{name}_right/preview.gif'); durations = []
    for i in range(source_gif.n_frames):
        source_gif.seek(i); durations.append(source_gif.info['duration'])
    gifs[0].save(REVIEW / f'{name}-comparison.gif', save_all=True, append_images=gifs[1:], duration=durations, loop=0, disposal=2)
    gifs[0].save(REVIEW / f'{name}-comparison.png')


if __name__ == '__main__':
    assert not REVIEW.exists(), 'Keep previous review outputs; use a new version.'
    protected = {str(p.relative_to(ROOT)): sha(p) for p in [MASTER, ART/'reference/master-source.png', ART/'reference/energe-sword-grip.png']}
    for approval_path in (ART/'provisional-approved').glob('*/approval.json'):
        approval = json.loads(approval_path.read_text(encoding='utf-8'))
        for rel, digest in approval['frameSha256'].items():
            path = approval_path.parent/rel
            assert sha(path) == digest
            protected[str(path.relative_to(ROOT))] = digest
    report = {'master': restore_master(), 'clips': {}}
    REVIEW.mkdir()
    rigs = [('walk', ART/'walk-hibit/build_walk.py', ART/'provisional-approved/walk-v4'), ('run', ART/'sprint-hibit/build_sprint_v3.py', ART/'provisional-approved/run-v3'), ('attack', ART/'attack-hibit/build_attack.py', ART/'attack-hibit/review-v6')]
    for name, script, previous in rigs:
        module = load_rig(script, 'restore_'+name)
        PALETTE = set(map(tuple, module.PAL.tolist()))
        phases = [i/(module.N-1) if name == 'attack' else i/module.N+(module.PHASE_OFFSET if name == 'run' else 0) for i in range(module.N)]
        checks = inject(module.b if name == 'attack' else module, phases)
        frames = [module.render(p) for p in phases]
        report['clips'][name] = dict(save_clip(name, frames, previous), **checks, rigSha256=sha(script))
        comparison(name, previous)
        print(name, report['clips'][name], flush=True)
    assert all(sha(ROOT/p) == digest for p, digest in protected.items())
    report['protectedHashes'] = protected
    report['source'] = {'route': 'host-image_gen', 'motion': 'existing-code', 'editedSha256': sha(EDIT), 'restoredSha256': sha(RESTORED), 'status': 'review-only'}
    (REVIEW/'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
