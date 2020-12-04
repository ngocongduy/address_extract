from itertools import permutations
from fuzzywuzzy import process, fuzz
from .utils import *

from .load_data import load_address_dict, load_cities_data_normalized, load_address_dict_normalized, load_word_bag


class AddressExtractor():
    def __init__(self, cities_data_normalized=None, address_dict_normalized=None, nested_address_dict_normalized=None):
        if None in (cities_data_normalized, address_dict_normalized, nested_address_dict_normalized):
            self.cities_data_normalized = load_cities_data_normalized()
            self.address_dict_normalized = load_address_dict_normalized()
            self.nested_address_dict_normalized = load_address_dict()
        else:
            self.cities_data_normalized = cities_data_normalized
            self.address_dict_normalized = address_dict_normalized
            self.nested_address_dict_normalized = nested_address_dict_normalized
        word_bag = load_word_bag()
        self.word_bag = word_bag.get('word_bag')
        self.hot_words = word_bag.get('hot_words')
        self.ward_words = word_bag.get('ward_words')
        self.district_words = word_bag.get('district_words')
        self.province_words = word_bag.get('province_words')

    def assumption_brute_force_search(self, address: str, rate_province=85, rate_district=85, rate_ward=65,
                                      order=('street', 'ward', 'district', 'province'), key_value_pairs=None,
                                      extra_rate=65):
        group_names = ('wards', 'districts', 'provinces')
        fix_order = (('ward', rate_ward), ('district', rate_district), ('province', rate_province))
        order_keys = ('street', 'ward', 'district', 'province')
        if type(order) is not tuple:
            raise TypeError("Order should be a tuple with keys: {}".format(str(order_keys)))
        for ele in order:
            if ele not in order_keys:
                return None

        result = {}
        for k in order:
            result[k] = ''

        result['city_rate'] = 0
        result['all_rate'] = 0
        result['type'] = 'brute'
        if type(key_value_pairs) is not dict:
            key_value_pairs = extract_group(address, order)
        no_of_group = len(key_value_pairs.keys())

        if 1 <= no_of_group < 4:
            return self.assumption_search(address, key_value_pairs=key_value_pairs, extra_rate=extra_rate)
        elif no_of_group == 4:
            possibilities = permutations(order, len(order))
            # n!/(n-k)! , k = 4 => 24 permutations
            for order_pos in possibilities:
                # per_index+=1
                # Prepare material for each possibilities
                key_value_pairs_brute = extract_group(address, order_pos)
                iterate_dict = {}
                for i in range(len(group_names)):
                    iterate_dict[group_names[i]] = fix_order[i]

                district_node, wards = None, None
                for group in reversed(group_names):
                    group_key = iterate_dict.get(group)[0]
                    limit_rate = iterate_dict.get(group)[1]
                    search_term = key_value_pairs_brute[group_key]
                    if group == 'provinces':
                        cleaned_province_list = [clean(p.get('name'), is_city=True) for p in
                                                 self.nested_address_dict_normalized]
                        province_cleaned = clean(search_term, is_city=True)
                        if len(province_cleaned) > 0:
                            p_match, p_rate = process.extractOne(province_cleaned, cleaned_province_list)
                        else:
                            p_rate = 0
                        if p_rate <= limit_rate:
                            break
                        p_i = cleaned_province_list.index(p_match)
                        district_node = self.nested_address_dict_normalized[p_i].get('districts')
                        result['province'] = self.nested_address_dict_normalized[p_i].get('name')
                        result['city_rate'] = p_rate
                        continue
                    elif group == 'districts':
                        if district_node is None:
                            break
                        cleaned_district_list = [clean(d.get('name'), is_district=True) for d in district_node]
                        district_cleaned = clean(search_term, is_district=True)
                        if len(district_cleaned) > 0:
                            d_match, d_rate = process.extractOne(district_cleaned, cleaned_district_list)
                        else:
                            d_rate = 0
                        if d_rate <= limit_rate:
                            break
                        else:
                            d_i = cleaned_district_list.index(d_match)
                            wards = district_node[d_i].get('wards')
                            result['district'] = district_node[d_i].get('name')
                            continue
                    else:
                        if wards is None:
                            break
                        cleaned_ward_list = [clean(w.get('name'), is_ward=True) for w in wards]
                        ward_cleaned = clean(search_term, is_ward=True)
                        if len(ward_cleaned) > 0:
                            w_match, w_rate = process.extractOne(ward_cleaned, cleaned_ward_list)
                        else:
                            w_rate = 0
                        # Condition to finish
                        if w_rate >= rate_ward:
                            w_i = cleaned_ward_list.index(w_match)
                            ward = wards[w_i]
                            result['ward'] = ward.get('name')
                            result['street'] = key_value_pairs_brute['street']
                            result['all_rate'] = w_rate
                            result['count'] = 1000
                            return result

            # Reach this far means not found try another method
            return self.assumption_search(address, key_value_pairs=key_value_pairs, extra_rate=extra_rate)
        else:
            print("Can handle 1 to 4 groups!")
            return None

    def group_search(self, search_term_in_address: str, group_name: str, top_n=1, custom_list=None,
                     biased_group=''):
        allow_group_names = ('wards', 'districts', 'provinces')
        final_result = None
        if group_name not in allow_group_names:
            print('Group names allowed are: {}'.format(str(allow_group_names)))
            return final_result
        normalized_key = group_name + '_normalized'

        allow_biased_group = ('ward', 'district', 'province', '')
        if biased_group not in allow_biased_group:
            print('Group names allowed are: {}'.format(str(allow_biased_group)))
            return final_result

        # Cleaned custom_list before use
        if custom_list is None:
            # Use default
            cleaned_list = self.cities_data_normalized.get(normalized_key)
            list_to_look = self.cities_data_normalized.get(group_name)
        else:
            if group_name == 'provinces':
                cleaned_list = [clean(e, is_city=True) for e in custom_list]
            elif group_name == 'districts':
                cleaned_list = [clean(e, is_district=True) for e in custom_list]
            elif group_name == 'wards':
                cleaned_list = [clean(e, is_ward=True) for e in custom_list]
            else:
                cleaned_list = None
            list_to_look = custom_list
        if cleaned_list is None or list_to_look is None:
            print('Load data looks failed!')
            return final_result

        to_look_value = ''

        # Provide different cleaning ways
        if len(biased_group) > 0:
            to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
        else:
            if group_name == 'provinces':
                to_look_value = clean(search_term_in_address, is_city=True)
            elif group_name == 'districts':
                to_look_value = clean(search_term_in_address, is_district=True)
            elif group_name == 'wards':
                to_look_value = clean(search_term_in_address, is_ward=True)
        # print(to_look_value)
        # Compare and return top n matches
        if cleaned_list is not None and len(to_look_value) > 0:
            if 1 <= top_n <= 10:
                result_list = process.extractBests(query=to_look_value, choices=cleaned_list, limit=top_n)
                final_result = []
                try:
                    for e in result_list:
                        result = {'value': None, 'rate': 0}
                        value, rate = e[0], e[1]
                        if value is not None:
                            result['value'] = value
                            result['rate'] = rate
                            try:
                                index = cleaned_list.index(value)
                            except:
                                index = -1
                            if index >= 0:
                                if type(list_to_look[index]) is dict:
                                    for k in list_to_look[index].keys():
                                        result[k] = list_to_look[index].get(k)
                                else:
                                    result['original_value'] = list_to_look[index]
                            # print(result)
                        final_result.append(result)
                        # print(final_result)
                except Exception as e:
                    print(e)
                    final_result = None
            else:
                print('Only support top 1 - 10 element')
        return final_result

    def assumption_search(self, address: str, province_rate=75, extra_rate=65, key_value_pairs=None,
                          threshold_limit=2):
        # Assumpted a address ordered with orders:
        order = ('street', 'ward', 'district', 'province')

        result = {}
        for k in order:
            result[k] = ''

        province = ''
        # Consider if a dict of split address provided
        if type(key_value_pairs) is not dict:
            key_value_pairs = extract_group(address, order)
        else:
            province = key_value_pairs.get('province', '')

        # print(key_value_pairs.values())
        all_in_one = []
        for k in order:
            value = key_value_pairs.get(k)
            # In case key_value_pairs values are all the same
            if value is not None:
                try:
                    _ = all_in_one.index(value)
                except:
                    all_in_one.append(value)
        # print(all_in_one)
        no_of_group = len(all_in_one)

        if len(province) > 0:
            pass
        else:
            # assume that province is the last element
            for i in range(4):
                if no_of_group - 1 == i:
                    province = all_in_one[i]

        if no_of_group == 1:
            all_in_one_cleaned = clean_all_in_one(all_in_one[0])
            all_in_one_extra_cleaned = clean_all_extra(all_in_one[0])
        else:
            # Join by commas to work with cleaning functions
            all_in_one_cleaned = clean_all_in_one(','.join(all_in_one))
            all_in_one_extra_cleaned = clean_all_extra(','.join(all_in_one))

        # Redece the length if too long
        all_in_one_cleaned = self.__reduce_length_with_magic_number(all_in_one_cleaned)
        all_in_one_extra_cleaned = self.__reduce_length_with_magic_number(all_in_one_extra_cleaned)

        cleaned_list = self.address_dict_normalized.get('cleaned_list')
        cleaned_list_extra = self.address_dict_normalized.get('normalized_list')

        if cleaned_list is None or len(all_in_one_cleaned) < 1:
            return None

        province_node = self.group_search(search_term_in_address=province, group_name='provinces')
        ratio = 0
        start = -1
        end = -1
        if province_node is not None:
            province_node = province_node[0]
            ratio = province_node.get('rate')
            start = province_node.get('start_index')
            end = province_node.get('end_index')

        if ratio >= province_rate and start >= 0 and end >= 0:
            match, rate = process.extractOne(all_in_one_cleaned, cleaned_list[start:end + 1])
            # Add this check and look up will slow down but hope to increase accuracy
            if rate < extra_rate:
                other_match, rate = process.extractOne(all_in_one_extra_cleaned, cleaned_list_extra[start:end + 1])
                index = cleaned_list_extra[start:end + 1].index(other_match)
                index += start
                result['type'] = 'medium'
                result['count'] = end - start + 1
            else:
                index = cleaned_list[start:end + 1].index(match)
                index += start
                result['type'] = 'fast'
                result['count'] = end - start + 1
        else:
            # If province rate is low, try searching with word_bag
            threshold = -1
            if threshold_limit > 0:
                threshold = 0
                words = set(clean_and_split_into_words(address))
                # print(words)
                index_set = set()
                for word in words:
                    # print(word)
                    # print(self.hot_words)
                    index_list = self.word_bag.get(word)
                    if index_list is not None:
                        threshold += 1
                        index_set.update(index_list)

            if threshold >= threshold_limit:
                promise_list = [cleaned_list_extra[i] for i in index_set]
                match, rate = process.extractOne(all_in_one_extra_cleaned, promise_list)
                index = -1
                try:
                    index = int(match.split('_')[-1])
                except:
                    pass
                if index >= 0:
                    result['type'] = "trick"
                    result['count'] = len(promise_list)

            # if word_bag search is not used, check the length first and search in the whole list
            elif len(all_in_one_cleaned) > 3:
                match, rate = process.extractOne(all_in_one_cleaned, cleaned_list)
                index = cleaned_list.index(match)
                result['type'] = 'slow'
            else:
                for k in order:
                    result[k] = ""
                result['city_rate'] = 0.01
                result['all_rate'] = 0.01
                result['type'] = 'short_address'
                result['count'] = 100
        if rate >= extra_rate:
            original_list = self.address_dict_normalized.get('original_list')
            result['street'] = key_value_pairs['street']
            result['ward'] = original_list[index].get('ward_name')
            result['district'] = original_list[index].get('district_name')
            result['province'] = original_list[index].get('province_name')
            result['city_rate'] = ratio
            result['all_rate'] = rate
        else:
            for k in order:
                result[k] = ""
            result['city_rate'] = ratio
            result['all_rate'] = rate
            result['type'] = 'low_rate'
            result['count'] = 2000

        return result

    def __reduce_length_with_magic_number(self, number_as_string: str, magic_number=44):
        if len(number_as_string) > magic_number:
            return number_as_string[-magic_number:]
        return number_as_string

    def __split_check(self, string_value: str, bag_name='word_bag'):
        allow_words = []
        if len(string_value) > 0:
            if bag_name == 'word_bag':
                words = clean_and_split_into_words(string_value)
                allow_words = [w for w in words if (w in self.word_bag)]
            elif bag_name == 'ward_words':
                words = clean_and_split_into_words_for_word_bag(string_value, is_ward=True)
                allow_words = [w for w in words if (w in self.ward_words)]
            elif bag_name == 'district_words':
                words = clean_and_split_into_words_for_word_bag(string_value, is_district=True)
                allow_words = [w for w in words if (w in self.district_words)]
            elif bag_name == 'province_words':
                words = clean_and_split_into_words_for_word_bag(string_value, is_city=True)
                allow_words = [w for w in words if (w in self.province_words)]
        return allow_words

    def group_search_word_bag(self, search_term_in_address: str, group_name: str, top_n=1, custom_list=None,
                              biased_group=''):
        allow_group_names = ('wards', 'districts', 'provinces')
        final_result = None
        if group_name not in allow_group_names:
            print('Group names allowed are: {}'.format(str(allow_group_names)))
            return final_result
        normalized_key = group_name + '_normalized'

        allow_biased_group = ('ward', 'district', 'province', '')
        if biased_group not in allow_biased_group:
            print('Group names allowed are: {}'.format(str(allow_biased_group)))
            return final_result

        # Cleaned custom_list before use
        if custom_list is None:
            # Use default
            cleaned_list = self.cities_data_normalized.get(normalized_key)
            list_to_look = self.cities_data_normalized.get(group_name)
        else:
            if group_name == 'provinces':
                cleaned_list = [clean(e, is_city=True) for e in custom_list]
            elif group_name == 'districts':
                cleaned_list = [clean(e, is_district=True) for e in custom_list]
            elif group_name == 'wards':
                cleaned_list = [clean(e, is_ward=True) for e in custom_list]
            else:
                cleaned_list = None
            list_to_look = custom_list
        if cleaned_list is None or list_to_look is None:
            print('Load data looks failed!')
            return final_result
        allow_words = []
        if group_name == 'provinces':
            allow_words = self.__split_check(search_term_in_address, bag_name='province_words')
        elif group_name == 'districts':
            allow_words = self.__split_check(search_term_in_address, bag_name='district_words')
        elif group_name == 'wards':
            allow_words = self.__split_check(search_term_in_address, bag_name='ward_words')

        # print("Allow word {}".format(allow_words))

        if len(allow_words) > 0:
            to_look_value = ''.join(allow_words)
        else:
            return final_result
        # print("To look value {}".format(to_look_value))
        if cleaned_list is not None and len(to_look_value) > 0:
            if 1 <= top_n <= 10:
                result_list = process.extractBests(query=to_look_value, choices=cleaned_list, limit=top_n)
                final_result = []
                try:
                    for e in result_list:
                        result = {'value': None, 'rate': 0}
                        value, rate = e[0], e[1]
                        if value is not None:
                            result['value'] = value
                            result['rate'] = rate
                            try:
                                index = cleaned_list.index(value)
                            except:
                                index = -1
                            if index >= 0:
                                if type(list_to_look[index]) is dict:
                                    for k in list_to_look[index].keys():
                                        result[k] = list_to_look[index].get(k)
                                else:
                                    # For custom list
                                    result['original_value'] = list_to_look[index]
                            # print(result)
                        final_result.append(result)
                        # print(final_result)
                except Exception as e:
                    print(e)
                    final_result = None
            else:
                print('Only support top 1 - 10 element')
        return final_result

    def assumption_search_word_bag(self, address: str, province_rate=75, extra_rate=65, key_value_pairs=None,
                                   threshold_limit=2):
        # Assumpted a address ordered with orders:
        order = ('street', 'ward', 'district', 'province')

        result = {}
        for k in order:
            result[k] = ''

        province = ''
        # Consider if a dict of split address provided
        if type(key_value_pairs) is not dict:
            key_value_pairs = extract_group(address, order)
        else:
            province = key_value_pairs.get('province', '')

        # print(key_value_pairs.values())
        all_in_one = []
        words_for_threshold = set()
        for k in order:
            value = key_value_pairs.get(k)
            # In case key_value_pairs values are all the same
            if value is not None:
                try:
                    _ = all_in_one.index(value)
                except:
                    all_in_one.append(value)

        # Get the raw province first split and check
        no_of_group = len(all_in_one)
        if len(province) > 0:
            pass
        else:
            # assume that province is the last element
            for i in range(4):
                if no_of_group - 1 == i:
                    province = all_in_one[i]

        for i in range(len(all_in_one)):
            allow_words = self.__split_check(all_in_one[i])
            if len(allow_words) > 0:
                words_for_threshold.update(allow_words)
            all_in_one[i] = ''.join(allow_words)

        all_in_one_cleaned = ''.join(all_in_one)

        # Reduce the length if too long
        all_in_one_cleaned = self.__reduce_length_with_magic_number(all_in_one_cleaned)

        cleaned_list = self.address_dict_normalized.get('cleaned_list')
        cleaned_list_extra = self.address_dict_normalized.get('normalized_list')

        if cleaned_list is None or len(all_in_one_cleaned) < 1:
            return None

        province_node = self.group_search_word_bag(search_term_in_address=province, group_name='provinces')
        ratio = 0
        start = -1
        end = -1
        if province_node is not None:
            province_node = province_node[0]
            ratio = province_node.get('rate')
            start = province_node.get('start_index')
            end = province_node.get('end_index')

            # value = province_node.get('value')
            # print(value)
            # print(ratio)
            # print(province_node)
        if ratio >= province_rate and start >= 0 and end >= 0:
            match, rate = process.extractOne(all_in_one_cleaned, cleaned_list[start:end + 1])
            # Add this check and look up will slow down but hope to increase accuracy
            if rate < extra_rate:
                other_match, rate = process.extractOne(all_in_one_cleaned, cleaned_list_extra[start:end + 1])
                index = cleaned_list_extra[start:end + 1].index(other_match)
                index += start
                result['type'] = 'medium'
                result['count'] = end - start + 1
            else:
                index = cleaned_list[start:end + 1].index(match)
                index += start
                result['type'] = 'fast'
                result['count'] = end - start + 1
        else:
            # If province rate is low, try searching with word_bag
            threshold = -1
            if threshold_limit > 0:
                threshold = 0
                # print(words_for_threshold)
                index_set = set()
                for word in words_for_threshold:
                    index_list = self.word_bag.get(word)
                    if index_list is not None:
                        threshold += 1
                        index_set.update(index_list)

            if threshold >= threshold_limit:
                promise_list = [cleaned_list_extra[i] for i in index_set]
                match, rate = process.extractOne(all_in_one_cleaned, promise_list)
                index = -1
                try:
                    index = int(match.split('_')[-1])
                except:
                    pass
                if index >= 0:
                    result['type'] = "trick"
                    result['count'] = len(promise_list)

            # if word_bag search is not used, check the length first and search in the whole list
            elif len(all_in_one_cleaned) > 3:
                match, rate = process.extractOne(all_in_one_cleaned, cleaned_list)
                index = cleaned_list.index(match)
                result['type'] = 'slow'
            else:
                for k in order:
                    result[k] = ""
                result['city_rate'] = 0.01
                result['all_rate'] = 0.01
                result['type'] = 'short_address'
                result['count'] = 100
        if rate >= extra_rate:
            original_list = self.address_dict_normalized.get('original_list')
            result['street'] = key_value_pairs['street']
            result['ward'] = original_list[index].get('ward_name')
            result['district'] = original_list[index].get('district_name')
            result['province'] = original_list[index].get('province_name')
            result['city_rate'] = ratio
            result['all_rate'] = rate
        else:
            for k in order:
                result[k] = ""
            result['city_rate'] = ratio
            result['all_rate'] = rate
            result['type'] = 'low_rate'
            result['count'] = 2000

        return result

    def assumption_brute_force_search_word_bag(self, address: str, rate_province=85, rate_district=85, rate_ward=65,
                                               order=('street', 'ward', 'district', 'province'), key_value_pairs=None,
                                               extra_rate=65):
        group_names = ('wards', 'districts', 'provinces')
        fix_order = (('ward', rate_ward), ('district', rate_district), ('province', rate_province))
        order_keys = ('street', 'ward', 'district', 'province')
        if type(order) is not tuple:
            raise TypeError("Order should be a tuple with keys: {}".format(str(order_keys)))
        for ele in order:
            if ele not in order_keys:
                return None

        result = {}
        for k in order:
            result[k] = ''

        result['city_rate'] = 0
        result['all_rate'] = 0
        result['type'] = 'brute'
        if type(key_value_pairs) is not dict:
            key_value_pairs = extract_group(address, order)
        no_of_group = len(key_value_pairs.keys())

        if 1 <= no_of_group < 4:
            return self.assumption_search_word_bag(address, key_value_pairs=key_value_pairs, extra_rate=extra_rate)
        elif no_of_group == 4:
            possibilities = permutations(order, len(order))
            # n!/(n-k)! , k = 4 => 24 permutations
            for order_pos in possibilities:
                # per_index+=1
                # Prepare material for each possibilities
                key_value_pairs_brute = extract_group(address, order_pos)
                iterate_dict = {}
                for i in range(len(group_names)):
                    iterate_dict[group_names[i]] = fix_order[i]

                district_node, wards = None, None
                for group in reversed(group_names):
                    group_key = iterate_dict.get(group)[0]
                    limit_rate = iterate_dict.get(group)[1]
                    search_term = key_value_pairs_brute[group_key]
                    if group == 'provinces':
                        cleaned_province_list = [clean(p.get('name'), is_city=True) for p in
                                                 self.nested_address_dict_normalized]
                        # allowed_province_words = self.__split_check(search_term, bag_name='province_words')
                        # province_cleaned = ''.join(allowed_province_words)

                        province_cleaned = clean(search_term, is_city=True)

                        if len(province_cleaned) > 0:
                            p_match, p_rate = process.extractOne(province_cleaned, cleaned_province_list)
                        else:
                            p_rate = 0
                        if p_rate <= limit_rate:
                            break
                        p_i = cleaned_province_list.index(p_match)
                        district_node = self.nested_address_dict_normalized[p_i].get('districts')
                        result['province'] = self.nested_address_dict_normalized[p_i].get('name')
                        result['city_rate'] = p_rate
                        continue
                    elif group == 'districts':
                        if district_node is None:
                            break
                        cleaned_district_list = [clean(d.get('name'), is_district=True) for d in district_node]
                        district_cleaned = clean(search_term, is_district=True)

                        if len(district_cleaned) > 0:
                            d_match, d_rate = process.extractOne(district_cleaned, cleaned_district_list)
                        else:
                            d_rate = 0
                        if d_rate <= limit_rate:
                            break
                        else:
                            d_i = cleaned_district_list.index(d_match)
                            wards = district_node[d_i].get('wards')
                            result['district'] = district_node[d_i].get('name')
                            continue
                    else:
                        if wards is None:
                            break
                        cleaned_ward_list = [clean(w.get('name'), is_ward=True) for w in wards]
                        ward_cleaned = clean(search_term, is_ward=True)

                        if len(ward_cleaned) > 0:
                            w_match, w_rate = process.extractOne(ward_cleaned, cleaned_ward_list)
                        else:
                            w_rate = 0
                        # Condition to finish
                        if w_rate >= rate_ward:
                            w_i = cleaned_ward_list.index(w_match)
                            ward = wards[w_i]
                            result['ward'] = ward.get('name')
                            result['street'] = key_value_pairs_brute['street']
                            result['all_rate'] = w_rate
                            result['count'] = 1000
                            return result

            # Reach this far means not found try another method
            return self.assumption_search_word_bag(address, key_value_pairs=key_value_pairs, extra_rate=extra_rate)
        else:
            print("Can handle 1 to 4 groups!")
            return None


class AddressExtractorNew():
    def __init__(self, cities_data_normalized=None, address_dict_normalized=None, nested_address_dict_normalized=None):
        if None in (cities_data_normalized, address_dict_normalized, nested_address_dict_normalized):
            self.cities_data_normalized = load_cities_data_normalized()
            self.address_dict_normalized = load_address_dict_normalized()
            self.nested_address_dict_normalized = load_address_dict()
        else:
            self.cities_data_normalized = cities_data_normalized
            self.address_dict_normalized = address_dict_normalized
            self.nested_address_dict_normalized = nested_address_dict_normalized
        word_bag = load_word_bag()
        self.word_bag = word_bag.get('word_bag')
        self.hot_words = word_bag.get('hot_words')
        self.ward_words = word_bag.get('ward_words')
        self.district_words = word_bag.get('district_words')
        self.province_words = word_bag.get('province_words')

    def __find_and_rearrange_address_part(self, part_as_string: str, words_in_address):
        """
        Take the address and a term (ward/district/province name) try to find the term in the address
        :param part_as_string: ward/district/province name
        :param words_in_address: the address (list of word or a condensed string)
        :return: new address as string with the term moved to the end, a reduced address (removed the term), the term
        """

        if type(words_in_address) is list:
            address = ' '.join(words_in_address)
            address = clean_all_extra(address)
        elif type(words_in_address) is str:
            address = words_in_address
        else:
            print("Type of words_in_address should be list or str")
            return None
        index = -1
        reversed_address = address[::-1]
        reversed_part = part_as_string[::-1]
        try:
            # Find with reversed positions
            index = reversed_address.index(reversed_part)
        except:
            pass
        if index == 0:
            # Mean the province is at the end
            reduced_address = reversed_address.replace(reversed_part, '', 1)[::-1]
            return address, reduced_address, part_as_string
        elif index > 0:
            # Return a new rearranged string
            reduced_address = reversed_address.replace(reversed_part, '', 1)[::-1]
            new_address = reduced_address + part_as_string
            return new_address, reduced_address, part_as_string
        else:
            return None

    def __find_potential_address_part(self, address_words: list, address_part='provinces'):
        """
        This function will return the start/end index of the address_part in the flattened address dictionary
        :param address_words: words in address as a list
        :param address_part: directive param, expect: provinces/districts/wards
        :param address_as_string:
        :return:
        """
        is_contained = False
        potentials = []
        for w in address_words:
            part_words = []
            if address_part == 'provinces':
                part_words = self.province_words
            elif address_part == 'districts':
                part_words = self.district_words
            elif address_part == 'wards':
                part_words = self.ward_words
            for w_ in part_words:
                # Use fuzzy compare here to allow typo errors
                ratio = fuzz.partial_ratio(w, w_)
                if ratio >= 95:
                    is_contained = True
                    break
        if not is_contained:
            return None
        else:
            part_node = self.cities_data_normalized.get(address_part)
            if part_node is None:
                print("Can not load provinces data")
                return None
            else:
                for e in part_node:
                    string = None
                    if address_part == 'provinces':
                        string = e.get('province_words')
                    elif address_part == 'districts':
                        string = e.get('district_words')
                    elif address_part == 'wards':
                        string = e.get('ward_words')
                    if string is None:
                        return None
                    else:
                        string = ''.join(string)
                        new_addresses = self.__find_and_rearrange_address_part(string, address_words)
                        if new_addresses is None:
                            continue
                        else:
                            start_index = e.get('start_index')
                            end_index = e.get('end_index')
                            potentials.append((new_addresses, (start_index, end_index)))
        return potentials

    def __find_matched_result(self, address, to_look_list, match, ratio, original_list, start_index):
        """
        This helper function to find the data stored in flattened addresses
        :param address: original address
        :param to_look_list: the reduced flattened addresses
        :param match: the value to find
        :param ratio: matching ratio return by fuzzy compare of the match value
        :param original_list: the original flattened addresses
        :param start_index: give extra info to find the corresponding element in original_list
        :return:
        """
        index_short_list = -1
        try:
            index_short_list = to_look_list.index(match)
        except:
            pass
        result = {}
        if index_short_list >= 0:
            real_index = index_short_list + start_index
            result['all_rate'] = ratio
            result['province'] = original_list[real_index].get('province_name')
            result['district'] = original_list[real_index].get('district_name')
            result['ward'] = original_list[real_index].get('ward_name')
            result['street'] = address
            result['type'] = 'all_in_one'
        else:
            result['all_rate'] = ratio
            result['province'] = ""
            result['district'] = ""
            result['ward'] = ""
            result['street'] = address
            result['type'] = 'error'
        return result

    def word_dict_search_brute(self, address: str, all_rate=60):
        """
        This function use word_dict (a dict contains all possible words for wards/districts/provinces) approach.
        Search it the address for province words then jump to that province and continue with district and ward the same logic
        :param address: original address
        :param all_rate: matching confidence when approximation with condensed address (contain street ward district and province)
        :return: a dictionary-like result with matching rate, and mapped values for ward, district, province. The street part is populated by the original address
        """
        address_words = clean_and_split_into_words(address)

        # Try to determine whether the address contains province words
        # If exist, return a list of potential provinces with the addresses get modified
        potential_provinces = self.__find_potential_address_part(address_words)

        cleaned_list_extra = self.address_dict_normalized.get('normalized_list')
        original_list = self.address_dict_normalized.get('original_list')
        result_list = []

        fall_back_result = {'all_rate': 0, 'province': "", 'district': "", 'ward': "", 'street': address,
                            'type': 'error'}
        removed_parts = {}
        if potential_provinces is None:
            return fall_back_result
        # Each possible province, we will try to pick out warddistrictprovince and use it find locate the best approximation
        extra_search = []
        for i in range(len(potential_provinces)):
            removed_parts[i] = []

            potential_province = potential_provinces[i]

            # modified_address means the province words are moved to the end
            modified_address = potential_province[0][0]
            reduced_address = potential_province[0][1]
            start_index = potential_province[1][0]
            end_index = potential_province[1][1]

            to_look_list = cleaned_list_extra[start_index:end_index+1]
            matches = process.extractBests(modified_address,to_look_list, limit=1)

            removed_province = potential_province[0][2]

            # For each province matched, we jump in it's districts
            province_code = original_list[start_index].get('province_code')
            province_node = None
            for inner_i in range(len(self.nested_address_dict_normalized)):
                province_ = self.nested_address_dict_normalized[inner_i]
                if province_.get('code') == province_code:
                    province_node = province_
                    break

            ############
            districts_ = province_node.get('districts')
            # Each province then give some possible district and ward combinations
            for d in districts_:
                potential_combination = [removed_province]
                district_name = d.get('short_codename')
                check_number_district = district_name.split('_')
                if check_number_district[-1][0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
                    district_name = check_number_district[-1].lstrip('0')
                    # print(district_name)
                else:
                    district_name = district_name.replace('_', '')
                # reduced address is a string with province words removed
                district_result = self.__find_and_rearrange_address_part(district_name, reduced_address)
                if district_result is not None:
                    ward_node = d.get('wards')
                    reduced_address_2 = district_result[1]
                    removed_district = district_result[2]
                    # removed_parts[i].append(removed_district)
                    try:
                        potential_combination[1] = removed_district
                    except:
                        potential_combination.append(removed_district)

                    if ward_node is not None:
                        # Loop through each ward to find a ward
                        for w in ward_node:
                            ward_name = w.get('short_codename')
                            check_number_ward = ward_name.split('_')
                            if check_number_ward[-1][0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
                                ward_name = check_number_ward[-1].lstrip('0')
                                # print(ward_name)
                            else:
                                ward_name = ward_name.replace('_', '')
                            ward_result = self.__find_and_rearrange_address_part(ward_name, reduced_address_2)
                            if ward_result is not None:
                                # Happy case we found
                                street = ward_result[1]
                                removed_ward = ward_result[2]
                                # removed_parts[i].append(removed_ward)
                                # removed_parts[i].append(street)
                                try:
                                    potential_combination[2] = removed_ward
                                except:
                                    potential_combination.append(removed_ward)
                                try:
                                    potential_combination[3] = street
                                except:
                                    potential_combination.append(street)
                                # If we can find all perfect province, district and ward, we will pick this case
                                removed_parts[i].append(potential_combination.copy())

            # Make decision for each potential province
            # print("Potential province {}".format(i))
            if len(removed_parts[i]) > 0:
                # Prepare material for extra search
                for p in removed_parts[i]:
                    if len(p) == 4:
                        pro_dis_ward = p[0:-1]
                        perfect_address = ''.join(reversed(pro_dis_ward))
                        material = {}
                        material['start_index'] = start_index
                        material['end_index'] = end_index
                        material['perfect_address'] = perfect_address
                        material['modified_address'] = modified_address
                        # print(material)
                        extra_search.append(material)

            # Still want to use pick-first approach if potential province idea fails
            low_rate = 0
            chosen_match = None
            if len(matches) > 0:
                if matches[0][1] >= all_rate:
                    chosen_match = matches[0]
                else:
                    low_rate = matches[0][1]
            if chosen_match is not None:
                match = chosen_match[0]
                ratio = chosen_match[1]
                result = self.__find_matched_result(address, to_look_list, match, ratio, original_list, start_index)
                result_list.append(result)
            else:
                # If low rate detected
                if low_rate > 0:
                    low_rate_result = fall_back_result.copy()
                    low_rate_result['all_rate'] = low_rate
                    low_rate_result['type'] = "low_rate"

                    result_list.append(low_rate_result)
                else:
                    result_list.append(fall_back_result)

        max_index = -1
        max_rate = 0
        # Do extra search and return a result with potential province approach
        if len(extra_search) > 0:
            hopeful_list = []
            hopeful_perfect_address = []
            for combo in extra_search:
                start = combo.get('start_index')
                end = combo.get('end_index')
                perfect_address = combo.get('perfect_address')
                to_look_list = cleaned_list_extra[start:end + 1]

                # Still fuzzy due to elements of to_look_list contains id number at the end
                top_matches = process.extractBests(perfect_address, to_look_list, limit=20)

                # Make a new list without id number and find the best match
                top_matches_list = [ele[0].split('_')[0] for ele in top_matches]
                final, final_ratio = process.extractOne(perfect_address, top_matches_list)

                # Refer back to top_matches
                fake_index = top_matches_list.index(final)
                hopeful_match = top_matches[fake_index][0]
                hopeful_ratio = top_matches[fake_index][1]

                hopeful_result = self.__find_matched_result(address, to_look_list, hopeful_match, hopeful_ratio,
                                                            original_list, start)
                hopeful_list.append(hopeful_result)

                modified_address = combo.get('modified_address')
                hopeful_perfect_address.append((perfect_address, modified_address))
            # print(hopeful_list)
            if len(hopeful_list) > 0:
                hopeful_max_rate = 0
                hopeful_max_index = -1

                # Compare the modified address with the perfect address and pick one with highest rate
                # Modified address only has province part move to the end
                for i in range(len(hopeful_perfect_address)):
                    pa, ma = hopeful_perfect_address[i]
                    checked_ratio = fuzz.partial_ratio(pa, ma)
                    if checked_ratio > hopeful_max_rate:
                        hopeful_max_rate = checked_ratio
                        hopeful_max_index = i
                if hopeful_max_index >= 0:
                    return hopeful_list[hopeful_max_index]
        else:
            for k in range(len(result_list)):
                all_rate_ = result_list[k].get('all_rate')
                if all_rate_ > max_rate:
                    max_rate = all_rate_
                    max_index = k
        if max_index >= 0:
            return result_list[max_index]
        else:
            return fall_back_result

    def assumption_brute_force_search_word_dict(self, address: str, rate_province=85, rate_district=85, rate_ward=65,
                                                order=('street', 'ward', 'district', 'province'), key_value_pairs=None,
                                                all_rate=65):
        """
        This function will split the address string into maximum 4 parts, and iterate through all possible permutations constructed by 4 parts of order
        If 4 parts splited by commas, it will try to locate province first, then district, then ward.
        If 1-3 parts splited, it will return the result of word_dict_search_brute
        :param address: original address as string
        :param rate_province: province confidence rate for acceptance
        :param rate_district: district confidence rate for acceptance
        :param rate_ward: ward confidence rate for acceptance
        :param order: prefered order keys to make all possible permutations
        :param key_value_pairs: pre splited address, if pass, it will skip the split step
        :param all_rate: the confidence rate for function word_dict_search_brute
        :return: a dictionary-like result with matching rate, mapped part values (if found)
        """
        group_names = ('wards', 'districts', 'provinces')
        fix_order = (('ward', rate_ward), ('district', rate_district), ('province', rate_province))
        order_keys = ('street', 'ward', 'district', 'province')
        if type(order) is not tuple:
            raise TypeError("Order should be a tuple with keys: {}".format(str(order_keys)))
        for ele in order:
            if ele not in order_keys:
                return None

        result = {}
        for k in order:
            result[k] = ''
        result['all_rate'] = 0
        result['type'] = 'brute'
        if type(key_value_pairs) is not dict:
            key_value_pairs = extract_group(address, order)
        no_of_group = len(key_value_pairs.keys())

        if 1 <= no_of_group < 4:
            return self.word_dict_search_brute(address, all_rate=all_rate)
        elif no_of_group == 4:
            possibilities = permutations(order, len(order))
            # n!/(n-k)! , k = 4 => 24 permutations
            for order_pos in possibilities:
                all_rate_ = 0
                # per_index+=1
                # Prepare material for each possibilities
                key_value_pairs_brute = extract_group(address, order_pos)
                iterate_dict = {}
                for i in range(len(group_names)):
                    iterate_dict[group_names[i]] = fix_order[i]

                district_node, wards = None, None
                for group in reversed(group_names):
                    group_key = iterate_dict.get(group)[0]
                    limit_rate = iterate_dict.get(group)[1]
                    search_term = key_value_pairs_brute[group_key]
                    if group == 'provinces':
                        if len(search_term) <= 3:
                            break
                        cleaned_province_list = [clean(p.get('name'), is_city=True) for p in
                                                 self.nested_address_dict_normalized]
                        province_cleaned = clean(search_term, is_city=True)

                        if len(province_cleaned) > 0:
                            p_match, p_rate = process.extractOne(province_cleaned, cleaned_province_list)
                        else:
                            p_rate = 0
                        if p_rate <= limit_rate:
                            break
                        p_i = cleaned_province_list.index(p_match)
                        district_node = self.nested_address_dict_normalized[p_i].get('districts')
                        result['province'] = self.nested_address_dict_normalized[p_i].get('name')
                        all_rate_ += p_rate
                        continue
                    elif group == 'districts':
                        if district_node is None:
                            break
                        cleaned_district_list = [clean(d.get('name'), is_district=True) for d in district_node]
                        district_cleaned = clean(search_term, is_district=True)

                        if len(district_cleaned) > 0:
                            d_match, d_rate = process.extractOne(district_cleaned, cleaned_district_list)
                        else:
                            d_rate = 0
                        if d_rate <= limit_rate:
                            break
                        else:
                            d_i = cleaned_district_list.index(d_match)
                            wards = district_node[d_i].get('wards')
                            result['district'] = district_node[d_i].get('name')
                            all_rate_ += d_rate
                            continue
                    else:
                        if wards is None:
                            break
                        cleaned_ward_list = [clean(w.get('name'), is_ward=True) for w in wards]
                        ward_cleaned = clean(search_term, is_ward=True)

                        if len(ward_cleaned) > 0:
                            w_match, w_rate = process.extractOne(ward_cleaned, cleaned_ward_list)
                        else:
                            w_rate = 0
                        # Condition to finish
                        if w_rate >= rate_ward:
                            w_i = cleaned_ward_list.index(w_match)
                            ward = wards[w_i]
                            result['ward'] = ward.get('name')
                            result['street'] = key_value_pairs_brute['street']
                            all_rate_ += w_rate
                            result['all_rate'] = all_rate_ / 3
                            return result

            # Reach this far means not found try another method
            return self.word_dict_search_brute(address, all_rate=all_rate)
        else:
            print("Can handle 1 to 4 groups!")
            return None
