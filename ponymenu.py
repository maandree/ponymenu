#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
ponymenu – terminal based application menu

Copyright © 2012, 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import sys
from subprocess import Popen, PIPE



VERSION = 1.0
'''
This version ponymenu
'''



TERM_INIT = True
'''
Set to false if debugging

This flag specifies whether the terminal will be initialised
'''



def print(text = '', end = '\n'):
    '''
    Hack to enforce UTF-8 in output (in the future, if you see anypony not using utf-8 in
    programs by default, report them to Princess Celestia so she can banish them to the moon)
    
    @param  text:str  The text to print (empty string is default)
    @param  end:str   The appendix to the text to print (line breaking is default)
    '''
    sys.stdout.buffer.write((str(text) + end).encode('utf-8'))
    sys.stdout.buffer.flush()

def printerr(text = '', end = '\n'):
    '''
    stderr equivalent to print()
    
    @param  text:str  The text to print (empty string is default)
    @param  end:str   The appendix to the text to print (line breaking is default)
    '''
    sys.stderr.buffer.write((str(text) + end).encode('utf-8'))
    sys.stderr.buffer.flush()

def printf(master, *slave):
    '''
    Print a non-ended line to stdout with formating
    '''
    sys.stdout.buffer.write((master % slave).encode('utf-8'))

def flush():
    '''
    Flush stdout
    '''
    sys.stdout.buffer.flush()



class Ponymenu:
    '''
    Ponymenu mane class
    
    @param  args:list<str>  Arguments to pass to the executed command
    '''
    def __init__(self, args):
        '''
        Constructor and mane
        '''
        action = None
        try:
            if TERM_INIT:
                print('\033[?1049h\033[?25l', end='')
            Popen(['stty', '-icanon', '-echo', '-isig', '-ixoff', '-ixon', '-ixany'], stdin=sys.stdout).wait()
            
            
            self.HOME = os.environ['HOME'] if 'HOME' in os.environ else ''
            if len(self.HOME) == 0:
                os.environ['HOME'] = self.HOME = os.path.expanduser('~')
            
            
            '''
            Parse a file name encoded with environment variables
            
            @param   file  The encoded file name
            @return        The target file name, None if the environment variables are not declared
            '''
            def parsefile(file):
                if '$' in file:
                    buf = ''
                    esc = False
                    var = None
                    for c in file:
                        if esc:
                            buf += c
                            esc = False
                        elif var is not None:
                            if c == '/':
                                var = os.environ[var] if var in os.environ else ''
                                if len(var) == 0:
                                    return None
                                buf += var + c
                                var = None
                            else:
                                var += c
                        elif c == '$':
                            var = ''
                        elif c == '\\':
                            esc = True
                        else:
                            buf += c
                    return buf
                return file
            
            
            self.env = os.environ
            self.linuxvt = ('TERM' in self.env) and (self.env['TERM'] == 'linux')
            self.display = ('DISPLAY' in self.env) and self.env['DISPLAY'].startswith(':')
            self.graphical = self.display and not self.linuxvt
            
            
            ## Change system enviroment variables with ponymenurc
            for file in ('$XDG_CONFIG_HOME/ponymenu/ponymenurc',
                         '$HOME/.config/ponymenu/ponymenurc',
                         '$HOME/.ponymenurc',
                         '/etc/ponymenurc'):
                file = parsefile(file)
                if (file is not None) and os.path.exists(file):
                    with open(file, 'rb') as ponymenurc:
                        code = ponymenurc.read().decode('utf8', 'replace') + '\n'
                        code = compile(code, file, 'exec')
                        exec(code)
                    break
            
            
            self.HOME = self.env['HOME'] if 'HOME' in self.env else '' # in case ~/.ponymenurc changes it
            if len(self.HOME) == 0:
                self.env['HOME'] = self.HOME = os.path.expanduser('~')
            
            
            menuFound = False
            self.root = Entry(None, None, None, None)
            
            for file in ('$XDG_CONFIG_HOME/ponymenu/ponymenu',
                         '$HOME/.config/ponymenu/ponymenu',
                         '$HOME/.ponymenu',
                         '/etc/ponymenu'):
                file = parsefile(file)
                if (file is not None) and os.path.exists(file):
                    with open(file, 'rb') as ponymenu:
                        code = ponymenu.read().decode('utf8', 'replace')
                        self.loadMenu(code)
                        menuFound = True
                    break
            
            if not menuFound:
                Popen(['stty', 'icanon', 'echo', 'isig', 'ixoff', 'ixon'], stdin=sys.stdout).wait()
                if TERM_INIT:
                    print('\033[?1049h', end='')
                print('ponymenu: no menu file found')
                return
            
            action = self.interact(args)
            
        finally:
            Popen(['stty', 'icanon', 'echo', 'isig', 'ixoff', 'ixon', 'ixany'], stdin=sys.stdout).wait()
            if TERM_INIT:
                print('\033[1;1H\033[2J\033[?25h\033[?1049l', end='')
            if action is not None:
                action()
    
    
    def loadMenu(self, code):
        '''
        Load the menu
        
        @param  code:str  Unparsed menu markup
        '''
        def make(items):
            rc = []
            for item in items:
                (name, desc, cmd, inner) = (None, None, None, None)
                add = None
                for tag in item:
                    if   tag[0] == 'name':  name = ' '.join(tag[1:])
                    elif tag[0] == 'desc':  desc = ' '.join(tag[1:])
                    elif tag[0] == 'cmd':
                        cmd  = tag[1:]
                        if (len(cmd) == 1) and isinstance(cmd[0], list):
                            cmd = cmd[0]
                    elif tag[0] == 'inner':
                        inner = make(tag[1:])
                    elif tag[0] == 'req':
                        for req in tag[1:]:
                            if not isinstance(req, list):
                                req = [req]
                            qual = True
                            for r in req:
                                if r == 'tty':
                                    qual &= not self.graphical
                                elif (r == 'x') or (r == 'graphical'):
                                    qual &= self.graphical
                            if add is None:
                                add = False
                            add |= qual
                if add is None:
                    add = True
                if add:
                    rc.append(Entry(name, desc, cmd, inner))
            return rc
        self.root.inner = make(Parser.parse(code))
    
    
    @staticmethod
    def execute(command):
        '''
        Execute command
        
        @param  command:list<str>  The command
        '''
        Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr).wait()
    
    
    def interact(self, args):
        '''
        Start menu interaction
        
        @param  args:list<str>  Arguments to pass to the executed command
        '''
        def clean(items):
            i = 0
            while i < len(items):
                item = items[i]
                if item.cmd is None:
                    if (item.inner is None) or (len(item.inner) == 0):
                        items[i : i + 1] = []
                        continue
                i += 1
            return items
        
        stack = []
        allitems = clean(self.root.inner)
        items = allitems
        maxlen = UCS.dispLen(max([entry.name for entry in items], key = UCS.dispLen))
        selectedIndex = 0
        count = len(items)
        offset = 0
        
        def printEntry(entry, selected, maxlen):
            first = entry.name + fill[UCS.dispLen(entry.name) : maxlen + 12]
            second = entry.desc + fill[maxlen + 12 + 6 + UCS.dispLen(entry.desc):]
            if len(first) >= self.termw - 6:
                second = ''
                if len(entry.name) > self.termw - 6:
                    first = entry.name[:self.termw - 6 - 1] + '…'
                else:
                    first = first[:self.termw - 6]
            elif len(first) + len(second) > self.termw - 6:
                second = second[:self.termw - 6 - len(first) - 1] + '…'
            printf('    %s \033[%sm%s\033[21m%s\033[m\n', '\033[1;34m>\033[m' if selected else ' ',
                                                          ('1;37;44' if self.linuxvt else '97;44') if selected else '34',
                                                          first, second)
        
        searchString = ''
        def printSearch():
            printf('\033[%i;1H\033[K%s\033[7;41;1m<\033[m', self.termh, searchString)
        
        def printAll(items, selectedIndex, maxlen, offset):
            index = 0
            ending = 0
            for entry in items:
                if index >= offset:
                    if index >= offset + self.termh - 8:
                        ending += 1
                    else:
                        selected = entry is items[selectedIndex]
                        printEntry(entry, selected, maxlen)
                index += 1
            arrows = min(len(filldown), ending)
            printf('      %s%s', filldown[:arrows], fill[arrows:])
        
        def redraw(items, selectedIndex, maxlen, offset):
            termsize = (24, 80)
            for channel in (sys.stderr, sys.stdout, sys.stdin):
                termsize = Popen(['stty', 'size'], stdin=channel, stdout=PIPE, stderr=PIPE).communicate()[0]
                if len(termsize) > 0:
                    termsize = termsize.decode('utf8', 'replace')[:-1].split(' ') # [:-1] removes a \n
                    termsize = [int(item) for item in termsize]
                    break
            
            (self.termh, self.termw) = termsize
            
            global fill
            global filldown
            fill = ' ' * self.termw
            filldown = '↓' * (self.termw - 6)
            fillup = '↑' * (self.termw - 6)
            printf('\033[m\033[1;1H\033[2J\033[7;1m%s\033[27;21m\033[%i;1H\033[7m%s\033[27m\n%s\033[4;1H', ' ponymenu, press C-q to quit' + fill[28:], self.termh - 1, fill, '\033[7;41;1m<\033[m' + fill[1:])
            arrows = min(len(fillup), offset)
            printf('      %s%s\033[5;1H', fillup[:arrows], fill[arrows:])
            
            printAll(items, selectedIndex, maxlen, offset)
            printSearch()
        
        redraw(items, selectedIndex, maxlen, offset)
        
        global fill
        while True:
            flush()
            c = sys.stdin.read(1)
            if (ord(c) == ord('Q') - ord('@')) or (ord(c) == ord('D') - ord('@')):
                break
            if c == '\033':
                c += sys.stdin.read(1)
                if c == '\033[':
                    while True:
                        end = sys.stdin.read(1)
                        c += end
                        if (end == '~') or (('a' <= end) and (end <= 'z')) or (('A' <= end) and (end <= 'Z')) or (ord(end) == ord('G') - ord('@')):
                            break
            if c == '\033[D':
                c = chr(8)
            
            if c == chr(ord('L') - ord('@')):
                redraw(items, selectedIndex, maxlen, offset)
            elif c.startswith('\033['):
                if c == '\033[A':
                    printf('\033[%i;1H', selectedIndex + 5 - offset)
                    printEntry(items[selectedIndex], False, maxlen)
                    selectedIndex = (count if selectedIndex == 0 else selectedIndex) - 1
                    oldOffset = offset
                    while selectedIndex < offset:
                        offset -= (self.termh - 8) >> 1
                    if offset < 0:
                        offset = 0
                    while selectedIndex >= offset + self.termh - 8:
                        offset = count - self.termh + 9
                    if offset == oldOffset:
                        printf('\033[%i;1H', selectedIndex + 5 - offset)
                        printEntry(items[selectedIndex], True, maxlen)
                    else:
                        redraw(items, selectedIndex, maxlen, offset)
                elif c == '\033[B':
                    printf('\033[%i;1H', selectedIndex + 5 - offset)
                    printEntry(items[selectedIndex], False, maxlen)
                    selectedIndex = (selectedIndex + 1) % count
                    if selectedIndex == 0:
                        offset = 0
                        redraw(items, selectedIndex, maxlen, offset)
                    else:
                        oldOffset = offset
                        while selectedIndex >= offset + self.termh - 8:
                            offset += (self.termh - 8) >> 1
                        if offset == oldOffset:
                            printf('\033[%i;1H', selectedIndex + 5 - offset)
                            printEntry(items[selectedIndex], True, maxlen)
                        else:
                            redraw(items, selectedIndex, maxlen, offset)
                elif c == '\033[C':
                    at = len(searchString)
                    while True:
                        expand = True
                        if at == len(items[0].name):
                            break
                        else:
                            expect = items[0].name[at]
                            for item in items:
                                if item.name[at] != expect:
                                    expand = False
                                    break
                        if expand:
                            at += 1
                        else:
                            break
                    if at != len(searchString):
                        searchString = items[0].name[:at]
                        drop = count
                        newItems = []
                        for item in items:
                            if item.name.startswith(searchString):
                                newItems.append(item)
                        items = newItems
                        count = len(items)
                        selectedIndex %= count
                        selectedIndex %= self.termh - 8
                        drop = '\033[5;1H' + (fill + '\n') * drop
                        maxlen = UCS.dispLen(max([entry.name for entry in items], key = UCS.dispLen))
                        redraw(items, selectedIndex, maxlen, offset)
            elif (c == '\n') or (c == '\t'):
                if c == '\n':
                    stack.append(allitems)
                    item = items[selectedIndex]
                    if item.inner is not None:
                        allitems = clean(item.inner)
                    else:
                        class ExecFunctor:
                            def __init__(self, command):
                                self.command = command
                            def __call__(self):
                                Ponymenu.execute(self.command + args)
                        return ExecFunctor(item.cmd)
                else:
                    if len(stack) == 0:
                        continue
                    allitems = stack[-1]
                    stack = stack[:-1]
                items = allitems
                searchString = ''
                selectedIndex = 0
                drop = count
                count = len(items)
                drop = '\033[5;1H' + (fill + '\n') * drop
                maxlen = UCS.dispLen(max([entry.name for entry in items], key = UCS.dispLen))
                redraw(items, selectedIndex, maxlen, offset)
            elif (len(c) == 1) and ((ord(c) >= 32) or (c == chr(8)) or (c == chr(127))):
                further = False
                if (c == chr(8)) or (c == chr(127)):
                    if len(searchString) == 0:
                        continue
                    searchString = searchString[:len(searchString) - 1]
                else:
                    searchString += c
                    further = True
                newItems = []
                for item in (items if further else allitems):
                    if item.name.startswith(searchString):
                        newItems.append(item)
                if len(newItems) == 0:
                    searchString = searchString[:~0]
                else:
                    items = newItems
                    drop = count
                    count = len(items)
                    selectedIndex %= count
                    selectedIndex %= self.termh - 8
                    drop = '\033[5;1H' + (fill + '\n') * drop
                    maxlen = UCS.dispLen(max([entry.name for entry in items], key = UCS.dispLen))
                    redraw(items, selectedIndex, maxlen, offset)
                printSearch()
        
        return None



class Entry:
    '''
    Menu entry
    '''
    def __init__(self, name, desc, cmd, inner):
        '''
        Constructor
        
        @param  name:str?          The title of the entry
        @param  desc:str?          The description of the entry
        @param  cmd:list<str>?     The command executed when running the entry
        @param  inner:list<Entry>  Inner entries
        '''
        self.name = name if name is not None else '[untitled]'
        self.desc = desc if desc is not None else ''
        self.cmd = cmd
        self.inner = inner
    
    def __cmp__(self, other):
        '''
        Comparator
        
        @param   other  The right hand comparand
        @return         Less than zero if right hand is greater, more than zero if left hand is greater, otherwise 0
        '''
        if (self.cmd is None) ^ (other.cmd is None):
            return -1 if self.cmd is None else 1
        return cmp(self.name, other.name)



class UCS():
    '''
    UCS utility class
    '''
    @staticmethod
    def isCombining(char):
        '''
        Checks whether a character is a combining character
        
        @param   char:chr  The character to test
        @return  :bool     Whether the character is a combining character
        '''
        o = ord(char)
        if (0x0300 <= o) and (o <= 0x036F):  return True
        if (0x20D0 <= o) and (o <= 0x20FF):  return True
        if (0x1DC0 <= o) and (o <= 0x1DFF):  return True
        if (0xFE20 <= o) and (o <= 0xFE2F):  return True
        return False
    
    
    @staticmethod
    def countCombining(string):
        '''
        Gets the number of combining characters in a string
        
        @param   string:str  A text to count combining characters in
        @return  :int        The number of combining characters in the string
        '''
        rc = 0
        for char in string:
            if UCS.isCombining(char):
                rc += 1
        return rc
    
    
    @staticmethod
    def dispLen(string):
        '''
        Gets length of a string not counting combining characters
        
        @param   string:str  The text of which to determine the monospaced width
        @return              The determine the monospaced width of the text, provided it does not have escape sequnces
        '''
        return len(string) - UCS.countCombining(string)



class Parser:
    '''
    Bracket tree parser
    '''
    @staticmethod
    def parse(code):
        '''
        Parse a code and return a tree
        
        @param   code:str      The code to parse
        @return  :list<↑|str>  The root node in the tree
        '''
        stack = []
        stackptr = -1
        
        comment = False
        escape = False
        quote = None
        buf = None
        
        for charindex in range(0, len(code)):
            c = code[charindex]
            if comment:
                if c in '\n\r\f':
                    comment = False
            elif escape:
                escape = False
                if   c == 'a':  buf += '\a'
                elif c == 'b':  buf += chr(8)
                elif c == 'e':  buf += '\033'
                elif c == 'f':  buf += '\f'
                elif c == 'n':  buf += '\n'
                elif c == 'r':  buf += '\r'
                elif c == 't':  buf += '\t'
                elif c == 'v':  buf += chr(11)
                elif c == '0':  buf += '\0'
                else:
                    buf += c
            elif c == quote:
                quote = None
            elif (c in ';#') and (quote is None):
                if buf is not None:
                    stack[stackptr].append(buf)
                    buf = None
                comment = True
            elif (c == '(') and (quote is None):
                if buf is not None:
                    stack[stackptr].append(buf)
                    buf = None
                stackptr += 1
                if stackptr == len(stack):
                    stack.append([])
                else:
                    stack[stackptr] = []
            elif (c == ')') and (quote is None):
                if buf is not None:
                    stack[stackptr].append(buf)
                    buf = None
                if stackptr == 0:
                    return stack[0]
                stackptr -= 1
                stack[stackptr].append(stack[stackptr + 1])
            elif (c in ' \t\n\r\f') and (quote is None):
                if buf is not None:
                    stack[stackptr].append(buf)
                    buf = None
            else:
                if buf is None:
                    buf = ''
                if c == '\\':
                    escape = True
                elif (c in '\'\"') and (quote is None):
                    quote = c
                else:
                    buf += c
        
        raise Exception('premature end of file')
    


if __name__ == '__main__':
    plus = False
    for arg in sys.argv[1:]:
        if arg in ('-v', '--version'):
            print('ponymenu ' + VERSION)
            
        elif arg in ('-h', '--help'):
            print('ponymenu – terminal based application menu')
            print()
            print('Run `info ponymenu` for usage information')
            print()
            print('-h,  --help        Print this table')
            print('-v,  --version     Print the program name and version')
            print('-c,  --copyright   Print copyright information')
            print()
            print()
            
        elif arg in ('-c', '--copyright'):
            print('ponymenu – terminal based application menu')
            print()
            print('Copyright © 2012, 2013  Mattias Andrée (maandree@member.fsf.org)')
            print()
            print('This program is free software: you can redistribute it and/or modify')
            print('it under the terms of the GNU General Public License as published by')
            print('the Free Software Foundation, either version 3 of the License, or')
            print('(at your option) any later version.')
            print()
            print('This program is distributed in the hope that it will be useful,')
            print('but WITHOUT ANY WARRANTY; without even the implied warranty of')
            print('MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the')
            print('GNU General Public License for more details.')
            print()
            print('You should have received a copy of the GNU General Public License')
            print('along with this program.  If not, see <http://www.gnu.org/licenses/>.')
            print()
            print()
            
        elif arg == '+':
            plus = True
            break
        else:
            printerr('ponymenu: unrecognised option: ' + arg)
    
    if plus:
        plus = 2
        for arg in sys.argv[1:]:
            if arg == '+':
                break
            plus += 1
        Ponymenu(sys.argv[plus:])
    else:
        Ponymenu([])

