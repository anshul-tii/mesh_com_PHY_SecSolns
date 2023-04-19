import asyncio
import nats
import json
import config

async def main():
    # Connect to NATS!
    nc = await nats.connect(f"{config.MODULE_IP}:{config.MODULE_PORT}")


    rep = await nc.request("comms.settings",
                           b"""{"api_version": 1,"ssid": "test_mesh","key": "1234567890","ap_mac": "00:11:22:33:44:55","country": "FI","frequency": "5220","ip": "192.168.1.2","subnet": "255.255.255.0","tx_power": "5","mode": "mesh"}""",
                           timeout=2)
    parameters = json.loads(rep.data)
    print(parameters)

    await nc.close()
    exit(0)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    loop.close()