"""Local adapter boundaries and recovery; no GPU jobs or network in these tests."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("comfy_media", ROOT / "scripts/comfy-media/media.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class ComfyMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def job(self, **values):
        job = {"schema": "circuit-warden.comfy-job.v1", "server": "http://127.0.0.1:8188",
               "state": "queued", "prompt_id": "known-id"}
        job.update(values)
        path = self.folder / "job.json"
        media.save_json(path, job)
        return path

    def test_server_cannot_redirect_to_external_service(self):
        for address in ("https://127.0.0.1:8188", "http://example.com", "http://localhost@evil.com",
                        "http://localhost/path", "http://localhost?token=x"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                media.Client(address)
        with self.assertRaises(ValueError):
            media.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")

    def test_file_records_reject_traversal_and_wrong_storage(self):
        for fields in ({"filename": "../x.mp4"}, {"subfolder": "../outside"},
                       {"subfolder": "C:/outside"}, {"type": "input"}):
            record = {"filename": "clip.mp4", "subfolder": "sprite-ltx25", "type": "output", **fields}
            with self.subTest(record=record), self.assertRaises(ValueError):
                media.safe_file(record, "output")

    def test_doctor_handles_both_model_combo_schemas_without_posting(self):
        graphs = [media.workflow("i2v"), media.workflow("flf2v")]
        fields = {"UNETLoader": "unet_name", "CLIPLoader": "clip_name", "VAELoader": "vae_name",
                  "LatentUpscaleModelLoader": "model_name"}
        info = {}
        for graph in graphs:
            for node in graph.values():
                kind = node["class_type"]
                info.setdefault(kind, {"input": {"required": {}}})
                if kind in fields:
                    field = fields[kind]
                    required = info[kind]["input"]["required"]
                    if kind == "LatentUpscaleModelLoader":
                        required[field] = ["COMBO", {"options": [node["inputs"][field]]}]
                    else:
                        required.setdefault(field, [[], {}])[0].append(node["inputs"][field])
        client = MagicMock(address="http://127.0.0.1:8188")
        client.json.side_effect = [{"system": {"comfyui_version": "test"}}, info]
        self.assertFalse(media.check_server(client, graphs)["generationSubmitted"])
        self.assertTrue(all(len(call.args) == 1 for call in client.json.call_args_list))

    def test_prepare_both_routes_preserves_source_and_never_uploads(self):
        image = self.folder / "source.png"
        prompt = self.folder / "prompt.txt"
        Image.new("RGB", (320, 240), "magenta").save(image)
        prompt.write_text("The same character, fixed camera.", encoding="utf-8")
        original = media.sha(image)
        for pin in (False, True):
            args = argparse.Namespace(prompt_file=prompt, reference=image, last_frame=image if pin else None,
                                      duration=2, resolution="480p", seed=42,
                                      server="http://127.0.0.1:8188", out_dir=self.folder / str(pin))
            with patch.object(media, "Client") as client, patch.object(media, "check_server"), \
                    patch.object(media, "executable", return_value="unused"):
                client.return_value.address = args.server
                path = media.prepare(args)
                client.return_value.upload.assert_not_called()
                client.return_value.json.assert_not_called()
            job = media.read_json(path)
            graph = media.read_json(path.parent / "workflow-api.json")
            self.assertEqual((job["width"], job["height"], job["frames"]), (704, 512, 49))
            self.assertEqual(graph["222" if pin else "364"]["inputs"]["text"], prompt.read_text())
            self.assertEqual(graph["201" if pin else "356"]["inputs"]["length"], 49)
            self.assertEqual(graph["68" if pin else "75"]["inputs"]["format.codec"], "h264")
            self.assertEqual(job["state"], "prepared")
            self.assertEqual(media.sha(image), original)
            with patch.object(media, "check_server"), patch.object(media, "executable"), \
                    self.assertRaises(FileExistsError):
                media.prepare(args)

    def test_invalid_inputs_fail_before_server_access(self):
        image = self.folder / "alpha.png"
        Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(image)
        prompt = self.folder / "prompt.txt"
        prompt.write_text("motion", encoding="utf-8")
        args = argparse.Namespace(prompt_file=prompt, reference=image, last_frame=None, duration=2,
                                  resolution="480p", seed=42, server="http://localhost:8188",
                                  out_dir=self.folder / "new")
        with patch.object(media, "Client") as client, self.assertRaises(ValueError):
            media.prepare(args)
        client.assert_not_called()
        self.assertFalse(args.out_dir.exists())

    def test_lost_submit_response_is_saved_and_not_retried(self):
        path = self.job(state="prepared", prompt_id=None, kind="i2v", sources=[], client_id="client")
        media.save_json(self.folder / "workflow-api.json", media.workflow("i2v"))
        with patch.object(media, "Client") as factory:
            factory.return_value.json.side_effect = OSError("connection lost")
            with self.assertRaises(OSError):
                media.submit(path)
            self.assertEqual(media.read_json(path)["state"], "submitting")
            with self.assertRaises(ValueError):
                media.submit(path)
            self.assertEqual(factory.return_value.json.call_count, 1)

    def test_timeout_then_resume_uses_only_existing_prompt_id(self):
        path = self.job()
        with patch.object(media, "Client") as factory:
            factory.return_value.json.return_value = {}
            with self.assertRaises(TimeoutError):
                media.resume(path, .001, poll=.001)
            self.assertEqual(media.read_json(path)["state"], "timeout")
            factory.return_value.json.return_value = {"known-id": {"status": {"completed": True}}}
            with patch.object(media, "collect", return_value={"status": "ok"}):
                self.assertEqual(media.resume(path, 1)["status"], "ok")
            for call in factory.return_value.json.call_args_list:
                self.assertEqual(call.args, ("/history/known-id",))

    def test_cached_result_integrity_and_existing_sprite_caller(self):
        path = self.job(state="complete")
        clip = self.folder / "clip.mp4"
        clip.write_bytes(b"contract fixture, no GPU")
        media.save_json(self.folder / "result.json", {"status": "ok", "route": media.ROUTE,
                                                       "artifact": str(clip), "sha256": media.sha(clip)})
        sprite_path = ROOT / ".agents/skills/video2dsprite/scripts/sprite_set.py"
        if not sprite_path.is_file():
            self.skipTest("local sprite skill is not installed")
        sprite_spec = importlib.util.spec_from_file_location("sprite_set_contract", sprite_path)
        sprite = importlib.util.module_from_spec(sprite_spec)
        sys.modules[sprite_spec.name] = sprite
        sprite_spec.loader.exec_module(sprite)
        runner = sprite.SetRunner.__new__(sprite.SetRunner)
        runner.media_argv = [sys.executable, str(media.HERE / "media.py")]
        result = runner._call_media(["resume", "--job", path], timeout=30)
        self.assertEqual(result["code"], 0, result)
        self.assertEqual(result["summary"]["route"], media.ROUTE)
        clip.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            media.resume(path, 1)

    def test_invalid_timeout_never_prepares_or_submits(self):
        with patch.object(media, "prepare") as prepare, patch("sys.stderr", io.StringIO()):
            code = media.main(["video", "--prompt-file", "x", "--reference", "x", "--out-dir", "x",
                               "--timeout", "nan"])
        self.assertEqual(code, 1)
        prepare.assert_not_called()


if __name__ == "__main__":
    unittest.main()
