# -*- coding: utf-8 -*-
# Copyright (C) 2012 Sun Ning<classicning@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# clojure literals => python types
#
# clojure vector [1 2 3 4] => python list [1 2 3 4] *coll
# clojure list (1 2 3 4) => python list [1 2 3 4] *coll
# clojure set #{1 2 3 4} => python set set(1 2 3 4) *coll
# clojure map {:a 1 :b 2} => python dict dict(a=1,b=2) *coll
# clojure string "a" => python unicode "a"
# clojure character \a => python unicode "a"
# clojure keyword :a => python unicode "a"
# clojure integer 123 => python integer 123
# clojure float 12.3 => python float 12.3
# clojure BigDecimal 12.34M => python decimal.Decimal
# clojure boolean true => python boolean true
# clojure nil => python None
#
# clojure datetime => python datetime
# clojure uuid => python uuid
#


__all__ = ["dump", "dumps", "load", "loads"]

import os
from io import StringIO
from io import BytesIO
import json

import decimal
import uuid
from datetime import datetime
import pyrfc3339
import pytz


def number(v):
    if v.endswith('M'):
        out = decimal.Decimal(v[:-1])
    else:
        try:
            out = int(v)
        except ValueError as e:
            out = float(v)
    return out


_STOP_CHARS = [" ", ",", "\n", "\r", "\t"]
_COLL_OPEN_CHARS = ["#", "[", "{", "("]
_COLL_CLOSE_CHARS = ["]", "}", ")"]
_EXTRA_NUM_CHARS = ["-", "+", ".", "e", "E", "M"]


class CljDecoder(object):
    def __init__(self, fd):
        self.fd = fd
        self.cur_line = 1
        self.cur_pos = 1
        self.value_stack = []
        self.terminator = None ## for collection type

    def decode(self):
        while True:
            v = self.__read_token()
            if len(self.value_stack) == 0:
                return v

    def __seek_back(self, size):
        self.fd.seek(self.fd.tell()-size, 0)

    def __read_and_back(self, size):
        s = self.fd.read(size)
        self.__seek_back(size)
        return s

    def __get_type_from_char(self, c):
        """return a tuple of type information
        * type name
        * a flag to indicate if it's a collection
        """
        if c.isdigit() or c =='-':
            return ("number", False, None)
        elif c == 't' or c == 'f': ## true/false
            return ("boolean", False, None)
        elif c == 'n': ## nil
            return ("nil", False, None)
        elif c == '\\' :
            return ("char", False, None)
        elif c == ':':
            return ("keyword", False, None)
        elif c == '"':
            return ("string", False, None)
        elif c == '#':
            if self.__read_and_back(1) == '{':
                return ("set", True, "}")
            if self.__read_and_back(1) == ':':
                return ("namespaced_dict", True, "}")
            if self.__read_and_back(4) == 'inst':
                return ("datetime", False, None)
            if self.__read_and_back(4) == 'uuid':
                return ("uuid", False, None)
        elif c == '{':
            return ("dict", True, "}")
        elif c == '(':
            return ("list", True, ")")
        elif c == '[':
            return ('list', True, "]")

        return (None, False, None)

    def __read_fd(self, size):
        if size == 1:
            c = self.fd.read(size)
            if  c == '\n':
                self.cur_pos = 0
                self.cur_line = self.cur_line + 1
            return c
        else:
            self.cur_pos = self.cur_pos + size
            cs = self.fd.read(size)
            return cs

    def __read_token(self):
        c = self.__read_fd(1)

        ## skip all stop chars if necessary
        while c in _STOP_CHARS:
            c = self.__read_fd(1)

        ## raise exception when unexpected EOF found
        if c == '':
            raise ValueError("Unexpected EOF")

        t, coll, term = self.__get_type_from_char(c)
        if coll:
            ## move cursor
            if t == "set":
                ## skip {
                self.__read_fd(1)
            namespace = None
            if t == "namespaced_dict":
                ## skip :
                self.__read_fd(1)
                ## get namespace
                buf = []
                while c != '{':
                    c = self.__read_fd(1)
                    buf.append(c)
                namespace = ''.join(buf[:-1])

            self.terminator = term

            self.value_stack.append(([], self.terminator, t, namespace))
            return None
        else:
            v = None ## token value
            e = None ## end char
            r = True ## the token contains data or not

            if t == "boolean":
                if c == 't':
                    chars = self.__read_fd(4)
                    if chars[:3] != 'rue':
                        raise ValueError('Expect true, got t%s at line %d, col %d' % (chars[:3], self.cur_line, self.cur_pos))
                    e = chars[-1]
                    v = True
                else:
                    chars = self.__read_fd(5)
                    if chars[:4] != 'alse':
                        raise ValueError('Expect true, got t%s at line %d, col %d' % (chars[:3], self.cur_line, self.cur_pos))
                    e = chars[-1]
                    v = False

            elif t == "char":
                buf = []
                while c is not self.terminator and c is not "" and c not in _STOP_CHARS:
                    c = self.__read_fd(1)
                    buf.append(c)

                e = c
                v = ''.join(buf[:-1])

            elif t == "nil":
                chars = self.__read_fd(3)
                if chars[:2] != 'il':
                    raise ValueError('Expect nil, got n%s at line %d, col %d' % (chars[:2], self.cur_line, self.cur_pos))
                e = chars[-1]
                v = None

            elif t == "number":
                buf = []
                while c.isdigit() or (c in _EXTRA_NUM_CHARS):
                    buf.append(c)
                    c = self.__read_fd(1)
                e = c
                numstr = ''.join(buf)
                v = number(numstr)

                ## special case for
                ## [23[12]]
                ## this is a valid clojure form
                if e in _COLL_OPEN_CHARS:
                    self.__seek_back(1)

            elif t == "keyword":
                buf = []    ##skip the leading ":"
                while c is not self.terminator and c is not "" and c not in _STOP_CHARS:
                    c = self.__read_fd(1)
                    buf.append(c)

                e = c
                v = ''.join(buf[:-1])

            elif t == "string":
                buf = []
                cp = c = self.__read_fd(1) ## to check escaping character \

                while not(c == '"' and cp != '\\'):
                    buf.append(c)
                    cp = c
                    c = self.__read_fd(1)
                e = c
                v = unicode(''.join(buf).decode('unicode-escape'))

            elif t == "datetime":
                ## skip "inst"
                self.__read_fd(4)

                ## read next value as string
                s = self.__read_token()
                if not isinstance(s, basestring):
                    raise ValueError('Str expected, but got %s' % str(s))

                ## remove read string from the value_stack
                if len(self.value_stack) > 0:
                    self.value_stack[-1][0].pop()
                e = '"'
                v = pyrfc3339.parse(s)

            elif t == "uuid":
                ## skip "uuid"
                self.__read_fd(4)

                ## read next value as string
                s = self.__read_token()
                if not isinstance(s, basestring):
                    raise ValueError('Str expected, but got %s' % str(s))

                ## remove read string from the value_stack
                if len(self.value_stack) > 0:
                    self.value_stack[-1][0].pop()
                e = '"'
                v = uuid.UUID(s)

            else:
                if c not in _COLL_CLOSE_CHARS:
                    raise ValueError('Unexpected char: "%s" at line %d, col %d' % (c, self.cur_line, self.cur_pos))
                r = False
                e = c

            if e == self.terminator:
                current_scope, _, container, namespace = self.value_stack.pop()

                if r:
                    current_scope.append(v)

                if container == "set":
                    try:
                        v = set(current_scope)
                    except TypeError:
                        v = tuple(current_scope)
                elif container == "list":
                    v = current_scope
                elif container in ["dict", "namespaced_dict"]:
                    v = {}
                    for i in range(0, len(current_scope), 2):
                        key = '%s/%s' % (namespace, current_scope[i]) if namespace else current_scope[i]
                        v[key] = current_scope[i+1]
                r = True

            if r and len(self.value_stack) > 0:
                self.value_stack[-1][0].append(v)
                self.terminator = self.value_stack[-1][1]

            return v


class CljEncoder(object):
    def __init__(self, data, fd):
        self.data = data
        self.fd = fd
        self.circular = {}

    def encode(self):
        self.__do_encode(self.data)

    def get_type(self, t):
        if t is None:
            return ("None", False)
        elif isinstance(t, str):
            return ("string", False)
        elif isinstance(t, bool):
            return ("boolean", False)
        elif isinstance(t, (int,float)):
            return ("number", False)
        elif isinstance(t, decimal.Decimal):
            return ("decimal", False)
        elif isinstance(t, dict):
            return ("dict", True)
        elif isinstance(t, (list,tuple)):
            return ("list", True)
        elif isinstance(t, set):
            return ("set", True)
        elif isinstance(t, datetime):
            return ("datetime", False)
        elif isinstance(t, uuid.UUID):
            return ("uuid", False)
        else:
            return ("unknown", False)

    def __do_encode(self, d):
        fd = self.fd
        t,coll = self.get_type(d)

        if coll:
            refid = id(d)
            if refid in self.circular:
                raise ValueError('Circular reference detected')
            else:
                self.circular[refid] = True

            if t == "dict":
                fd.write("{")
                if len(d) > 0:
                    for k,v in d.items():
                        self.__do_encode(k)
                        fd.write(" ")
                        self.__do_encode(v)
                        fd.write(" ")
                    fd.seek(-1, os.SEEK_CUR)
                fd.write("}")
            elif t == "list":
                fd.write("[")
                if len(d) > 0:
                    for v in d:
                        self.__do_encode(v)
                        fd.write(" ")
                    fd.seek(-1, os.SEEK_CUR)
                fd.write("]")
            elif t == "set":
                fd.write("#{")
                if len(d) > 0:
                    for v in d:
                        self.__do_encode(v)
                        fd.write(" ")
                    fd.seek(-1, os.SEEK_CUR)
                fd.write("}")
        else:
            if t == "number":
                fd.write(str(d))
            elif t == "decimal":
                fd.write(str(d) + 'M')
            elif t == "string":
                s = json.encoder.py_encode_basestring_ascii(unicode(d))
                fd.write(s)
            elif t == "boolean":
                if d:
                    fd.write('true')
                else:
                    fd.write('false')
            elif t == 'None':
                fd.write('nil')
            elif t == 'datetime':
                if not d.tzinfo:
                    ## replace naive datetime
                    d = d.replace(tzinfo=pytz.utc)
                s = pyrfc3339.generate(d)
                fd.write("#inst \"%s\"" % s)
            elif t == 'uuid':
                s = str(d)
                fd.write("#uuid \"%s\"" % s)
            else:
                s = json.encoder.py_encode_basestring_ascii(unicode(d))
                fd.write(s)


def dump(obj, fp):
    return CljEncoder(obj, fp).encode()


def dumps(obj):
    buf = BytesIO()
    dump(obj, buf)
    result = buf.getvalue()
    buf.close()
    return result


def load(fp):
    decoder = CljDecoder(fp)
    return decoder.decode()


def loads(s):
    buf = StringIO(s)
    result = load(buf)
    buf.close()
    return result
