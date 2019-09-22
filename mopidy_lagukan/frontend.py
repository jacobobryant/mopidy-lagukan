import pykka

from mopidy import core
import webbrowser

class LagukanFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(LagukanFrontend, self).__init__()
        if config.get('autostart', True):
            webbrowser.open("http://localhost:6680/lagukan")
