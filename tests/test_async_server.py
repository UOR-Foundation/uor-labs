import unittest
from unittest import mock
import asyncio

import assembler
import async_server


class AsyncServerTest(unittest.TestCase):
    def test_assemble(self):
        asm = "PUSH 1\nPRINT"
        req = async_server.AssembleRequest(text=asm)
        result = asyncio.run(async_server.assemble_route(req))
        self.assertEqual(result, {"chunks": assembler.assemble(asm)})

    def test_run_text(self):
        asm = "PUSH 2\nPRINT"
        req = async_server.RunRequest(text=asm)
        result = asyncio.run(async_server.run_route(req))
        self.assertEqual(result, {"output": "2"})

    def test_run_chunks(self):
        asm = "PUSH 3\nPRINT"
        chunks_list = assembler.assemble(asm)
        req = async_server.RunRequest(chunks=chunks_list)
        result = asyncio.run(async_server.run_route(req))
        self.assertEqual(result, {"output": "3"})

    def test_generate(self):
        req = async_server.GenerateRequest(prompt="hi", provider="openai")
        with (
            mock.patch(
                "uor.async_llm_client.async_call_model",
                new=mock.AsyncMock(return_value="PUSH 1\nPRINT"),
            ) as call,
            mock.patch(
                "uor.ipfs_storage.async_add_data",
                new=mock.AsyncMock(return_value="CID"),
            ) as add,
        ):
            result = asyncio.run(async_server.generate_route(req))
            self.assertEqual(result, {"cid": "CID"})
            call.assert_called_with("openai", "hi")
            add.assert_called()


if __name__ == "__main__":
    unittest.main()
