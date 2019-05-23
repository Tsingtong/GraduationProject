# coding:utf-8
import cv2
import numpy as np
import base64
from PIL import Image
from io import BytesIO
import redis
import time
import re


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
    frame_id = int(re.findall(r"'(.+?)-", str(read_id[0][1][0][0]))[0])
    return data, frame_id


def draw_on_frame(data):
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(data, 'License Expired!', (10, 60), font, 3, (255, 255, 255), 2)
    return data


def check_stream_5():
    if w.exists('stream_5'):
        print('stream_5 exists')
        w.delete('stream_5')
        print('stream_5 deleted')


if __name__ == '__main__':
    r = redis.Redis(host='192.168.1.149', port=6379)
    w = redis.Redis(host='192.168.1.149', port=6380)
    while True:
        if r.exists('stream_4'):
            break
        else:
            time.sleep(0.5)

    check_stream_5()

    while True:
        # get b64 data
        try:
            data, frame_id = get_frame(r)
        except redis.exceptions.ResponseError:
            check_stream_5()
            continue
        else:
            print('processing : ', frame_id)
            r.incr('num_processed')

            # process
            data = draw_on_frame(data)
            # set back
            base64_data = frame2base64(data)  # 读取视频帧，并给赋值

            # send back to stream
            w.hset("stream_5", frame_id, base64_data)

