#!/usr/bin/python
import fastbencode
import pprint
import sys
import traceback

MAXSZ = 4 * 1024 * 1024
PATH_INFO = {('path',): 'str', ('encoding',): 'str', ('created by',): 'str', ('announce',): 'str',
             ('announce-list',): 'str', ('info', 'files', 'path'): 'str', ('info', 'name'): 'str', ('info', 'source'): 'str'}


args = list(map(lambda s: s.strip(), sys.argv[1:]))

if len(args) == 0 or any(map(lambda s: s.startswith('-'), args)):
    print(f"Usage: {sys.argv[0]} FILES")
    exit(0 if '-h' in args or '--help' in args else 1)


class BadEncoding:
    def __init__(self, *, data: bytes, expectedEncoding: str = None):
        self.data = data
        self.expectedEncoding = expectedEncoding

    def repr(self):
        return f'BadEncoding(data={repr(self.data)}, expectedEncoding={repr(self.expectedEncoding)})'

    def __bool__(self):
        return False


def decodeBytes(bs: bytes, *, encoding: str):
    try:
        s = bs.decode(encoding=encoding)
    except UnicodeDecodeError:
        return BadEncoding(data=bs, expectedEncoding=encoding)
    return s


def makeLogger(name):
    def f(s, *, end='\n'):
        return sys.stderr.write(name + ': ' + s + end)
    return f


info = makeLogger('INFO')
error = makeLogger('ERROR')


def pretty(dic):
    pprint.pprint(dic)


def decode(node, *, path: tuple[str] = tuple([]), encoding: str = 'utf8') -> dict:
    def rec(node, *, path=path):
        return decode(node, path=path, encoding=encoding)

    def decs(bs: bytes):
        return decodeBytes(bs, encoding=encoding)

    if isinstance(node, dict):
        res = {}
        for k, v in node.items():
            ks = decs(k)
            res[ks] = rec(v, path=path+(ks,))
        return res
    elif isinstance(node, list):
        return [rec(x) for x in node]
    elif isinstance(node, bytes):
        pinfo = PATH_INFO.get(path)
        if pinfo:
            if pinfo == 'str':
                return decs(node)
            else:
                assert False
        else:
            return node
    elif isinstance(node, int):
        return node
    else:
        raise Exception(
            f"Following node has unknown type {type(node)}: {node}")


errcnt = 0

for fn in args:
    was_error = False
    info('Doing ' + fn)
    for _ in [None]:
        with open(fn, 'rb') as f:
            bs = f.read(MAXSZ)
            if f.read(1):
                error(f'File size > {MAXSZ} bytes')
                was_error = True
                break
            try:
                dic = fastbencode.bdecode(bs)
            except Exception as e:
                error('Error happened during parsing:\n' + ''.join(traceback.format_exception(e)), end='')
                was_error = True
                break
            encoding = dic.get(b'encoding')
            if encoding is None:
                encoding = 'utf8'
                info('Encoding not found in torrent file. Using ' + encoding)
            else:
                encoding = decodeBytes(encoding, encoding='ascii')
                if encoding:
                    info('Using encoding ' + encoding)
                else:
                    error('Cannot understand encoding: ' + str(encoding))
                    was_error = True
                    break
            pretty(decode(dic, encoding=encoding))
    if was_error:
        errcnt += 1

sys.exit(0 if errcnt == 0 else 1)
