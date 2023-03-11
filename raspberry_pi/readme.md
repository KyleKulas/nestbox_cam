# Setting up the Raspberry Pi
The python scripts that run on the raspberry pi are run as services handled by systemd. This way, when the system boots up, the scripts are automatically started and no input is required. 
### List of scripts:
- [fan control](./scripts/fan_control.py) - Monitors cpu temperatures and automatically controls the case fan on the Pi 
- [temp logger](./scripts/temp_logger.py) - Takes readings from the temperature and humidity sensors and logs them to a csv file
- [video capture picam](./scripts/video_capture_picam.py) - Continuously captures video and audio and saves to the external hard drive in 10 minute segments
- [video preview](./scripts/view_preview.py) - Used during development to get a preview of the video feed when setting up the the camera and adjusting focus
- [view sensor modes](./scripts/view_sensor_modes.py) - Used during development to check the available sensor modes of the camera

## Setting up the external hard drive
The pi desktop interface will automatically mount an attached external drive to ```/media/pi```. To automatically mount the drive to another location, we need to modify the ```fstab``` file:

1. Create the directory where the disk will be mounted:
    ```
    sudo mkdir /mnt/exdisk
    ```
2.  Get the UUID of the disk partition.
    ```
    sudo blkid
    ```
    ![uuid](/images/uuid.png)
3. Open fstab.
    ```
    sudo nano /etc/fstab
    ```
4. Add the following line with the appropriate UUID:
    ```
    UUID=0A8C8F8B8C8F6FCD /mnt/exdisk ntfs uid=1000,gid=1000,auto,users,rw,nofail,noatime 0 0
    ```
5. reboot

## Setting up scripts to run automatically using systemd
systemd uses unit files to configure services. The unit files are found [here](./systemd_unit_files/). Unit files can be either system level or user level and are placed in

```
/etc/systemd/system/
``` 
or 
```
/etc/systemd/user/
```
Once the unit file has been placed in the appropriate directory, the following commands are used to enable the service.
```
sudo systemctl daemon-reload
sudo systemctl enable fan_control.service
```
After reboot, the service with start automatically. It can also be started manually using:
```
sudo systemctl start fan_control.service
```
To view the status of the a service use:
```
sudo systemctl status fan_control.service
```
This will display the status of the service as well as the last 20 lines of the console log. To view more lines of the log use the -n flag:
```
sudo systemctl status fan_control.service -n100
```
The video capture script needs to be run as a user service due to an issue with pulse audio. To work with user level services, use the --user flag:
```
systemctl --user status video_capture.service -n100
```


## Setting up static ip 
It is helpful but not necessary for the Raspberry Pi to have a static ip address.
1. Get router ip, interface, and Pi ip 
    ```
    ip r
    ```
    ![router ip](/images/router_ip_interface_pi_ip.png)

2. Get nameservers
    ```
    grep "nameserver" /etc/resolv.conf
    ```
    ![nameservers](/images/nameservers.png)

3. Edit network preferences. 
    - Right click on the network icon and choose "Wireless and Wired Network Settings".
    - Choose the interface and enter appropriate information in the boxes
    ![network_preferences](/images/network_preferences.png)

    **Alternatively:**

    - Edit dhcpcd.conf
        ```
        nano /etc/dhcpcd.conf
        ```
    - Uncomment or add the following lines and put in the appropriate information:
        ```
        interface [INTERFACE]
        static ip_address=[STATIC IP ADDRESS YOU WANT]/24
        static_routers=[ROUTER IP]
        static domain_name_servers=[DNS IP]
        ```
        Like this:
        ```
        interface eth0
        inform ip_address=192.168.1.81/24
        static routers=192.168.1.254
        static domain_name_servers=192.168.1.254 75.153.171.116 2001:568:ff09:10c::67 2001:568:ff09:10a::116
        ```
        Substitute "inform" for "static" on the ip_address line. Using inform means that the Raspberry Pi will attempt to get the IP address requested if available, otherwise it will choose another. If static is used, it will have no IP v4 address at all if the requested one is in use.