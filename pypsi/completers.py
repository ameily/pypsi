

import os

def path_completer(shell, args, prefix):
    root = None
    if args:
        root = args[-1]
        if root:
            if not root.startswith('/') and not root.startswith('./'):
                root = './' + root
        else:
            root = './'
    else:
        root = './'

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
                    dirs.append(entry + '/')
                else:
                    files.append(entry)
        files = sorted(files)
        dirs = sorted(dirs)
        return dirs + files
    else:
        return []

def choice_completer(choices):
    def complete(shell, args, prefix):
        r = []
        for choice in choices:
            if choice.startswith(prefix.lower()):
                r.append(choice)
        return r
    return complete