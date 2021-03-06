import json
from os import path
from pathlib import Path

data_path = Path(__file__).parent / 'data'

NESTED_DIVISIONS_JSON_PATH = path.join(data_path, "nested-divisions.json")
FLAT_DIVISIONS_JSON_PATH = path.join(data_path, "flat-divisions.json")


def load_word_dict():
    import os
    file_name = 'word_dict.json'
    file_path = os.path.join(data_path, file_name)
    with open(file_path, encoding="utf8") as f:
        data = json.load(f)
    return data


def load_word_bag():
    import os
    file_name = 'word_bag.json'
    file_path = os.path.join(data_path, file_name)
    with open(file_path, encoding="utf8") as f:
        data = json.load(f)
    return data


def load_address_dict():
    # print(NESTED_DIVISIONS_JSON_PATH)
    with open(NESTED_DIVISIONS_JSON_PATH, encoding="utf8") as f:
        provinces = json.load(f)
    return provinces


def make_normalized_data():
    from address_extract.utils import clean, clean_all_test
    with open(FLAT_DIVISIONS_JSON_PATH, encoding="utf8") as f:
        combinations = json.load(f)
    print(len(combinations))
    to_save_dict = {
        'original_list': [],
        'cleaned_list': [],
        'normalized_list': []
    }
    # for e in combinations:
    #     ward = e.get('ward_name')
    #     district = e.get('district_name')
    #     province = e.get('province_name')
    #     all_in_one = ward + district + province
    #     all_in_one_cleaned_test = clean_all_test(all_in_one) + str(e.get('ward_code')) #to make it unique
    #     # e['cleaned_address'] = all_in_one_cleaned_test
    #
    #     ward_cleaned = clean(e.get('ward_name'), is_ward=True)
    #     district_cleaned = clean(e.get('district_name'), is_district=True)
    #     province_cleaned = clean(e.get('province_name'), is_city=True)
    #     all_in_one_cleaned = ward_cleaned+district_cleaned+province_cleaned+str(e.get('ward_code')) #to make it unique
    #     # e['normalized_address'] = all_in_one_cleaned
    #
    #     to_save_dict['original_list'].append(e)
    #     to_save_dict['cleaned_list'].append(all_in_one_cleaned_test)
    #     to_save_dict['normalized_list'].append(all_in_one_cleaned)
    for i in range(len(combinations)):
        e = combinations[i]
        ward = e.get('ward_name')
        district = e.get('district_name')
        province = e.get('province_name')
        all_in_one = ward + district + province
        all_in_one_cleaned_test = clean_all_test(all_in_one) + "_{}".format(i)

        ward_cleaned = clean(e.get('ward_name'), is_ward=True)
        district_cleaned = clean(e.get('district_name'), is_district=True)
        province_cleaned = clean(e.get('province_name'), is_city=True)
        all_in_one_cleaned = ward_cleaned + district_cleaned + province_cleaned + "_{}".format(i)

        to_save_dict['original_list'].append(e)
        to_save_dict['cleaned_list'].append(all_in_one_cleaned_test)
        to_save_dict['normalized_list'].append(all_in_one_cleaned)

    import os
    file_name = 'address_dict_normalized.json'
    file_path = os.path.join(data_path, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(to_save_dict, f, ensure_ascii=False, indent=4)


# make_normalized_data()

def load_address_dict_normalized():
    import os
    file_name = 'address_dict_normalized.json'
    file_path = os.path.join(data_path, file_name)
    with open(file_path, encoding="utf8") as f:
        data = json.load(f)
    return data


def make_cities_data_normalized():
    from collections import Counter
    # from .utils import clean, clean_all_test
    from utils import clean, clean_all_test
    with open(FLAT_DIVISIONS_JSON_PATH, encoding="utf8") as f:
        combinations = json.load(f)
    print(len(combinations))

    for e in combinations:
        ward = clean(e.get('ward_name'), is_ward=True)
        if ward[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            ward = clean_all_test(e.get('ward_name'))
        district = clean(e.get('district_name'), is_district=True)
        if district[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            district = clean_all_test(e.get('district_name'))
        province = clean(e.get('province_name'), is_city=True)
        e['normalized_ward'] = ward + "_{}".format(e.get('ward_code'))
        e['normalized_district'] = district + "_{}".format(e.get('district_code'))
        e['normalized_province'] = province + "_{}".format(e.get('province_code'))

    p_list = []
    d_list = []
    w_list = []
    for e in combinations:
        p_list.append((e.get('province_name'), e.get('province_code')))
        d_list.append((e.get('district_name'), e.get('district_code')))
        w_list.append((e.get('ward_name'), e.get('ward_code')))

    print(len(p_list))
    print(len(d_list))
    print(len(w_list))
    p_dict = dict(Counter(p_list))
    d_dict = dict(Counter(d_list))
    w_dict = dict(Counter(w_list))

    ip = {}
    id = {}
    iw = {}
    for e in p_dict.keys():
        ip[e] = []
        for i in range(len(combinations)):
            if e[1] == combinations[i].get('province_code'):
                ip[e].append((i, combinations[i].get('normalized_province')))

    for e in d_dict.keys():
        id[e] = []
        for i in range(len(combinations)):
            if e[1] == combinations[i].get('district_code'):
                id[e].append((i, combinations[i].get('normalized_district')))

    for e in w_dict.keys():
        iw[e] = []
        for i in range(len(combinations)):
            if e[1] == combinations[i].get('ward_code'):
                iw[e].append((i, combinations[i].get('normalized_ward')))
    city_dict = {
        'provinces': [],
        'districts': [],
        'wards': [],
        'provinces_normalized': [],
        'districts_normalized': [],
        'wards_normalized': []
    }

    import re
    from unidecode import unidecode
    def remove_leading_zero_for_one_digit_number(num_as_string: str):
        splits = num_as_string.split(' ')
        if len(splits) > 0:
            clean_list = [i.lstrip('0') for i in splits]
            result = ' '.join(clean_list)
            return result
        return num_as_string

    def clean_keep_space(address: str, is_city=False, is_district=False, is_ward=False):
        def only_alphanumeric(address: str):
            return re.sub(r'[^A-Za-z0-9\s]', '', address)

        def normalized_city(address: str):
            return re.sub(r'(tp\.)|(tp\s)|(^tinh\s)|(thanh\spho\s)', '', address, flags=re.IGNORECASE)

        def normalized_district(address: str):
            return re.sub(r'(^huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(^quan\s)', '', address,
                          flags=re.IGNORECASE)

        def normalized_ward(address: str):
            return re.sub(r'(^xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(p\.)|([^a-z]+p\s+)|(^phuong\s)', '', address,
                          flags=re.IGNORECASE)

        try:
            result = unidecode(address)
            result = remove_leading_zero_for_one_digit_number(result)
            if is_city:
                result = normalized_city(result)
            elif is_district:
                result = normalized_district(result)
            elif is_ward:
                result = normalized_ward(result)
            return only_alphanumeric(result).lower()
        except Exception as e:
            print(e)

    for pk in p_dict.keys():
        province_node = {}
        province_node['province_name'] = pk[0]
        province_node['province_code'] = pk[1]
        province_node['start_index'] = ip[pk][0][0]
        province_node['end_index'] = ip[pk][-1][0]
        province_node['normalized_province'] = ip[pk][0][1]
        print(pk[0])
        province_cleaned = clean_keep_space(pk[0], is_city=True)
        ps = province_cleaned.split(' ')
        ps = [i for i in ps if i]
        province_node['province_words'] = ps

        city_dict['provinces'].append(province_node)
        city_dict['provinces_normalized'].append(province_node['normalized_province'])

    for dk in d_dict.keys():
        district_node = {}
        district_node['district_name'] = dk[0]
        district_node['district_code'] = dk[1]
        district_node['start_index'] = id[dk][0][0]
        district_node['end_index'] = id[dk][-1][0]
        district_node['normalized_district'] = id[dk][0][1]

        district_cleaned = clean_keep_space(dk[0], is_district=True)
        ds = district_cleaned.split(' ')
        ds = [i for i in ds if i]
        district_node['district_words'] = ds

        city_dict['districts'].append(district_node)
        city_dict['districts_normalized'].append(district_node['normalized_district'])

    for wk in w_dict.keys():
        ward_node = {}
        ward_node['ward_name'] = wk[0]
        ward_node['ward_code'] = wk[1]
        ward_node['start_index'] = iw[wk][0][0]
        ward_node['end_index'] = iw[wk][-1][0]
        ward_node['normalized_ward'] = iw[wk][0][1]

        ward_cleaned = clean_keep_space(wk[0], is_ward=True)
        ws = ward_cleaned.split(' ')
        ws = [i for i in ws if i]
        ward_node['district_words'] = ws

        city_dict['wards'].append(ward_node)
        city_dict['wards_normalized'].append(ward_node['normalized_ward'])

    # print(city_dict['provinces'])

    # import os
    # file_name = 'cities_normalized.json'
    # file_path = os.path.join(data_path,file_name)
    # with open(file_path, 'w', encoding='utf-8') as f:
    #     json.dump(city_dict, f, ensure_ascii=False, indent=4)

    import os
    file_name = 'cities_normalized_new.json'
    file_path = os.path.join(data_path, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(city_dict, f, ensure_ascii=False, indent=4)


# make_cities_data_normalized()


def load_cities_data_normalized():
    import os
    # file_name = 'cities_normalized.json'
    file_name = 'cities_normalized.json'
    file_path = os.path.join(data_path, file_name)
    with open(file_path, encoding="utf8") as f:
        data = json.load(f)
    return data
