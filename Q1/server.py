# -- coding: utf-8 --

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from PIL import Image
import io
import os
import cv2
import random
import numpy as np
import time
import json
import onnxruntime as ort

app = FastAPI()

print('===================== START =========================')
cuda = True

# model_input_size = (640, 640)
model_input_size = (320, 320)

# model_path = "yolov7_640x640_fp32.onnx"
# model_path = "yolov7-tiny_640x640_fp32.onnx"

# model_path = "yolov7_320x320_int8.onnx"
model_path = "yolov7-tiny_320x320_int8.onnx"

providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
session = ort.InferenceSession(model_path, providers=providers)


def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleup=True, stride=32):
    shape = im.shape[:2] 
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:
        r = min(r, 1.0)

    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]

    if auto:
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)

    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return im, r, (dw, dh)

names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 
         'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 
         'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
         'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 
         'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
         'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 
         'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 
         'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 
         'hair drier', 'toothbrush']
colors = {name:[random.randint(0, 255) for _ in range(3)] for i,name in enumerate(names)}

################### 啟用GPU ###################
check_time = time.time()
image_path = 'images/horses.jpg'
image = Image.open(image_path)
image_array = np.array(image)
img = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

image = img.copy()
image, ratio, dwdh = letterbox(image, model_input_size, auto=False)
image = image.transpose((2, 0, 1))
image = np.expand_dims(image, 0)
image = np.ascontiguousarray(image)

im = image.astype(np.float32)
im /= 255

outname = [i.name for i in session.get_outputs()]
inname = [i.name for i in session.get_inputs()]

inp = {inname[0]:im}

outputs = session.run(outname, inp)[0]
print('啟動GPU花費時間 :',(time.time() - check_time))



@app.websocket("/image")
async def image(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            image_bytes = io.BytesIO(data)
            image = Image.open(image_bytes)
            image_array = np.array(image)

            img = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

            image = img.copy()
            image, ratio, dwdh = letterbox(image, model_input_size, auto=False)
            image = image.transpose((2, 0, 1))
            image = np.expand_dims(image, 0)
            image = np.ascontiguousarray(image)

            im = image.astype(np.float32)
            im /= 255

            outname = [i.name for i in session.get_outputs()]
            inname = [i.name for i in session.get_inputs()]
            inp = {inname[0]:im}

            outputs = session.run(outname, inp)[0]

            ori_images = [img.copy()]
            output_images = []
            detection_result = []

            for i,(batch_id,x0,y0,x1,y1,cls_id,score) in enumerate(outputs):
                box = np.array([x0,y0,x1,y1])
                box -= np.array(dwdh*2)
                box /= ratio
                box = box.round().astype(np.int32).tolist()
                cls_id = int(cls_id)
                score = round(float(score),3)
                name = names[cls_id]
                detection_result.append({'class': name, 'score': score, 'bbox': box}) 

            output_images.append(Image.fromarray(ori_images[0]))
            
            response_data = {
                'result': detection_result
            }
            await websocket.send_text(json.dumps(response_data))
    except:
        pass
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

