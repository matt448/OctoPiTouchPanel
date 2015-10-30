
#kivy imports
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.config import Config
from kivy.core.window import Window

#other imports
import time
import requests
import json
import ConfigParser
from subprocess import *




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


start_time = time.time()

Builder.load_string("""
<Panels>:
    size_hint: 1, 1
    pos_hint: {'center_x': .5, 'center_y': .5}
    do_default_tab: False
    #Tab1
    TabbedPanelItem:
        text: 'Status'
        BoxLayout:
            GridLayout:
                cols: 2
                Label:
                    font_size: 24
                    text: 'Hot End Temp'
                Label:
                    id: hotend_temp
                    font_size: 24
                    text: '0.0'
                Label:
                    font_size: 24
                    text: 'Bed Temp'
                Label:
                    id: bed_temp
                    font_size: 24
                    text: '0.1'
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
    pass


class TabbedPanelApp(App):
    def build(self):
        Window.size = (800, 480)
        return Panels()

if __name__ == '__main__':
    TabbedPanelApp().run()
