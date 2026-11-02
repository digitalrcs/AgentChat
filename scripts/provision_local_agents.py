"""Register two reusable perspectives using an explicitly selected local model."""
import argparse
import asyncio
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.local_llm import Runner
from app.store import Store

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--endpoint',required=True)
    parser.add_argument('--model',required=True)
    args=parser.parse_args()
    runner=Runner(Store())
    existing={p['name'] for p in runner.profiles()}
    for name,role in [
      ('Local investigator','Analyze the issue, distinguish evidence from assumptions, and propose a concrete next step.'),
      ('Local reviewer','Challenge unsupported claims, look for counterexamples, and identify verification steps. Build on useful prior messages.')]:
        if name not in existing:
            await runner.add(name,args.endpoint,args.model,role)
            print('Registered '+name)
        else: print('Already registered: '+name)
asyncio.run(main())
