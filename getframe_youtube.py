from pytube import YouTube
import cv2
import os
import re
import pandas as pd
from datetime import datetime, timedelta

# Input Configuration
output_video_folder_path = "./video"
output_image_folder_path = "./image"
excel_file_path = "./data_youtube_hanging.xlsx" # Path to the Excel file containing video information
frame_interval = 3

class YouTubeToImage:
    def __init__(self, video_time_segments, output_video_folder_path, output_image_folder_path, frame_interval, url):
        self.video_time_segments = video_time_segments
        self.output_video_folder_path = output_video_folder_path  
        self.output_image_folder_path = output_image_folder_path
        self.frame_interval = frame_interval
        self.url = url

        # Ensure the output folders exist or create them
        os.makedirs(self.output_video_folder_path, exist_ok=True)
        os.makedirs(self.output_image_folder_path, exist_ok=True)

    def download_video(self):
        video_path_by_url = os.path.join(self.output_video_folder_path, f"{self.url}.mp4")

        if os.path.exists(video_path_by_url):
            return video_path_by_url

        yt = YouTube(f'https://www.youtube.com/watch?v={self.url}', use_oauth=True, allow_oauth_cache=True)

        try:
            video_name = re.sub(r'[#:;.,\<"|/>*?\']', '', yt.title)
            stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()
            stream.download(self.output_video_folder_path)
            os.rename(os.path.join(self.output_video_folder_path, f"{video_name}.mp4"), video_path_by_url)

        except Exception as e:
            print(e)
            return None
        
        print(f'{self.url} video download: success')
        return video_path_by_url

    def extract_frames(self, video_file_path):
        self.video = cv2.VideoCapture(video_file_path)
        if not self.video.isOpened():
            print("Could not open video file")
            return
        
        for start_time, end_time in self.video_time_segments:
            if not start_time or not end_time:
                continue
            # Convert start_time from MM:SS format to datetime and add/subtract 1 second to exclude the frame boundary
            start_time = self.parse_time_stamp(start_time) + timedelta(seconds=1)
            end_time = self.parse_time_stamp(end_time) - timedelta(seconds=1)
            while start_time <= end_time:
                formatted_time = start_time.strftime("%M%S")
                image_name = f"YT_{self.url}_{formatted_time}.png" 
                start_time_sec = timedelta(minutes=start_time.minute, seconds=start_time.second).total_seconds()
                self.capture_image(start_time_sec, image_name)
                start_time += timedelta(seconds=self.frame_interval)

        self.video.release()
        cv2.destroyAllWindows()
    
    def capture_image(self, sec, image_name):
        self.video.set(cv2.CAP_PROP_POS_MSEC, sec*1000)
        ret, frame = self.video.read()

        if ret:
            image_path = os.path.join(self.output_image_folder_path, image_name)
            cv2.imwrite(image_path, frame)

    def parse_time_stamp(self, time_stamp):
        return datetime.strptime(time_stamp, "%M:%S")

def main():
    # Load Excel file containing video information
    df = pd.read_excel(excel_file_path, sheet_name='Sheet1')  
    url_list = df['Youtube ID'].unique()
    print('Number of videos in table:', len(url_list))

    for url in url_list:
        # Get time segments (Start time and End time) for the current video
        video_time_segments = df[df['Youtube ID'] == url][['Start time', 'End time']].values
        yt = YouTubeToImage(video_time_segments, output_video_folder_path, output_image_folder_path, frame_interval, url)

        # Download the video if not already downloaded and extract frames
        downloaded_video_path = yt.download_video()
        if downloaded_video_path is None:
            continue

        yt.extract_frames(downloaded_video_path)
        print(f'{url} image download: complete')

if __name__ == "__main__":
    main()