from ttk import *

from tkreadonly import ReadOnlyCode

from bugjar.connection import ConnectionNotBootstrapped, UnknownBreakpoint


class DebuggerCode(ReadOnlyCode):
    def __init__(self, *args, **kwargs):
        self.debugger = kwargs.pop('debugger')
        ReadOnlyCode.__init__(self, *args, **kwargs)

        # Set up styles for line numbers
        self.lines.tag_configure('enabled',
            background='red'
        )

        self.lines.tag_configure('disabled',
            background='gray'
        )

        self.lines.tag_configure('ignored',
            background='green'
        )

        self.lines.tag_configure('temporary',
            background='pink'
        )

    def enable_breakpoint(self, line, temporary=False):
        self.lines.tag_remove('disabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('ignored',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        if temporary:
            self.lines.tag_remove('enabled',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )
            self.lines.tag_add('temporary',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )
        else:
            self.lines.tag_remove('temporary',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )
            self.lines.tag_add('enabled',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )

    def disable_breakpoint(self, line):
        self.lines.tag_remove('enabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('ignored',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('temporary',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_add('disabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )

    def clear_breakpoint(self, line):
        self.lines.tag_remove('enabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('disabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('ignored',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('temporary',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )

    def on_line_double_click(self, line):
        "When a line number is double clicked, set a breakpoint"
        print "Toggle breakpoint"
        try:
            bp = self.debugger.breakpoint((self.current_file, line))
            if bp.enabled:
                self.debugger.disable_breakpoint(bp)
            else:
                self.debugger.enable_breakpoint(bp)
        except UnknownBreakpoint:
            self.debugger.create_breakpoint(self.current_file, line)
        except ConnectionNotBootstrapped:
            print "Connection not yet configured"

    def on_code_variable_double_click(self, var):
        "When a variable is double clicked, ..."
        pass


class BreakpointView(Treeview):
    def __init__(self, *args, **kwargs):
        Treeview.__init__(self, *args, **kwargs)

        # Set up styles for line numbers
        self.tag_configure('enabled',
            foreground='red'
        )

        self.tag_configure('disabled',
            foreground='gray'
        )

        self.tag_configure('ignored',
            foreground='green'
        )

        self.tag_configure('temporary',
            foreground='pink'
        )

    def update_breakpoint(self, bp):
        """Update the visualization of a breakpoint in the tree.

        If the breakpoint isn't arlready on the tree, add it.
        """
        if not self.exists(bp.filename):
            # First, establish the index at which to insert this child.
            # Do this by getting a list of children, sorting the list by name
            # and then finding how many would sort less than the label for
            # this node.
            files = sorted(self.get_children(''), reverse=False)
            index = len([item for item in files if item > bp.filename])

            # Now insert a new node at the index that was found.
            self.insert(
                '', index, bp.filename,
                text=bp.filename,
                open=True,
                tags=['file']
            )

        # Determine the right tag for the line number
        if bp.enabled:
            if bp.temporary:
                tag = 'temporary'
            else:
                tag = 'enabled'
        else:
            tag = 'disabled'

        # Update the display for the line number,
        # adding a new tree node if necessary.
        if self.exists(unicode(bp)):
            self.item(unicode(bp), tags=['breakpoint', tag])
        else:
            # First, establish the index at which to insert this child.
            # Do this by getting a list of children, sorting the list by name
            # and then finding how many would sort less than the label for
            # this node.
            lines = sorted((int(self.item(item)['text']) for item in self.get_children(bp.filename)), reverse=False)
            index = len([line for line in lines if line < bp.line])

            # Now insert a new node at the index that was found.
            self.insert(
                bp.filename, index, unicode(bp),
                text=unicode(bp.line),
                open=True,
                tags=['breakpoint', tag]
            )


class StackView(Treeview):
    def __init__(self, *args, **kwargs):
        # Only a single stack frame can be selected at a time.
        kwargs['selectmode'] = 'browse'
        Treeview.__init__(self, *args, **kwargs)

    def update_stack(self, stack):
        "Update the display of the stack"
        # Retrieve the current stack list
        displayed = self.get_children()

        # Iterate over the entire stack. Update each entry
        # in the stack to match the current frame description.
        # If we need to add an extra frame, do so.
        index = 0
        for line, frame in stack:
            if index < len(displayed):
                item = self.item(displayed[index],
                    text=frame['filename'],
                    values=(line,)
                )
            else:
                self.insert(
                    '', index, 'frame:%s' % index,
                    text=frame['filename'],
                    open=True,
                    values=(line,)
                )
            index = index + 1

        # If we've stepped back out of a frame, there will
        # be less frames than are currently displayed;
        # delete the excess entries.
        for i in range(index, len(displayed)):
            self.delete(displayed[i])
