import cv2
import argparse
import numpy as np

# argument
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='path to the input video', required=True)
parser.add_argument('-st', '--starttime', type=str, default='00:00:00')
parser.add_argument('-et', '--endtime', type=str, default='00:00:00')
args = vars(parser.parse_args())

webcam = cv2.VideoCapture(args['input'])
fps = webcam.get(cv2.CAP_PROP_FPS)

# start time, end time 설정
s_time = args['starttime']
e_time = args['endtime']

s_hour, e_hour = int(s_time[:2]), int(e_time[:2])
s_min, e_min = int(s_time[3:5]), int(e_time[3:5])
s_sec, e_sec = int(s_time[6:8]), int(e_time[6:8])

s_total_sec = s_hour * 3600 + s_min * 60 + s_sec
e_total_sec = e_hour * 3600 + e_min * 60 + e_sec

s_total_frame = s_total_sec * fps
e_total_frame = e_total_sec * fps

# start time으로 frame set
webcam.set(cv2.CAP_PROP_POS_FRAMES, s_total_frame)

# CSRT trackers로 지정
# 이 부분 바꿔서 다른 tracker 사용 가능
trackerName = 'CSRT'
tracker = cv2.TrackerCSRT_create()


while True:
    status, img = webcam.read()
    if status:
        cv2.imshow('Tracking', img)

        # 'y' 입력 시 재생 멈추고 ROI 선택 가능
        if cv2.waitKey(3) & 0xff == ord('y'):
            bbox = cv2.selectROI('Tracking', img, False)
            break
        

# tracker 초기화
tracker.init(img, bbox)
color = np.random.uniform(0, 255, size=(1, 3))[0]

def drawBox(img, bbox, line, color):
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    cv2.rectangle(img, (x, y), ((x+w), (y+h)), color, 3, 1)
    cv2.putText(img, trackerName, line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

# end time까지만 영상 출력
while True and webcam.get(cv2.CAP_PROP_POS_FRAMES) < e_total_frame:
    status, img = webcam.read()
    status, bbox = tracker.update(img)

    if status:
        drawBox(img, bbox, (20, 50), color)
    cv2.imshow('Tracking', img)

    if cv2.waitKey(1) & 0xff == ord('q'):
        break

webcam.release()
cv2.destroyAllWindows()