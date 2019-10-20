#!/usr/bin/python

# kivy imports
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import get_color_from_hex as rgb
from kivy.garden.graph import Graph, MeshLinePlot, SmoothLinePlot

# other imports
import time
import os
from math import sin, cos
import requests
import json
import configparser
import sys
from subprocess import *
import pprint
from collections import deque  # Fast pops from the ends of lists
import os_utils

# Temperature lists
hotendactual_list = deque([])
hotendtarget_list = deque([])
bedactual_list = deque([])
bedtarget_list = deque([])

# Initialize Temperature lists
for i in range(360):
    hotendactual_list.append(0)
    hotendtarget_list.append(0)
    bedactual_list.append(0)
    bedtarget_list.append(0)
# Fill timestamp list with 1000x time vals in seconds
graphtime_list = []
for i in range(360):  # Fill the list with zeros
    graphtime_list.append(0)

graphtime_list[0] = 30000
for i in range(359):  # Replace values with decreasing seconds from 30 to 0
    val = int(graphtime_list[i] - 83)
    graphtime_list[i + 1] = (val)


# Read settings from the config file
settings = configparser.ConfigParser()
settings.read('octoprint.cfg')
host = settings.get('APISettings', 'host')
nicname = settings.get('APISettings', 'nicname')
apikey = settings.get('APISettings', 'apikey')
debug = int(settings.get('Debug', 'debug_enabled'))
hotend_max = int(settings.get('MaxTemps', 'hotend_max'))
bed_max = int(settings.get('MaxTemps', 'bed_max'))
invert_X = int(settings.get('AxisInvert', 'invert_X'))
invert_Y = int(settings.get('AxisInvert', 'invert_Y'))
invert_Z = int(settings.get('AxisInvert', 'invert_Z'))

# Define Octoprint constants
httptimeout = 3   # http request timeout in seconds
printerapiurl = 'http://' + host + '/api/printer'
printheadurl = 'http://' + host + '/api/printer/printhead'
bedurl = 'http://' + host + '/api/printer/bed'
toolurl = 'http://' + host + '/api/printer/tool'
jobapiurl = 'http://' + host + '/api/job'
connectionurl = 'http://' + host + '/api/connection'
commandurl = 'http://' + host + '/api/printer/command'
headers = {'X-Api-Key': apikey, 'content-type': 'application/json'}

if debug:
    print("*********** DEBUG ENABLED ************")
    print(headers)

bed_temp_val = 0.0
hotend_temp_val = 0.0
jogincrement = 10

platform = sys.platform  # Grab platform name for platform specific commands

start_time = time.time()

################################
# Load the Kivy widget layout
Builder.load_file('panels.kv')


class Panels(TabbedPanel):
    global bed_max
    global hotend_max

    def gettemps(self, *args):
        self.ids.hotendslider.max = hotend_max
        self.ids.bedslider.max = bed_max
        try:
            if debug:
                print('[GET TEMPS] Trying /printer API request to Octoprint...')
            r = requests.get(printerapiurl, headers=headers, timeout=httptimeout)
            if debug:
                print('[GET TEMPS] STATUS CODE: ', str(r.status_code))
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('[GET TEMPS] ERROR: Couldn\'t contact Octoprint /printer API')
                print(e)
        if r and r.status_code == 200:
            if debug:
                print('[GET TEMPS] JSON Data: ' + str(r.json()))
        if r and r.status_code == 200 and 'tool0' in r.json()['temperature']:
            printeronline = True
            hotendactual = r.json()['temperature']['tool0']['actual']
            hotendtarget = r.json()['temperature']['tool0']['target']
            bedactual = r.json()['temperature']['bed']['actual']
            bedtarget = r.json()['temperature']['bed']['target']
            printing = r.json()['state']['flags']['printing']
            paused = r.json()['state']['flags']['paused']
            operational = r.json()['state']['flags']['operational']

            if debug:
                print('   BED ACTUAL: ' + str(bedactual))
                print('HOTEND ACTUAL: ' + str(hotendactual))
                print('     PRINTING: ' + str(printing))
                print('       PAUSED: ' + str(paused))
                print('  OPERATIONAL: ' + str(operational))

            # Update temperature arrays with new data
            hotendactual_list.popleft()
            hotendactual_list.append(hotendactual)
            hotendtarget_list.popleft()
            hotendtarget_list.append(hotendtarget)
            bedactual_list.popleft()
            bedactual_list.append(bedactual)
            bedtarget_list.popleft()
            bedtarget_list.append(bedtarget)

            # Update text color on Temps tab if values are above 40C
            if bedactual > 40:
                self.ids.tab3_bed_actual.color = [1, 0, 0, 1]
            else:
                self.ids.tab3_bed_actual.color = [1, 1, 1, 1]

            if bedtarget > 40:
                self.ids.tab3_bed_target.color = [1, 0, 0, 1]
            else:
                self.ids.tab3_bed_target.color = [1, 1, 1, 1]

            if hotendactual > 40:
                self.ids.tab3_hotend_actual.color = [1, 0, 0, 1]
            else:
                self.ids.tab3_hotend_actual.color = [1, 1, 1, 1]

            if hotendtarget > 40:
                self.ids.tab3_hotend_target.color = [1, 0, 0, 1]
            else:
                self.ids.tab3_hotend_target.color = [1, 1, 1, 1]

            # Enable/Disable extruder buttons
            if hotendactual < 130 or printing or paused:
                self.ids.extrude.disabled = True
                self.ids.retract.disabled = True
            else:
                self.ids.extrude.disabled = False
                self.ids.retract.disabled = False

            # Set pause/resume label on pause button
            if paused:
                self.ids.pausebutton.text = 'Resume'
            else:
                self.ids.pausebutton.text = 'Pause'

            # Enable/Disable print job buttons
            if printing or paused:
                self.ids.printbutton.disabled = True
                self.ids.cancelbutton.disabled = False
                self.ids.pausebutton.disabled = False
            else:
                self.ids.printbutton.disabled = False
                self.ids.cancelbutton.disabled = True
                self.ids.pausebutton.disabled = True

            # Set position of slider pointer
            self.ids.hotendpb.value = (hotendactual / self.ids.hotendslider.max) * 100
            self.ids.bedpb.value = (bedactual / self.ids.bedslider.max) * 100

            # Update tempurature values with new data
            self.ids.bed_actual.text = str(bedactual) + u"\u00b0" + ' C'
            self.ids.hotend_actual.text = str(hotendactual) + u"\u00b0" + ' C'
            if bedtarget > 0:
                self.ids.bed_target.text = str(bedtarget) + u"\u00b0" + ' C'
            else:
                self.ids.bed_target.text = 'OFF'
            if hotendtarget > 0:
                self.ids.hotend_target.text = str(hotendtarget) + u"\u00b0" + ' C'
            else:
                self.ids.hotend_target.text = 'OFF'
        else:
            if r:
                print('Error. API Status Code: ', str(r.status_code))  # Print API status code if we have one
            # If we can't get any values from Octoprint just fill values with not available.
            self.ids.bed_actual.text = 'N/A'
            self.ids.hotend_actual.text = 'N/A'
            self.ids.bed_target.text = 'N/A'
            self.ids.hotend_target.text = 'N/A'

    def home(self, *args):
        axis = args[0]
        print('HOME AXIS: ' + axis)
        if axis == 'xy':
            homedata = {'command': 'home', 'axes': ['x', 'y']}
        else:
            homedata = {'command': 'home', 'axes': ['z']}
        try:
            if debug:
                print('[HOME ' + axis + '] Trying /API request to Octoprint...')
            r = requests.post(printheadurl, headers=headers, json=homedata, timeout=httptimeout)
            if debug:
                print('[HOME ' + axis + '] STATUS CODE: ' + str(r.status_code))
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def jogaxis(self, *args):
        axis = args[0]
        direction = args[1]
        global invert_X
        global invert_Y
        global invert_Z
        global jogincrement
        invert_axis = {'x': invert_X, 'y': invert_Y, 'z': invert_Z}

        print('AXIS: ' + axis)
        print('DIRECTION: ' + direction)
        print('INCREMENT: ' + str(jogincrement))

        if direction == 'up' or direction == 'forward' or direction == 'left':
            if invert_axis[axis]:
                inc = jogincrement * -1
            else:
                inc = jogincrement

        if direction == 'down' or direction == 'backward' or direction == 'right':
            if invert_axis[axis]:
                inc = jogincrement
            else:
                inc = jogincrement * -1

        jogdata = {'command': 'jog', axis: inc}
        print('JOGDATA: ' + str(jogdata))
        try:
            if debug:
                print('[JOG ' + axis + ' ' + direction + '] Trying /API request to Octoprint...')
            r = requests.post(printheadurl, headers=headers, json=jogdata, timeout=httptimeout)
            if debug:
                print('STATUS CODE: ' + str(r.status_code))
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def jogincrement(self, *args):
        global jogincrement
        if debug:
            print('[JOG INCREMENT] Button pressed')
            print('[JOG INCREMENT] INC: ' + str(args[0]))
        jogincrement = args[0]

    def connect(self, *args):
        connectiondata = {'command': 'connect', 'port': '/dev/ttyACM0', 'baudrate': 250000,
                          'save': False, 'autoconnect': False}
        try:
            if debug:
                print('[CONNECT] Trying /job API request to Octoprint...')
                print('[CONNECT] ' + connectionurl + str(connectiondata))
            r = requests.post(connectionurl, headers=headers, json=connectiondata, timeout=httptimeout)
            if debug:
                print('[CONNECT] STATUS CODE: ' + str(r.status_code))
                print('[CONNECT] RESPONSE: ' + r.text)
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('[CONNECT] ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def disconnect(self, *args):
        disconnectdata = {'command': 'disconnect'}
        try:
            if debug:
                print('[DISCONNECT] Trying /job API request to Octoprint...')
                print('[DISCONNECT] ' + connectionurl + str(disconnectdata))
            r = requests.post(connectionurl, headers=headers, json=disconnectdata, timeout=httptimeout)
            if debug:
                print('[DISCONNECT] STATUS CODE: ' + str(r.status_code))
                print('[DISCONNECT] RESPONSE: ' + r.text)
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('[DISCONNECT] ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def setbedtarget(self, *args):
        bedsliderval = args[0]
        bedtargetdata = {'command': 'target', 'target': bedsliderval}
        if debug:
            print('[BED TARGET] New Value: ' + str(bedsliderval) + ' C')
        try:
            if debug:
                print('[BED TARGET] Trying /API request to Octoprint...')
            r = requests.post(bedurl, headers=headers, json=bedtargetdata, timeout=httptimeout)
            if debug:
                print ('[BED TARGET] STATUS CODE: ' + str(r.status_code))
        except requests.exceptions.RequestException as e:
            print('[BED TARGET] ERROR: Couldn\'t contact Octoprint /job API')
            print(e)
            r = False

    def sethotendtarget(self, *args):
        hotendsliderval = args[0]
        hotendtargetdata = {'command': 'target', 'targets': {'tool0': hotendsliderval}}
        if debug:
            print('[HOTEND TARGET] New Value: ' + str(hotendsliderval) + ' C')
        try:
            if debug:
                print('[HOTEND TARGET] Trying /API request to Octoprint...')
            r = requests.post(toolurl, headers=headers, json=hotendtargetdata, timeout=httptimeout)
            if debug:
                print('[HOTEND TARGET] STATUS CODE: ' + str(r.status_code))
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('[HOTEND TARGET] ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def extrudefilament(self, *args):
        posneg = args[0]
        extrudeamount = (int(self.ids.extrudeamount.text) * posneg)
        if debug:
            print('[EXTRUDE FILAMENT] Amount: ' + str(extrudeamount))
        extrudedata = {'command': 'extrude', 'amount': extrudeamount}
        if debug:
            print('[EXTRUDE FILAMENT] Extruding: ' + str(extrudeamount) + ' mm')
        try:
            if debug:
                print ('[EXTRUDE FILAMENT] Trying /API request to Octoprint...')
            r = requests.post(toolurl, headers=headers, json=extrudedata, timeout=httptimeout)
            if debug:
                print('[EXTRUDE FILAMENT] STATUS CODE: ' + str(r.status_code))
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('[EXTRUDE FILAMENT] ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def fanspeed(self, *args):
        speed_percent = int(args[0])
        speed_pwm = int(speed_percent * 2.551)
        fan_gcode = 'M106 S' + str(speed_pwm)
        fancmd = {"commands": [fan_gcode]}
        if debug:
            print('[FAN CONTROL] Speed: ' + str(speed_pwm))
            print('[FAN CONTROL] ' + str(fancmd))
        try:
            r = requests.post(commandurl, headers=headers, json=fancmd, timeout=httptimeout)
        except requests.exceptions.RequestException as e:
            r = False

    def jobcontrol(self, *args):
        jobcommand = args[0]
        jobdata = {'command': jobcommand}
        try:
            if debug:
                print ('[JOB COMMAND] Trying /API request to Octoprint...')
            # Send job request to the job api
            r = requests.post(jobapiurl, headers=headers, json=jobdata, timeout=httptimeout)
            if debug:
                print ('[JOB COMMAND] STATUS CODE: ' + str(r.status_code))
                print ('[JOB COMMAND]     COMMAND: ' + str(jobcommand))
                print ('[JOB COMMAND] BUTTON TEXT: ' + self.ids.pausebutton.text)
            # Update pause button text
            if r.status_code == 204 and jobcommand == 'pause' and self.ids.pausebutton.text == 'Pause':
                self.ids.pausebutton.text = 'Resume'
            elif r.status_code == 204 and jobcommand == 'pause' and self.ids.pausebutton.text == 'Resume':
                self.ids.pausebutton.text = 'Pause'

        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print ('[JOB COMMAND] ERROR: Couldn\'t contact Octoprint /job API')
                print(e)

    def getstats(self, *args):
        try:
            if debug:
                print ('[GET STATS] Trying /job API request to Octoprint...')
            r = requests.get(jobapiurl, headers=headers, timeout=1)
        except requests.exceptions.RequestException as e:
            r = False
            if debug:
                print('[GET STATS] ERROR: Couldn\'t contact Octoprint /job API')
                print(e)
        if r and r.status_code == 200:
            if debug:
                print ('[GET STATS] JSON Data: ' + str(r.json()))
            printerstate = r.json()['state']
            jobfilename = r.json()['job']['file']['name']
            jobpercent = r.json()['progress']['completion']
            jobprinttime = r.json()['progress']['printTime']
            jobprinttimeleft = r.json()['progress']['printTimeLeft']
            if debug:
                print ('[GET STATS] Printer state: ' + printerstate)
                print ('[GET STATS] Job percent: ' + str(jobpercent) + '%')
            if jobfilename is not None:
                jobfilenamefull = jobfilename
                jobfilename = jobfilename[:25]  # Shorten filename to 25 characters
                self.ids.jobfilename.text = jobfilename
                self.ids.jobfilenamefull.text = jobfilenamefull
            else:
                self.ids.jobfilename.text = '-'
            if printerstate is not None:
                self.ids.printerstate.text = printerstate
                self.ids.printerstate2.text = printerstate
                self.ids.printerstate3.text = printerstate
            else:
                self.ids.printerstate.text = 'Unknown'
                self.ids.printerstate2.text = 'Unknown'
                self.ids.printerstate3.text = 'Unknown'
            if jobpercent is not None:
                jobpercent = int(jobpercent)
                self.ids.jobpercent.text = str(jobpercent) + '%'
                self.ids.progressbar.value = jobpercent
            else:
                self.ids.jobpercent.text = '---%'
                self.ids.progressbar.value = 0
            if jobprinttime is not None:
                hours = int(jobprinttime / 60 / 60)
                if hours > 0:
                    minutes = int(jobprinttime / 60) - (60 * hours)
                else:
                    minutes = int(jobprinttime / 60)
                seconds = int(jobprinttime % 60)
                self.ids.jobprinttime.text = str(hours).zfill(2) + ':' + \
                    str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
            else:
                self.ids.jobprinttime.text = '00:00:00'
            if jobprinttimeleft is not None:
                hours = int(jobprinttimeleft / 60 / 60)
                if hours > 0:
                    minutes = int(jobprinttimeleft / 60) - (60 * hours)
                else:
                    minutes = int(jobprinttimeleft / 60)
                seconds = int(jobprinttimeleft % 60)
                self.ids.jobprinttimeleft.text = str(hours).zfill(2) + \
                    ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
            else:
                self.ids.jobprinttimeleft.text = '00:00:00'

        else:
            if r:
                print ('Error. API Status Code: ' + str(r.status_code))  # Print API status code if we have one
            # If we can't get any values from Octoprint API fill with these values.
            self.ids.jobfilename.text = 'N/A'
            self.ids.printerstate.text = 'Unknown'
            self.ids.printerstate2.text = 'Unknown'
            self.ids.printerstate3.text = 'Unknown'
            self.ids.jobpercent.text = 'N/A'
            self.ids.progressbar.value = 0
            self.ids.jobprinttime.text = '--:--:--'
            self.ids.jobprinttimeleft.text = '--:--:--'

    def update_ip_addr(self, *args):
        global platform
        global nicname  # Network card name from config file
        if 'linux' in platform or 'Linux' in platform:
            cmd = "ip addr show " + nicname + " | grep inet | grep -v inet6 | awk '{print $2}' | cut -d/ -f1"
            p = Popen(cmd, shell=True, stdout=PIPE)
            output = p.communicate()[0]
            self.ids.ipaddr.text = output.decode('utf-8')
        else:
            self.ids.ipaddr.text = 'Unknown Platform'

    def button_restart_os(self, *args):
        command = args[0]
        os_utils.restart_os(platform, command, debug)

    def button_exit_app(self, *args):
        os_utils.exit_app()

    def button_restart_networking(self, *args):
        os_utils.restart_networking(platform, nicname, debug)

    def graphpoints(self, *args):
        hotendactual_plot = SmoothLinePlot(color=[1, 0, 0, 1])
        hotendtarget_plot = MeshLinePlot(color=[1, 0, 0, .75])
        bedactual_plot = SmoothLinePlot(color=[0, 0, 1, 1])
        bedtarget_plot = MeshLinePlot(color=[0, 0, 1, .75])
        # Build list of plot points tuples from temp and time lists
        # FIXME - Need to reduce the number of points on the graph. 360 is overkill
        hotendactual_points_list = []
        hotendtarget_points_list = []
        bedactual_points_list = []
        bedtarget_points_list = []
        for i in range(360):
            hotendactual_points_list.append((graphtime_list[i] / 1000.0 * -1, hotendactual_list[i]))
            hotendtarget_points_list.append((graphtime_list[i] / 1000.0 * -1, hotendtarget_list[i]))
            bedactual_points_list.append((graphtime_list[i] / 1000.0 * -1, bedactual_list[i]))
            bedtarget_points_list.append((graphtime_list[i] / 1000.0 * -1, bedtarget_list[i]))

        # Remove all old plots from the graph before drawing new ones
        for plot in self.my_graph.plots:
            self.my_graph.remove_plot(plot)

        # Draw the new graphs
        hotendactual_plot.points = hotendactual_points_list
        self.my_graph.add_plot(hotendactual_plot)
        hotendtarget_plot.points = hotendtarget_points_list
        self.my_graph.add_plot(hotendtarget_plot)
        bedactual_plot.points = bedactual_points_list
        self.my_graph.add_plot(bedactual_plot)
        bedtarget_plot.points = bedtarget_points_list
        self.my_graph.add_plot(bedtarget_plot)


class TabbedPanelApp(App):
    def build(self):
        Window.size = (800, 480)
        panels = Panels()
        Clock.schedule_once(panels.gettemps, 0.5)  # Update bed and hotend at startup
        Clock.schedule_interval(panels.gettemps, 5)  # Update bed and hotend temps every 5 seconds

        Clock.schedule_interval(panels.getstats, 5)  # Update job stats every 5 seconds

        Clock.schedule_once(panels.update_ip_addr, 0.5)  # Update IP addr once right away
        Clock.schedule_interval(panels.update_ip_addr, 30)  # Then update IP every 30 seconds

        Clock.schedule_interval(panels.graphpoints, 10)  # Update graphs
        return panels


if __name__ == '__main__':
    TabbedPanelApp().run()
