import gspread
from oauth2client.service_account import ServiceAccountCredentials
import argparse
import numpy as np
import subprocess
import shlex
import cv2
from datetime import datetime, timedelta
import os

##실행예시: python getframe_v2.py -v "IP 카메라2_롯데 서초테라스힐_서초 테라스힐_20221203164659_20221203180811_337996298" -m X
##setting: input_path, output_path

def create_output_directories(output_path):
    # Define the subdirectory names
    hangingO_dir = os.path.join(output_path, "images_hangingO")
    hangingX_dir = os.path.join(output_path, "images_hangingX")
    labels_dir = os.path.join(output_path, "labels_hangingO")

    # Check if the directories already exist
    for dir_path in [hangingO_dir, hangingX_dir, labels_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

def str_to_dt(s_time, e_time):
    s_time_dt = datetime.strptime(s_time, "%H:%M:%S")
    e_time_dt = datetime.strptime(e_time, "%H:%M:%S")
    return s_time_dt, e_time_dt

def dt_to_str(s_time_dt, e_time_dt):
    s_time = datetime.strftime(s_time_dt, "%H:%M:%S")
    e_time = datetime.strftime(e_time_dt, "%H:%M:%S")
    return s_time, e_time

def count_files_in_directory(directory_path):
    return len([f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))])


class Video_to_image:
    def __init__(self, ss_array, input_path, output_path):
        
        video = cv2.VideoCapture(input_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        self.fps = fps
        self.ss_array = ss_array
        self.input_path = input_path
        self.output_path = output_path

    def oneframe_per_sec(self, idx, s_time, e_time, hanging):
        if hanging == True :
            command = f"ffmpeg -vsync 2 -ss {s_time} -to {e_time} -i '{self.input_path}' -vf thumbnail={self.fps} '{self.output_path}/images_hangingO/O_C{idx+1}_%06d.jpg'"
            
            process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process.communicate()

            if process.returncode == 0:
                print('hanging C' + str(idx+1) + ' : success')
            else:
                print('hanging C' + str(idx+1) + ' : failed')
        else:
            if hanging == "before":
                command = f"ffmpeg -vsync 2 -ss {s_time} -to {e_time} -i '{self.input_path}' -vf thumbnail={self.fps} '{self.output_path}/images_hangingX/X_C{idx+1}A_%06d.jpg'"
                id, AB = idx+1, 'A'
            elif hanging == "after":
                command = f"ffmpeg -vsync 2 -ss {s_time} -to {e_time} -i '{self.input_path}' -vf thumbnail={self.fps} '{self.output_path}/images_hangingX/X_C{idx+1}B_%06d.jpg'"
                id, AB = idx, 'B'
            process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process.communicate()

            if process.returncode == 0:
                print('nonhanging boundary C' + str(id) + AB + ' : success')
            else:
                print('nonhanging boundary C' + str(id) + AB + ' : failed')
        return

    # m초에 n개의 이미지 추출
    def nframes_per_msecs(self, idx, s_time, e_time, n, m):
        thumbnail_rate = m * self.fps / n
        command = f"ffmpeg -vsync 2 -ss {s_time} -to {e_time} -i '{self.input_path}' -vf thumbnail={thumbnail_rate} '{self.output_path}/images_hangingX/X_C{idx}C{idx+1}_%06d.jpg'"
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.communicate()

        if process.returncode == 0:
            print('nonhanging random C' + str(idx) + 'C' + str(idx+1) + ' : success')
        else:
            print('nonhanging random C' + str(idx) + 'C' + str(idx+1) + ' : failed')
        return

    def hangingO(self):
        for idx, i in enumerate(self.ss_array):
            s_time, e_time = i[0], i[1]

            s_time_dt, e_time_dt = str_to_dt(s_time, e_time)
            delta_dt = e_time_dt - s_time_dt
            delta_dt_sec = delta_dt.seconds
            self.ss_array[idx, 2] = delta_dt_sec

            self.oneframe_per_sec(idx, s_time, e_time, True)

        hanging_img_num = np.sum(self.ss_array[:, 2], dtype=np.uint32)
        print("number of hanging images : ", hanging_img_num)
        return hanging_img_num

    def hangingX(self, hanging_img_num):
        ss_array_nh = np.ravel(self.ss_array[:, :2])[:-1]
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
                self.oneframe_per_sec(idx, s_time, e_time, "before")
                boundary_img_num += boundary_frame_num
                e_time_dt -= delta
            else:
                self.oneframe_per_sec(idx, i[0], i[1], "before")
                boundary_img_num += (e_time_dt - s_time_dt).seconds
                ss_array_nh[idx] = [zero_dt, zero_dt]
                continue

            # s_time으로부터 {boundary_frame_num}개 만큼 이미지를 뽑을 수 있는 경우 추출 : 'B'에 해당
            if s_time_dt + delta < e_time_dt:
                if idx == 0:
                    ss_array_nh[idx] = [s_time_dt, e_time_dt]
                    continue
                s_time, e_time = dt_to_str(s_time_dt, s_time_dt + delta)
                self.oneframe_per_sec(idx, s_time, e_time, "after")
                boundary_img_num += boundary_frame_num
                s_time_dt += delta
            else:
                s_time, e_time = dt_to_str(s_time_dt, e_time_dt)
                self.oneframe_per_sec(idx, s_time, e_time, "after")
                boundary_img_num += (e_time_dt - s_time_dt).seconds
                ss_array_nh[idx] = [zero_dt, zero_dt]
                continue

            # boundary에 포함되지 않은 구간 저장 : 랜덤 추출 대상 구간 설정
            ss_array_nh[idx] = [s_time_dt, e_time_dt]

        print("number of boundary images : ", boundary_img_num)

        if hanging_img_num <= boundary_img_num:
            print("hanging image num(%s) < boundary image num(%s)"%(hanging_img_num, boundary_img_num))
        
        else:
            hanging_img_num = hanging_img_num - boundary_img_num

            ss_array_nh = ss_array_nh.astype(np.datetime64)
            delta_sec_list = (ss_array_nh[:, 1] - ss_array_nh[:, 0]).astype(np.int64)
            delta_sec_list_w = delta_sec_list/sum(delta_sec_list)
            randomimg_num_list = (hanging_img_num * delta_sec_list_w).astype(np.int64)
            ss_array_nh = ss_array_nh.astype('str')
            
            for idx, dt64 in enumerate(ss_array_nh):
                if randomimg_num_list[idx]:
                    s_time_dt64, e_time_dt64 = dt64
                    self.nframes_per_msecs(idx, s_time_dt64[-8:], e_time_dt64[-8:], randomimg_num_list[idx], delta_sec_list[idx])

            print("number of random images : ", np.sum(randomimg_num_list))
        return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--video_id', help='video id', required=True)
    parser.add_argument('-m', '--mode', help='hanging or not', default='all', required=False)
    args = vars(parser.parse_args())
    mode = args['mode']
    video_id = args['video_id']

    cam_num = video_id[6]
    input_path = 'C:/Users/SEPARK/Downloads/' + video_id + '.mp4' #동영상 파일 경로
    output_path = "G:/내 드라이브/1. Research/1. Subjects/3. Hanging Detection/Datasets/Labeling/Results/D%s/%s/"%(cam_num, video_id) #이미지 파일 경로
    print("cam_num: ", cam_num)
    print("input_path: ", input_path)
    print("output_path: ", output_path)
    
    create_output_directories(output_path)

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

    worksheet = doc.worksheet(f'D{cam_num}_labeling')
    array = np.array(worksheet.get_all_values()[2:])
    
    # 해당 영상의 start time, stop time 저장
    ss_array = array[array[:,1] == video_id][:, 2:4]
    insert_column = [0] * ss_array.shape[0]
    ss_array = np.c_[ss_array, insert_column]

    V1 = Video_to_image(ss_array, input_path, output_path)

    if mode == "O":
        V1.hangingO()
    elif mode == "X":
        hanging_img_num = count_files_in_directory(f'{output_path}/images_hangingO/')
        V1.hangingX(hanging_img_num)
    elif mode == "all":
        hanging_img_num = V1.hangingO()
        V1.hangingX(hanging_img_num)
    else:
        print("Wrong mode")

if __name__ == "__main__":
    main()
