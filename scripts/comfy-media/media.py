"""Local LTX-2.5 adapter for sprite_set.py --media-cli (no paid fallback)."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
ROUTE = "local:comfyui-ltx25"
FPS = 24


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("ComfyUI redirects are not allowed")


class Client:
    def __init__(self, address):
        parsed = urllib.parse.urlsplit(address)
        if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise ValueError("server must be a local HTTP address (127.0.0.1, localhost, or [::1])")
        self.address = address.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def open(self, path, data=None, content_type="application/json"):
        request = urllib.request.Request(self.address + path, data=data,
                                         headers={"Content-Type": content_type})
        try:
            return self.opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            detail = error.read(8192).decode("utf-8", "replace")
            raise RuntimeError(f"ComfyUI HTTP {error.code}: {detail}") from error

    def json(self, path, data=None):
        body = None if data is None else json.dumps(data).encode("utf-8")
        with self.open(path, body) as response:
            return json.load(response)

    def upload(self, path, name):
        boundary = "comfy" + uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
                f"filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n").encode()
        body += Path(path).read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        with self.open("/upload/image", body, f"multipart/form-data; boundary={boundary}") as response:
            uploaded = json.load(response)
        return safe_file(uploaded, "input")


def safe_file(record, kind):
    filename = record.get("filename", record.get("name", ""))
    subfolder = record.get("subfolder", "")
    if (not filename or any(c in filename for c in "/\\") or filename in (".", "..")
            or "\\" in subfolder or PurePosixPath(subfolder).is_absolute()
            or ".." in PurePosixPath(subfolder).parts or ":" in subfolder
            or record.get("type") != kind):
        raise ValueError("invalid ComfyUI file record")
    return str(PurePosixPath(subfolder) / filename)


def workflow(kind):
    return read_json(HERE / "workflows" / f"api_{kind}.json")


def check_server(client, graphs):
    stats = client.json("/system_stats")
    info = client.json("/object_info")
    missing = []
    loaders = {"UNETLoader": "unet_name", "CLIPLoader": "clip_name",
               "VAELoader": "vae_name", "LatentUpscaleModelLoader": "model_name"}
    for graph in graphs:
        for node in graph.values():
            name = node["class_type"]
            if name not in info:
                missing.append(f"node: {name}")
                continue
            if name in loaders:
                field = loaders[name]
                definition = info[name]["input"]["required"][field]
                available = definition[0] if isinstance(definition[0], list) else definition[1].get("options", [])
                if node["inputs"][field] not in available:
                    missing.append(f"model: {node['inputs'][field]}")
    if missing:
        raise ValueError("missing " + "; ".join(sorted(set(missing))))
    return {"status": "ok", "route": ROUTE, "server": client.address, "model": MODEL,
            "comfyVersion": stats.get("system", {}).get("comfyui_version"),
            "workflows": [len(graph) for graph in graphs], "generationSubmitted": False}


def build_prompt(kind, text, first, last, width, height, frames, seed, prefix):
    graph = workflow(kind)
    def put(node, **values):
        graph[str(node)]["inputs"].update(values)
    if kind == "i2v":
        put(395, image=first)
        put(364, text=text)
        put(339, noise_seed=seed)
        put(338, noise_seed=seed)
        put(356, width=width // 2, height=height // 2, length=frames)
        put(366, frames_number=frames, frame_rate=FPS)
        put(365, frame_rate=FPS)
        put(370, fps=FPS)
        put(75, filename_prefix=prefix)
    else:
        put(31, image=first)
        put(39, image=last)
        put(222, text=text)
        put(196, noise_seed=seed)
        for node in (213, 214):
            put(node, **{"resize_type.width": width, "resize_type.height": height,
                         "scale_method": "lanczos"})
        put(201, length=frames)
        put(197, frames_number=frames, frame_rate=FPS)
        put(202, frame_rate=FPS)
        put(218, fps=FPS)
        put(68, filename_prefix=prefix)
    return graph


def executable(name):
    matches = sorted((ROOT / ".local-tools" / "ffmpeg").glob(f"*/bin/{name}.exe"))
    found = str(matches[-1]) if matches else shutil.which(name)
    if not found:
        raise ValueError(f"{name} not found; load scripts/use-project-tools.ps1")
    return found


def prepare(args):
    text = args.prompt_file.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError("prompt is empty")
    if not math.isfinite(args.duration) or not 1 <= args.duration <= 20:
        raise ValueError("duration must be between 1 and 20 seconds")
    if not 0 <= args.seed < 2**63:
        raise ValueError("seed must be between 0 and 2^63-1")
    with Image.open(args.reference) as source:
        source.load()
        size = source.size
    if args.last_frame:
        with Image.open(args.last_frame) as last:
            last.load()
            if last.size != size:
                raise ValueError("first and last frames must have the same dimensions")
    for path in (args.reference, args.last_frame):
        if path:
            with Image.open(path) as source:
                if source.convert("RGBA").getchannel("A").getextrema()[0] != 255:
                    raise ValueError("reference must have an opaque chroma-key background")
    scale = {"480p": 512, "720p": 768}[args.resolution] / min(size)
    width, height = (max(64, int(value * scale / 64 + 0.5) * 64) for value in size)
    if max(width, height) > 2048:
        raise ValueError("reference aspect ratio exceeds the 2048px local limit")
    frames = max(9, int(args.duration * FPS / 8 + 0.5) * 8 + 1)
    client = Client(args.server)
    kind = "flf2v" if args.last_frame else "i2v"
    check_server(client, [workflow(kind)])
    executable("ffmpeg")
    executable("ffprobe")
    folder = args.out_dir.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    ident = uuid.uuid4().hex
    sources = []
    for path, name in ((args.reference, "first.png"), (args.last_frame, "last.png")):
        if path:
            with Image.open(path) as source:
                # Fixed whole-canvas resize preserves every extremity; no per-frame crop.
                source.convert("RGB").resize((width, height), Image.Resampling.LANCZOS).save(folder / name)
            sources.append({"path": str(path.resolve()), "sha256": sha(path), "prepared": name})
    (folder / "prompt.txt").write_text(text, encoding="utf-8")
    graph = build_prompt(kind, text, f"{ident}-first.png", f"{ident}-last.png", width, height,
                         frames, args.seed, f"sprite-ltx25/{ident}")
    save_json(folder / "workflow-api.json", graph)
    job = {"schema": "circuit-warden.comfy-job.v1", "state": "prepared", "server": client.address,
           "client_id": ident, "prompt_id": None, "kind": kind, "sources": sources,
           "sourceSize": list(size), "width": width, "height": height, "frames": frames,
           "fps": FPS, "durationRequested": args.duration, "seed": args.seed,
           "workflowSha256": sha(folder / "workflow-api.json"), "model": MODEL}
    save_json(folder / "job.json", job)
    return folder / "job.json"


def submit(path):
    job = read_json(path)
    if job["state"] != "prepared":
        raise ValueError("job already submitted; use resume")
    folder = path.parent
    client = Client(job["server"])
    graph = read_json(folder / "workflow-api.json")
    for source in job["sources"]:
        uploaded = client.upload(folder / source["prepared"], f"{job['client_id']}-{source['prepared']}")
        node = "395" if job["kind"] == "i2v" else ("31" if source["prepared"] == "first.png" else "39")
        graph[node]["inputs"]["image"] = uploaded
    save_json(folder / "workflow-api.json", graph)
    job.update(state="submitting", workflowSha256=sha(folder / "workflow-api.json"))
    save_json(path, job)
    # Never retry POST: a lost response may still mean the GPU job was queued.
    result = client.json("/prompt", {"prompt": graph, "client_id": job["client_id"]})
    if not result.get("prompt_id"):
        job.update(state="error", error=result)
        save_json(path, job)
        raise RuntimeError(f"ComfyUI rejected workflow: {result}")
    job.update(state="queued", prompt_id=result["prompt_id"], node_errors=result.get("node_errors", {}))
    save_json(path, job)


def collect(path, job, history, client):
    output_node = "75" if job["kind"] == "i2v" else "68"
    records = history.get("outputs", {}).get(output_node, {}).get("images", [])
    record = next((item for item in records if item.get("filename", "").lower().endswith(".mp4")), None)
    if not record:
        raise RuntimeError("completed job has no MP4 output")
    safe_file(record, "output")
    folder = path.parent
    raw = folder / "download.mp4.part"
    with client.open("/view?" + urllib.parse.urlencode({key: record[key] for key in ("filename", "subfolder", "type")})) as response:
        with raw.open("wb") as destination:
            shutil.copyfileobj(response, destination)
    clip = folder / "clip.mp4"
    if clip.exists():
        raise ValueError("clip.mp4 already exists without a verified result; preserve it and inspect the job")
    staged = folder / "verified.mp4"
    subprocess.run([executable("ffmpeg"), "-v", "error", "-y", "-i", str(raw), "-map", "0:v:0",
                    "-an", "-c:v", "copy", str(staged)], check=True, capture_output=True)
    probe = subprocess.run([executable("ffprobe"), "-v", "error", "-count_frames", "-show_streams",
                            "-show_format", "-of", "json", str(staged)], check=True, capture_output=True)
    media = json.loads(probe.stdout)
    streams = media["streams"]
    if len(streams) != 1 or streams[0]["codec_type"] != "video":
        raise ValueError("expected one silent video stream")
    video = streams[0]
    if (Fraction(video["avg_frame_rate"]) != job["fps"]
            or int(video["nb_read_frames"]) != job["frames"] or video["width"] != job["width"]
            or video["height"] != job["height"]):
        raise ValueError("decoded video dimensions/frame count differ from the prepared workflow")
    staged.replace(clip)
    raw.unlink()
    result = {"status": "ok", "route": ROUTE, "artifact": str(clip.resolve()), "sha256": sha(clip),
              "model": job["model"], "estimateUsd": 0, "lastFrameUsed": job["kind"] == "flf2v",
              "durationRequested": job["durationRequested"], "durationUsed": float(media["format"]["duration"]),
              "fps": job["fps"], "frames": job["frames"], "width": job["width"], "height": job["height"],
              "sourceSize": job["sourceSize"], "job": str(path.resolve()), "prompt_id": job["prompt_id"]}
    save_json(folder / "result.json", result)
    job.update(state="complete", output=record)
    save_json(path, job)
    return result


def resume(path, timeout, poll=2):
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive")
    path = path.resolve()
    job = read_json(path)
    if job.get("schema") != "circuit-warden.comfy-job.v1":
        raise ValueError("not a ComfyUI sprite job")
    client = Client(job["server"])
    if (path.parent / "result.json").exists():
        result = read_json(path.parent / "result.json")
        clip = path.parent / "clip.mp4"
        if not clip.is_file() or sha(clip) != result["sha256"]:
            raise ValueError("completed artifact is missing or changed")
        result["artifact"] = str(clip)
        return result
    if not job.get("prompt_id"):
        raise ValueError(f"job is {job['state']} with no prompt_id; inspect ComfyUI queue before any new submission")
    end = time.monotonic() + timeout
    while True:
        history = client.json("/history/" + urllib.parse.quote(job["prompt_id"], safe="")).get(job["prompt_id"])
        if history:
            status = history.get("status", {})
            if status.get("status_str") == "error":
                job.update(state="error", error=status.get("messages", []))
                save_json(path, job)
                raise RuntimeError(f"ComfyUI execution failed: {job['error']}")
            if status.get("completed"):
                save_json(path.parent / "history.json", history)
                return collect(path, job, history, client)
        if time.monotonic() >= end:
            job["state"] = "timeout"
            save_json(path, job)
            raise TimeoutError(f"job still pending; resume --job {path} (no automatic resubmission)")
        time.sleep(min(poll, max(0, end - time.monotonic())))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="read-only node/model check")
    doctor.add_argument("--server", default="http://127.0.0.1:8188")
    for name in ("video", "prepare"):
        command = commands.add_parser(name)
        command.add_argument("--prompt-file", type=Path, required=True)
        command.add_argument("--reference", type=Path, required=True)
        command.add_argument("--last-frame", type=Path)
        command.add_argument("--duration", type=float, default=6)
        command.add_argument("--resolution", choices=("480p", "720p"), default="720p")
        command.add_argument("--out-dir", type=Path, required=True)
        command.add_argument("--server", default="http://127.0.0.1:8188")
        command.add_argument("--seed", type=int, default=42)
        command.add_argument("--timeout", type=float, default=6900)
    command = commands.add_parser("resume")
    command.add_argument("--job", type=Path, required=True)
    command.add_argument("--timeout", type=float, default=6900)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = check_server(Client(args.server), [workflow("i2v"), workflow("flf2v")])
        elif args.command == "resume":
            result = resume(args.job, args.timeout)
        else:
            if not math.isfinite(args.timeout) or args.timeout <= 0:
                raise ValueError("timeout must be positive")
            path = prepare(args)
            if args.command == "prepare":
                result = {"status": "prepared", "job": str(path), "generationSubmitted": False}
            else:
                submit(path)
                print(f"ComfyUI job saved: {path}", file=sys.stderr, flush=True)
                result = resume(path, args.timeout)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print(f"error: {ROUTE}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
