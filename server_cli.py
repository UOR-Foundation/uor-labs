from __future__ import annotations

import uvicorn
from async_server import app


def main(argv: list[str] | None = None) -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
