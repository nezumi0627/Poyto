from poyto import PoytoClient

with PoytoClient() as client:
    print(client.profile())
    for market in client.iter_markets(limit=20):
        print(market.get("id"), market.get("title"))
