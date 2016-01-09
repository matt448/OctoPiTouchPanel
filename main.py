
#kivy imports
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

#other imports
import time
from math import sin, cos
import requests
import json
import ConfigParser
import sys
from subprocess import *
import pprint
from collections import deque #Fast pops from the ends of lists

#Temperature lists
hotendactual_list = deque([])
hotendtarget_list = deque([])
bedactual_list = deque([])
bedtarget_list = deque([])

#Initialize Temperature lists
for i in range(360):
    hotendactual_list.append(0)
    hotendtarget_list.append(0)
    bedactual_list.append(0)
    bedtarget_list.append(0)
#Fill timestamp list with 1000x time vals in seconds
graphtime_list = []
for i in range(360): #Fill the list with zeros
  graphtime_list.append(0)

graphtime_list[0] = 30000
for i in range(359): #Replace values with decreasing seconds from 30 to 0
    val = int(graphtime_list[i] - 83)
    graphtime_list[i+1] = (val)



# Read settings from the config file
settings = ConfigParser.ConfigParser()
settings.read('octoprint.cfg')
host = settings.get('APISettings', 'host')
nicname = settings.get('APISettings', 'nicname')
apikey = settings.get('APISettings', 'apikey')

# Define Octoprint constants
printerapiurl = 'http://'+ host + '/api/printer'
printheadurl = 'http://'+ host + '/api/printer/printhead'
jobapiurl = 'http://' + host + '/api/job'
connectionurl = 'http://' + host + '/api/connection'
headers = {'X-Api-Key': apikey, 'content-type': 'application/json'}
print headers

bed_temp_val = 0.0
hotend_temp_val = 0.0
jogincrement = 10

platform = sys.platform #Grab platform name for platform specific commands

start_time = time.time()


#Kivy widget layout
Builder.load_string("""
#:import rgb kivy.utils.get_color_from_hex
<Panels>:
    size_hint: 1, 1
    pos_hint: {'center_x': .5, 'center_y': .5}
    do_default_tab: False
    my_graph: my_graph
    ##############        
    # Tab1
    ##############        
    TabbedPanelItem:
        id: tab1
        text: 'Status'
        BoxLayout:
            orientation: 'horizontal'
            ######################
            # Left Stats Area
            ######################
            BoxLayout:
                size_hint: (.4, 1)
                orientation: 'vertical'
                padding: 10
                Image:
                    source: 'logo.png'
                    size_hint_y: None
                    height: 100
                GridLayout:
                    cols: 2
                    Label:
                        text: 'IP Address:'
                    Label:
                        id: ipaddr
                        size_hint_x: 1.75
                        text: 'N/A'
                    Label:
                        text: 'Machine State:'
                    Label:
                        id: printerstate
                        text: 'Unknown'
                    Label:
                        text: 'File:'
                    Label:
                        id: jobfilename
                        text: ' '
                    Label:
                        text: 'Time Elapsed:'
                    Label:
                        id: jobprinttime
                        text: '00:00:00'
                    Label:
                        text: 'Est. Time Left:'
                    Label:
                        id: jobprinttimeleft
                        text: '00:00:00'
                    Label:
                        text: 'Printed: '
                    Label:
                        id: jobpercent
                        text: '---%'
                ProgressBar:
                    id: progressbar
                    size_hint_x: .97
                    size_hint_y: None
                    height: '15dp'
                    value: 0
            ######################
            # Right Stats Area
            ######################
            BoxLayout:
                size_hint: (.6, 1)
                orientation: 'vertical'
                GridLayout:
                    cols: 3
                    size_hint: (1, .3)
                    Label:
                        text: ' '
                        size_hint_y: None
                        height: 20
                    Label:
                        text_size: self.size
                        halign: 'center'
                        valign: 'middle'
                        text: 'Actual'
                    Label:
                        text_size: self.size
                        halign: 'center'
                        valign: 'middle'
                        text: 'Target'
                    Label:
                        size_hint_y: None
                        height: 40
                        text_size: self.size
                        bold: True
                        halign: 'right'
                        valign: 'middle'
                        text: 'Hot End:'
                    Label:
                        id: hotend_actual
                        text_size: self.size
                        font_size: 30
                        bold: True
                        halign: 'center'
                        valign: 'middle'
                        text: 'N/A' + u"\u00b0" + ' C'
                    Label:
                        id: hotend_target
                        text_size: self.size
                        font_size: 30
                        bold: True
                        halign: 'center'
                        valign: 'middle'
                        text: 'N/A' + u"\u00b0" + ' C'
                    Label:
                        size_hint_y: None
                        height: 40
                        bold: True
                        text_size: self.size
                        halign: 'right'
                        valign: 'middle'
                        text: 'Bed:'
                    Label:
                        id: bed_actual
                        text_size: self.size
                        font_size: 30
                        bold: True
                        halign: 'center'
                        valign: 'middle'
                        text: 'N/A' + u"\u00b0" + ' C'
                    Label:
                        id: bed_target
                        text_size: self.size
                        font_size: 30
                        bold: True
                        halign: 'center'
                        valign: 'middle'
                        text: 'N/A' + u"\u00b0" + ' C'
                Graph:
                    id:my_graph
                    xlabel: 'Time'
                    ylabel: 'Temp'
                    x_ticks_minor: 5
                    x_ticks_major: 5
                    y_ticks_major: 50
                    y_grid_label: True
                    x_grid_label: True
                    padding: 5
                    xlog: False
                    ylog: False
                    x_grid: True
                    y_grid: True
                    xmin: -30
                    xmax: 0
                    ymin: 0
                    ymax: 300
                    label_options: { 'color': rgb('444444'), 'bold': True}
                    background_color: rgb('f8f8f2')  # back ground color of canvas
                    tick_color: rgb('808080')  # ticks and grid
                    border_color: rgb('808080')  # border drawn around each graph
    ##############        
    # Tab2
    ##############
    TabbedPanelItem:
        text: 'Control'
        FloatLayout:
            #X/Y Axis buttons
            Label:
                text: 'X/Y'
                font_size: '35sp'
                pos: -270, 20
            Button:
                text: '^'
                id: jogforward
                on_press: root.jogforward()
                pos: 100, 160
                size_hint: .07, .1
            Button:
                text: '<'
                id:jogleft
                on_press: root.jogleft()
                pos: 25, 100
                size_hint: .07, .1
            Button:
                text: 'H'
                id: homexy
                on_press: root.homexy()
                pos: 100, 100
                size_hint: .07, .1
            Button:
                text: '>'
                id: jogright
                on_press: root.jogright()
                pos: 175, 100
                size_hint: .07, .1
            Button:
                text: 'v'
                id: jogbackward
                on_press: root.jogbackward()
                pos: 100, 40
                size_hint: .07, .1
            #Z axis buttons
            Label:
                text: 'Z'
                font_size: '35sp'
                pos: -70, 20
            Button:
                size_hint_x: None
                width: '25dp'
                text: '^'
                on_press: root.jogzup()
                pos: 300, 160
                size_hint: .07, .1
            Button:
                text: 'H'
                id: homez
                on_press: root.homez()
                pos: 300, 100
                size_hint: .07, .1
            Button:
                text: 'v'
                id: jogzdown
                on_press: root.jogzdown()
                pos: 300, 40
                size_hint: .07, .1
            #Connect Button
            Label:
                id: printerstate2
                text: 'Unknown'
                pos: 310, 195
            Button:
                text: 'Connect'
                id: connect
                on_press: root.connect()
                pos: 650, 350
                size_hint: .15, .08
            Button:
                text: 'Disconnect'
                id: connect
                on_press: root.disconnect()
                pos: 650, 300
                size_hint: .15, .09
            ToggleButton:
                text: '0.1'
                id: joginc01
                on_press: root.jogincrement(0.1)
                group: 'jogincrement'
                state: 'normal'
                pos: 0, 0
                size_hint: .05, .09
            ToggleButton:
                text: '1'
                id: joginc1
                on_press: root.jogincrement(1)
                group: 'jogincrement'
                state: 'normal'
                pos: 60, 0
                size_hint: .05, .09
            ToggleButton:
                text: '10'
                id: joginc10
                on_press: root.jogincrement(10)
                group: 'jogincrement'
                state: 'down'
                pos: 120, 0
                size_hint: .05, .09
            ToggleButton:
                text: '100'
                id: joginc100
                on_press: root.jogincrement(100)
                group: 'jogincrement'
                state: 'normal'
                pos: 180, 0
                size_hint: .05, .09




    ##############        
    # Tab3
    ##############        
    TabbedPanelItem:
        ##NOTE: http://kivy.org/docs/examples/gen__camera__main__py.html
        text: 'Settings'
        RstDocument:
            text:
                '\\n'.join(("Hello world", "-----------",
                "You are in the third tab."))
""")


class Panels(TabbedPanel):
    def gettemps(self, *args):
        try:
            print 'Trying /printer API request to Octoprint...'
            r = requests.get(printerapiurl, headers=headers, timeout=1)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /printer API'
            print e
            r = False
        if r and r.status_code == 200 and r.json()['temperature']['tool0']:
            printeronline = True 
            hotendactual = r.json()['temperature']['tool0']['actual']
            hotendtarget = r.json()['temperature']['tool0']['target']
            bedactual = r.json()['temperature']['bed']['actual']
            bedtarget = r.json()['temperature']['bed']['target']
            print bedactual
            print hotendactual
            
            hotendactual_list.popleft()
            hotendactual_list.append(hotendactual)
            hotendtarget_list.popleft()
            hotendtarget_list.append(hotendtarget)
            bedactual_list.popleft()
            bedactual_list.append(bedactual)
            bedtarget_list.popleft()
            bedtarget_list.append(bedtarget)

            self.ids.bed_actual.text = str(bedactual) + u"\u00b0" + ' C'
            self.ids.hotend_actual.text = str(hotendactual)  + u"\u00b0" + ' C'
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
                print 'Error. API Status Code: ' + str(r.status_code) #Print API status code if we have one
            #If we can't get any values from Octoprint just fill values with not available.
            self.ids.bed_actual.text = 'N/A'
            self.ids.hotend_actual.text = 'N/A'
            self.ids.bed_target.text = 'N/A'
            self.ids.hotend_target.text = 'N/A'

    def homez(self, *args):
        homezdata = {'command': 'home', 'axes': ['z']}
        try:
            print '[HOME Z] Trying /API request to Octoprint...'
            r = requests.post(printheadurl, headers=headers, json=homezdata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogzup(self, *args):
        jogzupdata = {'command': 'jog', 'z': jogincrement}
        try:
            print '[JOG Z UP] Trying /API request to Octoprint...'
            r = requests.post(printheadurl, headers=headers, json=jogzupdata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogzdown(self, *args):
        jogzdowndata = {'command': 'jog', 'z': (jogincrement * -1)}
        try:
            print '[JOG Z UP] Trying /API request to Octoprint...'
            r = requests.post(printheadurl, headers=headers, json=jogzdowndata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def homexy(self, *args):
        homexydata = {'command': 'home', 'axes': ['x', 'y']}
        try:
            print '[HOME X/Y] Trying /API request to Octoprint...'
            r = requests.post(printheadurl, headers=headers, json=homexydata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogleft(self, *args):
        jogleftdata = {'command': 'jog', 'x': jogincrement}
        try:
            print '[JOG LEFT] Trying /API request to Octoprint...'
            print '[JOG LEFT] Data: ' + str(jogleftdata)
            r = requests.post(printheadurl, headers=headers, json=jogleftdata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogright(self, *args):
        jogrightdata = {'command': 'jog', 'x': (jogincrement * -1)}
        try:
            print '[JOG RIGHT] Trying /API request to Octoprint...'
            print '[JOG RIGHT] Data: ' + str(jogrightdata)
            r = requests.post(printheadurl, headers=headers, json=jogrightdata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogforward(self, *args):
        jogforwarddata = {'command': 'jog', 'y': jogincrement}
        try:
            print '[JOG FORWARD] Trying /API request to Octoprint...'
            r = requests.post(printheadurl, headers=headers, json=jogforwarddata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogbackward(self, *args):
        jogbackwarddata = {'command': 'jog', 'y': (jogincrement * -1)}
        try:
            print '[JOG BACKWARD] Trying /API request to Octoprint...'
            r = requests.post(printheadurl, headers=headers, json=jogbackwarddata, timeout=1)
            print 'STATUS CODE: ' + str(r.status_code)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def jogincrement(self, *args):
        global jogincrement
        print '[JOG INCREMENT] Button pressed'
        print '[JOG INCREMENT] INC: ' + str(args[0])
        jogincrement = args[0]

    def connect(self, *args):
        connectiondata = {'command': 'connect', 'port': '/dev/ttyACM0', 'baudrate': 250000, \
                'save': False, 'autoconnect': False}
        try:
            print '[CONNECT] Trying /job API request to Octoprint...'
            print '[CONNECT] ' + connectionurl + str(connectiondata)
            r = requests.post(connectionurl, headers=headers, json=connectiondata, timeout=1)
            print '[CONNECT] STATUS CODE: ' + str(r.status_code)
            print '[CONNECT] RESPONSE: ' + r.text
        except requests.exceptions.RequestException as e:
            print '[CONNECT] ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False

    def disconnect(self, *args):
        disconnectdata = {'command': 'disconnect'}
        try:
            print '[DISCONNECT] Trying /job API request to Octoprint...'
            print '[DISCONNECT] ' + connectionurl + str(disconnectdata)
            r = requests.post(connectionurl, headers=headers, json=disconnectdata, timeout=1)
            print '[DISCONNECT] STATUS CODE: ' + str(r.status_code)
            print '[DISCONNECT] RESPONSE: ' + r.text
        except requests.exceptions.RequestException as e:
            print '[DISCONNECT] ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False
 

    def getstats(self, *args):
        try:
            print 'Trying /job API request to Octoprint...'
            r = requests.get(jobapiurl, headers=headers, timeout=1)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False
        if r and r.status_code == 200:
            printerstate = r.json()['state']
            jobfilename = r.json()['job']['file']['name']
            jobpercent = r.json()['progress']['completion']
            jobprinttime = r.json()['progress']['printTime']
            jobprinttimeleft = r.json()['progress']['printTimeLeft']
            print 'Printer state: ' + printerstate
            print 'Job percent: ' + str(jobpercent) + '%'
            if jobfilename is not None:
                jobfilename = jobfilename[:25] #Shorten filename to 25 characters
                self.ids.jobfilename.text = jobfilename
            else:
                self.ids.jobfilename.text = '-'
            if printerstate is not None:
                self.ids.printerstate.text = printerstate
                self.ids.printerstate2.text = printerstate
            else:
                self.ids.printerstate.text = 'Unknown'
            if jobpercent is not None:
                jobpercent = int(jobpercent)
                self.ids.jobpercent.text = str(jobpercent) + '%'
                self.ids.progressbar.value = jobpercent
            else:
                self.ids.jobpercent.text = '---%'
                self.ids.progressbar.value = 0
            if jobprinttime is not None:
                hours = int(jobprinttime/60/60)
                if hours > 0:
                    minutes = int(jobprinttime/60)-(60*hours)
                else:
                    minutes = int(jobprinttime/60)
                seconds = int(jobprinttime % 60)
                self.ids.jobprinttime.text = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
            else:
                self.ids.jobprinttime.text = '00:00:00'
            if jobprinttimeleft is not None:
                hours = int(jobprinttimeleft/60/60)
                if hours > 0:
                    minutes = int(jobprinttimeleft/60)-(60*hours)
                else:
                    minutes = int(jobprinttimeleft/60)
                seconds = int(jobprinttimeleft % 60)
                self.ids.jobprinttimeleft.text = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
            else:
                self.ids.jobprinttimeleft.text = '00:00:00'

        else:
            if r:
                print 'Error. API Status Code: ' + str(r.status_code) #Print API status code if we have one
            #If we can't get any values from Octoprint API fill with these values.
            self.ids.jobfilename.text = 'N/A'
            self.ids.printerstate.text = 'Unknown'
            self.ids.jobpercent.text = 'N/A'
            self.ids.progressbar.value = 0
            self.ids.jobprinttime.text = '--:--:--'
            self.ids.jobprinttimeleft.text = '--:--:--'

    def updateipaddr(self, *args):
        global platform
        global nicname #Network card name from config file
        if 'linux' in platform or 'Linux' in platform:
            cmd = "ip addr show " + nicname + " | grep inet | awk '{print $2}' | cut -d/ -f1"
            p = Popen(cmd, shell=True, stdout=PIPE)
            output = p.communicate()[0]
            self.ids.ipaddr.text = output
        else:
            self.ids.ipaddr.text = 'Unknown Platform'
    
    def graphpoints(self, *args):
        hotendactual_plot = SmoothLinePlot(color=[1, 0, 0, 1])
        hotendtarget_plot = MeshLinePlot(color=[1, 0, 0, .75])
        bedactual_plot = SmoothLinePlot(color=[0, 0, 1, 1])
        bedtarget_plot = MeshLinePlot(color=[0, 0, 1, .75])
        #Build list of plot points tuples from temp and time lists
        ##FIXME - Need to reduce the number of points on the graph. 360 is overkill
        hotendactual_points_list = []
        hotendtarget_points_list = []
        bedactual_points_list = []
        bedtarget_points_list = []
        for i in range(360):
            hotendactual_points_list.append( (graphtime_list[i]/1000.0*-1, hotendactual_list[i]) )
            hotendtarget_points_list.append( (graphtime_list[i]/1000.0*-1, hotendtarget_list[i]) )
            bedactual_points_list.append( (graphtime_list[i]/1000.0*-1, bedactual_list[i]) )
            bedtarget_points_list.append( (graphtime_list[i]/1000.0*-1, bedtarget_list[i]) )

        #Remove all old plots from the graph before drawing new ones
        for plot in self.my_graph.plots:
            self.my_graph.remove_plot(plot)

        #Draw the new graphs
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
        Clock.schedule_once(panels.gettemps, 0.5) #Update bed and hotend temps every 5 seconds
        Clock.schedule_interval(panels.gettemps, 5) #Update bed and hotend temps every 5 seconds

        Clock.schedule_interval(panels.getstats, 5) #Update job stats every 5 seconds

        Clock.schedule_once(panels.updateipaddr, 0.5) #Update IP addr once right away
        Clock.schedule_interval(panels.updateipaddr, 30) #Then update IP every 30 seconds

        Clock.schedule_interval(panels.graphpoints, 10) #Update IP addr once right away
        #return Panels()
        return panels


if __name__ == '__main__':
    TabbedPanelApp().run()
