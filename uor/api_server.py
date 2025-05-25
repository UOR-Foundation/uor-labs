"""HTTP API server for generating and running programs."""
from __future__ import annotations

from typing import Any

import assembler
from decoder import decode
from vm import VM
from . import llm_client, ipfs_storage


def create_app() -> "Flask":
    try:
        from flask import Flask, request, jsonify
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Flask is not installed") from exc

    app = Flask(__name__)

    @app.after_request
    def add_cors(resp):
        resp.headers.setdefault("Access-Control-Allow-Origin", "*")
        return resp

    @app.post("/generate")
    def generate() -> Any:
        data = request.get_json(force=True)
        provider = data.get("provider")
        prompt = data.get("prompt")
        if not provider or not prompt:
            return jsonify({"error": "provider and prompt required"}), 400
        try:
            asm = llm_client.call_model(provider, prompt)
            program = assembler.assemble(asm)
            cid = ipfs_storage.add_data("\n".join(str(x) for x in program).encode("utf-8"))
            return jsonify({"cid": cid})
        except Exception as exc:  # pragma: no cover - unexpected errors
            return jsonify({"error": str(exc)}), 500

    @app.get("/run/<cid>")
    def run(cid: str) -> Any:
        try:
            data = ipfs_storage.get_data(cid)
            program = [int(x) for x in data.decode("utf-8").split() if x]
            output = "".join(VM().execute(decode(program)))
            return jsonify({"output": output})
        except Exception as exc:  # pragma: no cover - unexpected errors
            return jsonify({"error": str(exc)}), 500

    return app
