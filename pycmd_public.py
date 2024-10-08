"""
Public constants, objects and utilities exported by PyCmd.

These are meant to be used in init.py files; users can rely on them being kept
unchanged (interface-wise) throughout later versions.
"""
from __future__ import print_function

import os, sys, common, console

py2 = sys.version_info[0] == 2


def run(cmd, timeout_sec=None):
    import shlex
    from subprocess import Popen, PIPE
    from threading import Timer
    finished = False
    stdout = ""
    stderr = ""
    if timeout_sec != -1:
        proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
        if timeout_sec:
            timer = Timer(timeout_sec, proc.kill)
            try:
                timer.start()
                stdout, stderr = proc.communicate()
            finally:
                finished = timer.is_alive()
                timer.cancel()
        else:
            stdout, stderr = proc.communicate()
            finished = True
    if not py2:
        stderr = stderr.decode()
        stdout = stdout.decode()
    return finished, stdout, stderr


def abbrev_path(path = None):
    """
    Abbreviate a full path (or the current path, if None is provided) to make
    it shorter, yet still unambiguous.

    This function takes a directory path and tries to abbreviate it as much as
    possible while making sure that the resulting shortened path is not
    ambiguous: a path element is only abbreviated if its shortened form is
    unique in its directory (in other words, if a sybling would have the same
    abbreviation, the original name is kept).

    The abbreviation is performed by keeping only the first letter of each
    "word" composing a path element. "Words" are defined by CamelCase,
    underscore_separation or "whitespace separation".

    Before the abbreviation is performed, a leading home-dir is
    replaced with "~"
    """
    if not path:
        path = os.getcwd()
        path = path[0].upper() + path[1:]

    if path.lower().startswith(os.path.expanduser('~').lower()):
        # Replace home directory with ~
        current_dir = os.path.expanduser('~')
        path = path[len(os.path.expanduser('~')) + 1:]
        path_abbrev = '~'
    else:
        current_dir = path[ : 3]
        path = path[3 : ]
        path_abbrev = current_dir[ : 2]

    for elem in path.split('\\')[ : -1]:
        elem_abbrev = common.abbrev_string(elem)
        for other in os.listdir(current_dir):
            if os.path.isdir(current_dir + '\\' + other) and common.abbrev_string(other).lower() == elem_abbrev.lower() and other.lower() != elem.lower():
                # Found other directory with the same abbreviation
                # In this case, we use the entire name
                elem_abbrev = elem
                break
        current_dir += '\\' + elem
        path_abbrev += '\\' + elem_abbrev

    return path_abbrev if path_abbrev == '~' and not path else path_abbrev + '\\' + path.split('\\')[-1]


def find_updir(name, path=None):
    """
    Look for a file/directory named "name" in a given directory and all the
    ancestor directories. 
    If no starting directory is provided, the CWD is assumed.
    """
    if not path:
        path = os.getcwd()

    found = None
    while len(path) > 3:
        if os.path.exists(os.path.join(path, name)):
            found = os.path.join(path, name)
            break
        path = os.path.dirname(path)
        
    return found

def get_build_info():
    import platform
    arch_names = { '32bit': 'x86', '64bit': 'x64' }
    bits = platform.architecture()[0]
    arch = arch_names[bits]
    try:
        from buildinfo import build_version, build_date
    except ImportError as ie:
        build_version = None
        build_date = None
    return build_version, build_date, arch


def default_welcome():
    """
    Print some splash text.
    """
    build_version, build_date, arch = get_build_info()
    if not build_date:
        build_date = '<no build date>'
    print()
    print('Welcome to PyCmd %s-%s!' % (build_date, arch))
    print()


def default_good_bye():
    """
    Return some good-bye text.
    """
    return "Bye!"


def windows_cmd_welcome():
    """
    Print a welcome text similar to the default one of Windows cmd.exe
        Microsoft Windows [Version 10.0.22000.1219]
        (c) Microsoft Corporation. All rights reserved.
    """
    finished, stdout, stderr = run("cmd /c ver", 1)
    print(stdout.strip())
    print("(c) Microsoft Corporation. All rights reserved.")
    build_version, build_date, arch = get_build_info()
    if build_version and build_date:
        version_str = "%s-%s-%s" % (build_version, arch, build_date)
    else:
        version_str = "<no build info>-%s" % (arch)
    print("[PyCmd " + version_str + ": " + color.Fore.GREEN + "ON" + color.Fore.DEFAULT + "]")


def windows_cmd_good_bye():
    """
    Return some good-bye text fitting to the windows_cmd_welcome function.
    """
    return "[PyCmd: " + color.Fore.RED + "OFF" + color.Fore.DEFAULT + "]"


def prompt_prefix():
    """
    For optionally prefixing all prompts with an additional 'global' prefix,
    e.g., to display a named environment setup a la "[Py3] [master]>".
    """
    return ""


def get_errorlevel():
    if os.environ['ERRORLEVEL'] in ['0', '141']:
        errorlevel = ''
    else:
        errorlevel = (':' + color.Back.RED + color.Fore.WHITE + os.environ['ERRORLEVEL']
                      + color.Back.DEFAULT + color.Fore.DEFAULT + appearance.colors.prompt)
    return errorlevel

def windows_cmd_prompt():
    """
    Return a prompt similar to the default one of Windows cmd.exe.
    """
    path = os.getcwd()
    if py2:
        path = path.decode(sys.getfilesystemencoding())
    return color.Fore.DEFAULT + path + get_errorlevel() + '>'


def windows_cmd_prompt_short():
    """
    Return a prompt similar to the default one of Windows cmd.exe,
    but shortening very long directory names.
    """
    import win32api
    path = os.getcwd()
    if py2:
        path = path.decode(sys.getfilesystemencoding())
    path = win32api.GetShortPathName(path)
    return color.Fore.DEFAULT + path + get_errorlevel() + '>'


def simple_prompt():
    """
    Return a prompt containg the current path (abbreviated) plus the ERRORLEVEL
    of the previous command.

    This is the default PyCmd prompt. It uses the abbrev_path() function to
    obtain the shortened path and appends the ERRORLEVEL plus the typical '> '.
    """
    # When this is called, the current color is DEFAULT + appearance.colors.prompt
    if os.environ['ERRORLEVEL'] != '0' and os.environ['ERRORLEVEL'] != '141':
        # 141 is not usually an actual error, as it is returned when a
        # SIGPIPE occurs with a command whose output is piped into a
        # pager (such as less). A common example is `git log`, see
        # e.g. https://lore.kernel.org/git/YAG%2FvzctP4JwSp5x@zira.vinc17.org/
        # Note that other shells (e.g. fish) also hide this particular
        # exit value!
        errorlevel = (color.Fore.TOGGLE_BRIGHT + ':' + color.Fore.TOGGLE_BRIGHT
                      + color.Back.RED + color.Back.TOGGLE_BRIGHT
                      + color.Fore.WHITE + color.Fore.SET_BRIGHT
                      + os.environ['ERRORLEVEL']
                      + color.Back.DEFAULT + color.Fore.DEFAULT + appearance.colors.prompt)
    else:
        errorlevel = ''
    return abbrev_path() + errorlevel + '>' + color.Fore.DEFAULT + color.Back.DEFAULT + ' '


def git_prompt():
    """
    Custom prompt for git repositories.

    This prompt displays:
      * the name of the current git branch
      * "dirty" indicator 
      * count of unpushed/unpulled commits
    in addition to the typical "abbreviated current path" PyCmd prompt.

    Requires git to be present in the PATH.
    """
    # Many common modules (sys, os, subprocess, time, re, ...) are readily
    # shipped with PyCmd, you can directly import them for use in your
    # configuration script. If you need extra modules that are not bundled,
    # manipulate the sys.path so that they can be found (just make sure that the
    # version is compatible with the one used to build PyCmd -- check
    # README.txt)
    import re

    prompt = ''

    finished, stdout, stderr = run('git status -b --porcelain -uno', appearance.cvs_timeout)
    if finished and not stderr:
        lines = stdout.split('\n')
        match_branch = re.match(r'## (.+)\.\.\.(.+)?.*', lines[0])
        if not match_branch:
            finished, stdout, stderr = run('git describe --exact-match --tags HEAD',
                                           appearance.cvs_timeout)
            if finished and not stderr:
                # Maybe it's a tag
                tag_lines = stdout.split('\n')
                match_branch = re.match('(.+)', tag_lines[0])
            if not match_branch:
                # Fallback
                match_branch = re.match('## (.+)', lines[0])
        if match_branch:
            branch_name = match_branch.group(1)
            ahead = behind = ''
            match_ahead_behind = re.match(r'## .* \[(ahead (\d+))?(, )?(behind (\d+))?\]', lines[0])
            if match_ahead_behind:
                ahead = match_ahead_behind.group(2)
                behind = match_ahead_behind.group(5)
            dirty_files = lines[1:-1]
            mark = ''
            dirty = any(line[1] in ['M', 'D'] for line in dirty_files)
            staged = any(line[0] in ['A', 'M', 'D', 'R'] for line in dirty_files)
            if dirty:
                mark = color.Fore.RED + '*'
            if staged:
                mark = color.Fore.GREEN + '*'
            ahead = '+' + ahead if ahead else ''
            behind = '-' + behind if behind else ''
            prompt += (color.Fore.DEFAULT + '[' +
                       color.Fore.YELLOW + mark +
                       color.Fore.YELLOW + branch_name +
                       color.Fore.GREEN + ahead +
                       color.Fore.RED + behind +
                       color.Fore.DEFAULT + ']' +
                       ' ')
    else:
        prompt += (color.Fore.DEFAULT + '[?] ')
        
    prompt += color.Fore.DEFAULT + appearance.colors.prompt + appearance.simple_prompt()
    return prompt


def svn_prompt():
    """Custom prompt function for a SVN repository

    This prompt displays a dirty indicator if the current directory is under SVN
    control and the working copy is dirty.

    Requires svn to be present in the PATH.

    """
    prompt = ''
    path = abbrev_path()
    finished, stdout, stderr = run('svn stat -q', appearance.cvs_timeout)
    prompt += color.Fore.DEFAULT + '['
    if finished and not stderr:
        dirty = any(line[0] in ['M', 'A', 'D'] for line in stdout)
        if dirty:
            prompt += color.Fore.RED + '*'
        else:
            prompt += color.Fore.GREEN + '=' 
    else:
        prompt += '?' 
    prompt += color.Fore.DEFAULT + ']' + ' '

    prompt += color.Fore.DEFAULT + appearance.colors.prompt + appearance.simple_prompt()
    return prompt


def universal_prompt():
    """
    Universal prompt function

    This function selects the appropriate prompt sub-function (simple prompt,
    git prompt, svn prompt) based on the current directory.
    """
    if find_updir('.git'):
        return appearance.git_prompt()
    elif find_updir('.svn'):
        return appearance.svn_prompt()
    else:
        return appearance.simple_prompt()


class color(object):
    """
    Constants for color manipulation within PyCmd.

    These constants are similar to ANSI escape sequences, only more powerful in
    the sense that they support setting, resetting and toggling of individual R,
    G, B components
    """

    class Fore(object):
        """Color constants for the foreground"""

        # For individually setting a RGB field
        SET_RED = chr(27) + 'FSR'
        SET_GREEN = chr(27) + 'FSG'
        SET_BLUE = chr(27) + 'FSB'
        SET_BRIGHT = chr(27) +'FSX'

        # For individually clearing a RGB field
        CLEAR_RED = chr(27) + 'FCR'
        CLEAR_GREEN = chr(27) + 'FCG'
        CLEAR_BLUE = chr(27) + 'FCB'
        CLEAR_BRIGHT = chr(27) + 'FCX'

        # For individually toggling a RGB field
        TOGGLE_RED = chr(27) + 'FTR'
        TOGGLE_GREEN = chr(27) + 'FTG'
        TOGGLE_BLUE = chr(27) + 'FTB'
        TOGGLE_BRIGHT = chr(27) + 'FTX'


        # Standard colors defined as combinations of the RGB constants
        BLACK = CLEAR_RED + CLEAR_GREEN + CLEAR_BLUE
        RED = SET_RED + CLEAR_GREEN + CLEAR_BLUE
        GREEN = CLEAR_RED + SET_GREEN + CLEAR_BLUE
        YELLOW = SET_RED + SET_GREEN + CLEAR_BLUE
        BLUE = CLEAR_RED + CLEAR_GREEN + SET_BLUE
        MAGENTA = SET_RED + CLEAR_GREEN + SET_BLUE
        CYAN = CLEAR_RED + SET_GREEN + SET_BLUE
        WHITE = SET_RED + SET_GREEN + SET_BLUE

        # Default terminal color
        DEFAULT = console.get_current_foreground()


    class Back(object):
        """Color constants for the background"""

        # For individually setting a RGB field
        SET_RED = chr(27) + 'BSR'
        SET_GREEN = chr(27) + 'BSG'
        SET_BLUE = chr(27) + 'BSB'
        SET_BRIGHT = chr(27) +'BSX'

        # For individually clearing a RGB field
        CLEAR_RED = chr(27) + 'BCR'
        CLEAR_GREEN = chr(27) + 'BCG'
        CLEAR_BLUE = chr(27) + 'BCB'
        CLEAR_BRIGHT = chr(27) + 'BCX'

        # For individually toggling a RGB field
        TOGGLE_RED = chr(27) + 'BTR'
        TOGGLE_GREEN = chr(27) + 'BTG'
        TOGGLE_BLUE = chr(27) + 'BTB'
        TOGGLE_BRIGHT = chr(27) + 'BTX'

        # Standard colors defined as combinations of the RGB constants
        BLACK = CLEAR_RED + CLEAR_GREEN + CLEAR_BLUE
        RED = SET_RED + CLEAR_GREEN + CLEAR_BLUE
        GREEN = CLEAR_RED + SET_GREEN + CLEAR_BLUE
        YELLOW = SET_RED + SET_GREEN + CLEAR_BLUE
        BLUE = CLEAR_RED + CLEAR_GREEN + SET_BLUE
        MAGENTA = SET_RED + CLEAR_GREEN + SET_BLUE
        CYAN = CLEAR_RED + SET_GREEN + SET_BLUE
        WHITE = SET_RED + SET_GREEN + SET_BLUE

        # Default terminal color
        DEFAULT = console.get_current_background()

    @staticmethod
    def update():
        """
        Update the current values of the DEFAULT color constant -- we have
        to adapt these since they might change (e.g. with the "color"
        command).
        """
        color.Back.DEFAULT = console.get_current_background()
        color.Fore.DEFAULT = console.get_current_foreground()

    @staticmethod
    def back_to_fore(other):
        return other.replace(chr(27) + 'B', chr(27) + 'F')


class _Settings(object):
    """
    Generic settings class; extend this to create a "group" of options
    (accessible as instance members in the settings.py files)
    """
    def sanitize(self):
        """Make sure the settings have sane values"""
        pass


class _Appearance(_Settings):
    """Appearance settings"""

    class _ColorSettings(_Settings):
        """Color-related settings"""
        def __init__(self):
            self.text = ''
            self.prompt = color.Fore.TOGGLE_BRIGHT
            self.selection = (color.Fore.TOGGLE_RED +
                              color.Fore.TOGGLE_GREEN +
                              color.Fore.TOGGLE_BLUE +
                              color.Back.TOGGLE_RED +
                              color.Back.TOGGLE_GREEN +
                              color.Back.TOGGLE_BLUE)
            self.search_filter = (color.Back.TOGGLE_RED +
                                  color.Back.TOGGLE_BLUE +
                                  color.Fore.TOGGLE_BRIGHT)
            self.completion_match = color.Fore.TOGGLE_RED
            self.dir_history_selection = (color.Fore.TOGGLE_BRIGHT +
                                          color.Back.TOGGLE_BRIGHT)
            self.suggestion = color.back_to_fore(color.Back.DEFAULT) + color.Fore.TOGGLE_BRIGHT

    def __init__(self):
        # Prompt function (should return a string)
        self.prompt = universal_prompt

        # Some predefined prompts
        self.prompt_prefix = prompt_prefix
        self.simple_prompt = windows_cmd_prompt  # simple_prompt
        
        self.git_prompt = git_prompt
        self.svn_prompt = svn_prompt
        # The timeout in seconds for the SVN/Git status to be displayed:
        # On large repositories the status check might take several seconds,
        # thus the default value is 0.25 to prevent a 'hanging' command prompt.
        # 'None' or '0' unlimits the status check timeout. '-1' deactivates it.
        self.cvs_timeout = 0.25

        # Color configuration
        self.colors = self._ColorSettings()

        # Welcome and good-bye variants
        self.welcome = windows_cmd_welcome  # default_welcome
        self.good_bye = windows_cmd_good_bye  # default_good_bye

    def sanitize(self):
        if not callable(self.prompt):
            print('Prompt function doesn\'t look like a callable; reverting to PyCmd\'s default prompt')
            self.prompt = simple_prompt


class Behavior(_Settings):
    """Behavior settings"""
    def __init__(self):
        # Skip splash message (welcome and bye).
        # This can be also overriden with the '-Q' command line argument'
        self.quiet_mode = False

        # Enable delayed expansion of environment variables (this is
        # required for proper handling of ERRORLEVEL and should only
        # be disabled for compatibility reasons
        # Can be overridden with the '-V:OFF' command line argument
        self.delayed_expansion = True

        # Select the completion mode; currently supported: 'bash' and 'zsh'
        self.completion_mode = 'zsh'
    
        # Maximum allowed command history length
        self.max_cmd_history_length = 2000
    
        # Maximum allowed directory history length (if the history
        # gets too long it becomes hard to navigate)
        self.max_dir_history_length = 9
        
        # String with a fixed list of directories separated via linebreaks
        # (or alternatively a python list of strings) which can be listed
        # and navigated just like the direcory history, but with SHIFT + ALT + D.
        self.directory_favorites = []

    def sanitize(self):
        if not self.completion_mode in ['bash', 'zsh']:
            print('Invalid setting "' + self.completion_mode + '" for "completion_mode" -- using default "zsh"')
            self.completion_mode = 'zsh'


# Initialize global configuration instances with default values
#
# These objects are directly manipulated by the settings.py files, executed via
# apply_settings(). Then, they are directly used by PyCmd.py to get the current
# configuration settings
appearance = _Appearance()
behavior = Behavior()
