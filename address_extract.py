from itertools import permutations
from fuzzywuzzy import process
from .utils import *

from .load_data import load_address_dict, load_cities_data_normalized, load_address_dict_normalized, load_word_bag


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
        word_dict = load_word_bag()
        self.word_bag = word_dict.get('word_bag')
        self.hot_words = word_dict.get('hot_words')

    def assumption_brute_force_search(self, address: str, rate_province=85, rate_district=85, rate_ward=65,
                                      order=('street', 'ward', 'district', 'province'), key_value_pairs=None):
        """
        Given a full address as string, try to return 4 part: street, ward, district, province/city
        Givan a list of dictionary, each dictionary is a province/city and all of its districts and wards
        First try to find the proinvce -> district -> ward
        If failure in seperate address in to 4 parts, perform 'assumption_search'
        Try to iterate all possible order of ('street', 'ward', 'district', 'province'), prefered the shown order
        After iterating and still fail (cannot satisfy matching rates for each part), try 'assumption_search'
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

        if no_of_group >= 1 and no_of_group < 4:
            return self.assumption_search(address, key_value_pairs=key_value_pairs)
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
            return self.assumption_search(address, key_value_pairs=key_value_pairs)
        else:
            print("Can handle 1 to 4 groups!")
            return None

    def group_search(self, search_term_in_address: str, group_name: str, top_n=1, custom_list=None,
                     biased_group=''):
        """
        Given lists containing all provinces/cities, all districts, all wards
        Find n best matched element in those list, searching is directed by group_name
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
        if group_name == 'provinces':
            # to_look_value = clean(search_term_in_address, is_city=True)
            # Use this trick for province to work with assumption search
            # reduce length of to_look_value after cleaned for better matched
            # if reduce_district:
            #     magic_number = 13
            #     if len(to_look_value) >= magic_number:
            #         to_look_value = to_look_value[-magic_number:]
            if biased_group == 'province':
                to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
            elif biased_group == 'district':
                to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
            elif biased_group == 'ward':
                to_look_value = clean_and_reduce_length(search_term_in_address, biased_group=biased_group)
            else:
                to_look_value = clean(search_term_in_address, is_city=True)

        elif group_name == 'districts':
            to_look_value = clean(search_term_in_address, is_district=True)
        elif group_name == 'wards':
            to_look_value = clean(search_term_in_address, is_ward=True)
        if cleaned_list is not None and len(to_look_value) > 0:
            if 1 <= top_n <= 10:
                result_list = process.extractBests(query=to_look_value, choices=cleaned_list, limit=top_n)
                final_result = []
                try:
                    for e in result_list:
                        result = {'value': None, 'rate': 0}
                        value, rate = e[0], e[1]
                        # print(value)
                        # print(cleaned_list)
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
        def reduce_length_with_magic_number(number_as_string: str, magic_number=44):
            if len(number_as_string) > magic_number:
                return number_as_string[-magic_number:]
            return number_as_string

        # Assumpted a address ordered with orders:
        order = ('street', 'ward', 'district', 'province')

        result = {}
        for k in order:
            result[k] = ''
        if type(key_value_pairs) is not dict:
            key_value_pairs = extract_group(address, order)
        # all_in_one = [i for i in key_value_pairs.values()]
        all_in_one = []
        for k in order:
            value = key_value_pairs.get(k)
            if value is not None:
                all_in_one.append(value)

        no_of_group = len(all_in_one)
        # assume that province is the last element
        province = ''
        for i in range(4):
            if no_of_group - 1 == i:
                province = all_in_one[i]
        if no_of_group == 1:
            all_in_one_cleaned = clean_all_in_one(all_in_one[0])
            all_in_one_extra_cleaned = clean_all_extra(all_in_one[0])
        else:
            # all_in_one[0] = ''
            all_in_one_cleaned = clean_all_in_one(','.join(all_in_one))
            all_in_one_extra_cleaned = clean_all_extra(','.join(all_in_one))

        all_in_one_cleaned = reduce_length_with_magic_number(all_in_one_cleaned)
        all_in_one_extra_cleaned = reduce_length_with_magic_number(all_in_one_extra_cleaned)

        cleaned_list = self.address_dict_normalized.get('cleaned_list')
        cleaned_list_extra = self.address_dict_normalized.get('normalized_list')

        if cleaned_list is None or len(all_in_one_cleaned) < 1:
            return None

        # Try 4 times
        max_ratio = 0
        max_index = -1
        potential_provinces = []
        for i in range(len(order)):
            group = order[i]
            province_node = self.group_search(search_term_in_address=province, group_name='provinces',biased_group=group)
            potential_provinces.append(province_node)
            if province_node is not None:
                province_node = province_node[0]
                ratio = province_node.get('rate')
                if ratio > max_ratio:
                    max_index = i
                    max_ratio = ratio
            else:
                return None
        if max_index >= 0:
            province_node = potential_provinces[max_index][0]
        else:
            return None

        value = province_node.get('value')
        ratio = province_node.get('rate')
        start = province_node.get('start_index')
        end = province_node.get('end_index')
        # print(province_node)
        if ratio >= province_rate and start >= 0 and end >= 0:
            match, rate = process.extractOne(all_in_one_cleaned, cleaned_list[start:end])
            # Add this check and look up will slow down but hope to increase accuracy
            if rate < extra_rate:
                other_match, rate = process.extractOne(all_in_one_extra_cleaned, cleaned_list_extra[start:end])
                index = cleaned_list_extra[start:end].index(other_match)
                index += start
                result['type'] = 'medium'
                result['count'] = end - start + 1
            else:
                index = cleaned_list[start:end].index(match)
                index += start
                result['type'] = 'fast'
                result['count'] = end - start + 1
        else:
            ###
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
            ###
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
