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

##### TODO 2 : choose output image file name #####
outputfilename = "/Users/haeun/Desktop/HODproject/HOD/Results/" + video_id 

# 해당 영상의 start time, stop time 저장
ss_array = array[array[:,1] == video_id][:, 2:4]
insert_column = [0] * ss_array.shape[0]
ss_array = np.c_[ss_array, insert_column]



# 1초에 하나씩 이미지 추출
def oneframe_per_sec(s_time, e_time, hanging):
    if hanging == True :
        command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -vf thumbnail=" + str(fps) + " '" + outputfilename + "/images_hangingO/O_C" + str(idx+1) + "_%06d.jpg'"
        
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.communicate()

        if process.returncode == 0:
            print('hanging C' + str(idx+1) + ' : success')
        else:
            print('hanging C' + str(idx+1) + ' : failed')
    else:
        if hanging == "before":
            command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -vf thumbnail=" + str(fps) + " '" + outputfilename + "/images_hangingX/X_C" + str(idx+1) + "A_%06d.jpg'"
            id, AB = idx+1, 'A'
        elif hanging == "after":
            command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -vf thumbnail=" + str(fps) + " '" + outputfilename + "/images_hangingX/X_C" + str(idx) + "B_%06d.jpg'"
            id, AB = idx, 'B'
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.communicate()

        if process.returncode == 0:
            print('nonhanging boundary C' + str(id) + AB + ' : success')
        else:
            print('nonhanging boundary C' + str(id) + AB + ' : failed')




# m초에 n개의 이미지 추출
def nframes_per_msecs(s_time, e_time, n, m):
    thumbnail_rate = m * fps / n
    command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -vf thumbnail=" + str(thumbnail_rate) + " '" + outputfilename + "/images_hangingX/X_C" + str(idx) + "C" + str(idx+1) + "_%06d.jpg'"
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process.communicate()

    if process.returncode == 0:
        print('nonhanging random C' + str(idx) + 'C' + str(idx+1) + ' : success')
    else:
        print('nonhanging random C' + str(idx) + 'C' + str(idx+1) + ' : failed')

def str_to_dt(s_time, e_time):
    s_time_dt = datetime.strptime(s_time, "%H:%M:%S")
    e_time_dt = datetime.strptime(e_time, "%H:%M:%S")
    return s_time_dt, e_time_dt

def dt_to_str(s_time_dt, e_time_dt):
    s_time = datetime.strftime(s_time_dt, "%H:%M:%S")
    e_time = datetime.strftime(e_time_dt, "%H:%M:%S")
    return s_time, e_time



# ---------------------------------------------------------
# 양중O 이미지프레임 추출

for idx, i in enumerate(ss_array):

    s_time, e_time = i[0], i[1]

    # 구간에서 추출된 frame 개수 저장
    s_time_dt, e_time_dt = str_to_dt(s_time, e_time)
    delta_dt = e_time_dt - s_time_dt
    delta_dt_sec = delta_dt.seconds
    ss_array[idx, 2] = delta_dt_sec


    oneframe_per_sec(s_time, e_time, True)

hanging_img_num = np.sum(ss_array[:, 2], dtype=np.uint32)
print("number of hanging images : ", hanging_img_num)



# ---------------------------------------------------------
# 주요 비양중 구간 추출 : 양중구간 앞뒤의 boundary에서 {boundary_frame_num}개 이미지프레임 추출

ss_array_nh = np.ravel(ss_array[:, :2])[:-1]
ss_array_nh = np.insert(ss_array_nh, 0, "00:00:00").reshape(-1, 2)
boundary_frame_num = 10
boundary_img_num = 0
zero_dt = datetime(1, 1, 1, 0, 0)

for idx, i in enumerate(ss_array_nh):
    s_time_dt, e_time_dt = str_to_dt(i[0], i[1])

    delta = timedelta(seconds=boundary_frame_num)

    # e_time으로부터 {boundary_frame_num}개 만큼 이미지를 뽑을 수 있는 경우 추출 : 'A'에 해당
    if s_time_dt < e_time_dt - delta:
        s_time, e_time = dt_to_str(e_time_dt - delta, e_time_dt)
        oneframe_per_sec(s_time, e_time, "before")
        boundary_img_num += boundary_frame_num
        e_time_dt -= delta
    else:
        oneframe_per_sec(i[0], i[1], "before")
        boundary_img_num += (e_time_dt - s_time_dt).seconds
        ss_array_nh[idx] = [zero_dt, zero_dt]
        continue

    # s_time으로부터 {boundary_frame_num}개 만큼 이미지를 뽑을 수 있는 경우 추출 : 'B'에 해당
    if s_time_dt + delta < e_time_dt:
        if idx == 0:
            ss_array_nh[idx] = [s_time_dt, e_time_dt]
            continue
        s_time, e_time = dt_to_str(s_time_dt, s_time_dt + delta)
        oneframe_per_sec(s_time, e_time, "after")
        boundary_img_num += boundary_frame_num
        s_time_dt += delta
    else:
        s_time, e_time = dt_to_str(s_time_dt, e_time_dt)
        oneframe_per_sec(s_time, e_time, "after")
        boundary_img_num += (e_time_dt - s_time_dt).seconds
        ss_array_nh[idx] = [zero_dt, zero_dt]
        continue
    
    # boundary에 포함되지 않은 구간 저장 : 랜덤 추출 대상 구간 설정
    ss_array_nh[idx] = [s_time_dt, e_time_dt]

print("number of boundary images : ", boundary_img_num)


# -------------------------------------------
# [양중구간 / 주요비양중구간] 제외한 구간에서의 랜덤 추출

hanging_img_num = hanging_img_num - boundary_img_num

ss_array_nh = ss_array_nh.astype(np.datetime64)
delta_sec_list = (ss_array_nh[:, 1] - ss_array_nh[:, 0]).astype(np.int64)
delta_sec_list_w = delta_sec_list/sum(delta_sec_list)
randomimg_num_list = (hanging_img_num * delta_sec_list_w).astype(np.int64)
ss_array_nh = ss_array_nh.astype('str')
for idx, dt64 in enumerate(ss_array_nh):
    if randomimg_num_list[idx]:
        s_time_dt64, e_time_dt64 = dt64
        nframes_per_msecs(s_time_dt64[-8:], e_time_dt64[-8:], randomimg_num_list[idx], delta_sec_list[idx])

print("number of random images : ", np.sum(randomimg_num_list))
