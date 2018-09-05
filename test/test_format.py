from datetime import datetime
import pytest
from pypsi import format as fmt


class TestFormat:

    def test_get_lines_multi(self):
        assert list(fmt.get_lines("hello\nnew line")) == [('hello', True), ('new line', False)]

    def test_get_lines_single(self):
        assert list(fmt.get_lines('hello')) == [('hello', False)]

    def test_get_lines_empty(self):
        assert list(fmt.get_lines('')) == []

    def test_get_lines_trailing_endl(self):
        assert list(fmt.get_lines('hello\n')) == [('hello', True)]

    def test_wrap_line_ascii(self):
        assert list(fmt.wrap_line('hello adam', 5)) == ['hello', 'adam']

    def test_wrap_line_ansi_single(self):
        ANSI = '\x1b[1;32mhello\x1b[0m \x1b[1;30madam\x1b[0m'
        assert list(fmt.wrap_line(ANSI, 10)) == [ANSI]

    def test_wrap_line_ansi_multi(self):
        ANSI = '\x1b[1;32mhello\x1b[0m \x1b[1;30madam\x1b[0m'
        assert list(fmt.wrap_line(ANSI, 5)) == ANSI.split(' ', 1)

    def test_wrap_line_prefix(self):
        TXT = 'hello, adam'
        assert list(fmt.wrap_line(TXT, 6, '>> ')) == ['hello,', '>> adam']

    def test_wrap_line_nowrap(self):
        assert list(fmt.wrap_line('hello adam', 0)) == ['hello adam']

    def test_wrap_line_long_word(self):
        assert list(fmt.wrap_line('areallylongword', 4)) == ['areal', 'lylon', 'gword']

    def test_highlight_multi(self):
        TXT = 'hello, this is another instance of hello'
        ANS = '\x1b[1;32mhello\x1b[0m, this is another instance of \x1b[1;32mhello\x1b[0m'
        assert fmt.highlight(TXT, 'hello') == ANS

    def test_highlight_none(self):
        TXT = 'hello, this is another instance of hello'
        assert fmt.highlight(TXT, 'hello2') == TXT

    def test_highlight_nocolor(self):
        TXT = 'hello, this is another instance of hello'
        assert fmt.highlight(TXT, 'hello', None) == TXT

    @pytest.mark.parametrize('unit', [('Kb', 1), ('Mb', 2), ('Gb', 3), ('Tb', 4)])
    def test_file_size_str_mid(self, unit):
        postfix, exp = unit
        val = 1 * (1024 ** exp)
        assert fmt.file_size_str(val) == '1.00 ' + postfix

    def test_file_size_str_byte(self):
        assert fmt.file_size_str(100) == '100 B'

    def test_file_size_str_pb(self):
        assert fmt.file_size_str(1024 ** 5) == '1024.00 Tb'

    @pytest.mark.parametrize('type_cls', (int, bool))
    def test_obj_str_simple(self, type_cls):
        val = type_cls(0)
        assert fmt.obj_str(val) == type_cls.__name__ + '( ' + str(val) + ' )'

    def test_obj_str_float(self):
        assert fmt.obj_str(1.561) == 'float( 1.561 )'

    def test_obj_str_str(self):
        assert fmt.obj_str('hello') == 'hello'

    def test_obj_str_list_short(self):
        assert fmt.obj_str(['1', '2', '3']) == 'list( 1, 2, 3 )'

    def test_obj_str_list_trunc(self):
        assert fmt.obj_str(['1', '2', '3', '4']) == 'list( 1, 2, 3, ... )'

    def test_obj_str_list_notrunc(self):
        assert fmt.obj_str(['1', '2', '3', '4', '5'], max_children=0) == 'list( 1, 2, 3, 4, 5 )'

    def test_obj_str_list_type(self):
        assert fmt.obj_str([1, 2]) == 'list( int( 1 ), int( 2 ) )'

    def test_obj_str_none(self):
        assert fmt.obj_str(None) == '<null>'

    def test_obj_str_unknown(self):
        now = datetime.now()
        assert fmt.obj_str(now) == str(now)
