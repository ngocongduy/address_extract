from vietnam_provinces import NESTED_DIVISIONS_JSON_PATH, FLAT_DIVISIONS_JSON_PATH
import json

def load_address_dict():
    print(NESTED_DIVISIONS_JSON_PATH)
    with open(NESTED_DIVISIONS_JSON_PATH, encoding="utf8") as f:
        provinces = json.load(f)
    return provinces
# sum = 0
# for prod_or_city in provinces:
#     print(prod_or_city)
#     for district_list in prod_or_city.get('districts'):
#         # print(district_list)
#         for ward_list in district_list.get('wards'):
#             sum+= len(ward_list)
#
# print(sum)

# with open(FLAT_DIVISIONS_JSON_PATH, encoding="utf8") as f:
#     combinations = json.load(f)
# sum = 0
# for e in combinations:
#     print(e)
#     sum+=1
#
# print(sum)