import gspread
from oauth2client.service_account import ServiceAccountCredentials
import argparse
import numpy as np
import subprocess
import shlex
import cv2
from datetime import datetime, timedelta


# 명령어 관련
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='path to the input video', required=True)
args = vars(parser.parse_args())


# 구글 스프레드시트 연동
scope = [
'https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive',
]
json_file_name = 'sheetapi.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
gc = gspread.authorize(credentials)
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1oBu9HhFP1oQyHJTc-re3B7b56_fB-FEcA_cG3oW9Cng/edit?pli=1#gid=58112834'
# 스프레스시트 문서 가져오기 
doc = gc.open_by_url(spreadsheet_url)


##### TODO 1 : select worksheet #####
worksheet = doc.worksheet('D1_labeling')

array = np.array(worksheet.get_all_values()[2:])


# input으로부터 video id 구하기
input_path = args['input']
video = cv2.VideoCapture(input_path)
fps = video.get(cv2.CAP_PROP_FPS)
video_id = input_path[input_path.find('IP'):-4]


# 해당 영상의 start time, stop time 저장
ss_array = array[array[:,1] == video_id][:, 2:4]
insert_column = [0] * ss_array.shape[0]
ss_array = np.c_[ss_array, insert_column]



# 양중O 이미지프레임 추출

for idx, i in enumerate(ss_array):

    s_time, e_time = i[0], i[1]

    # 구간에서 추출된 frame 개수 저장
    s_time_dt = datetime.strptime(s_time, "%H:%M:%S")
    e_time_dt = datetime.strptime(e_time, "%H:%M:%S")
    delta_dt = e_time_dt - s_time_dt
    delta_dt_sec = delta_dt.seconds
    ss_array[idx, 2] = delta_dt_sec + 1


    ##### TODO 2 : choose output image file name #####
    command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -vf thumbnail=" + str(fps) + " '[output image 저장할 파일]/O_C" + str(idx+1) + "_%06d.jpg'"
    # cpu 코어 수에 맞춰 멀티쓰레드 지정 (좀 더 빨라짐)
    # command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -threads 6 -vf thumbnail=" + str(fps) + " 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/" + str(idx+1) + "%03d.jpg'"
    
    
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outs, errors = process.communicate()

    if process.returncode == 0:
        print('hanging command : success')
    else:
        print('hanging command : failed')


hanging_img_num = np.sum(ss_array[:, 2], dtype=np.uint32)
print("number of hanging images : ", hanging_img_num)


# 양중X 이미지프레임 추출
# 비양중용 array
ss_array_nh = np.ravel(ss_array[:, :2])[:-1]
ss_array_nh = np.insert(ss_array_nh, 0, "00:00:00").reshape(-1, 2)

ss_array_numframe = np.insert(ss_array[:, 2].astype(np.uint32), 0, 0)
L = len(ss_array_numframe)
for i in range(L-1, 0, -1):
    ss_array_numframe[i] = np.floor((ss_array_numframe[i] + ss_array_numframe[i-1]) / 2)    # 내림 : 양중 image중에서 제외되는 것들 있을 수 있기 때문에

# ss_array_nh 각 row에 대한 구간 시간 구하기
delta_dt_list = []
for i, j in ss_array_nh:
    delta_dt_list.append((datetime.strptime(j, "%H:%M:%S") - datetime.strptime(i, "%H:%M:%S")).seconds)

# ss_array_nh = [시작시간, 끝시간, 구간 시간(sec), 추출frame개수]
ss_array_numframe = ss_array_numframe[1:]
ss_array_nh = np.c_[ss_array_nh, np.array(delta_dt_list), ss_array_numframe]

for idx, (s_time, e_time, delta_sec, numframe) in enumerate(ss_array_nh):
    delta_sec, numframe = map(int, (delta_sec, numframe))
    delta_frame = delta_sec * fps / numframe   # 추출 frame 간격

    if delta_frame <= 150:
        ##### TODO 2 : choose output image file name #####
        command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -threads 6 -vf thumbnail=" + str(delta_frame) + " 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/X_C" + str(idx) + str(idx+1) + "_%06d.jpg'"
        # cpu 코어 수에 맞춰 멀티쓰레드 지정 (좀 더 빨라짐)
        # command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -threads 6 -vf thumbnail=" + str(fps) + " 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/" + str(idx+1) + "%03d.jpg'"
        
        
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        outs, errors = process.communicate()

    else:
        delta_sec_num = np.floor(delta_sec / numframe)
        s_time_dt = datetime.strptime(s_time, "%H:%M:%S")
        for i in range(numframe):
            s_time_dt += timedelta(seconds=delta_sec_num)
            s_time = datetime.strftime(s_time_dt, "%H:%M:%S")

            ##### TODO 2 : choose output image file name #####
            command = "ffmpeg -ss " + s_time + " -i '" + input_path + "' -frames:v 1 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/X_C" + str(idx) + str(idx+1) + "_" + str(i+1).zfill(6) + ".jpg'"
            # cpu 코어 수에 맞춰 멀티쓰레드 지정 (좀 더 빨라짐)
            # command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -threads 6 -vf thumbnail=" + str(fps) + " 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/" + str(idx+1) + "%03d.jpg'"
            
            
            process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            outs, errors = process.communicate()

            if process.returncode == 0:
                print('nonhanging command : success')
            else:
                print('nonhanging command : failed')



nonhanging_img_num = np.sum(ss_array_numframe)
print("number of nonhanging images : ", nonhanging_img_num)