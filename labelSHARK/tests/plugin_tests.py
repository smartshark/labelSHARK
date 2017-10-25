#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import unittest

from labelSHARK.core import LabelSHARK

WRONG_BASECLASS_APPROACH = """
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import LabelSHARK, BaseLabelApproach

@LabelSHARK.approach
class WrongApproach(object):

    def configure(self, config):
        pass

    def get_labels(self, commit):
        pass
"""

# add ./labelSHARK to path so that we can import like we would do in an installation
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(1, os.path.abspath('./labelSHARK'))


class TestPluginStructure(unittest.TestCase):
    """Just some very basic tests for the plugin system."""

    def test_no_baseclass(self):
        # 1. write new plugin
        with open('./labelSHARK/approaches/test.py', 'w') as f:
            f.write(WRONG_BASECLASS_APPROACH)

        # 2. import plugin, this should fail with an exception complaining about wrong baseclass
        try:
            __import__('approaches.test')
        except Exception as e:
            self.assertTrue('not of type BaseLabelApproach' in str(e))

        # 3. test plugin
        # l = LabelSHARK()
        # l.configure({})
        # l.get_labels({})
