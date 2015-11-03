
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




# Define Octoprint constants
settings = ConfigParser.ConfigParser()
settings.read('octoprint.cfg')
host = settings.get('APISettings', 'host')
nicname = settings.get('APISettings', 'nicname')
apikey = settings.get('APISettings', 'apikey')
printerapiurl = 'http://'+ host + '/api/printer'
printheadurl = 'http://'+ host + '/api/printer/printhead'
jobapiurl = 'http://' + host + '/api/job'
headers = {'X-Api-Key': apikey, 'content-type': 'application/json'}
print headers

bed_temp_val = 0.0
hotend_temp_val = 0.0

platform = sys.platform

start_time = time.time()

Builder.load_string("""
<Panels>:
    size_hint: 1, 1
    pos_hint: {'center_x': .5, 'center_y': .5}
    do_default_tab: False
    #Tab1
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
                    size_hint: (1, .25)
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
            r = requests.get(printerapiurl, headers=headers, timeout=0.5)
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
            r = requests.get(jobapiurl, headers=headers, timeout=0.5)
        except requests.exceptions.RequestException as e:
            print 'ERROR: Couldn\'t contact Octoprint /job API'
            print e
            r = False
        if r and r.status_code == 200:
            printerstate = r.json()['state']
            jobfilename = r.json()['job']['file']['name']
            jobpercent = r.json()['progress']['completion']
            jobprinttime = r.json()['progress']['printTime']
            jobprinttimeleft = r.json()['job']['estimatedPrintTime']
            print 'Printer state: ' + printerstate
            print 'Job percent: ' + str(jobpercent) + '%'
            if jobfilename is not None:
                self.ids.jobfilename.text = jobfilename
            if printerstate is not None:
                self.ids.printerstate.text = printerstate
            if jobpercent is not None:
                self.ids.jobpercent.text = str(jobpercent) + '%'
                self.ids.progressbar.value = jobpercent
            if jobprinttime is not None:
                hours = int(jobprinttime/60/60)
                if hours > 0:
                    minutes = int(jobprinttime/60)-(60*hours)
                else:
                    minutes = int(jobprinttime/60)
                seconds = int(jobprinttime % 60)
                self.ids.jobprinttime.text = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
        else:
            if r:
                print 'Error. API Status Code: ' + str(r.status_code) #Print API status code if we have one
            #If we can't get any values from Octoprint just fill values with not available.
            self.ids.jobfilename.text = 'N/A'
            self.ids.printerstate.text = 'Unknown'
            self.ids.jobpercent.text = 'N/A'
            self.ids.progressbar.value = 0


    def updateipaddr(self, *args):
        global platform
        global nicname
        if 'linux' in platform or 'Linux' in platform:
            cmd = "ip addr show " + nicname + " | grep inet | awk '{print $2}' | cut -d/ -f1"
            p = Popen(cmd, shell=True, stdout=PIPE)
            output = p.communicate()[0]
            self.ids.ipaddr.text = output
        else:
            self.ids.ipaddr.text = 'Unknown Platform'

class TabbedPanelApp(App):
    def build(self):
        Window.size = (800, 480)
        panels = Panels()
        Clock.schedule_interval(panels.gettemps, 5) #Update bed and hotend temps every 5 seconds
        Clock.schedule_interval(panels.getstats, 5) #Update bed and hotend temps every 5 seconds
        Clock.schedule_once(panels.updateipaddr, 0.5) #Update IP addr once right away
        Clock.schedule_interval(panels.updateipaddr, 30) #Then update IP every 30 seconds
        #return Panels()
        return panels


if __name__ == '__main__':
    TabbedPanelApp().run()
