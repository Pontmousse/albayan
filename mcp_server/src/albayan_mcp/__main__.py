from __future__ import annotations

import argparse
import os

from albayan_mcp.server import create_server
from albayan_mcp.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="خادم MCP لمجلة البيان")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=settings.host)
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", str(settings.port))),
    )
    parser.add_argument("--streamable-http-path", default="/mcp")
    args = parser.parse_args()

    server = create_server()

    if args.transport == "stdio":
        server.run("stdio")
        return

    server.run(
        "streamable-http",
        host=args.host,
        port=args.port,
        streamable_http_path=args.streamable_http_path,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
