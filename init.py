from __future__ import print_function

from datetime import datetime
import os
import platform
import sys

from pycmd_public import appearance, behavior, color

py2 = sys.version_info[0] == 2


def windows_cmd_like_prompt():
    path = os.getcwd()
    if py2:
        path = path.decode(sys.getfilesystemencoding())
    # import win32api
    # path = win32api.GetShortPathName(path)
    return color.Fore.DEFAULT + path + '>'


cmd_quiet_mode = ['/Q', '-Q']
cmd_switches = [arg.upper() for arg in sys.argv]
if not any(switch in cmd_quiet_mode for switch in cmd_switches):
    print('Microsoft Windows [Version %s]' % platform.version())
    print('(c) %s Microsoft Corporation. All rights reserved.' % datetime.now().year)

appearance.simple_prompt = windows_cmd_like_prompt
behavior.quiet_mode = True
behavior.completion_mode = 'bash'
