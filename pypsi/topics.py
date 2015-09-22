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

from pypsi.commands.help import Topic


IoRedirection = Topic(
    id='redirection',
    name='I/O Redirection',
    content=(
        "This shell supports redirection for stdin and stdout. Redirection "
        "allows command output to be writen to a file instead of the screen "
        "and allows command input to be from a file rather than user input on "
        "the command line. Similar to Bash and DOS, redirection is performed "
        "with the < and > operators and must follow a valid command.\n\n"

        "Input redirection is performed by using the < operator. The text "
        "after the operator has to be the path to a file that exists on disk. "
        "If the file does not exist, an error will be printed to the screen "
        "and the command will not be executed. For example, the xargs command "
        "reads stdin and executes a command on each line. To print each line "
        "from the file test.txt to the screen using the echo command, execute "
        "the following:\n\n"

        "    xargs echo {} < test.txt\n\n"

        "Output redirection is performed by using the > or >> operators. The "
        "text after the operator has to be a valid path that the current user "
        "can write to. Unlike input redirection, the file redirecting to does "
        "not have to exist on disk. A single > redirection will truncate the "
        "any existing file and remove all its content. A double >> "
        "redirection will append to any existing file and the original "
        "content will be perserved. Currently, only stdout can be redirected. "
        "For example, to write the string 'Hello World' to the test.txt file, "
        "execute the following:\n\n"

        "    echo 'Hello World' > test.txt\n\n"

        "As stated earlier, this command will overwrite any existing content "
        "in the test.txt file. To append to the file rather than truncate it, "
        "execute the following:\n\n"

        "    echo 'Hello world' >> test.txt"
    )
)
