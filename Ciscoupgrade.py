import getpass
import sys
import datetime
import time
from netmiko import ConnectHandler, file_transfer
import os
import re

# Cisco IOS device details
host = "10.10.100.1"
username = "cisco"
password = "cisco"

# Safe harbour versions
version_c800 = "15.4(3)M9"
version_c1921 = "15.7(3)M3"
version_c2901 = "15.6(3)M5"

# Defines router parameters
router = {
    'device_type': "cisco_ios",
    'ip': host,
    'username': username,
    'password': password,
}


#Attempts login to router
def login(router):
    try:
        ssh = ConnectHandler(**router)
        return ssh
        print ("connection successful\n")
    except:
        print ("login failure\n")
        sys.exit()

# Function to enable SCP to facilitate SCP  transfer of IOS to cisco device
def enablescp(ssh):
    print ("Enabling SCP to Initialize file copy\n")
    ssh.send_config_set("ip scp server enable")


# Function to capture model of router, software version, and running Image
def version(ssh):
    version = ssh.send_command("show version", use_textfsm=True)
    version = version[0]
    currentversion = version["version"]
    runningimage= version["running_image"]
    return currentversion, runningimage

# Function to confirm if the Cisco device is already on the pre-defined  safe-harbour versions
def confirmver(ver,ssh,runningimage):
    if "c800" in runningimage:
        if ver == version_c800:
            print ("Router already on the safe harbour version")
            ssh.disconnect()
            sys.exit()
        else:
            print ("The router is currently running version " + ver + " and will be put on the safe harbour version of 15.4(3)M9")
            return "c800-universalk9-mz.SPA.154-3.M9.bin"
    
    elif "c1900" in runningimage:
        if ver == version_c1921:
            print ("Router already on the safe harbour version")
            ssh.disconnect()
            sys.exit()

        else:
            print ("The router is currently running version " + ver + " and will be put on the safe harbour version of 15.7(3)M3")
            return "c1900-universalk9-mz.SPA.157-3.M3.bin"

    elif "c2900" in runningimage:
        if ver == version_c2901:
            print ("Router already on the safe harbour version")
            ssh.disconnect()
            ssh.exit()
        else:
            print ("The router is currently running version " + ver + " and will be put on the safe harbour version of 15.6(3)M5")
            return "c2900-universalk9-mz.SPA.156-3.M5.bin"

    else:
        print ("Error in determining version\n")
        ssh.disconnect()
        sys.exit()

# Uses Netmiko's file_transfer function to transfer IOS images.
# It checks if the new IOS is already present on device Flash 
# avaliable space on device flash,
# MD5 hash to confirm there was no errors. 
def uploadios(ssh,source_file,dest_file):
    print ("Initiating IOS copy\n")
    transfer_dict = file_transfer(ssh,
                                 source_file=source_file,
                                 dest_file=dest_file,
                                 file_system="flash:",
                                 direction="put",
                                 overwrite_file=False)
    #print (transfer_dict)
    return transfer_dict

# Function changes Book sequence on device
def changebootsequence(ssh,source_file,runningimage):
    cbs = ssh.send_config_set("boot system flash:" + source_file)
    cbs = ssh.send_config_set("no boot system flash:{}".format(runningimage))
    print (cbs)

# Function to disable SCP on device after file transfer
def disscpandsave(ssh):
    ssh.send_config_set("no ip scp server enable")
    ssh.save_config()


# Function that reloads the router.
def reloadrouter(ssh):
    try:
        ssh.send_command_timing("reload")
        ssh.send_command_timing("\n")
    except:
        print ("Unable to reload Router\n")
        ssh.disconnect()
        sys.exit()



def main():

    starttime = datetime.datetime.now()

    print ("\n")
    print ("\n")

# Defines the base path for location of IOS images
    basefilename = os.environ.get("MYSCRIPTHOME") + "/Projects/Cisco-ios-upgrade/CiscoIOS"

#checking Login
    print ("Loggin into router with IP: " + host + "\n")
    ssh = login(router)

# checking version of the ROUTER
    ver, runningimage = version(ssh)

# Confirming version of router
    filename = confirmver(ver,ssh,runningimage)
    source_file = os.path.join(basefilename, filename)
    dest_file = filename

#Enable SCP on the ROUTER
    enablescp(ssh)

#Check Version and Initiate SCP transfer
    upload=uploadios(ssh,source_file,dest_file)
    if upload["file_verified"] == True:
        print ("File transfer was successful\n")
    else:
        print("Error in uploading correct IOS\n")

#Changing Book Sequence
    print("changing boot sequence\n")
    changebootsequence(ssh,filename,runningimage)

# Disabling SCP on the cisco device after new IOS has been transferred
    print("Disabling SCP on the router and saving config\n")
    disscpandsave(ssh)

#Prompts user if the router can be reloaded
    reload = input("Do you want to reload the router now? [y/n] : ")
    if reload == "y":
        print ("Reloading router\n")
        reloadrouter(ssh)
    else:
        print ("A safe harbour version of IOS has been copied to the router")
        print ("and boot sequesce changes. Reload router to boot to new version\n")

    endtime = datetime.datetime.now()
    totaltime = endtime - starttime
    print ("Total execution time is = {}".format(totaltime))


main()
