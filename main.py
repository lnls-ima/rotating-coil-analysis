# -*- coding: utf-8 -*-

"""Run the rotating coil analysis application."""

from rotcoilanalysis import rotcoilapp


_thread = True


if (__name__ == '__main__'):
    if _thread:
        thread = rotcoilapp.run_in_thread()
    else:
        rotcoilapp.run()
