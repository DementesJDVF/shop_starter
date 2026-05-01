import asyncio
import random
from channels.layers import get_channel_layer

async def simulate():
    channel_layer = get_channel_layer()
    lat, lng = 2.44, -76.61  # tu zona

    while True:
        lat += random.uniform(-0.0003, 0.0003)
        lng += random.uniform(-0.0003, 0.0003)

        await channel_layer.group_send("tracking", {
            "type": "send_location",
            "lat": lat,
            "lng": lng
        })

        await asyncio.sleep(1)