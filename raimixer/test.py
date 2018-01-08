import sys
import unittest
from raimixer.cli import convert_amount
from raimixer.utils import normalize_amount
from raimixer.rairpc import MRAI_TO_RAW, KRAI_TO_RAW

class TestMixerHelpers(unittest.TestCase):
    def test_010_normalize_amount(self) -> None:
        self.assertEqual(normalize_amount('1', MRAI_TO_RAW), 1 * MRAI_TO_RAW)
        self.assertEqual(normalize_amount('10', MRAI_TO_RAW), 10 * MRAI_TO_RAW)
        self.assertEqual(normalize_amount('0.1', MRAI_TO_RAW), (1 * MRAI_TO_RAW) // 10)
        self.assertEqual(normalize_amount('0.00001', MRAI_TO_RAW), (1 * MRAI_TO_RAW) // (10 ** 5))
        self.assertEqual(normalize_amount('1.234', MRAI_TO_RAW), (1234 * MRAI_TO_RAW) // (10 ** 3))

    def test_020_convert_amount(self) -> None:
        self.assertEqual(convert_amount('10xrb'), 10 * MRAI_TO_RAW)
        self.assertEqual(convert_amount('10XRB'), 10 * MRAI_TO_RAW)
        self.assertEqual(convert_amount('10mrai'), 10 * MRAI_TO_RAW)
        self.assertEqual(convert_amount('10krai'), 10 * KRAI_TO_RAW)
        self.assertEqual(convert_amount('10KrAi'), 10 * KRAI_TO_RAW)
        self.assertEqual(convert_amount('0.1xrb'), MRAI_TO_RAW // 10)
        self.assertEqual(convert_amount('3.12345krai'), 312345 * (KRAI_TO_RAW // (10 ** 5)))

        with self.assertRaises(SystemExit): convert_amount('1')
        with self.assertRaises(SystemExit): convert_amount('1m')
        with self.assertRaises(SystemExit): convert_amount('1k')
        with self.assertRaises(SystemExit): convert_amount('1x')
        with self.assertRaises(SystemExit): convert_amount('1,12mrai')
        with self.assertRaises(SystemExit): convert_amount('1.12.12mrai')
