# -*- coding=UTF-8 -*-
"""Test `files` module.  """

import time

from wlf import files


def test_is_same(tmpdir):
    file1 = tmpdir.dirpath('file1')
    file1.write('aaa')
    file2 = tmpdir.dirpath('file2')
    file2.write('aaa')
    file2.setmtime(0)

    assert not files.is_same(file1, file2)
    current_time = time.time()
    file1.setmtime(current_time)
    file2.setmtime(current_time)
    assert files.is_same(file1, file2)
    file2.write('bbbb')
    assert not files.is_same(file1, file2)
