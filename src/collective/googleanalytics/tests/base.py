from collective.googleanalytics.testing import INTEGRATION_TESTING
from collective.googleanalytics.testing import FUNCTIONAL_TESTING

import unittest


class TestCase(unittest.TestCase):
    """Base class used for test cases
    """

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

class FunctionalTestCase(TestCase):
    """Test case class used for functional (doc-)tests
    """

    layer = FUNCTIONAL_TESTING
