from __future__ import annotations

from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import assembler
import decoder
from vm import VM
from uor import async_llm_client, ipfs_storage

app = FastAPI()


class AssembleRequest(BaseModel):
    text: str


class RunRequest(BaseModel):
    text: Optional[str] = None
    chunks: Optional[List[int]] = None


class GenerateRequest(BaseModel):
    prompt: str
    provider: str = "openai"


@app.post("/assemble")
async def assemble_route(req: AssembleRequest):
    program = assembler.assemble(req.text)
    return {"chunks": program}


@app.post("/run")
async def run_route(req: RunRequest):
    if isinstance(req.text, str):
        program = assembler.assemble(req.text)
    elif isinstance(req.chunks, list):
        try:
            program = [int(x) for x in req.chunks]
        except Exception:
            raise HTTPException(status_code=400, detail="invalid chunks")
    else:
        raise HTTPException(status_code=400, detail="text or chunks required")
    vm = VM()
    output = "".join(vm.execute(decoder.decode(program)))
    return {"output": output}


@app.post("/generate")
async def generate_route(req: GenerateRequest):
    asm = await async_llm_client.async_call_model(req.provider, req.prompt)
    chunks_list = assembler.assemble(asm)
    data_bytes = "\n".join(str(x) for x in chunks_list).encode("utf-8")
    cid = await ipfs_storage.async_add_data(data_bytes)
    return {"cid": cid}


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
