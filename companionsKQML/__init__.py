# -*- coding: utf-8 -*-
# @Author: Samuel Hill
# @Date:   2020-02-10 15:30:23
# @Last Modified by:   Samuel Hill
# @Last Modified time: 2020-03-02 15:21:07

"""Package containing a low level Companions specific KQML server module as
well as the Pythonian module for higher level KQML communication."""

__version__ = '1.0.1'

# from logging import basicConfig, INFO
from .pythonian import Pythonian
from .companionsKQMLModule import CompanionsKQMLModule, \
      ControlledCompanionsKQMLModule, listify, performative, \
      convert_to_boolean, convert_to_int

__authors__ = "Samuel Hill, Willie Wilson, and Joe Blass"
__copyright__ = "Copyright 2020, Samuel Hill"
__credits__ = ["Samuel Hill", "Willie Wilson", "Joe Blass",
               "Irina Rabkina", "Constantine Nakos", "Will Hancock"]
__license__ = "BSD-3-Clause"  # https://opensource.org/licenses/BSD-3-Clause
__maintainer__ = "Samuel Hill"
__email__ = "samuelhill2020@northwestern.edu"
__status__ = "Prototype"

# Can't seem to override pykqml format...
# basicConfig(format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
#             level=INFO)
