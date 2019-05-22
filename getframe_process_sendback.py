# coding:utf-8
import cv2
import numpy as np
import base64
from PIL import Image
from io import BytesIO
import redis
import time
import threading


frame01 = None
frame02 = None


def frame2base64(frame):
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))   # 将每一帧转为Image
    output_buffer = BytesIO()  # 创建一个BytesIO
    img.save(output_buffer, format='JPEG')  # 写入output_buffer
    byte_data = output_buffer.getvalue()  # 在内存中读取
    base64_data = base64.b64encode(byte_data)  # 转为BASE64
    return base64_data  # 转码成功 返回base64编码


def readb64(base64_string):
    sbuf = BytesIO()
    sbuf.write(base64.b64decode(base64_string))
    pimg = Image.open(sbuf)
    cv2img = cv2.cvtColor(np.asarray(pimg),cv2.COLOR_RGB2BGR)
    return cv2img


def get_frame(r):
    read_id = r.xreadgroup('group_1', 'consumer_1', {'stream_4': ">"}, block=0, count=1)
    base64_data_redis = read_id[0][1][0][1][b'jpeg']
    r.xack('stream_4', 'group_1', *[read_id[0][1][0][0]])
    r.xdel('stream_4', *[read_id[0][1][0][0]])
    data = readb64(base64_data_redis)  # 把二进制文件解码，并复制给data
    return data


def display_video():
    time.sleep(1)
    while True:
        frame001 = frame01
        frame002 = frame02
        cv2.imshow("frame001", frame01)  # 显示摄像头当前帧内容
        cv2.imshow("frame002", frame02)  # 显示摄像头当前帧内容
        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()


if __name__ == '__main__':
    r = redis.Redis(host='127.0.0.1', port=6379)
    while True:
        if r.exists('stream_4'):
            break
        else:
            time.sleep(0.5)
    while True:
        # get b64 data
        data = get_frame(r)

        # process
        cv2.imshow("data", data)  # 显示摄像头当前帧内容
        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # send back to stream


    cv2.destroyAllWindows()
