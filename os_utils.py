##########################################
# These are items for the 'OS Utils' tab
from subprocess import Popen
from subprocess import PIPE
from subprocess import os

###################################
# Exit the touchscreen application
def exit_app():
    exit()

####################################
# Ask the OS to restart networking
# This will restart the nic listed in the config file
def restart_networking(platform, nicname, debug):
    if 'linux' in platform or 'Linux' in platform:
        cmd = "sudo ifdown " + nicname
        p = Popen(cmd, shell=True, stdout=PIPE)
        cmd_output = p.communicate()[0].decode('utf-8')
        if debug:
            print('[RESTART NETWORK]: ' + output)
        cmd = "sudo ifup " + nicname
        p = Popen(cmd, shell=True, stdout=PIPE)
        cmd_output = p.communicate()[0].decode('utf-8')
        if debug:
            print('[RESTART NETWORK]: ' + cmd_output)
    else:
        if debug:
            print('Unknown Platform. Not restarting network interface')


##########################################
# Request an OS restart
def restart_os(platform, command, debug):
    if 'linux' in platform or 'Linux' in platform:
        print ('[RESTART] OS is going to ' + str(command))
        if command == 'reboot':
            cmd = "sudo shutdown now -r"
        elif command == 'shutdown':
            cmd = "sudo shutdown now -h"
        else:
            cmd = "true"
        os.system(cmd)
    else:
        print ('[RESTART] ' + str(command) + ' Unsupported OS')


#############################################
# Detect IP address of the OS
def get_ip_address(platform, nicname, debug):
    ip = ''
    if 'linux' in platform or 'Linux' in platform:
        cmd = "ip addr show " + nicname + " | grep inet | grep -v inet6 | awk '{print $2}' | cut -d/ -f1"
        p = Popen(cmd, shell=True, stdout=PIPE)
        cmd_output = p.communicate()[0].decode('utf-8')
        ip = cmd_output
    else:
        if debug:
            print('Unknown platform. Can\'t detect IP address')
    return(ip)