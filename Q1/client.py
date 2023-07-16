# -- coding: utf-8 --

import io
import time
from PIL import Image
import asyncio
import websockets
import json

image_paths = ['test/Q1/images/horses.jpg'] * 10
websocket_url = "ws://localhost:8000/image"

async def send_image(image_paths):
    try:
        async with websockets.connect('ws://localhost:8000/image') as websocket:
            loop_time = time.time()
            for image_path in image_paths:
                byteImgIO = io.BytesIO()
                byteImg = Image.open(image_path)
                byteImg = byteImg.resize((1280, 720))
                byteImg.save(byteImgIO, "jpeg")
                byteImgIO.seek(0)
                image_data = byteImgIO.read()
                await websocket.send(image_data)
                result = await websocket.recv()
                result = json.loads(result)
                # print(result['result'])
            print('loop time :',(time.time() - loop_time))
    except websockets.exceptions.ConnectionClosedError:
        pass


asyncio.get_event_loop().run_until_complete(send_image(image_paths))

