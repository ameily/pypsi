#
# Copyright (c) 2015, Adam Meily <meily.adam@gmail.com>
# Pypsi - https://github.com/ameily/pypsi
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#


import sys
import threading
import itertools


def _prefix(s):
    return str(s) if s is not None else ''


class ProgressBar(object):
    '''
    A basic text-based progress bar.
    '''

    def __init__(self, count, stream=None, width=None, activity=None):
        '''
        :param int count: the total number of items
        :param stream: the output stream, defaults to ``sys.stdout``
        :param int width: total progress bar width, including activity
        :param str activity: short description to print in front of the
            progress bar
        '''
        self.count = count
        self.stream = stream or sys.stdout
        self.i = 0
        self.current_percent = 0.0
        self.activity = activity
        self.width = width
        if width is None:
            if hasattr(self.stream, 'width'):
                self.width = min(self.stream.width, 80 + len(activity or ''))
            else:
                self.width = 80
        else:
            self.width = min(width, 80 + len(activity or ''))

        self.draw()

    def draw(self, cancel=False):
        '''
        Force a redraw of the progress bar
        '''
        col = 0
        prefix = _prefix(self.activity)
        if prefix:
            col = len(prefix)

        # [XXXXXX] YY.Y%
        # 8 char count = [] YYY.Y%
        bar_width = self.width - col - 9
        percent = self.i / self.count
        fill = '=' * int(percent * bar_width)
        bar = "{prefix}[{fill}{empty}] {percent:6.1%}".format(
            prefix=prefix,
            fill=fill,
            empty=(' ' * (bar_width - len(fill))),
            percent=percent
        )

        if self.i < self.count and not cancel:
            end = ''
        else:
            end = '\n'
        print('\r', bar, sep='', end=end, flush=True)

        self.last_draw_percent = percent

    def cancel(self):
        '''
        Cancel the progress bar.
        '''
        self.draw(cancel=True)

    def tick(self):
        '''
        Increment the total number of processed items and redraw if necessarys.
        '''
        self.i += 1
        diff = (self.i / self.count) - self.last_draw_percent
        if self.i == self.count or diff >= 0.001:
            self.draw()


class ThreadedSpinner(threading.Thread):
    '''
    A basic spinner that updates at regular intervals.
    '''

    def __init__(self, delta=0.1, seq='|/-\\', activity=None, stream=None):
        '''
        :param float delta: the number of seconds to wait between updates
        :param str seq: sequence of characters to iterate over
        :param str activity: brief description of activity to display prior to
            the spinner
        :param stream: the output stream, defaults to stdout
        '''
        super(ThreadedSpinner, self).__init__()
        self.delta = delta
        self.seq = seq
        self.activity = activity
        self.stream = stream or sys.stdout
        self.stop_lock = threading.Lock()
        self.stop_lock.acquire()
        self.complete_msg = ''

    def run(self):
        i = itertools.cycle(self.seq)

        while not self.stop_lock.acquire(timeout=self.delta):
            prefix = _prefix(self.activity)
            print('\r', prefix, next(i), sep='', end='', flush=True,
                  file=self.stream)

        prefix = _prefix(self.activity)
        print('\r', prefix, self.complete_msg, sep='', flush=True,
              file=self.stream)

    def complete(self, msg='Done'):
        self.complete_msg = msg
        self.stop_lock.release()
        self.join()


class Spinner(object):

    def __init__(self, count=1, seq='|/-\\', activity=None, stream=None):
        '''
        :param int count: the number of ticks before the spinner is updated
        :param str seq: sequence of character to iterate over
        :param str activity: brief description of activity to display prior to
            the spinner
        :param stream: the output stream, defaults to stdout
        '''
        self.count = count
        self.offset = 0
        self.iter = itertools.cycle(seq)
        self.activity = activity
        self.stream = stream or sys.stdout

    def draw(self):
        '''
        Force a redraw of the spinner.
        '''
        prefix = _prefix(self.activity)
        print('\r', prefix, next(self.iter), end='', flush=True, sep='',
              file=self.stream)

    def tick(self):
        '''
        Increment proress
        '''
        self.offset += 1
        if self.offset >= self.count:
            self.offset = 0
            self.draw()

    def complete(self, msg='Done'):
        '''
        Complete the spinner.

        :param str msg: optional message to display
        '''
        prefix = str(self.activity) if self.activity is not None else ''
        print('\r', prefix, msg, file=self.stream, sep='')
