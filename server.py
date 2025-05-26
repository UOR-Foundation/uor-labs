from __future__ import annotations

from flask import Flask, jsonify, request

import assembler
import decoder
from vm import VM
from uor import async_llm_client, ipfs_storage

app = Flask(__name__)


@app.post('/assemble')
def assemble_route():
    data = request.get_json(force=True)
    text = data.get('text')
    if not isinstance(text, str):
        return jsonify({'error': 'text is required'}), 400
    program = assembler.assemble(text)
    return jsonify({'chunks': program})


@app.post('/run')
def run_route():
    data = request.get_json(force=True)
    if isinstance(data.get('text'), str):
        program = assembler.assemble(data['text'])
    elif isinstance(data.get('chunks'), list):
        try:
            program = [int(x) for x in data['chunks']]
        except Exception:  # pragma: no cover - invalid numbers
            return jsonify({'error': 'invalid chunks'}), 400
    else:
        return jsonify({'error': 'text or chunks required'}), 400
    vm = VM()
    output = ''.join(vm.execute(decoder.decode(program)))
    return jsonify({'output': output})


@app.post('/generate')
async def generate_route():
    data = request.get_json(force=True)
    prompt = data.get('prompt')
    if not isinstance(prompt, str):
        return jsonify({'error': 'prompt is required'}), 400
    provider = data.get('provider', 'openai')
    asm = await async_llm_client.async_call_model(provider, prompt)
    chunks_list = assembler.assemble(asm)
    data_bytes = '\n'.join(str(x) for x in chunks_list).encode('utf-8')
    cid = await ipfs_storage.async_add_data(data_bytes)
    return jsonify({'cid': cid})


def create_app() -> Flask:
    return app


if __name__ == '__main__':
    app.run()
