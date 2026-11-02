"""Explicit live smoke test using synthetic text in an isolated database."""
import asyncio
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.store import Store,ROOT
from app.local_llm import Runner

async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint',required=True,help='Approved local LM Studio base URL ending in /v1')
    parser.add_argument('--model',required=True,help='Exact chat model ID selected by the operator')
    args=parser.parse_args()
    store=Store(ROOT/'data'/'inference-verification.sqlite3')
    runner=Runner(store)
    profiles=runner.profiles()
    if not profiles:
        for name,role in [('Local investigator','Suggest one simple way to verify a toy calculator function.'),('Local reviewer','Review the preceding suggestion and identify one missing edge case.')]:
            await runner.add(name,args.endpoint,args.model,role)
        profiles=runner.profiles()
    room=store.create_conversation('Synthetic local-model smoke test','Discuss testing a pure function that adds two integers. Do not execute code. Keep each answer under 60 words.')
    await runner.start(room['id'],[p['participant_id'] for p in profiles],2)
    print('Local two-agent run started',flush=True)
    await runner.task
    status=runner.status(room['id'])
    print(status,flush=True)
    assert status['status']=='completed',status
    assert store.stats(room['id'])['total_messages']==2
    print('Verified two named local agents exchanging durable messages.',flush=True)
asyncio.run(main())
