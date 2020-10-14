from address_extract import extract_group, clean
from tests.constants import *

import unittest
class TestExtractGroup(unittest.TestCase):
    def setUp(self):
        self.group_keys = ('street', 'ward', 'district', 'city')
    def tearDown(self):
        self.group_keys = None

    def test_extract_group(self):
        # Expected a tuple and order does matter

        vi_addr = ADDRESSES.get('vi')
        en_addr = ADDRESSES.get('en')
        result = extract_group(vi_addr, self.group_keys)
        expected = EXPECTED_ADDRESSES_AS_GROUP.get('vi')
        self.assertDictEqual(result, expected)
        result = extract_group(en_addr, self.group_keys)
        expected = EXPECTED_ADDRESSES_AS_GROUP.get('en')
        self.assertDictEqual(expected,result)

    def test_extract_group_one_two_three_group(self):
        # Expected a tuple and order does matter
        cases = ADDRESSES_ONE_TWO_THREE.keys()
        for c in cases:
            addr = ADDRESSES_ONE_TWO_THREE[c]
            result = extract_group(addr, self.group_keys)
            # print(result)
            expected = EXPECTED_ADDRESSES_ONE_TWO_THREE.get(c)
            # print(expected)
            self.assertDictEqual(expected,result)

    def test_extract_group_five_six_empty_group(self):
        # Expected a tuple and order does matter
        cases = ADDRESSES_FIVE_SIX_EMPTY.keys()
        for c in cases:
            addr = ADDRESSES_FIVE_SIX_EMPTY[c]
            result = extract_group(addr, self.group_keys)
            # print(result)
            expected = EXPECTED_ADDRESSES_FIVE_SIX_EMPTY.get(c)
            # print(expected)
            self.assertDictEqual(expected, result)

    def test_clean_english_string(self):
        s = "~!@#$%^&*()1 werty 1234567890 2` 3\ // \ 4/\\|,.' 5+=-"
        expected = "1werty12345678902345"
        result = clean(s)
        self.assertEqual(expected, result)

    def test_clean_vietnamese_string(self):
        s = "HỒ CHÍ MINH ~!@#$%^&*()1 werty 1234567890 2` 3\ // \ 4/\\|,.' 5+=-"
        expected = "hochiminh1werty12345678902345"
        result = clean(s)
        self.assertEqual(expected, result)

    def test_clean_vietnamese_string_city(self):
        s = "tỉnh Tỉnh Tp. thành phố THANH PHO tP tp~!@#$%^&*()1 werty 1234567890 2` 3\ // \ 4/\\|,.' 5+=-"
        expected = "tinhtp1werty12345678902345"
        result = clean(s, is_city=True)
        self.assertEqual(expected, result)

    def test_clean_vietnamese_string_district(self):
        s = " Quận QUẬN THÀNH PHỐ tHỊ xã Huyện HUYỆN huyện TX. tx ~!@#$%^&*()1 werty 1234567890 2` 3\ // \ 4/\\|,.' 5+=-"
        expected = "1werty12345678902345"
        result = clean(s, is_district=True)
        self.assertEqual(expected, result)

    def test_clean_vietnamese_string_ward(self):
        s = "p. P pp tT tt. phường Phường xã XÃ THỊ TRẤN thị trấn Thị Trấn ~!@#$%^&*()1 werty 1234567890 2` 3\ // \ 4/\\|,.' 5+=-"
        expected = "pp1werty12345678902345"
        result = clean(s, is_ward=True)
        self.assertEqual(expected, result)
