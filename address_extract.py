def extract_group(add: str, group_keys: tuple):
    groups = add.split(',')
    for i in range(len(groups)):
        value = groups[i].strip()
        if len(value) > 0:
            groups[i] = value
        else:
            groups[i] = None
    # Remove None
    groups = [e for e in groups if e]
    # If more than 4 elements then merged all head elements into one
    if len(groups) > 4:
        boundary = len(groups) - 3
        all_head_in_one = ' '.join(groups[0:boundary])
        groups = [all_head_in_one] + groups[boundary:]
        # print(groups)
        # print(len(groups))

    # Mapping values from address groups, address groups assumped to be smaller than groups keys
    result = dict()
    for i in range(len(groups)):
        result[group_keys[i]] = groups[i]
    return result

from unidecode import unidecode
import re

# def clean(address: str, is_city = False, is_district=False, is_ward=False):
#     def only_alphanumeric(address: str):
#         return re.sub(r'[^A-Za-z0-9]', '', address)
#     def normalized_city(address: str):
#         return re.sub(r'(tp\.)|(tp\s)|(tinh\s)|(thanh\spho\s)','', address, flags=re.IGNORECASE)
#     def normalized_district(address: str):
#         return re.sub(r'(huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(quan\s)', '', address, flags=re.IGNORECASE)
#     def normalized_ward(address: str):
#         return re.sub(r'(xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(p\.)|(p\s)|(phuong\s)', '', address, flags=re.IGNORECASE)
#     try:
#         result = unidecode(address)
#         if is_city:
#             result = normalized_city(result)
#         elif is_district:
#             result = normalized_district(result)
#         elif is_ward:
#             result = normalized_ward(result)
#         return only_alphanumeric(result).lower()
#     except Exception as e:
#         print(e)

# This way is expected to work faster
def clean(address: str, is_city = False, is_district=False, is_ward=False):
    def only_alphanumeric(address: str):
        return re.sub(r'[^a-z0-9]', '', address)
    def normalized_city(address: str):
        return re.sub(r'(tp\.)|(tp\s)|(tinh\s)|(thanh\spho\s)','', address)
    def normalized_district(address: str):
        return re.sub(r'(huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(quan\s)', '', address)
    def normalized_ward(address: str):
        return re.sub(r'(xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(p\.)|(p\s)|(phuong\s)', '', address)
    try:
        result = unidecode(address)
        result = result.lower()
        if is_city:
            result = normalized_city(result)
        elif is_district:
            result = normalized_district(result)
        elif is_ward:
            result = normalized_ward(result)
        return only_alphanumeric(result)
    except Exception as e:
        print(e)

def look_up(key_value_pairs: dict, address_dict: list, rate_city = 90, rate_district = 80, rate_ward = 65):
    # Searching data procedure:
    # Decide how much group
    no_of_group = len(key_value_pairs.keys())
    guess_result = {}
    for k, v in key_value_pairs.items():
        guess_result[k] = v
    # 1st: City
    # print(key_value_pairs)
    to_look_city = key_value_pairs.get('city')
    if to_look_city is None:
        return False, None
    to_look_city_cleaned = clean(to_look_city, is_city=True)
    city_list = [clean(pc.get('name'),is_city=True) for pc in address_dict]
    if len(to_look_city_cleaned) > 0:
        # Get the city name
        city_value, rate1 = process.extractOne(to_look_city_cleaned, city_list)
        if rate1 < rate_city:
            return False, None
        else:
            # 2nd Dictrict
            index = city_list.index(city_value)
            city_node = address_dict[index]
            guess_result['city'] = city_node.get('name')
            # if only 2 groups means passed
            if no_of_group == 2:
                return True, guess_result

            district_node = city_node.get('districts')
            to_look_district = key_value_pairs.get('district')
            # Get the district name
            cleaned_to_look_district = clean(to_look_district, is_district=True)
            if len(cleaned_to_look_district) <= 0:
                return False, guess_result

            district_list = [clean(d.get('name'),is_district=True) for d in district_node]
            district_value, rate2 = process.extractOne(cleaned_to_look_district, district_list)
            if rate2 < rate_district:
                return False, guess_result
            else:
                # 3rd Ward
                d_index = district_list.index(district_value)
                ward_node = district_node[d_index].get('wards')
                guess_result['district'] = district_node[d_index].get('name')
                # if only 3 groups means passed, no need to check for ward
                if no_of_group == 3:
                    return True, guess_result
                to_look_ward = key_value_pairs.get('ward')
                cleaned_to_look_ward = clean(to_look_ward, is_ward=True)
                if len(cleaned_to_look_ward) <= 0:
                    return False, guess_result
                ward_list = [clean(w.get('name'),is_ward=True) for w in ward_node]
                ward_value, rate3 = process.extractOne(cleaned_to_look_ward, ward_list)
                if rate3 < rate_ward:
                    return False, None
                else:
                    w_index = ward_list.index(ward_value)
                    guess_result['ward'] = ward_node[w_index].get('name')
                    # print("Happy caes: {}".format(str(guess_result)))
                    return True, guess_result
    return False, None

from itertools import permutations
from fuzzywuzzy import process

def brute_force_search(address_dict: list, key_value_pairs: dict, address: str):
    group_names = {'street', 'ward', 'district', 'city'}
    no_of_group = len(key_value_pairs.keys())
    if no_of_group == 1:
        return key_value_pairs, None
    elif no_of_group >= 2 and no_of_group <= 4:
        if no_of_group == 2:
            group_names.remove('ward')
            group_names.remove('district')
        elif no_of_group == 3:
            group_names.remove('ward')
        possibilities = permutations(group_names, len(group_names))
        # n!/(n-k)! , k = 4 => 24 permutations
        for group_keys in possibilities:
            # print(group_keys)
            key_value_pairs_2_4 = extract_group(address, group_keys)
            # print(key_value_pairs_2_4)
            is_found, guess_result = look_up(key_value_pairs_2_4, address_dict)
            # print(guess_result)
            if is_found:
                return key_value_pairs_2_4, guess_result
        print("Not found any matched")
        return None, None
    else:
        print("Can handle 1 to 4 groups!")
        return None, None


# from load_data import load_address_dict
# address_dict = load_address_dict()
# addresses = ["04 Doan van bo, phuong 10, quan 4, thanh pho ho chi minh", " số 4 Đoàn Văn Bơ, Phường 10 , QUẬn 4, Thành phố Hồ chí minh"]
# addresses = [".,.,Hoà thuận 2,Xã Trường Bình,Cần Giuộc,Tỉnh Long An"]
# group_keys = ('street', 'ward', 'district', 'city')

# for addr in addresses:
#     key_value_pairs = extract_group(addr,group_keys)
#     result, guess =  brute_force_search(address_dict, key_value_pairs, addr)
#     print(key_value_pairs)
#     print(result)
#     print(guess)

# kp = {"city":"Thành phố hồ chí minh","district":"Quan 4", "ward":"Phuong 10", "street": "some value"}
# look_up(kp,address_dict)



