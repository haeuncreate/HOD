from pytube import YouTube
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import subprocess
import shlex
import cv2
import os
import re

# 유튜브 영상 하나 당 생기는 클래스
class Youtube_to_image:
    def __init__(self, ss_array, output_path, url):
        self.ss_array = ss_array
        self.output_path = output_path
        self.url = url

    def youtube_download(self):
        download_folder = os.path.join(self.output_path, 'video')
        yt = YouTube('https://www.youtube.com/watch?v=' + self.url, use_oauth=True, allow_oauth_cache=True)
        try:
            video_name = yt.title
        except Exception as e:
            print(e)
            return 0
        
        video_name = re.sub(r'[#:;.,\<"|/>*?]', '', video_name)
        video_name = re.sub(r"[']", '', video_name)

        try:
            stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()
        except Exception as e:
            print(e)
            return 0
        
        try:
            stream.download(download_folder)
        except Exception as e:
            print(e)
            return 0
        
        dir = download_folder
        old_file = os.path.join(dir, video_name) + '.mp4'
        print(video_name)
        new_file = os.path.join(dir, self.url) + '.mp4'
        
        try:
            os.rename(old_file, new_file)
        except Exception as e:
            print(e)
            return 0

        video_path = new_file
        print(self.url + ' image download : success')
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
                print(self.url + ' : success')
            else:
                print(self.url + ' : failed')
        

def main():
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
    array = np.array(worksheet.get_all_values()[2:])[:, 1:4]

    url_list = list(set(array[:, 0]))
    print(len(url_list))
    url_list.remove('')

    for url in url_list:
        ss_array = array[array[:, 0] == url][:, 1:3]
        yt = Youtube_to_image(ss_array, output_path, url)
        video_path = yt.youtube_download()
        if video_path == 0:
            continue
        yt.oneframe_per_sec(video_path)
        print(url + ' complete')
    

if __name__ == "__main__":
    main()


