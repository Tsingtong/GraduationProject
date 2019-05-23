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


def getTimeStamp():
    t = int(round(time.time() * 1000))
    print('Saved video name:', t, '.mp4')
    return t


if __name__ == '__main__':
    r = redis.Redis(host='192.168.1.149', port=6379)
    w = redis.Redis(host='192.168.1.149', port=6380)

    while True:
        # acquire status
        while True:
            time.sleep(0.5)
            load_status = r.get('load_status')
            # 判断视频是拆帧完了，既load_status == 1
            if int(re.findall(r"'(.+?)'", str(load_status))[0]) == 1:
                while True:
                    num_loaded = r.get("num_loaded")
                    num_processed = r.get("num_processed")
                    # 判断视频是否处理完，既num_loaded == num_processed
                    if num_loaded == num_processed:
                        print('fuck yeah')
                        break
                    else:
                        print('waiting the job done!')
                        time.sleep(0.5)
                        continue
                break

        # concat video
        fps = r.get('fps')
        width = r.get('width')
        height = r.get('height')
        fps = int(re.findall(r"'(.+?).0", str(fps))[0])
        width = int(re.findall(r"'(.+?)'", str(width))[0])
        height = int(re.findall(r"'(.+?)'", str(height))[0])
        print(fps)

        # initiate video video writer
        time_stamp = getTimeStamp()
        size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        videowriter = cv2.VideoWriter('./outputs/'+str(time_stamp)+'.mp4', fourcc, fps, size)

        for i in range(int(re.findall(r"'(.+?)'", str(num_processed))[0])):
            b64_data = w.hget('stream_5', i+1)
            w.hdel('stream_5', i+1)
            data = readb64(b64_data)

            # save to disk
            videowriter.write(data)

        videowriter.release()
        print('Video Saved!:', './outputs/'+str(time_stamp)+'.mp4')

        # reset redis
        r.set('load_status', 0)
        r.set("num_loaded", 0)
        r.set("num_processed", 0)
        w.delete('stream_5')
