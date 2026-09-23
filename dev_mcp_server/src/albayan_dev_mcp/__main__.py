from __future__ import annotations

import argparse
import os

from albayan_dev_mcp.server import create_server
from albayan_dev_mcp.settings import Settings


def main() -> None:
    settings = Settings()
    parser = argparse.ArgumentParser(description="Al-Bayan developer-only MCP diagnostics")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=settings.dev_mcp_host)
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", str(settings.dev_mcp_port))),
    )
    parser.add_argument("--streamable-http-path", default="/mcp")
    args = parser.parse_args()

    server = create_server(settings)
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
