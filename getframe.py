import gspread
from oauth2client.service_account import ServiceAccountCredentials
import argparse
import numpy as np
import subprocess
import shlex
import cv2


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

# 비양중 영상의 경우
# ss_array = np.ravel(ss_array)[1:-1].reshape(-1, 2)


count = 0
for i in ss_array:

    s_time, e_time = i

    count += 1

    ##### TODO 2 : choose output image file name #####
    command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -vf thumbnail=" + str(fps) + " 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/" + str(count) + "%03d.jpg'"
    # cpu 코어 수에 맞춰 멀티쓰레드 지정 (좀 더 빨라짐)
    # command = "ffmpeg -vsync 2 -ss " + s_time + " -to " + e_time +  " -i '" + input_path + "' -threads 6 -vf thumbnail=" + str(fps) + " 'C:/Users/Snucem_W1/Desktop/VideoToImage/output/변환후 img/" + str(count) + "%03d.jpg'"
    
    
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outs, errors = process.communicate()

    if process.returncode == 0:
        print('command : success')
    else:
        print('command : failed')
