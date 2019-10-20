##########################################
# These are items for the 'OS Utils' tab
from subprocess import *

###################################
# Exit the touchscreen application
def exit_app():
    exit()

####################################
# Ask the OS to restart networking
def restart_networking(platform, nicname, debug):
    if 'linux' in platform or 'Linux' in platform:
        cmd = "sudo ifdown " + nicname
        p = Popen(cmd, shell=True, stdout=PIPE)
        output = p.communicate()[0]
        if debug:
            print('[RESTART NETWORK]: ' + output)
        cmd = "sudo ifup " + nicname
        p = Popen(cmd, shell=True, stdout=PIPE)
        output = p.communicate()[0]
        if debug:
            print('[RESTART NETWORK]: ' + output)
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