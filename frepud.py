#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2021 Ferhat Geçdoğan All Rights Reserved.
# Distributed under the terms of the MIT License.
#
# fre.p.u(b).d
#   cli e-pub renderer (only for libreoffice and libepubgen)
#   mostly based on totem (less like tool) & freud (totem based fpaper renderer)
#
#   github.com/ferhatgec/frepud
#   github.com/ferhatgec/freud
#   github.com/ferhatgec/fpaper
#   github.com/ferhatgec/totem
#   github.com/ferhatgec/totem.py

import os
import pathlib
import sys
import termios
import tty

escape = 27
up = 65
down = 66


class Totem:
    def __init__(self, filename: str):
        import zipfile
        import re
        import html

        self.file_data: str = ''
        self.__up__: int = 0
        self.__down__: int = 0
        self.__full_length__: int = 0
        self.__w__, self.__h__ = Totem.get_terminal_size()
        self.old__ = termios.tcgetattr(sys.stdin.fileno())
        self.new__ = termios.tcgetattr(sys.stdin.fileno())

        self.author = ''
        self.title = ''

        if pathlib.Path(filename).suffix == '.epub':
            with zipfile.ZipFile(filename) as epub:
                if 'mimetype' in epub.namelist():
                    for file in epub.namelist():
                        if file == 'OEBPS/content.opf':
                            content = epub.read(file).decode('UTF-8')
                            self.title = re.search('<dc:title>(.*)</dc:title>', content).group(1)
                            self.author = re.search('<dc:creator>(.*)</dc:creator>', content).group(1)
                            continue

                        if 'OEBPS/sections' in file:
                            content = epub.read(file).decode('UTF-8')
                            spans = re.findall('<span class=\"(?:(span0|span1|span2|span3))\">(.*?)</span>', content)

                            for line in spans:
                                self.file_data += f'{html.unescape(line[1])}\n'
                                self.__down__ += 1
                else:
                    print('Invalid e-pub')
                    exit(1)
        else:
            print('Invalid file extension')
            exit(1)

        self.center()

        self.__full_length__ = self.__down__

    def __center(self, val: str) -> str:
        data = ''
        for _ in range(int(self.__w__ / 1.1)):
            data += ' '

        data += val

        for _ in range(int(self.__w__ / 1.1)):
            data += ' '

        return data

    def center(self):
        if self.file_data is None:
            return

        full_data = ''

        for line in self.file_data.splitlines():
            data = ''
            for _ in range(int(self.__w__ / 1.1)):
                data += ' '

            data += line

            for _ in range(int(self.__w__ / 1.1)):
                data += ' '

            line = data

            full_data += f'{line}\n'

        self.file_data = full_data

    def init_buffer(self):
        self.clear()
        self.to_up()
        self.__down__ = (self.__h__ / 3.9)
        self.__from__(False)
        self.disable_cursor()

        self.new__[3] = self.new__[3] & ~termios.ECHO
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.new__)
            while True:
                ch = self.getchar()

                if ch.lower() == 'q':
                    break

                ch = self.getchar()
                ch = self.getchar()
                if ch == 'A':
                    if 1 <= self.__up__:
                        self.__up__ -= 1
                        self.__down__ -= 1
                        self.__from__(False)
                        continue
                if ch == 'B':
                    if self.__down__ < self.__full_length__:
                        self.__down__ += 1
                        self.__up__ += 1
                        self.__from__(False)
                        continue
        finally:
            self.enable_cursor()
            self.clear()
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.old__)

    def __from__(self, is_up: bool):
        i = 0
        __new: str = ''
        if is_up:
            for line in self.file_data.splitlines():
                if i >= self.__up__:
                    __new += f'{line}\n'

                i += 1
        else:
            for line in self.file_data.splitlines():
                if i < self.__down__:
                    __new += f'{line}\n'

                i += 1

        self.clear()

        print(self.__center(f'{self.title} | {self.author}'),
              self.__center('-' * (len(self.title) + len(self.author) + 3)), sep='\n')
        print(end=f'\x1b[0;97m{__new}\x1b[0m')

        self.up_to(self.__up__)

    @staticmethod
    def getchar():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    @staticmethod
    def refresh():
        print(end='\x1b[2J')

    @staticmethod
    def clear():
        Totem.refresh()
        print(end='\x1b[H')

    @staticmethod
    def to_up():
        print(end='\x1b[0A')

    @staticmethod
    def up_to(n: int):
        print(end='\x1b[' + str(n) + 'A')

    @staticmethod
    def disable_cursor():
        print(end='\x1b[?25l')

    @staticmethod
    def enable_cursor():
        print(end='\x1b[?25h')

    @staticmethod
    def get_terminal_size() -> (int, int):
        from fcntl import ioctl
        from struct import pack, unpack

        with open(os.ctermid(), 'r') as fd:
            packed = ioctl(fd, termios.TIOCGWINSZ, pack('HHHH', 0, 0, 0, 0))
            rows, cols, h_pixels, v_pixels = unpack('HHHH', packed)

        return rows, cols


if len(sys.argv) < 2:
    exit(1)

init = Totem(sys.argv[len(sys.argv) - 1])

init.init_buffer()
