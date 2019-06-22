from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from mopidy import commands
import json

def pprint(x):
    print(json.dumps(x, indent=2))

class LagukanCommand(commands.Command):

    def __init__(self):
        super(LagukanCommand, self).__init__()
        self.add_child('refresh', RefreshCommand())

class RefreshCommand(commands.Command):
    def run(self, args, config):
        print(args.registry)
