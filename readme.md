# Nest box Camera
This project uses a raspberry pi to record video and audio of the interior of a nesting box located on our patio. Two summers ago, a pair of chickadees used the box for nesting and we were happy to see 4 baby chickadees fletch the nest. This year we have a camera mounted inside the box so we can hopefully watch the entire process. The box was put up on 23 Feb 2023 and had its first visitor within 30 minutes: 
![chickadee](/images/chickadee_checkout.gif)

Video is continually recorded in 10 minute segments and saved to an external harddrive on the Pi. When the drive is full, the oldest videos get overwritten. There are also 2 temperature/humidity sensors that log readings to a csv file every 5 minutes. Code running on the Raspberry Pi is [here](/raspberry_pi/)

The external harddrive on the Pi can hold over a month worth of video but on a regular basis the videos are transferred to a more powerful laptop for processing. Processing involves looking through all the footage and splitting the clips into only segments that contain movement. This process is fully automated. The code for the video analysis is [here](/video_analysis/)