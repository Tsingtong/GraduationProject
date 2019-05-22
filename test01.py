import threading
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
from aip import AipFace
import random
import face_recognition
import requests


frame_of_stream = None
camera_open = False

g_names = []

UserList = {
    '1': '聂辰席',
    '2': '高建民',
    '3': '范卫平',
    '4': '张宏森',
    '5': '郭沛宇',
    '6': '王磊',
    '7': '薛子育',
    '8': '刘庆同',
}


def basic_info(Res):
    print(
        '-------------------------------------------------------- log -------------------------------------------------'
        '-------')
    if 'error_msg' in Res:
        pass
    else:
        print('log id:', Res['log_id'])
        print('Number of people:', Res['result_num'])


def paint_chinese_opencv(im, chinese, pos, color):

    img_PIL = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    font = ImageFont.truetype('/home/gky/.local/share/fonts/SimHei.ttf', 27)
    fillColor = color #(255,0,0)
    position = pos #(100,100)

    # fillColor = (255,0,0)
    # position = (100,100)
    # chinese.decode('utf-8')
    draw = ImageDraw.Draw(img_PIL)
    draw.text(position, chinese, font=font, fill=fillColor)

    img = cv2.cvtColor(np.asarray(img_PIL),cv2.COLOR_RGB2BGR)

    return img


class RtspStreamThread(threading.Thread):
    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def run(self):
        cap = cv2.VideoCapture(self.device_id)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

        global frame_of_stream, camera_open
        while True:
            ret, frame = cap.read()
            if ret:
                frame_of_stream = frame
                camera_open = True
            else:
                camera_open = False
                print('error')


class ProcessThread(threading.Thread):
    def __init__(self, face_score_threshold):
        super().__init__()
        self.options = {
            "ext_fields": "faceliveness",
            "detect_top_num": 10,  # 检测多少个人脸进行比对，默认值1（最对返回10个）
            "user_top_num": 1  # 返回识别结果top人数”当同一个人有多张图片时，只返回比对最高的1个分数
        }
        self.Group_Id = "CCBN"
        self.client = call_aip()
        self.face_score_threshold = face_score_threshold * 100
        self.names = []

    def parse_results(self):
        print(basic_info(self.Res))
        if 'error_msg' in self.Res:
            print('error_msg:' + self.Res['error_msg'])
            self.names = []
        else:
            # clear self.names
            self.names = []
            # print result for each person
            for i in range(self.Res['result_num']):
                uid = self.Res['result'][i]['uid']
                info = str(str(self.Res['result'][i]['uid']) + "," + str(
                    self.Res['result'][i]['group_id']) + "," + str(
                    self.Res['result'][i]['scores'][0]))
                if self.Res['result'][i]['scores'][0] >= self.face_score_threshold:
                    self.names.append(UserList[self.Res['result'][i]['uid']])
                    print('scores:', self.Res['result'][i]['scores'][0])
                print('User:' + UserList[self.Res['result'][i]['uid']] + '    '
                      + 'Probability:' + str(self.Res['result'][i]['scores'][0]))

    def query_baidu(self):
        # Use Baidu API to find the best matches for the test face

        # # Find all the faces and query Baidu in the current frame of video
        # small_frame = cv2.resize(self.frame, (0, 0), fx=0.25, fy=0.25)
        # # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        # rgb_small_frame = small_frame[:, :, ::-1]

        rgb_small_frame = self.frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_small_frame, model='cnn')

        if len(face_locations) == 0:
            self.names = []
            return
        else:
            cv2.imwrite('face.jpg', self.frame)
            with open("face.jpg", 'rb') as fp:
                image = fp.read()
            self.Res = self.client.multiIdentify(self.Group_Id, image, self.options)
            self.parse_results()
            # print(self.Res)

    def run(self):
        # Initialize some variables
        save_pic_count = 0
        face_locations = []
        face_encodings = []
        face_names = []
        global frame_of_stream, camera_open, g_names

        process_this_frame = True

        while not camera_open:
            time.sleep(random.uniform(0.1, 0.2))

        while True:
            self.frame = frame_of_stream

            # Only process every other frame of video to save time
            if process_this_frame:
                time.sleep(random.uniform(0.1, 0.2))
                self.query_baidu()
                g_names = self.names

            process_this_frame = not process_this_frame


def draw_rectangle(frame, face_locations, names):
    font = cv2.FONT_HERSHEY_SIMPLEX
    # Display result
    for top, right, bottom, left in face_locations:
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 1
        right *= 1
        bottom *= 1
        left *= 1

        # Draw a box around the face
        # (0, 255, 0) B G R
        cv2.rectangle(frame, (left, top), (right, bottom), (147, 20, 255), 4)

        # Draw a label with a name below the face
        text = 'Person'
        cv2.rectangle(frame, (left, bottom - 15), (right, bottom), (147, 20, 255), cv2.FILLED)
        cv2.putText(frame, text, (left + 6, bottom - 3), font, 0.5, (255, 255, 255), 1)
        # cv2.putText(frame, text, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1)

    # Display names
    left = 100
    bottom = 100
    top = 100
    right = 300
    draw_count = 0

    for draw_count, name in enumerate(names):
        if draw_count <= 6:
            bottom = bottom + draw_count * 70
            cv2.rectangle(frame, (left, bottom + 37), (right, bottom + 35), (147, 20, 255), cv2.FILLED)
            # cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            frame = paint_chinese_opencv(im=frame, chinese=name, pos=(left + 5, bottom - 0), color=(102, 129, 181))
        else:
            left = 100 + 300
            right = 300 + 300

            bottom = bottom + draw_count % 6 * 70

            cv2.rectangle(frame, (left, bottom + 37), (right, bottom + 35), (147, 20, 255), cv2.FILLED)
            # cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            frame = paint_chinese_opencv(im=frame, chinese=name, pos=(left + 5, bottom - 0), color=(102, 129, 181))

    # for name in names:
    #     bottom = bottom + draw_count * 70
    #     cv2.rectangle(frame, (left, bottom + 37), (right, bottom + 35), (147, 20, 255), cv2.FILLED)
    #     # cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
    #     frame = paint_chinese_opencv(im=frame, chinese=name, pos=(left + 5, bottom - 0), color=(255, 255, 255))
    #
    #     draw_count += 1

    return frame


def display_video():
    license_status = getLicenseStatus()

    cv2.namedWindow('FaceRecognition', 0)
    cv2.setWindowProperty('FaceRecognition', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if license_status == 0:
        print('Permission Verification Passed')
        loop_count = 0
        while True:
            if loop_count <= 300:
                if camera_open:
                    frame = frame_of_stream

                    # detect face
                    # small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    # rgb_small_frame = small_frame[:, :, ::-1]
                    rgb_small_frame = frame[:, :, ::-1]
                    face_locations = face_recognition.face_locations(rgb_small_frame, model='cnn')

                    # Draw Info
                    font = cv2.FONT_HERSHEY_DUPLEX
                    # cv2.putText(frame, 'Identified Students:', (160, 100), font, 3, (3, 168, 158), 2)
                    # cv2.putText(frame, 'Student Attendance System', (990, 630), font, 0.625, (255, 255, 255), 1)
                    # cv2.putText(frame, 'Alpha: v1.1.0 (Haw)', (990, 660), font, 0.625, (255, 255, 255), 1)
                    # cv2.putText(frame, 'Positioning Mode : HOG', (990, 690), font, 0.625, (255, 255, 255), 1)
                    # cv2.putText(frame, '@author:liuqingtong', (540, 700), font, 0.5, (255, 255, 255), 1)
                    # cv2.putText(frame, '@email:1504030521@st.btbu.edu.cn', (480, 715), font, 0.5, (255, 255, 255), 1)

                    frame = draw_rectangle(frame=frame, face_locations=face_locations, names=g_names)
                    # Display the resulting image
                    cv2.imshow('FaceRecognition', frame)

                # Hit 'q' on the keyboard to quit!
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                loop_count += 1
            else:
                license_status = getLicenseStatus()
                if license_status != 0:
                    print('License Expired!')
                    cv2.destroyAllWindows()
                    while True:
                        if camera_open:
                            frame = frame_of_stream
                            font = cv2.FONT_HERSHEY_DUPLEX
                            cv2.rectangle(frame, (250, 400 + 30), (270 + 800, 400 - 80), (0, 0, 255), cv2.FILLED)
                            cv2.putText(frame, 'License Expired!', (260, 400), font, 3, (255, 255, 255), 2)
                            cv2.imshow('FaceRecognition', frame)

                            # Hit 'q' on the keyboard to quit!
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    cv2.destroyAllWindows()
                    break
                else:
                    print('Permission Verification Passed')
                    loop_count = 0

        # Release handle to the webcam
        cv2.destroyAllWindows()
    else:
        print('License Expired!')
        while True:
            if camera_open:
                frame = frame_of_stream
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.rectangle(frame, (250, 400 + 30), (270 + 800, 400 - 80), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, 'License Expired!', (260, 400), font, 3, (255, 255, 255), 2)
                cv2.imshow('FaceRecognition', frame)

                # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

                # Release handle to the webcam
        cv2.destroyAllWindows()


def call_aip():
    APP_ID = '15791102'
    API_KEY = "DahTjTGtfwSGZk14IFa1fVt6"
    SECRET_KEY = "VGrWHnntBlKXzFtS8CfGhNtBPLw1CGbs"
    aip_client = AipFace(APP_ID, API_KEY, SECRET_KEY)
    return aip_client


def getLicenseStatus():
    url = 'http://liuqingtong.com:8000/AcquireDRMLicense/'
    username = 'gky'
    data = {
        'ClientInfo': username,
    }
    r = requests.post(url, data=data)
    return int(r.text[-2])


def webcam(device_id):
    rtsp_thread = RtspStreamThread(device_id=device_id)
    frame_process_thread = ProcessThread(face_score_threshold=0.8)

    rtsp_thread.setDaemon(True)
    frame_process_thread.setDaemon(True)

    rtsp_thread.start()
    frame_process_thread.start()

    display_video()


if __name__ == '__main__':
    webcam(0)

