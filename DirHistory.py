import os, sys
import os.path
from console import get_cursor, move_cursor, get_buffer_size
from sys import stdout
from common import abbrev_tilde
from pycmd_public import appearance, color, behavior

def _norm(path):
    return os.path.normcase(os.path.expanduser(path))

class DirHistory:
    """
    Handle a history of visited directories, somewhat similar to a browser
    history.
    """

    def __init__(self):
        """Create an empty directory history"""
        self.locations = []
        self.index = -1
        self.keep = True

    def go_left(self):
        """Go to the previous location (checks whether it's still valid)"""
        self.index -= 1
        if self.index < 0:
            self.index = len(self.locations) - 1
        return self._apply()

    def go_right(self):
        """Go to the next location (checks whether it's still valid)"""
        self.index += 1
        if self.index >= len(self.locations):
            self.index = 0
        return self._apply()

    def jump(self, location):
        """Jump to the specified location (this must be an actual entry from the locations list!)"""
        self.index = self.locations.index(location)
        return self._apply()

    def _apply(self):
        """Change to the currently selected directory (checks if still valid)"""
        try:
            os.chdir(os.path.expanduser(self.locations[self.index]))
            self.keep = True  # keep saved entries even if no command is executed
        except OSError as error:
            stdout.write('\n  ' + str(error) + '\n')
            self.locations.pop(self.index) 
            self.index -= 1
            if self.index < 0:
                self.index = len(self.locations) - 1
            self.shown = False
        return

    def visit_cwd(self):
        """Add the current directory to the history of visited locations"""
        cwd = abbrev_tilde(os.getcwd())
        if self.locations and _norm(cwd) == _norm(self.locations[self.index]):
            return

        if self.keep:
            # some command has actually executed here, keep this location
            self.locations.insert(self.index + 1, cwd)
            self.index += 1
        else:
            # discard current location, we were just passing by
            self.locations[self.index] = cwd

        # by default we don't keep a new location, if a command is executed here at
        # a later time the flag will be marked True then
        self.keep = False

        # remove duplicates
        self.locations = ([l for l in self.locations[:self.index] if _norm(l) != _norm(cwd)]
                          + [cwd]
                          + [l for l in self.locations[self.index + 1:] if _norm(l) != _norm(cwd)])
        self.index = self.locations.index(cwd)

        # rotate the history so that the current directory is last
        self.locations = self.locations[self.index + 1:] + self.locations[:self.index + 1]

        # shorten
        self.locations = self.locations[-behavior.max_dir_history_length:]
        self.index = len(self.locations) - 1
