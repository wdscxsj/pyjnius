'''
Pyjnius
=======

Accessing Java classes from Python.

All the documentation is available at: http://pyjnius.readthedocs.org
'''

__version__ = '1.2.1.dev5'

from .env import get_jnius_lib_location, get_jdk_home

import os
import sys
if sys.platform == 'win32' and sys.version_info >= (3, 8):
    path = os.path.dirname(__file__)
    jdk_home = get_jdk_home(sys.platform)
    with os.add_dll_directory(path):
        for suffix in (
            ('bin', 'client'),
            ('bin', 'server'),
            ('jre', 'bin', 'client'),
            ('jre', 'bin', 'server'),
        ):
            path = os.path.join(jdk_home, *suffix)
            if not os.path.isdir(path):
                continue

            with os.add_dll_directory(path):
                try:
                    from .jnius import *  # noqa
                    from .reflect import *  # noqa
                except Exception as e:
                    pass
                else:
                    break
        else:
            raise Exception("Unable to create jni env, no jvm dll found.")
else:
    from .jnius import *  # noqa
    from .reflect import *  # noqa

from six import with_metaclass

# XXX monkey patch methods that cannot be in cython.
# Cython doesn't allow to set new attribute on methods it compiled

HASHCODE_MAX = 2 ** 31 - 1


class PythonJavaClass_(with_metaclass(MetaJavaBase, PythonJavaClass)):

    @java_method('()I', name='hashCode')
    def hashCode(self):
        return id(self) % HASHCODE_MAX

    @java_method('()Ljava/lang/String;', name='hashCode')
    def hashCode_(self):
        return '{}'.format(self.hashCode())

    @java_method('()Ljava/lang/String;', name='toString')
    def toString(self):
        return repr(self)

    @java_method('(Ljava/lang/Object;)Z', name='equals')
    def equals(self, other):
        return self.hashCode() == other.hashCode()


PythonJavaClass = PythonJavaClass_


# from https://gist.github.com/tito/09c42fb4767721dc323d
import os
if "ANDROID_ARGUMENT" in os.environ:
    # on android, catch all exception to ensure about a jnius.detach
    import threading
    import jnius
    orig_thread_run = threading.Thread.run

    def jnius_thread_hook(*args, **kwargs):
        try:
            return orig_thread_run(*args, **kwargs)
        finally:
            jnius.detach()

    threading.Thread.run = jnius_thread_hook
