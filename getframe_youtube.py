from pytube import YouTube
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import subprocess
import shlex
import cv2
import os
import re

# 유튜브 url(영상) 하나에 대해 생기는 클래스
class Youtube_to_image:
    def __init__(self, ss_array, output_path, url):
        self.ss_array = ss_array
        self.output_path = output_path
        self.url = url

    def youtube_download(self):
        download_folder = os.path.join(self.output_path, 'video')

        new_file = os.path.join(download_folder, self.url) + '.mp4'
        # 이미 영상이 존재하는 경우
        if os.path.exists(new_file):
            print(self.url + ' video file already exists')
            return new_file

        yt = YouTube('https://www.youtube.com/watch?v=' + self.url, use_oauth=True, allow_oauth_cache=True)

        try:
            video_name = yt.title

            # 영상 title 로컬에 저장되는 형식으로 변경
            video_name = re.sub(r'[#:;.,\<"|/>*?]', '', video_name)
            video_name = re.sub(r"[']", '', video_name)
            stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()
            stream.download(download_folder)

            # 영상 title url로 형식으로 변경
            old_file = os.path.join(download_folder, video_name) + '.mp4'
            os.rename(old_file, new_file)

        except Exception as e:
            print(e)
            return 0
        

        video_path = new_file
        print(self.url + ' video download : success')
        return video_path


    def oneframe_per_sec(self, input_path):
        video = cv2.VideoCapture(input_path)
        self.fps = video.get(cv2.CAP_PROP_FPS)
        self.input_path = input_path
        for idx, time in enumerate(self.ss_array):
            s_time, e_time = time
            if s_time == '':
                return
            command = f"ffmpeg -vsync 2 -ss {s_time} -to {e_time} -i '{self.input_path}' -vf thumbnail={self.fps} '{self.output_path}/image/O_{self.url}{idx+1}_%06d.jpg'"
            process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process.communicate()

            if process.returncode == 0:
                print(self.url + ' image download : success')
            else:
                print(self.url + ' image download : failed')
        

def main():
    # 추출된 이미지를 담을 output path 설정
    output_path = "C:/Users/Snucem_W1/Desktop/YoutubeToImage"
    
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

    worksheet = doc.worksheet('Youtube')
    # B, C, D열에 해당하는 정보만 가져오기
    array = np.array(worksheet.get_all_values()[2:])[:, 1:4]

    url_list = list(set(array[:, 0]))
    url_list.remove('')
    print('number of videos in table :', len(url_list))

    for url in url_list:
        # 해당 url에 대응하는 start, stop 표를 가져오기
        ss_array = array[array[:, 0] == url][:, 1:3]
        yt = Youtube_to_image(ss_array, output_path, url)
        video_path = yt.youtube_download()
        if video_path == 0:
            continue
        yt.oneframe_per_sec(video_path)
        print(url + ' complete')
    

if __name__ == "__main__":
    main()


