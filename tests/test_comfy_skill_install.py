"""Check the installer's local skill patches without editing the installed skills."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "scripts/comfy-media"
SPRITE = Path(".agents/skills/video2dsprite/scripts/sprite_set.py")
spec = importlib.util.spec_from_file_location("comfy_skill_install", TOOLS / "install_skill_route.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@unittest.skipUnless((ROOT / SPRITE).is_file(), "project-local video2dsprite skill is not installed")
class ComfySkillInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = (ROOT / SPRITE).read_text(encoding="utf-8-sig")
        self.caller = self.root / SPRITE
        self.caller.parent.mkdir(parents=True)
        for old, new in reversed(installer.CALLER_PATCHES):
            source = source.replace(new, old)
        self.caller.write_text(source, encoding="utf-8", newline="\r\n")
        self.skills = [self.root / ".agents/skills" / name / "SKILL.md" for name in installer.SKILLS]
        for name, path in zip(installer.SKILLS, self.skills):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"---\nname: {name}\ndescription: Example\n---\n\n# Original\n",
                            encoding="utf-8-sig", newline="\r\n")

    def test_check_is_read_only_and_reinstall_is_idempotent(self):
        before = [path.read_bytes() for path in [*self.skills, self.caller]]
        self.assertEqual(len(installer.install(self.root, check=True)), 4)
        self.assertEqual([path.read_bytes() for path in [*self.skills, self.caller]], before)
        self.assertEqual(len(installer.install(self.root)), 4)
        self.assertEqual(installer.install(self.root, check=True), [])
        self.assertEqual(installer.install(self.root), [])
        for path in self.skills:
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf---\r\n"))
            self.assertEqual(path.read_text(encoding="utf-8-sig").count(installer.START), 1)

    def test_unexpected_caller_fails_before_editing_any_skill(self):
        before = [path.read_bytes() for path in self.skills]
        source = self.caller.read_text(encoding="utf-8")
        anchor = installer.CALLER_PATCHES[-1][0]
        self.assertIn(anchor, source)
        self.caller.write_text(source.replace(anchor, "                    if outcome == 'no-route':\n"
                                                      "                        blocked = True"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, r"upstream sprite_set\.py changed"):
            installer.install(self.root)
        self.assertEqual([path.read_bytes() for path in self.skills], before)

    def test_sprite_run_stops_on_timeout_and_resumes_same_take(self):
        installer.install(self.root)
        sprite_spec = importlib.util.spec_from_file_location("sprite_set_comfy_review", ROOT / SPRITE)
        sprite = importlib.util.module_from_spec(sprite_spec)
        self.addCleanup(sys.modules.pop, sprite_spec.name, None)
        sys.modules[sprite_spec.name] = sprite
        exec(compile(self.caller.read_bytes(), str(ROOT / SPRITE), "exec"), sprite.__dict__)

        record = {"take": 1, "round": 1, "dir": "take-1", "status": "open"}
        state = {"takes": [record], "round": 1, "status": "pending", "job": {"dir": "reference"}}
        runner = sprite.SetRunner.__new__(sprite.SetRunner)
        runner.root = self.root
        runner.plan_sha = "plan"
        runner.plan = {"finish": {}, "actions": [{"id": "idle"}],
                       "generation": {"duration": 2, "resolution": "480p"}}
        runner.state = {"plan": {"sha256": "plan"}, "actions": {"idle": state}}
        runner.entries = {"idle": {"pinLastFrame": True}}
        runner.save = Mock()
        runner.check_masters = Mock()
        runner.ensure_job = Mock()
        runner.post_process = Mock()
        runner.summary = Mock(return_value=({}, 1))
        runner.evaluate = Mock(side_effect=lambda *args: state.update(chosen={"take": 1}))
        directory = self.root / "take-1/media"
        clip = directory / "clip.mp4"
        job = directory / "job.json"

        def call(args, timeout):
            if args[0] == "video":
                directory.mkdir(parents=True)
                job.write_text('{"schema":"circuit-warden.comfy-job.v1"}', encoding="utf-8")
                return {"code": -1, "summary": None, "message": "timed out waiting for last frame"}
            self.assertEqual(args, ["resume", "--job", job, "--timeout", 25.0])
            self.assertEqual(timeout, 30)
            return {"code": 0, "summary": {"status": "ok", "route": "local:comfyui-ltx25",
                                           "artifact": str(clip), "lastFrameUsed": True}, "message": ""}

        runner._call_media = Mock(side_effect=call)
        settings = {"max_takes": 3, "jobs": 1, "stagger": 0, "timeout": 30}
        runner.run(None, media_cli=str(TOOLS / "media.py"), **settings)
        self.assertEqual(record["status"], "open")
        self.assertEqual(state["takes"], [record])
        self.assertEqual(runner._call_media.call_count, 1)
        runner.evaluate.assert_not_called()

        # A pre-existing local file must be checked by the local adapter and
        # preserve its route metadata instead of being treated as a supplied clip.
        clip.write_bytes(b"offline clip fixture")
        with patch.object(sprite, "ROUTE_MEDIA", self.caller):
            runner.run(None, media_cli=None, **settings)
        self.assertEqual(runner._call_media.call_count, 1)
        self.assertEqual(record["status"], "open")
        runner.run(None, media_cli=str(TOOLS / "media.py"), **settings)
        self.assertEqual(runner._call_media.call_count, 2)
        self.assertEqual(record["status"], "generated")
        self.assertEqual(record["route"], "local:comfyui-ltx25")
        self.assertTrue(record["pinnedLastFrame"])
        route = json.loads((directory.parent / "route.json").read_bytes())
        self.assertEqual(route["summary"]["lastFrameUsed"], True)
        self.assertEqual(state["takes"], [record])


if __name__ == "__main__":
    unittest.main()
