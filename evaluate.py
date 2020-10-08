# Helper functions
def extract_dict(value_set, dictionary, result=None):
    """
    This function will return a new dict with contains key-value pair in original dict
    :param value_set: set of keys to search in original dict
    :param dictionary: original dict to pick value out
    :param result: a dict to return - default is None
    :return: a dict contains key-value where keys in value_set
    """
    if type(result) is not dict:
        # First made a dict contains all keys
        none_list = []
        for _ in range(len(value_set)):
            none_list.append(None)
        result = dict(zip(value_set, none_list))
    if type(value_set) is not set:
        return None
    if type(dictionary) is not dict:
        return None
    else:
        # print("___________________________")
        # print(dictionary)
        for k, v in dictionary.items():
            if k.lower() in map(lambda e: e.lower(), value_set):
                key = k
                for ik in value_set:
                    if ik.lower() == k.lower():
                        key = ik
                result[key] = v
                # print("Value " + str(v))
                # continue
            if type(v) is dict:
                # print("v is dict")
                # print(v)
                extract_dict(value_set, v, result)
        # Let the loop finish
        return result


def make_cols_dict_by_rows(rows, cols_name):
    result_dic = dict()
    no_of_cols = len(cols_name)
    cols = list(zip(*rows))
    for i in range(no_of_cols):
        result_dic[cols_name[i]] = list(cols[i])
    return result_dic


import ast
import json

def extract_data_from_col(dict_data, extract_keys, col_name=None):
    data = None
    result_dic = dict()
    for k in extract_keys:
        result_dic[k] = []
    try:
        data = dict_data.get(col_name)
    except:
        print("No data for this column!")
        return None
    if data is not None:
        for r in data:
            d_as_dic = None
            try:
                d_as_dic = ast.literal_eval(r)
            except:
                try:
                    d_as_dic = json.loads(r)
                except:
                    for k in result_dic.keys():
                        result_dic[k].append('not_json_data')
                    pass
            if type(d_as_dic) is dict:
                cell_as_dic = extract_dict(dictionary=d_as_dic, value_set=extract_keys)
                # Append corresponding values for new keys
                for k in extract_keys:
                    value = cell_as_dic[k]
                    if value is not None:
                        result_dic[k].append(value)
                    else:
                        result_dic[k].append('')
    return result_dic

# To work with excel
import os
import pandas as pd
from datetime import datetime

def read_data_excel(file_name, path_to_file=None, is_tranpose=False, key_as_index=None, is_index=False):
    cd = path_to_file
    if cd is None:
        cd = os.getcwd()
    file_path = os.path.join(cd, file_name)
    if os.path.exists(file_path):
        try:
            if is_index:
                df = pd.read_excel(file_path, index_col=0, dtype=str)
            else:
                df = pd.read_excel(file_path, dtype=str)  # , index_col=0)
            # print(df.dtypes)
            # print(df.describe())
            dic_data = None
            if is_tranpose:
                if key_as_index is not None:
                    indexes = df.loc[:, key_as_index]
                    print(indexes)
                    if len(indexes) > 0:
                        df.index = indexes
                df = df.transpose()
                # df['Indexes'] = df.index
                # df.reset_index(drop=True, inplace=True)
                dic_data = df.to_dict()
            else:
                dic_data = df.to_dict()
            return dic_data
        except Exception as e:
            print(e)
    return None

def save_data_excel(data_as_dict, file_name, path_to_file=None):
    cd = path_to_file
    if cd is None:
        cd = os.getcwd()
    file_path = os.path.join(cd, file_name)
    df = pd.DataFrame(data_as_dict)  # , index_col=0)
    try:
        if os.path.exists(file_path):
            today = datetime.now()
            day_as_string = str(int(today.timestamp()))
            cd = os.getcwd()
            file_name = day_as_string + '.xlsx'
            file_path = os.path.join(cd, file_name)
        df.to_excel(file_path)
    except Exception as e:
        print(e)
        return False
    return True

def save_data_excel_multi_sheet(tables, file_name, path_to_file):
    if path_to_file is None:
        path_to_file = os.getcwd()
    else:
        path_to_file = path_to_file
    try:
        if not os.path.exists(path_to_file):
            return False
            # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(os.path.join(path_to_file, file_name), engine='xlsxwriter')
        for name, data in tables.items():
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=name)
        writer.save()
    except Exception as e:
        print(e)
        return False
    return True


path_to_file = os.path.join(os.getcwd(), 'address')
save_file_name = 'addresses_preprocessed_.xlsx'
save_file_name = 'test.xlsx'
# query_and_save(path_to_file,save_file_name)

import time

t0 = time.time()

from load_data import load_address_dict
from address_extract import extract_group, brute_force_search

address_dict = load_address_dict()

data_as_dict = read_data_excel(save_file_name, path_to_file, is_index=True)
print(data_as_dict)
to_proccess_addresses = data_as_dict.get('address')

group_keys = ('street', 'ward', 'district', 'city')
col_names = ('no', 'address') + group_keys
print(col_names)
to_save_dict = {}
to_save_guess = {}
for e in col_names:
    to_save_dict[e] = []
    to_save_guess[e] = []
count = 0
for no, addr in to_proccess_addresses.items():
    print("Processing record {}".format(count + 1))
    key_value_pairs = extract_group(addr, group_keys)
    # print(key_value_pairs)
    result, guess_result = brute_force_search(address_dict, key_value_pairs, addr)
    to_save_dict['no'].append(no)
    to_save_dict['address'].append(addr)
    for k in group_keys:
        if type(result) is dict:
            value = result.get(k)
            if value is not None:
                to_save_dict[k].append(value)
            else:
                to_save_dict[k].append("no info")
        else:
            to_save_dict[k].append("error")

    to_save_guess['no'].append(no)
    to_save_guess['address'].append(addr)
    for k in group_keys:
        if type(guess_result) is dict:
            value = guess_result.get(k)
            if value is not None:
                to_save_guess[k].append(value)
            else:
                to_save_guess[k].append("no info")
        else:
            to_save_guess[k].append("error")

    count += 1
    if count == 3000:
        break

processed_file_name = 'test_result.xlsx'
if save_data_excel(to_save_dict, processed_file_name, path_to_file):
    print("Beautiful!")
processed_file_name_guess = 'test_result_guess.xlsx'
if save_data_excel(to_save_guess, processed_file_name_guess, path_to_file):
    print("Beautiful!")
t1 = time.time()
elapsed = t1 - t0
print("Total time elapsed: {}".format(elapsed))


path_to_file = os.path.join(os.getcwd(), 'address')
save_file_name = 'test.xlsx'

# from load_data import load_address_dict
# from address_extract import extract_group, brute_force_search
# address_dict = load_address_dict()

data_as_dict = read_data_excel(save_file_name,path_to_file, is_index=True)
to_proccess_addresses = data_as_dict.get('address')

group_keys = ('street', 'ward', 'district', 'city')
col_names = ('no','address') + group_keys
print(col_names)
to_save_dict = {}
to_save_guess = {}
for e in col_names:
    to_save_dict[e] = []
    to_save_guess[e] = []
count = 0
for no, addr in to_proccess_addresses.items():
    print("Processing record {}".format(count + 1))
    key_value_pairs = extract_group(addr, group_keys)
    # print(key_value_pairs)
    result, guess_result = brute_force_search(address_dict, key_value_pairs, addr)
    to_save_dict['no'].append(no)
    to_save_dict['address'].append(addr)
    for k in group_keys:
        if type(result) is dict:
            value = result.get(k)
            if value is not None:
                to_save_dict[k].append(value)
            else:
                to_save_dict[k].append("no info")
        else:
            to_save_dict[k].append("error")

    to_save_guess['no'].append(no)
    to_save_guess['address'].append(addr)
    for k in group_keys:
        if type(guess_result) is dict:
            value = guess_result.get(k)
            if value is not None:
                to_save_guess[k].append(value)
            else:
                to_save_guess[k].append("no info")
        else:
            to_save_guess[k].append("error")

    count += 1
    if count == 3000:
        break
