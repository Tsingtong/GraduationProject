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


class ReadStreamThread01(threading.Thread):
    def __init__(self, redis_conn):
        super().__init__()
        self.r = redis_conn

    def run(self):
        while True:  # 若初始化摄像头或者打开视频文件成功，isOpened()返回值是True，则表明成功，否则返回值是False
            global frame01
            # 从redis读data
            read_id = self.r.xreadgroup('group_1', 'consumer_1', {'stream_4': ">"}, block=0, count=1)
            base64_data_redis = read_id[0][1][0][1][b'jpeg']
            self.r.xack('stream_4', 'group_1', *[read_id[0][1][0][0]])
            self.r.xdel('stream_4', *[read_id[0][1][0][0]])
            data = readb64(base64_data_redis)  # 把二进制文件解码，并复制给data

            frame01 = data

            # print(self.r.xlen('stream_4'))
            print('frame01_read!')


class ReadStreamThread02(threading.Thread):
    def __init__(self, redis_conn):
        super().__init__()
        self.r = redis_conn

    def run(self):
        while True:  # 若初始化摄像头或者打开视频文件成功，isOpened()返回值是True，则表明成功，否则返回值是False
            global frame02
            # 从redis读data
            read_id = self.r.xreadgroup('group_1', 'consumer_1', {'stream_4': ">"}, block=0, count=1)
            base64_data_redis = read_id[0][1][0][1][b'jpeg']
            self.r.xack('stream_4', 'group_1', *[read_id[0][1][0][0]])
            self.r.xdel('stream_4', *[read_id[0][1][0][0]])
            data = readb64(base64_data_redis)  # 把二进制文件解码，并复制给data

            frame02 = data

            # print(self.r.xlen('stream_4'))
            print('frame02_read!')


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

    thread01 = ReadStreamThread01(redis_conn=r)
    thread02 = ReadStreamThread02(redis_conn=r)

    thread01.setDaemon(True)
    thread02.setDaemon(True)

    thread01.start()
    thread02.start()

    display_video()
