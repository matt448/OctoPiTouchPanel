
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
headers = {'X-Api-Key': apikey, 'content-type': 'application/json'}
print headers

bed_temp_val = 0.0
hotend_temp_val = 0.0

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
            Button:
                text: 'Button 1'
                size_hint: (.10, .10)
                pos: 100, 100
            Button:
                text: 'Button 2'
                size_hint: (.10, .10)
                pos: 200, 100
            Button:
                text: 'Button 3'
                size_hint: (.10, .10)
                pos: 300, 100
            ProgressBar:
                id: pb
                size_hint_x: .5
                size_hint_y: None
                height: '64dp'
                value: 73

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
        if r and r.status_code == 200:
            printeronline = True 
            hotendactual = r.json()['temperature']['tool0']['actual']
            hotendtarget = r.json()['temperature']['tool0']['target']
            bedactual = r.json()['temperature']['bed']['actual']
            bedtarget = r.json()['temperature']['bed']['target']
            print bedactual
            print hotendactual
            
            print 'hotendactual_list length: ' + str(len(hotendactual_list))
            print hotendactual_list
            print hotendactual_list[358]
            print hotendactual_list[359]
            hotendactual_list.popleft()
            hotendactual_list.append(hotendactual)
            print 'hotendactual_list length: ' + str(len(hotendactual_list))
            print hotendactual_list
            print hotendactual_list[358]
            print hotendactual_list[359]


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
                self.ids.jobfilename.text = jobfilename
            else:
                self.ids.jobfilename.text = '-'
            if printerstate is not None:
                self.ids.printerstate.text = printerstate
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
            self.ids.jobprinttime = '00:00:00'
            self.ids.jobprinttimeleft = '00:00:00'

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
        plot = SmoothLinePlot(color=[1, 0, 0, 1])
        #Build the plot points list
        points_list = []
        for i in range(360):
            points_list.append( (graphtime_list[i]/1000.0*-1, hotendactual_list[i]) )

        #Remove old plots from the graph before drawing new ones
        for plot in self.my_graph.plots:
            self.my_graph.remove_plot(plot)
        #plot.points = [(-30, 150), (-29, 150), (-28, 150), (-27, 150), (-26, 0)]

        #Draw the new graph
        plot.points = points_list
        self.my_graph.add_plot(plot)

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
