from picamera2 import Picamera2, Preview
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={'size': (1296, 972)},display='main')
picam2.configure(video_config)
picam2.start_preview(Preview.QTGL)
picam2.set_controls({'ExposureValue': -.5})
picam2.start()
print(video_config['main'])
