from django.test import TestCase
from django.conf import settings

from sfmmanager.storage_utils import PlyHeader

import os

# test Ply parser
class PlyTestCase(TestCase):

    def test_missing_signature(self):
        data = open(os.path.join(settings.MEDIA_ROOT, "testing/ply/nosign.ply"))
        self.assertRaises(Exception, PlyHeader, data)

    def test_good(self):
        data = open(os.path.join(settings.MEDIA_ROOT, "testing/ply/result2.ply"))
        ply = PlyHeader(data)
        self.assertEqual(ply.elements["vertex"].number, 5729)
        self.assertEqual(ply.format, "binary_little_endian")
