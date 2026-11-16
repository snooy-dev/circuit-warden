"""Apply the Circuit Warden video route to the project-local sprite skills."""

import argparse
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ("generate2dsprite", "video2dsprite", "generate2dmedia")
START = "<!-- circuit-warden-comfy-route:start -->"
END = "<!-- circuit-warden-comfy-route:end -->"
OVERRIDE = f"""{START}
## Circuit Warden 프로젝트 영상 경로

- 이 프로젝트 영상 생성에는 로컬 ComfyUI LTX-2.5를 우선한다. 유료 API와 다른 영상 생성 경로로 자동 전환하지 않는다.
- 단일 I2V는 도구 Python으로 `scripts/comfy-media/media.py video`를 실행한다. 세트는 `sprite_set.py run --plan <set_plan.json> --media-cli scripts/comfy-media/media.py --jobs 1 --timeout 7200`을 사용한다.
- 시간 초과 후에는 같은 세트 명령을 다시 실행한다. 단일 클립은 `scripts/comfy-media/media.py resume --job <job.json>`으로 이어받는다. [도구 구성](../../../docs/tooling.md)을 따른다.
{END}"""

# Each anchor is checked before writing any skill files. The upstream CLI can
# change independently of this project, so avoid guessing where to patch it.
CALLER_PATCHES = (
    (
        '_CLIP_SUFFIXES = (".mp4", ".webm", ".mov", ".m4v")\n_LAST_FRAME_WORDS',
        '_CLIP_SUFFIXES = (".mp4", ".webm", ".mov", ".m4v")\n'
        '_COMFY_MEDIA = (Path(__file__).parent / "../../../../scripts/comfy-media/media.py").resolve()\n'
        '_LAST_FRAME_WORDS',
    ),
    (
        '        media = folder / "media"\n        clip = _find_clip(media)',
        '''        media = folder / "media"
        local = self.media_argv is not None and Path(self.media_argv[1]) == _COMFY_MEDIA
        local_job = media / "job.json"
        if local_job.is_file() and not local:
            saved = forge_core.read_json(local_job)
            if isinstance(saved, dict) and saved.get("schema") == "circuit-warden.comfy-job.v1":
                return {"status": "pending", "message": f"use --media-cli {_COMFY_MEDIA} to resume this local job"}
        resume_local = local and local_job.is_file()
        clip = None if resume_local else _find_clip(media)''',
    ),
    (
        '        if os.path.lexists(media):\n            _move_aside(media)\n        job = self.root',
        '        if os.path.lexists(media) and not resume_local:\n            _move_aside(media)\n        job = self.root',
    ),
    (
        '''        result = self._call_media(base + (["--last-frame", job / "input.png"] if pin else []), timeout)
        pin_note = None
        if pin and result["code"] not in (0, EXIT_NO_ROUTE) and _LAST_FRAME_WORDS.search(result["message"] or ""):''',
        '''        args = ["resume", "--job", local_job] if resume_local else (
            base + (["--last-frame", job / "input.png"] if pin else []))
        if local:
            args += ["--timeout", max(1.0, timeout - 5)]
        result = self._call_media(args, timeout)
        pin_note = None
        if not local and pin and result["code"] not in (0, EXIT_NO_ROUTE) and _LAST_FRAME_WORDS.search(result["message"] or ""):''',
    ),
    (
        '''        if result["code"] == EXIT_NO_ROUTE:
            return {"status": "no-route", "message": result["message"] or "no generation route (exit 3)"}
        summary = result["summary"] or {}
        if result["code"] != 0 or summary.get("status", "ok") != "ok":
            return {"status": "error", "message": result["message"] or f"media CLI status {summary.get('status')!r}"}''',
        '''        if not local and result["code"] == EXIT_NO_ROUTE:
            return {"status": "no-route", "message": result["message"] or "no generation route (exit 3)"}
        failed = "pending" if local else "error"
        summary = result["summary"] or {}
        if result["code"] != 0 or summary.get("status", "ok") != "ok":
            return {"status": failed, "message": result["message"] or f"media CLI status {summary.get('status')!r}"}''',
    ),
    (
        '''        artifact = artifact or _find_clip(media)
        if artifact is None:
            return {"status": "error", "message": f"the media CLI reported''',
        '''        if not local:
            artifact = artifact or _find_clip(media)
        if artifact is None:
            return {"status": failed, "message": f"the media CLI reported''',
    ),
    (
        '''        record["message"] = result["message"]
        if result["status"] == "no-route":''',
        '''        record["message"] = result["message"]
        if result["status"] == "pending":
            record["status"], st["status"] = "open", "generating"
            st["message"] = f"take {record['take']}: {result['message']} (the next run continues this take)"
            self.save()
            return "pending"
        if result["status"] == "no-route":''',
    ),
    (
        '                    if outcome == "no-route":\n                        blocked = True',
        '                    if outcome in ("no-route", "pending"):\n                        blocked = True',
    ),
)


def patch_skill(source, name):
    lines = source.splitlines(keepends=True)
    if lines[:2] != ["---\n", f"name: {name}\n"] or "---\n" not in lines[2:]:
        raise ValueError("unexpected SKILL.md front matter")
    if START in source or END in source:
        if source.count(START) == source.count(END) == source.count(OVERRIDE) == 1:
            return source
        raise ValueError("local route marker has changed; inspect the file before reinstalling")
    end = lines.index("---\n", 2) + 1
    return "".join(lines[:end]) + "\n" + OVERRIDE + "\n" + "".join(lines[end:])


def patch_caller(source):
    for old, new in CALLER_PATCHES:
        if source.count(old) == 1:
            source = source.replace(old, new, 1)
        elif source.count(new) != 1 or old in source:
            raise ValueError(f"upstream sprite_set.py changed near {old.strip().splitlines()[0]!r}")
    compile(source.lstrip("\ufeff"), "sprite_set.py", "exec")
    return source


def planned_changes(root):
    skills = root / ".agents/skills"
    patches = [(skills / name / "SKILL.md", lambda source, name=name: patch_skill(source, name))
               for name in SKILLS]
    patches.append((skills / "video2dsprite/scripts/sprite_set.py", patch_caller))
    changes = []
    for path, patch in patches:
        raw = path.read_bytes()
        source = raw.decode("utf-8-sig").replace("\r\n", "\n")
        try:
            updated = patch(source)
        except (ValueError, SyntaxError) as error:
            raise ValueError(f"{path}: {error}") from error
        if updated != source:
            if b"\r\n" in raw:
                updated = updated.replace("\n", "\r\n")
            encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
            changes.append((path, updated.encode(encoding)))
    return changes


def install(root, check=False):
    changes = planned_changes(root)
    if not check:
        for path, data in changes:
            with NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
            try:
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
    return [path.relative_to(root) for path, _ in changes]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report missing installation without writing")
    args = parser.parse_args(argv)
    try:
        paths = install(ROOT, check=args.check)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    for path in paths:
        print(f"{'needs install' if args.check else 'installed'}: {path}")
    if not paths:
        print("local sprite skill route is installed")
    return int(args.check and bool(paths))


if __name__ == "__main__":
    sys.exit(main())
