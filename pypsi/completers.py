

import os

def path_completer(shell, args, prefix):
    root = None
    if args:
        root = args[-1]
        if root:
            if not root.startswith(os.path.sep) and not root.startswith('.' + os.path.sep):
                root = '.' + os.path.sep + root
        else:
            root = '.' + os.path.sep
    else:
        root = '.' + os.path.sep

    if root.endswith(prefix) and prefix:
        root = root[:0 - len(prefix)]

    #return ['prefix:'+prefix, 'root:'+root]

    if not os.path.exists(root):
        return []

    if os.path.isdir(root):
        files = []
        dirs = []
        for entry in os.listdir(root):
            full = os.path.join(root, entry)
            if entry.startswith(prefix):
                if os.path.isdir(full):
                    dirs.append(entry + os.path.sep)
                else:
                    files.append(entry)
        files = sorted(files)
        dirs = sorted(dirs)
        return dirs + files
    else:
        return []

def choice_completer(choices, case_sensitive=False):
    def complete(shell, args, prefix):
        r = []
        for choice in choices:
            if choice.startswith(prefix if case_sensitive else prefix.lower()):
                r.append(choice)
        return r
    return complete
