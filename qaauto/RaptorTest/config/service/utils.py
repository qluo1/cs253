"""

"""
import os
from datetime import date
import mmap
import ctypes

class SeqNumber():
    """ quick/dirty sequence generator."""

    def __init__(self,root_dir,name):
        """ """
        fn = os.path.join(root_dir,\
                    '%s_%s.mmap' %(name,date.today().isoformat()))
        if os.path.exists(fn):
            fd = os.open(fn,os.O_RDWR)
        else:
            fd = os.open(fn,os.O_CREAT|os.O_TRUNC|os.O_RDWR)
            assert os.write(fd,'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE

        self.buf_ = mmap.mmap(fd,mmap.PAGESIZE,mmap.MAP_SHARED)

    @property
    def next(self):
        """ return next seq nmber"""
        seq = ctypes.c_int64.from_buffer(self.buf_)

        seq.value +=1

        return seq.value

    def set_next(self,val):
        seq = ctypes.c_int64.from_buffer(self.buf_)
        seq.value = val

    @property
    def current(self):
        seq = ctypes.c_int64.from_buffer(self.buf_)
        return seq.value

class Priority:
    """ message priority and category."""
    order = 0
    er = 1
    info = 9

