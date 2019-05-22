# coding:utf-8
import cv2
import numpy as np
import base64
from PIL import Image
from io import BytesIO
import redis
import time


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


if __name__ == '__main__':
    # 获取摄像头对象
    cap = cv2.VideoCapture(0)  # 0号摄像头，也可以1、2，lsusb查看

    # 使用函数 cap.get(propId) 来获得视频的一些参数信息
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获得码率
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),  # 获得尺寸
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    r = redis.Redis(host='127.0.0.1', port=6379)
    # if r.exists('stream_4'):
    #     r.delete('stream_4')
    if r.exists('stream_4'):
        pass
    else:
        r_temp = r.xadd('stream_4', {'jpeg': ''})
        r.xgroup_create('stream_4', 'group_1', id=0)
        red = r.xreadgroup('group_1', 'consumer_1', {'stream_4': ">"}, block=0, count=1)
        print('r_temp:', r_temp)
        r.xack('stream_4', 'group_1', *[r_temp])
        r.xdel('stream_4', *[r_temp])

    while cap.isOpened():  # 若初始化摄像头或者打开视频文件成功，isOpened()返回值是True，则表明成功，否则返回值是False
        ret, frame = cap.read()
        if ret:
            base64_data = frame2base64(frame)  # 读取视频帧，并给赋值
            # 写入redis
            clock1_1 = time.time()
            add_id = r.xadd('stream_4', {'jpeg': base64_data})
            clock1_2 = time.time()
            print('写入redis的时间：', clock1_2 - clock1_1)

        else:
            continue

    cap.release()
    cv2.destroyAllWindows()