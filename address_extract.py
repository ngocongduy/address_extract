from itertools import permutations
from fuzzywuzzy import process, fuzz
from .utils import *

from .load_data import load_address_dict, load_cities_data_normalized, load_address_dict_normalized, load_word_bag, \
    load_word_dict


class AddressExtractor():
    def __init__(self, cities_data_normalized=None, address_dict_normalized=None, nested_address_dict_normalized=None):
        """
        Initilized backed data used for the works, if using your own, please have a look on data files and code
        :param cities_data_normalized: json file containing lists of provinces, districts and wards used as indexer for address_dict_normalized
        :param address_dict_normalized: json file containing flat records. Each is a combinations of possible (province, district, ward)
        :param nested_address_dict_normalized: json containing tree-liked data: first level is province -> district -> ward
        """
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
        word_dict = load_word_dict()
        self.bag_of_words = word_dict.get('bag_of_words')

    def assumption_brute_force_search(self, address: str, rate_province=85, rate_district=85, rate_ward=65,
                                      order=('street', 'ward', 'district', 'province'), key_value_pairs=None,
                                      extra_rate=65):
        """
        Given a full address as string, try to return 4 part: street, ward, district, province/city
        Givan a list of dictionary, each dictionary is a province/city and all of its districts and wards
        First try to find the proinvce -> district -> ward
        If failure in seperate address in to 4 parts, perform 'assumption_search'
        Try to iterate all possible order of ('street', 'ward', 'district', 'province'), prefered the shown order
        After iterating and still fail (cannot satisfy matching rates for each part), try 'assumption_search'
        :param extra_rate:
        :param key_value_pairs:
        :param address: address as string, expected parts seperated by a comma ','
        :param rate_province: limit to continue district search
        :param rate_district: limit to continue ward search
        :param rate_ward: limit to return
        :param order: expected and allowed keywords to do extraction
        :return: a object containing 4 parts, 'street' is the 1 part of input address, 3 other parts are standard values from our dictionary
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
        """
        Given lists containing all provinces/cities, all districts, all wards
        Find n best matched element in those list, searching is directed by group_name
        :param biased_group:
        :param reduce_district:
        :param search_term_in_address: expected a part of address such as ward/ district/ province/city
        :param group_name: expected one of  ('wards', 'districts', 'provinces')
        :param top_n: n best matched elements, 1 <= n <= 10
        :param custom_list: a list to look up instead of default list
        :return: a list containing n best matched elements, each one is a object in
        """
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

        # Clean to_look_value before comparing
        # to_look_value = ''
        # if group_name == 'provinces':
        #     # Provide different cleaning ways for provinces
        #     if biased_group == 'province':
        #         to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
        #     elif biased_group == 'district':
        #         to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
        #     elif biased_group == 'ward':
        #         to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
        #     else:
        #         to_look_value = clean(search_term_in_address, is_city=True)
        #
        # elif group_name == 'districts':
        #     to_look_value = clean(search_term_in_address, is_district=True)
        # elif group_name == 'wards':
        #     to_look_value = clean(search_term_in_address, is_ward=True)

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

        # Try 4 times with 4 cleaning ways and pick the best one
        # Only do it for province due to the searching list is short
        # This approach give bad result due to the randomness feature of input data
        # max_ratio = 0
        # max_index = -1
        # potential_provinces = []
        # # print(province)
        # for i in range(3):
        #     group = order[1:][i]
        #     province_node = self.group_search(search_term_in_address=province, group_name='provinces',biased_group=group)
        #     potential_provinces.append(province_node)
        #     if province_node is not None:
        #         province_node = province_node[0]
        #         ratio = province_node.get('rate')
        #         if ratio > max_ratio:
        #             max_index = i
        #             max_ratio = ratio
        #     else:
        #         return None
        # if max_index >= 0:
        #     province_node = potential_provinces[max_index][0]
        # else:
        #     return None

        province_node = self.group_search(search_term_in_address=province, group_name='provinces')
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
            match, rate = process.extractOne(all_in_one_cleaned, cleaned_list[start:end+1])
            # Add this check and look up will slow down but hope to increase accuracy
            if rate < extra_rate:
                other_match, rate = process.extractOne(all_in_one_extra_cleaned, cleaned_list_extra[start:end+1])
                index = cleaned_list_extra[start:end+1].index(other_match)
                index += start
                result['type'] = 'medium'
                result['count'] = end - start + 1
            else:
                index = cleaned_list[start:end+1].index(match)
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
        """
        This function expect raw search term
        :param search_term_in_address:
        :param group_name:
        :param top_n:
        :param custom_list:
        :param biased_group:
        :return:
        """
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
            match, rate = process.extractOne(all_in_one_cleaned, cleaned_list[start:end+1])
            # Add this check and look up will slow down but hope to increase accuracy
            if rate < extra_rate:
                other_match, rate = process.extractOne(all_in_one_cleaned, cleaned_list_extra[start:end+1])
                index = cleaned_list_extra[start:end+1].index(other_match)
                index += start
                result['type'] = 'medium'
                result['count'] = end - start + 1
            else:
                index = cleaned_list[start:end+1].index(match)
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
                        # allowed_district_words = self.__split_check(search_term, bag_name='district_words')
                        # district_cleaned = ''.join(allowed_district_words)

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
                        # allowed_ward_words = self.__split_check(search_term, bag_name='ward_words')
                        # ward_cleaned = ''.join(allowed_ward_words)

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

    ##### New method with bag of words approach
    def __count_word_in_address(self, allow_words: list):
        words = set(allow_words)
        result = {}
        for w in words:
            c = 0
            for w_ in allow_words:
                if w_ == w:
                    c += 1
            result[w] = c
        return result

    def __compare_count_dict(self, allow_words: list, count_dict: dict):
        word_count = self.__count_word_in_address(allow_words)
        words = list(count_dict.keys())
        no_of_words = len(words)
        avg = 0
        for i in range(no_of_words):
            w = words[i]
            c1 = word_count.get(w, 0)
            c2 = count_dict.get(w)
            if c1 >= c2:
                avg += 1
        if (avg + 1) >= no_of_words:
            return True

    def __rebuild_address_by_allowed_words(self, allow_words: list, province_words: list):
        if province_words is not None:
            no_of_province_words = len(province_words)
            check_list = [0 for _ in allow_words]
            # print(allow_words)
            # print(province_words)
            # print(check_list)
            for i in range(len(allow_words)):
                check_word = allow_words[i]
                if check_word in province_words:
                    check_list[i] = 1
            indexes = [index for index, value in enumerate(check_list) if value == 1]
            # print(indexes)
            found = None
            for i in range(len(indexes)):
                try:
                    index = indexes[i]
                    check = check_list[index:index + no_of_province_words]
                    # print(check_list)
                    # print(check)
                    is_sequence = True
                    # print(check[1:])
                    for e in check[1:]:
                        if e != 1:
                            is_sequence = False
                            break
                    # print(is_sequence)
                    if is_sequence:
                        found = index
                        # print(found)
                        break
                except:
                    pass
            if found is not None:
                temp_list = allow_words.copy()
                # print(temp_list)
                for i in range(found, no_of_province_words):
                    # print(i)
                    temp_list[i] = ''
                temp_list.extend(province_words)
                # print(temp_list)
                return ''.join(temp_list)

    def word_dict_search(self, address: str, all_rate=75):
        allow_words = self.__split_check(address)
        index_set = set()
        pronvince_list = []
        for word in allow_words:
            word_info = self.bag_of_words.get(word)
            if word_info is not None:
                index_list = []

                for info in word_info:
                    exist_index = info.get('exist_index')
                    count_dict = info.get('count_dict')
                    province_words = info.get('province_words')
                    if not (None in (exist_index, count_dict)):
                        if self.__compare_count_dict(allow_words, count_dict):
                            index_list.append(exist_index)
                            pronvince_list.append(province_words)
                index_set.update(index_list)
        # rebuild
        check_list = []
        rebuilt_addresses = []
        for province_words in pronvince_list:
            province = ''.join(province_words)
            try:
                _ = check_list.index(province)
            except:
                rebuilt_address = self.__rebuild_address_by_allowed_words(allow_words, province_words)
                if rebuilt_address is not None:
                    rebuilt_addresses.append(rebuilt_address)
                check_list.append(province)

        if len(index_set) > 0:
            print(len(index_set))
            # result_list = []
            # original_list = self.address_dict_normalized.get('original_list')
            # for index in index_set:
            #     result = {}
            #     result['street'] = address
            #     result['ward'] = original_list[index].get('ward_name')
            #     result['district'] = original_list[index].get('district_name')
            #     result['province'] = original_list[index].get('province_name')
            #     result_list.append(result)
            # return result_list

            result = self.__assumption_search_word_dict(address, allow_words, list(index_set), rebuilt_addresses,
                                                        all_rate=all_rate)
            return result
        else:
            print("Not found any matches!")
            return None

    def __assumption_search_word_dict(self, address: str, allowed_words: list, prefered_indexes: list,
                                      rebuilt_addresses: list, all_rate=75):
        # Assumpted a address ordered with orders:
        order = ('street', 'ward', 'district', 'province')

        result = {}
        for k in order:
            result[k] = ''
        """
        key_value_pairs = extract_group(address, order)
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

        if no_of_group == 1:
            all_in_one_cleaned = clean_all_in_one(all_in_one[0])
            all_in_one_extra_cleaned = clean_all_extra(all_in_one[0])
        else:
            # Join by commas to work with cleaning functions
            all_in_one_cleaned = clean_all_in_one(','.join(all_in_one))
            all_in_one_extra_cleaned = clean_all_extra(','.join(all_in_one))

        all_in_one_cleaned = self.__reduce_length_with_magic_number(all_in_one_cleaned)
        all_in_one_extra_cleaned = self.__reduce_length_with_magic_number(all_in_one_extra_cleaned)



        cleaned_list = self.address_dict_normalized.get('cleaned_list')
        cleaned_list = [cleaned_list[i] for i in prefered_indexes]
        """
        joined_allowed_words = ''.join(allowed_words)
        joined_allowed_words = self.__reduce_length_with_magic_number(joined_allowed_words)

        cleaned_list_extra = self.address_dict_normalized.get('normalized_list')
        cleaned_list_extra = [cleaned_list_extra[i] for i in prefered_indexes]
        # print(all_in_one_cleaned)
        # print(all_in_one_extra_cleaned)
        # print(joined_allowed_words)

        # terms = [all_in_one_cleaned,all_in_one_extra_cleaned,joined_allowed_words]
        terms = [joined_allowed_words]
        # lists = [cleaned_list,cleaned_list_extra,cleaned_list_extra]
        lists = [cleaned_list_extra]
        # print(prefered_indexes)
        # print(rebuilt_addresses)

        for rebuilt_address in rebuilt_addresses:
            if len(rebuilt_address) > 0:
                terms.append(rebuilt_address)
                lists.append(cleaned_list_extra)
        max_rate = 0
        max_index = -1
        for term, search_list in zip(terms, lists):
            # print(term)
            # print(search_list)
            match, rate = process.extractOne(term, search_list)
            index = search_list.index(match)
            if rate > max_rate:
                max_rate = rate
                max_index = index

        if max_rate >= all_rate and max_index >= 0:
            original_list = self.address_dict_normalized.get('original_list')
            result['street'] = address
            real_index = prefered_indexes[max_index]
            result['ward'] = original_list[real_index].get('ward_name')
            result['district'] = original_list[real_index].get('district_name')
            result['province'] = original_list[real_index].get('province_name')
            result['city_rate'] = 0.01
            result['all_rate'] = max_rate
            result['type'] = 'word_bag'
            result['count'] = len(prefered_indexes)
        else:
            for k in order:
                result[k] = ""
            result['city_rate'] = 0.01
            result['all_rate'] = max_rate
            result['type'] = 'low_rate'
            result['count'] = 2000

        return result


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
        word_dict = load_word_dict()
        self.bag_of_words = word_dict.get('bag_of_words')

    def __find_and_rearrange_address_part(self, part_as_string: str, words_in_address):
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
        reversed_province = part_as_string[::-1]
        try:
            # Find with reversed positions
            index = reversed_address.index(reversed_province)
        except:
            pass
        if index == 0:
            # Mean the province is at the end
            reduced_address = reversed_address.replace(reversed_province, '', 1)[::-1]
            return address, reduced_address, part_as_string
        elif index > 0:
            # Return a new rearranged string
            reduced_address = reversed_address.replace(reversed_province, '', 1)[::-1]
            new_address = reduced_address + part_as_string
            return new_address, reduced_address, part_as_string
        else:
            return None

    def __find_potential_address_part(self, address_words: list, address_part='provinces', address_as_string=''):
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
            # if w in part_words:
            #     is_contained = True
            #     break
            for w_ in part_words:
                ratio = fuzz.partial_ratio(w,w_)
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
                        if len(address_as_string) > 0:
                            new_addresses = self.__find_and_rearrange_address_part(string, address_as_string)
                        else:
                            new_addresses = self.__find_and_rearrange_address_part(string, address_words)
                        if new_addresses is None:
                            continue
                        else:
                            start_index = e.get('start_index')
                            end_index = e.get('end_index')
                            potentials.append((new_addresses, (start_index, end_index)))
        return potentials

    def __find_matched_result(self, address ,to_look_list, match, ratio, original_list, start_index):
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

    def word_dict_search(self, address: str, all_rate=60):
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
        # print(potential_provinces)
        extra_search = []
        for i in range(len(potential_provinces)):
            #
            removed_parts[i] = []

            # For each potential province, find some matches
            potential_province = potential_provinces[i]
            cleaned_address = potential_province[0][0]
            reduced_address = potential_province[0][1]
            start_index = potential_province[1][0]
            end_index = potential_province[1][1]
            to_look_list = cleaned_list_extra[start_index:end_index + 1]
            matches = process.extractBests(cleaned_address, to_look_list, limit=10)
            # print(start_index)
            # print(end_index)
            # print(matches)
            chosen_match = None

            removed_province = potential_province[0][2]
            removed_parts[i].append(removed_province)

            for j in range(len(matches)):
                # For each province matched, we jump in it's districts
                matching = matches[j]
                match_value = matching[0]
                match_rate = matching[1]
                temp_index = to_look_list.index(match_value)
                used_index = temp_index + start_index
                # Use the province code to align data between 02 data files: nested and flattened
                province_code = original_list[used_index].get('province_code')
                # print(province_code)
                province_node = None
                for inner_i in range(len(self.nested_address_dict_normalized)):
                    province_ = self.nested_address_dict_normalized[inner_i]
                    # print(province_)
                    if province_.get('code') == province_code:
                        province_node = province_
                        break

                districts_ = province_node.get('districts')
                ward_node = None
                # For each district in the province node
                for d in districts_:
                    district_name = d.get('short_codename')
                    check_number_district = district_name.split('_')
                    if check_number_district[-1][0] in ('0','1','2','3','4','5','6','7','8','9'):
                        district_name = check_number_district[-1].lstrip('0')
                        # print(district_name)
                    else:
                        district_name = district_name.replace('_', '')
                    # reduced address is a string with provide words removed
                    district_result = self.__find_and_rearrange_address_part(district_name, reduced_address)
                    if district_result is not None:
                        ward_node = d.get('wards')
                        reduced_address_2 = district_result[1]
                        removed_district = district_result[2]
                        removed_parts[i].append(removed_district)
                        break

                if ward_node is not None:
                    # Loop throuh each ward to find a ward
                    for w in ward_node:
                        ward_name = w.get('short_codename')
                        check_number_ward = ward_name.split('_')
                        if check_number_ward[-1][0] in ('0','1','2','3','4','5','6','7','8','9'):
                            ward_name = check_number_ward[-1].lstrip('0')
                            # print(ward_name)
                        else:
                            ward_name = ward_name.replace('_', '')
                        ward_result = self.__find_and_rearrange_address_part(ward_name, reduced_address_2)
                        if ward_result is not None:
                            # Happy case we found
                            street = ward_result[1]
                            removed_ward = ward_result[2]
                            removed_parts[i].append(removed_ward)
                            removed_parts[i].append(street)
                            # hopes.append((j, street))
                            break
                    break

            # print(removed_parts)
            low_rate = 0
            # Make decision for each potential province
            # print("Potential province {}".format(i))
            if len(removed_parts[i]) == 4:
                # Prepare material for extra search
                pro_dis_ward = removed_parts[i][0:-1]
                perfect_address = ''.join(reversed(pro_dis_ward))
                material = {}
                material['start_index'] = start_index
                material['end_index'] = end_index
                material['perfect_address'] = perfect_address
                # print(material)
                extra_search.append(material)

            if len(matches) > 0:
                if matches[0][1] >= all_rate:
                    chosen_match = matches[0]
                else:
                    low_rate = matches[0][1]
            # print(all_rate)
            # print(chosen_match)
            if chosen_match is not None:
                match = chosen_match[0]
                ratio = chosen_match[1]
                result = self.__find_matched_result(address,to_look_list,match,ratio, original_list, start_index)
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
        # print(extra_search)
        # Do extra search:
        if len(extra_search) > 0:
            hopeful_list = []
            for combo in extra_search:
                # print(combo)
                start = combo.get('start_index')
                end = combo.get('end_index')
                perfect_address = combo.get('perfect_address')
                # print(start)
                # print(end)
                to_look_list = cleaned_list_extra[start:end + 1]
                # print(to_look_list)
                hopeful_match, hopeful_ratio = process.extractOne(perfect_address,to_look_list)
                hopeful_result = self.__find_matched_result(address,to_look_list,hopeful_match,hopeful_ratio,original_list,start)
                hopeful_list.append(hopeful_result)
            # print(hopeful_list)
            if len(hopeful_list) > 0:
                return hopeful_list[0]
        else:
            for k in range(len(result_list)):
                # print(result_list[k])
                all_rate_ = result_list[k].get('all_rate')
                if all_rate_ > max_rate:
                    max_rate = all_rate_
                    max_index = k
        if max_index >= 0:
            # print(result_list[max_index])
            return result_list[max_index]
        else:
            # print(fall_back_result)
            return fall_back_result

    def assumption_brute_force_search_word_dict(self, address: str, rate_province=85, rate_district=85, rate_ward=65,
                                                order=('street', 'ward', 'district', 'province'), key_value_pairs=None,
                                                all_rate=65):
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
            return self.word_dict_search(address, all_rate=all_rate)
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
            return self.word_dict_search(address, all_rate=all_rate)
        else:
            print("Can handle 1 to 4 groups!")
            return None
