import pykka

from mopidy import core
import webbrowser

class LagukanFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(LagukanFrontend, self).__init__()
        webbrowser.open("http://localhost:6680/lagukan")
        self.core = core

    def playback_state_changed(self, old_state, new_state):
        if new_state == "stopped":
            self.core.tracklist.clear()
