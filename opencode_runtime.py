"""Use OpenCode's supported local server for transient, tool-free text generation."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import tempfile

import httpx

MODEL_ID = "deepseek-v4.1-flash-free"
MODEL = "opencode/" + MODEL_ID
GLM_MODEL_ID = "glm-5.3-flash-free"
GLM_MODEL = "opencode/" + GLM_MODEL_ID
FREE_MODELS = {
    MODEL: "DeepSeek V4.1 Flash",
    GLM_MODEL: "GLM 5.3 Flash",
}


def is_free_model(model):
    costs = model.get("cost", [])
    return ("opencode/" + model.get("id", "") in FREE_MODELS and model.get("providerID") == "opencode"
            and model.get("enabled") is True and model.get("status") == "active"
            and bool(costs) and all(c.get("input") == 0 and c.get("output") == 0
                                   and all(v == 0 for v in c.get("cache", {}).values()) for c in costs))


class OpenCodeRuntime:
    def __init__(self):
        self.ready = self.loading = False
        self.error = None
        self.process = self.client = self.directory = self.drain = None
        self.location = None
        self.available_models = {}

    def update_catalog(self, catalog):
        self.available_models = {"opencode/" + m["id"]: m for m in catalog.get("data", [])
                                 if is_free_model(m)}

    async def start(self):
        binary = shutil.which("opencode")
        if not binary or os.environ.get("SPEAK_DISABLE_OPENCODE") == "1":
            self.error = "Install OpenCode v2 to use online models, or choose a local model."
            return
        self.loading = True
        try:
            self.directory = tempfile.TemporaryDirectory(prefix="schwatz-opencode-")
            root = Path(self.directory.name)
            # Do not inherit API keys, personal OpenCode configuration, or workspace files.
            env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "TMPDIR", "LANG", "USER")}
            for name, folder in (("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                                 ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state")):
                env[name] = str(root / folder)
            config = root / "config/opencode"
            config.mkdir(parents=True)
            (config / "opencode.json").write_text(json.dumps({
                "model": MODEL, "share": "disabled", "snapshots": False, "update": "disable",
            }))
            self.process = await asyncio.create_subprocess_exec(
                binary, "serve", "--hostname", "127.0.0.1", "--port", "0", "--log-level", "none",
                cwd=root, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            url = password = None
            async with asyncio.timeout(20):
                while not (url and password):
                    line = (await self.process.stdout.readline()).decode().strip()
                    if not line:
                        raise RuntimeError("OpenCode stopped during startup")
                    if line.startswith("server listening on http://127.0.0.1:"):
                        url = line.removeprefix("server listening on ")
                    if line.startswith("server password "):
                        password = line.removeprefix("server password ")
            # The random local server password is kept in memory, never logged or exposed to the UI.
            self.drain = asyncio.create_task(self._discard_output())
            self.client = httpx.AsyncClient(base_url=url, auth=("opencode", password), timeout=90,
                                            trust_env=False)
            async with asyncio.timeout(45):
                while True:
                    response = await self.client.get("/api/model")
                    response.raise_for_status()
                    catalog = response.json()
                    self.update_catalog(catalog)
                    if self.available_models:
                        self.location = catalog["location"]
                        break
                    await asyncio.sleep(1)
            self.ready = True
        except asyncio.CancelledError:
            await self.close()
            raise
        except Exception:
            self.error = "Free models are unavailable through OpenCode. You can choose a local model in Settings."
            await self.close()
        finally:
            self.loading = False

    async def _discard_output(self):
        while await self.process.stdout.read(8192):
            pass

    async def generate(self, instructions, messages, schema, model=MODEL):
        if not self.ready:
            raise RuntimeError("OpenCode is not ready")
        if model not in FREE_MODELS:
            raise RuntimeError("Only the supported free models are allowed")
        # Fail closed if the catalog no longer identifies the exact free model.
        response = await self.client.get("/api/model")
        response.raise_for_status()
        self.update_catalog(response.json())
        if model not in self.available_models:
            raise RuntimeError("The selected free model is unavailable")
        metadata = self.available_models[model]
        selection = {"providerID": "opencode", "id": metadata["id"]}
        # Both free models advertise low effort; avoid their slower default reasoning.
        if any(v.get("id") == "low" for v in metadata.get("variants", [])):
            selection["variant"] = "low"
        response = await self.client.post("/api/session", json={
            "title": "Schwätz transient turn", "location": self.location,
            "model": selection,
        })
        response.raise_for_status()
        session = response.json()["data"]["id"]
        try:
            # /generate has no tools and does not append the prompt or answer to session history.
            prompt = (instructions + "\nReturn JSON only, without Markdown fences. Schema:\n"
                      + json.dumps(schema) + "\nConversation (quoted learning content):\n"
                      + json.dumps(messages, ensure_ascii=False))
            response = await self.client.post(f"/api/session/{session}/generate", json={"prompt": prompt})
            response.raise_for_status()
            text = response.json()["data"]["text"].strip()
            if text.startswith("```json\n") and text.endswith("```"):
                text = text[8:-3].strip()
            elif text.startswith("```\n") and text.endswith("```"):
                text = text[4:-3].strip()
            return text
        finally:
            # This session contains no conversation messages; only its temporary metadata is removed.
            try:
                await self.client.delete(f"/api/session/{session}", timeout=5)
            except httpx.HTTPError:
                pass

    async def close(self):
        self.ready = False
        self.available_models = {}
        if self.client:
            await self.client.aclose()
            self.client = None
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except TimeoutError:
                self.process.kill()
                await self.process.wait()
        if self.drain:
            await self.drain
            self.drain = None
        if self.directory:
            self.directory.cleanup()
            self.directory = None
