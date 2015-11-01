
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

#other imports
import time
import requests
import json
import ConfigParser
from subprocess import *
import pprint




# Define Octoprint constants
settings = ConfigParser.ConfigParser()
settings.read('octoprint.cfg')
host = settings.get('APISettings', 'host')
apikey = settings.get('APISettings', 'apikey')
printerapiurl = 'http://'+ host + '/api/printer'
printheadurl = 'http://'+ host + '/api/printer/printhead'
jobapiurl = 'http://' + host + '/api/job'
headers = {'X-Api-Key': apikey, 'content-type': 'application/json'}
print headers

bed_temp_val = 0.0
hotend_temp_val = 0.0

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
            GridLayout:
                cols: 2
                Label:
                    font_size: 30
                    bold: True
                    halign: 'right'
                    text: 'Hot End:'
                Label:
                    id: hotend_temp
                    font_size: 30
                    bold: True
                    text: 'N/A' + u"\u00b0" + ' C'
                Label:
                    font_size: 30
                    bold: True
                    halign: 'right'
                    text: 'Bed:'
                Label:
                    id: bed_temp
                    font_size: 30
                    bold: True
                    text: 'N/A' + u"\u00b0" + ' C'
            Label:
                text: 'Graph Area'
            
    #Tab2
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

    #Tab3
    TabbedPanelItem:
        text: 'Settings'
        RstDocument:
            text:
                '\\n'.join(("Hello world", "-----------",
                "You are in the third tab."))
""")


class Panels(TabbedPanel):
    def gettemps(self, *args):
        r = requests.get(printerapiurl, headers=headers)
        if r.status_code == 200:
            printeronline = True 
            hotendactual = r.json()['temperature']['tool0']['actual']
            hotendtarget = r.json()['temperature']['tool0']['target']
            hotmsg = ('Hotend:') + str(hotendactual) + chr(223) + '/' + str(hotendtarget) + chr(223)
            bedactual = r.json()['temperature']['bed']['actual']
            bedtarget = r.json()['temperature']['bed']['target']
            print bedactual
            print hotendactual
            self.ids.bed_temp.text = str(bedactual) + u"\u00b0" + ' C'
            self.ids.hotend_temp.text = str(hotendactual)  + u"\u00b0" + ' C'
        else:
            print 'Error. Status Code: ' + r.status_code

class TabbedPanelApp(App):
    def build(self):
        Window.size = (800, 480)
        panels = Panels()
        Clock.schedule_interval(panels.gettemps, 5)
        #return Panels()
        return panels


if __name__ == '__main__':
    TabbedPanelApp().run()
