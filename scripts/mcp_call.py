"""Call an AgentChat MCP tool from a terminal using an existing identity file."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

async def main():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity-file', type=Path, required=True)
    parser.add_argument('--tool', required=True)
    parser.add_argument('--arguments-file', type=Path)
    args = parser.parse_args()
    payload = json.loads(args.arguments_file.read_text(encoding='utf-8-sig')) if args.arguments_file else {}
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT/'run.py'), 'mcp', '--identity-file', str(args.identity_file.resolve())])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool(args.tool, payload)
            for block in result.content:
                if block.type == 'text': print(block.text)
            if result.isError: raise SystemExit(1)

if __name__ == '__main__': asyncio.run(main())
