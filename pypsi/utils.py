
from chardet.universaldetector import UniversalDetector
import codecs


def Title(title):
    return "{title}\n{underline}\n".format(title=title, underline='='*len(title))


def safe_open(path, mode='r'):
    u = UniversalDetector()
    first = None
    with open(path, 'rb') as fp:
        for line in fp:
            if not first:
                first = line
            u.feed(line)
            if u.done:
                break
    u.close()

    fp = codecs.open(path, 'r', encoding=u.result['encoding'])
    for bom in (codecs.BOM_UTF8, codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE, 
                codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE):
        if first.startswith(bom):
            fp.read(1)
            break

    return fp



