import os
import time
from datetime import timedelta
from configparser import ConfigParser

import pysftp
import numpy as np
import cv2
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from tqdm import trange, tqdm

VIDEO_DIR = r'C:\Users\kylek\nest_cam_videos'

def download_new_videos():
    config = ConfigParser()
    config.read(r"C:\Users\kylek\OneDrive\Documents\Code\shared_with_VM\nest_cam\video_analysis\config.ini")
    hostname = config.get('pi_server', 'hostname')
    username = config.get('pi_server', 'username')
    password = config.get('pi_server', 'password')
    remote_path = config.get('pi_server', 'path')

    try:
        connection = pysftp.Connection(
                        host=hostname,
                        username=username,
                        password=password,
                        port=22)
    except pysftp.SSHException:
        print('Could not connect to Pi')
        return
    
    remote_videos = sorted([f for f in connection.listdir(remote_path) if f.endswith('.mp4')])
    # remove last video as it is the video that is currently recording
    remote_videos = remote_videos[:-1]

    # Remove videos from list that are already processed or already on local machine
    videos_checked = get_checked_video_list()
    local_videos = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')])
    videos_to_download = [f for f in remote_videos if f not in videos_checked and f not in local_videos]

    for file in tqdm(videos_to_download):
        connection.get(f'{remote_path}/{file}', os.path.join(VIDEO_DIR, file))

def get_movement_times(
        file_path, 
        movement_threshold=1_000_000, 
        frames_to_skip=10):
    """Function to analyze video file and return times which contain movement. 
    Uses OpenCV background subtractor to create a movement mask where white 
    pixels represent movement and black represents no movement. The pixels are 
    then summed. Higher sums indicates more movement in the frame. If the sum
    is above the movement_threshold, movement is detected and the frame number
    is noted. Subsequent frames are processed and when the sum drops below the
    movement_threshold and the movement end time is noted. 
    
    Parameters:
    file_path:      path to the video file
    movement_threshold:     Threshold for which the sum of all pixel in the 
                            movement mask indicated movement within the frame.
                            Higher number results in less false positives but 
                            may not detect small movements within the frame.
                            Default = 20,000,000
    frames_to_skip:     Number of frames that are skipped during analysis. 
                        Default = 10

    Returns:
    movement_times:     List containing movement times in the form of 
                        [[start, finish], ...]

    """
    # Initialize variables
    movement_detected = False
    movement_times = []
    movement_start_time = 0
    movement_finish_time = 0
    frame_sum = 0

    # Initialize background subtractor
    background_subtractor = cv2.createBackgroundSubtractorMOG2(history=30) 
    
    # Start video capture
    cap = cv2.VideoCapture(file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Loop through all frames in video 
    for current_frame in trange(0, total_frame_count, frames_to_skip):
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        success, frame = cap.read()
        if success:
            # Apply background subtractor, then threshold to get only areas with
            # high difference, then erode to reduce noise
            fg_mask = background_subtractor.apply(frame)
            _, fg_mask = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)
            kernel = np.ones((5,5),np.uint8)
            fg_mask = cv2.erode(fg_mask,kernel,iterations = 1)
            # Sum all movement pixel in the frame
            frame_sum = fg_mask.sum()

            # Record start of movement time
            if frame_sum > movement_threshold and movement_detected == False:
                movement_start_time = current_frame / fps
                movement_detected = True
            # Record end of movement time
            if frame_sum < movement_threshold and movement_detected == True:
                movement_finish_time = current_frame / fps
                movement_times.append([movement_start_time,movement_finish_time])
                movement_detected = False

        else:
            # Frame capture read not successful, go to next frame
            continue

    # Record end of movement time if movement continues through the last frame
    if frame_sum > movement_threshold and movement_detected == True:
        movement_finish_time = current_frame / fps
        movement_times.append([movement_start_time,movement_finish_time])
        movement_detected = False

    cap.release()

    return movement_times

def combine_movement_times(movement_times, max_time_between_movements=5):
    """Function to combine movement times that are close together into single
    movement times"""

    if len(movement_times) == 0:
        return []
    elif len(movement_times) == 1:
        return movement_times.copy()

    cleaned_movement_times = []    
    new_movement = movement_times[0].copy()
    # look ahead to the next movement, if it happens less than the max time, 
    # combine movements. Otherwise start a new movement
    for idx in range(len(movement_times)-1):
        next_movement_start = movement_times[idx + 1][0]
        if next_movement_start - new_movement[1] < max_time_between_movements:
            new_movement[1] = movement_times[idx + 1][1]
        else:
            cleaned_movement_times.append(new_movement)
            new_movement = movement_times[idx + 1].copy()

    # since the for loop does not append the last movement, we need to check if
    # the last movement time is a new movement of part of the previous movement
    if movement_times[-1][1] == new_movement[1]:
        cleaned_movement_times.append(new_movement)
    else:
        cleaned_movement_times.append(movement_times[-1].copy())
    
    return cleaned_movement_times
        
def remove_short_movements(movement_times, min_duration=2):
    """Remove movement times that are short duration"""
    cleaned_movement_times = []
    for movement in movement_times:
        if movement[1] - movement[0] > min_duration:
            cleaned_movement_times.append(movement)
    
    return cleaned_movement_times

def create_movement_subclips(movement_times, video_file):
    """Split video file into separate clips based on movement_times"""
    highlights_dir = os.path.join(VIDEO_DIR, 'highlights')
    # Create highlights directory if it doesn't exist
    if os.path.exists(highlights_dir) == False:
        os.mkdir(highlights_dir)
    # Split video base on movement_times
    for idx, movement in enumerate(movement_times):
        ffmpeg_extract_subclip(
            os.path.join(VIDEO_DIR,video_file), 
            t1=movement[0]-1, 
            t2=movement[1]+1, 
            targetname=os.path.join(highlights_dir,f"{video_file[:-4]}_{idx}.mp4"))
        
def add_video_to_checked_log(video):
    """Add video name to log of processed videos"""
    with open(os.path.join(VIDEO_DIR,"videos_checked.txt"), "a") as f:
        f.write(video + '\n')

def get_checked_video_list():
    """Get list of videos that have already been processed"""
    try:
        with open(os.path.join(VIDEO_DIR,"videos_checked.txt"), 'r') as f:
            return [line.rstrip('\n') for line in f]
    except FileNotFoundError:
        return []
    

def main():
    start_time = time.time()
    print('Starting Nest Box Video Processor')
    print('Getting new videos from Pi')
    download_new_videos()
    videos_checked = get_checked_video_list()
    video_files = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')])
    new_videos = [video for video in video_files if video not in videos_checked]
    counter = 1
    total_highlights_found = 0
    total_videos_to_process = len(new_videos)
    print(f'{total_videos_to_process} new videos found.')
    for video in new_videos:
        print(f'Processing video {counter}/{total_videos_to_process}: {video}')
        movement_times = get_movement_times(os.path.join(VIDEO_DIR,video))
        condensed_movement_times = combine_movement_times(movement_times)
        cleaned_movement_times = remove_short_movements(condensed_movement_times)
        create_movement_subclips(cleaned_movement_times,video)
        add_video_to_checked_log(video)
        print(f'{len(cleaned_movement_times)} highlights found.')
        total_highlights_found += len(cleaned_movement_times)
        counter += 1
    elapsed = time.time() - start_time
    print(f'Total time: {str(timedelta(seconds=elapsed))}')
    print(f'{total_highlights_found} total highlights found')
    os.system("pause")
if __name__ == '__main__':
    main()