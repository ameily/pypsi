# pypsi

Python Pluggable Shell Interface, or pypsi, is a framework for developing
command line based shell interfaces, akin to bash or csh.

## Why not just use the `cmd` module?

I was developing a project whose primary requirement was that it had to have a
command line interface. Python was the language we chose and the Python cmd
module appeared to ahave the capabilities we required. We found that the cmd
module provided a fast prototyping environment for adding new commands and it
hid all of the `readline` and `raw_input()` functionality under the covers so
we didn't need to worry about it.

The `cmd` module allowed us to develop a CLI in very little time. But, around
the fouth prototype release of our software, we found that we were reaching the
limits of the `cmd` module. The `cmd` module is great at one thing: developing
a small number of commands that follow a simple format in very little time. Once
we started inplemented I/O redirection, piping, and so on, I found that heavy
modifications to the core `cmd` module for this functionality to be even
possible.

So, I found the `cmd2` module and began experimenting with it. Although, on the
surface, it had what I was looking for, I found that it, too, would require
heavy modifications (and for me to understand the `pyparsing` API, which still
seems like jibberish to me.)

Finally, I came to the conclusion that a new framework would be required. I took
what I had learnt from the `cmd` module, added in some bash candy and Python
magic, and pypsi was born.

## Who should use pypsi?

As I stated earlier, I'm not discrediting or putting the `cmd` module down, I 
think it still has a use. It was great at getting out of the developer's way and
allowing us to develop new commands in little time. But, as the number of
commands exploded and multiple sub-shells were developed, it was becoming more
and more difficult to maintain and add new features to the core shell.

If you're project has over 20 commands, multiple shells, or just needs the core
features provided by pypsi, I truly believe that pypsi is the way to go.

One of the many plugins that ship with pypsi is the `cmd` plugin. This plugin
will help migrate over old `cmd`-based shells for use in pypsi. So, if you're
unsure if your project needs pypsi or cmd, starting working on a `cmd`
implementation and if it is unsuccessful, you can easily port over old commands.

## Caveats

The only major caveat when using pypsi is that it only supports Python 3.
Originally, I intended on it being compatible with both 2.7 and 3+, but after
further researching Python 3, I though it was critical that I drop 2.x support.
There are so many benefits surrounding Python 3 that I will not list them here.

## Features

* I/O redirection
* String-based pipes
* Flexible API
* Tab completion
* Multiplatform
* Minimal dependencies
* Colors

## Capabilities

Before you jump into the API, here is a list of examples that show the power of
the pypsi module, using only the commands and plugins that ship with pypsi.

### Variables

```
pypsi)> var name = "Paul"
pypsi)> var house = "Atredis"
pypsi)> echo My name is $name, and I belong to House $house
My name is Paul, and I belong to House Atredis
pypsi)> var -l
name     Paul
house    Atredis
pypsi)> var -d name
pypsi)> echo $name

pypsi)> var name = "Paul $house"
pypsi)> echo $name
Paul Atredis
```

### I/O redirection

```
pypsi)> echo Hello
Hello
pypsi)> echo Hello > output.txt
pypsi)> echo Goodbye
pypsi)> xargs -I{} "echo line: {}" < output.txt
line: Hello
line: Goodbye
```

### System commands

Allows execution of external applications. Command mimics Python's `os.system()`
function.

```
pypsi)> ls
pypsi: ls: command not found
pypsi)> system ls
include/
src/
README.md
pypsi)> system ls | system grep md
README.md
```

### Fallback command

Allows the developer to set which command gets called if one does not exist in
the current shell. This is very useful, for example, if you want to fallback on
any OS installed executables. In this example, the fallback command is `system`.
Currently, setting of the fallback command can only be done in the API and not
through the shell.

```
pypsi)> ls
include/
src/
README.md
```

### Command chaining

```
pypsi)> echo Hello && echo --bad-arg && echo goodbye
Hello
echo: unrecgonized arguments: --bad-arg
pypsi)> echo Hello ; echo --bad-arg ; echo goodbye
Hello
echo: unrecgonized arguments: --bad-arg
goodbye
pypsi)> echo --bad-arg || echo first failed
echo: unrecgonized arguments: --bad-arg
first failed
```

### Multiline commands

```
pypsi)> echo Hello, \
> Dave
Hello, Dave
pypsi)> echo This \
> is \
> pypsi \
> and it rocks
This is pypsi and it rocks
```

### Macros

```
pypsi)> macro hello
> echo Hello, $1
> echo Goodbye from macro $0
> end
pypsi)> hello Adam
Hello, Adam
Goodbye from macro hello
```

### History

```
pypsi)> history list
  1 echo hello
  2 command2
```
