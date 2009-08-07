from common import parse_line
from completion import complete_file, complete_env_var
import win32clipboard as wclip

# Stop points when navigating one word at a time
word_sep = [' ', '\t', '\\', '-', '_', '.']

class InputState:
    """
    Handles the current state of the input line:
        * user input chars
        * displaying the prompt and command line
        * handling text selection and Cut/Copy/Paste
        * the command history
    """
    
    def __init__(self):

        # Current state of the input line
        self.prompt = ''
        self.before_cursor = ''
        self.after_cursor = ''

        # Previous state of the input line
        self.prev_prompt = ''
        self.prev_before_cursor = ''
        self.prev_after_cursor = ''

        # History
        self.history = []
        self.history_filter = ''
        self.history_index = 0

        # Text selection
        self.selection_start = -0

    def step_line(self):
        """Prepare for a new key event"""
        self.prev_prompt = self.prompt
        self.prev_before_cursor = self.before_cursor
        self.prev_after_cursor = self.after_cursor

    def reset_line(self, prompt):
        """Prepare for a new input line"""
        self.prompt = prompt
        self.before_cursor = ''
        self.after_cursor = ''
        self.reset_prev_line()

    def reset_prev_line(self):
        """Reset previous line (current line will repaint as new)"""
        self.prev_prompt = ''
        self.prev_before_cursor = ''
        self.prev_after_cursor = ''

    def changed(self):
        """Check whether a change has occurred in the input state (e.g. for repaint)"""
        return self.prompt != self.prev_prompt \
               or self.before_cursor != self.prev_before_cursor \
               or self.after_cursor != self.prev_after_cursor

    def key_left(self, select=False):
        """
        Move cursor one position to the left
        Also handle text selection according to flag
        """
        if self.before_cursor != '':
            self.after_cursor = self.before_cursor[-1] + self.after_cursor
            self.before_cursor = self.before_cursor[0 : -1]
        if not select:
            self.reset_selection()
        else:
            self.reset_history()

    def key_right(self, select=False):
        """
        Move cursor one position to the right
        Also handle text selection according to flag
        """
        if self.after_cursor != '':
            self.before_cursor = self.before_cursor + self.after_cursor[0]
            self.after_cursor = self.after_cursor[1 : ]
        if not select:
            self.reset_selection()
        else:
            self.reset_history()

    def key_home(self, select=False):
        """
        Home key
        Also handle text selection according to flag
        """
        self.after_cursor = self.before_cursor + self.after_cursor
        self.before_cursor = ''
        if not select:
            self.reset_selection()
        else:
            self.reset_history()


    def key_end(self, select=False):
        """
        End key
        Also handle text selection according to flag
        """
        self.before_cursor = self.before_cursor + self.after_cursor
        self.after_cursor = ''
        if not select:
            self.reset_selection()
        else:
            self.reset_history()


    def key_left_word(self, select=False):
        """Move backward one word (Ctrl-Left)"""
        # Skip spaces
        while self.before_cursor != '' and self.before_cursor[-1] in  word_sep:
            self.key_left(select)

        # Jump over word
        while self.before_cursor != '' and not self.before_cursor[-1] in word_sep:
            self.key_left(select)

    def key_right_word(self, select=False):
        """Move forward one word (Ctrl-Right)"""
        # Skip spaces
        while self.after_cursor != '' and self.after_cursor[0] in word_sep:
            self.key_right(select)

        # Jump over word
        while self.after_cursor != '' and not self.after_cursor[0] in word_sep:
            self.key_right(select)

    def key_backspace_word(self):
        """Delte backwards one word (Ctrl-Left), or delete selection"""
        if self.get_selection() != '':
            self.delete_selection()
        else:
            # Skip spaces
            while self.before_cursor != '' and self.before_cursor[-1] in word_sep:
                self.key_backspace()

            # Jump over word
            while self.before_cursor != '' and not self.before_cursor[-1] in word_sep:
                self.key_backspace()

    def key_del_word(self):
        """Delete forwards one word (Ctrl-Right), or delete selection"""
        if self.get_selection() != '':
            self.delete_selection()
        else:
            # Skip spaces
            while self.after_cursor != '' and self.after_cursor[0] in word_sep:
                self.key_del()

            # Jump over word
            while self.after_cursor != '' and not self.after_cursor[0] in word_sep:
                self.key_del()
            
    def key_del(self):
        """Delete character at cursor"""
        if self.get_selection() != '':
            self.delete_selection()
        else:
            self.after_cursor = self.after_cursor[1 : ]
            self.reset_history()
            self.reset_selection()

    def key_kill_line(self):
        """Kill the rest of the current line"""
        if self.get_selection() != '':
            self.delete_selection()
        else:
            self.after_cursor = ''

    def key_up(self):
        """Arrow up (history previous)"""
        # print '\n\n', history, history_index, '\n\n'
        if (self.before_cursor + self.after_cursor).strip() != '' and self.history_index == len(self.history) and self.history_filter == '':
            # Start history navigation; save current line
            self.history.append(self.before_cursor + self.after_cursor)
            self.history_filter = self.before_cursor + self.after_cursor
        prev_index = self.history_index
        self.history_index -= 1
        while self.history_index >= 0 and self.history[self.history_index].lower().find(self.history_filter.lower()) < 0:
            self.history_index -= 1
        if self.history_index < 0:
            self.history_index = prev_index
        if self.history_index < len(self.history):
            self.before_cursor = self.history[self.history_index]
            self.after_cursor = ''
        self.reset_selection()

    def key_down(self):
        """Arrow down (history next)"""
        # print '\n\n', history, history_index, '\n\n'
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            while self.history_index < len(self.history) and self.history[self.history_index].lower().find(self.history_filter.lower()) < 0:
                self.history_index += 1
            self.before_cursor = self.history[self.history_index]
        else:
            if self.history_filter != '':
                self.reset_history()
        self.reset_selection()

    def key_esc(self):
        """Esc key"""
        if self.get_selection() != '':
            self.reset_selection()
        else:
            if self.history_filter == '':
                self.add_to_history(self.before_cursor + self.after_cursor)
                self.before_cursor = ''
                self.after_cursor = ''
            self.reset_history()

    def key_backspace(self):
        """Backspace key"""
        if self.get_selection() != '':
            self.delete_selection()
        else:
            self.before_cursor = self.before_cursor[0 : -1]
            self.reset_history()
            self.reset_selection()

    def key_copy(self):
        """Copy selection to clipboard"""
        wclip.OpenClipboard()
        wclip.EmptyClipboard()
        wclip.SetClipboardText(self.get_selection())
        wclip.CloseClipboard()
        self.reset_history()

    def key_cut(self):
        """Cut selection to clipboard"""
        self.key_copy()
        self.delete_selection()
        self.reset_history()

    def key_paste(self):
        """Paste from clipboard"""
        wclip.OpenClipboard()
        if wclip.IsClipboardFormatAvailable(wclip.CF_TEXT):
            text = wclip.GetClipboardData()
            
            # Purge garbage chars that some apps put in the clipboard
            text = text.strip('\0')
            
            # Convert newlines to blanks
            text = text.replace('\r', '').replace('\n', ' ')

            # Insert into command line
            if self.get_selection() != '':
                self.delete_selection()
            self.before_cursor = self.before_cursor + text
            self.reset_selection()
            self.reset_history()
        wclip.CloseClipboard()

    def add_to_history(self, line):
        """Add a new line to the history"""
        if line != '':
            if line in self.history:
                self.history.remove(line)
            self.history.append(line)
            self.reset_history()

    def reset_history(self):
        """Reset browsing through the history"""
        if self.history_filter != '':
            self.history = self.history[:-1]
        self.history_index = len(self.history)
        self.history_filter = ''

    def reset_selection(self):
        """Reset text selection"""
        self.selection_start = len(self.before_cursor)

    def delete_selection(self):
        """Remove currently selected text"""
        len_before = len(self.before_cursor)
        if self.selection_start < len_before:
            self.before_cursor = self.before_cursor[: self.selection_start]
        else:
            self.after_cursor = self.after_cursor[self.selection_start - len_before: ]
        self.reset_selection()

    def get_selection_range(self):
        """Return the start and end indexes of the selection"""
        return (min(len(self.before_cursor), self.selection_start),
                max(len(self.before_cursor), self.selection_start))

    def get_selection(self):
        """Return the current selected text"""
        start, end = self.get_selection_range()
        return (self.before_cursor + self.after_cursor)[start: end]
