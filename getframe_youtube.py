from pytube import YouTube
from pytube.cli import on_progress

url = 'https://www.youtube.com/watch?v='
url += 'dKNKzeR_t3w'
video = YouTube(url, on_progress_callback=on_progress)

extension = "mp4"


DOWNLOAD_FOLDER = "C:/Users/Snucem_W1/Desktop/yt/"

yt = YouTube(url)
stream = yt.streams.get_highest_resolution()
stream.download(DOWNLOAD_FOLDER)
