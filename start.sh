#!/bin/bash

# This script can be used to start the touchscreen app in the background.
# If you want to start and stop the app with init use the script etc/init.d/touchscreen

DAEMON='/root/OctoPiTouchPanel/main.py'
PIDFILE=/var/run/touchscreen.pid
CHDIR='/root/OctoPiTouchPanel'
start-stop-daemon --start --quiet --chdir $CHDIR --pidfile $PIDFILE --exec $DAEMON
