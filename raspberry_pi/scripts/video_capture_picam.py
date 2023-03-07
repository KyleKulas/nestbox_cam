#!/usr/bin/python3
import time
from datetime import datetime
import psutil
import os
import logging

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

SAVE_DIR = '/mnt/exdisk/nest_cam_videos'
VIDEO_LENGTH = 600 #length in seconds
MIN_DISK_SPACE = 5000 # min megabytes before oldest video files are deleted


def make_disk_space():
    bytes_avail = psutil.disk_usage(SAVE_DIR).free
    megabytes_avail = bytes_avail / 1024 / 1024
    print('Disk space available (MB): ', megabytes_avail)
    if megabytes_avail < MIN_DISK_SPACE:
        #delete files
        files = os.listdir(SAVE_DIR)
        video_files = sorted([file for file in files if 'video' in file])
        for file in video_files:
            os.remove(os.path.join(SAVE_DIR, file))
            bytes_avail = psutil.disk_usage(SAVE_DIR).free
            megabytes_avail = bytes_avail / 1024 / 1024
            if megabytes_avail > MIN_DISK_SPACE:
                break

def setup_camera():
    setup_attempts = 0
    while True:
        try:
            picam2 = Picamera2()
            video_config = picam2.create_video_configuration({'size': (1296, 972)})
            picam2.configure(video_config)
            picam2.set_controls({'ExposureValue': -.25})
            encoder = H264Encoder(10000000)
            setup_attempts = 0
            return picam2, encoder
        except Exception:
            setup_attempts += 1
            if setup_attempts >= 3:
                raise
            

count = 0
recording_attempts = 0
picam2, encoder = setup_camera()
while True:
    print('Sequence #: ', count)
    try:
        make_disk_space()
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = FfmpegOutput(os.path.join(SAVE_DIR, f'video_{now}.mp4'), audio=True)
        picam2.start_recording(encoder, output)
        time.sleep(VIDEO_LENGTH)
        picam2.stop_recording()
        recording_attempts = 0
    except Exception:
        recording_attempts += 1
        if recording_attempts >= 3:
            raise
        picam2.close()
        picam2, encoder = setup_camera()
        
    count += 1

