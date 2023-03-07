
import os
import time
import board
import adafruit_dht
import psutil
from datetime import datetime

sleep_time = 60 * 5
sensor1 = adafruit_dht.DHT11(board.D17)
sensor2 = adafruit_dht.DHT11(board.D22)
output_path='/mnt/exdisk/temp_log.csv'


# not sure if this is needed
# # We first check if a libgpiod process is running. If yes, we kill it!
# for proc in psutil.process_iter():
#     if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
#         proc.kill()

def format_csv_row(readings):
    readings_as_string = [str(x) for x in readings]
    return ', '.join(readings_as_string) + '\n'

header = ['inside_temp', 'outside_temp', 'inside_humid', 'outside_humid', 'datetime']
    
while True:
    try:
        readings = [sensor1.temperature,
                    sensor2.temperature,
                    sensor1.humidity,
                    sensor2.humidity,
                    datetime.now().strftime('%Y%m%d %H%M%S')]

    except RuntimeError as error:
        # trouble reading sensor, try again immediately
        print(error)
        continue
    except Exception as error:
        sensor1.exit()
        sensor2.exit()
        raise error

    
    if os.path.exists(output_path):
        with open(output_path, 'a') as f:
            f.write(format_csv_row(readings))
    else:
        with open(output_path, 'w') as f:
            f.write(format_csv_row(header))
            f.write(format_csv_row(readings))

    time.sleep(sleep_time)
