import argparse
import json

from poyto import PoytoClient


parser = argparse.ArgumentParser()
parser.add_argument("market_id")
args = parser.parse_args()

with PoytoClient.from_env() as client:
    snapshot = {
        "market": client.market(args.market_id),
        "positions": client.my_market_positions(args.market_id),
        "activity": client.market_activity(args.market_id),
    }

print(json.dumps(snapshot, ensure_ascii=False, indent=2))
