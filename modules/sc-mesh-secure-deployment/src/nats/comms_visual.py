"""
mesh visualization publisher
"""
import threading
import asyncio
import signal
import ssl
import argparse
from nats.aio.client import Client as NATS

from visualisation.batstat import Batman
from visualisation.batadvvis import BatAdvVis


class MeshTelemetry:
    """
    Mesh network executor
    """

    def __init__(self):
        self.t1 = None
        self.t2 = None
        self.batman_visual = BatAdvVis()
        self.batman = Batman()
        self.runner = True

    def mesh_visual(self):
        return f"[{self.batman_visual.latest_topology}," \
               f"{self.batman.latest_stat}]". \
            replace(": ", ":"). \
            replace(", ", ",")

    async def run(self):
        """
        Run method for e

        :return: never
        """
        self.t1 = threading.Thread(target=self.batman_visual.run)
        self.t1.start()
        self.t2 = threading.Thread(target=self.batman.run)
        self.t2.start()

    async def stop(self):
        self.batman_visual.thread_running = False
        self.t1.join()
        self.batman.thread_running = False
        self.t2.join()


async def main(server, port, keyfile=None, certfile=None, interval=1):
    """
    main
    """
    mesh_telemetry = MeshTelemetry()
    await mesh_telemetry.run()

    nc = NATS()

    async def stop():
        await asyncio.sleep(1)
        asyncio.get_running_loop().stop()

    def signal_handler():
        if nc.is_closed:
            return
        print("Disconnecting...")
        asyncio.create_task(nc.close())
        asyncio.create_task(stop())

    for sig in ('SIGINT', 'SIGTERM'):
        asyncio.get_running_loop().add_signal_handler(getattr(signal, sig),
                                                      signal_handler)

    async def disconnected_cb():
        print("Got disconnected...")

    async def reconnected_cb():
        print("Got reconnected...")

    # Create SSL context if certfile and keyfile are provided
    ssl_context = None
    if certfile and keyfile:
        ssl_context = ssl.create_default_context()
        ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # Connect to NATS server with TLS enabled if ssl_context is provided
    if ssl_context:
        await nc.connect(f"tls://"+str(server)+":"+str(port),
                         tls=ssl_context,
                         reconnected_cb=reconnected_cb,
                         disconnected_cb=disconnected_cb,
                         max_reconnect_attempts=-1)
    else:
        await nc.connect(f"nats://"+str(server)+":"+str(port),
                         reconnected_cb=reconnected_cb,
                         disconnected_cb=disconnected_cb,
                         max_reconnect_attempts=-1)

    print("Publisher loop...")
    while True:
        await asyncio.sleep(interval)
        try:
            await nc.publish("comms.visual",
                             mesh_telemetry.mesh_visual().encode())
        except Exception as e:
            print("Error:", e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mesh Settings')
    parser.add_argument('-s', '--server', help='Server IP', required=True)
    parser.add_argument('-p', '--port', help='Server port', required=True)
    parser.add_argument('-k', '--keyfile', help='TLS keyfile', required=False)
    parser.add_argument('-c', '--certfile', help='TLS certfile', required=False)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(args.server, args.port,
                                     args.keyfile, args.certfile))
        loop.run_forever()
        loop.close()
    except:
        pass
