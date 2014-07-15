#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
        "any existing file and remove all its content. A double >> redirection "
        "will append to any existing file and the original content will be "
        "perserved. Currently, only stdout can be redirected. For example, to "
        "write the string 'Hello World' to the test.txt file, execute the "
        "following:\n\n"

        "    echo 'Hello World' > test.txt\n\n"

        "As stated earlier, this command will overwrite any existing content "
        "in the test.txt file. To append to the file rather than truncate it, "
        "execute the following:\n\n"

        "    echo 'Hello world' >> test.txt"
    )
)
