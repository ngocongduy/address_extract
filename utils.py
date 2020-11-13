import re
from unidecode import unidecode

def clean_and_reduce_length(addr: str, biased_group: str, magic_number=13, mid_number=27):
    if len(addr) > 0 and mid_number > magic_number:
        if biased_group == 'province':
            addr = clean(addr, is_city=True)
            if len(addr) > magic_number:
                return addr[-magic_number:]
        elif biased_group == 'district':
            addr = clean(addr, is_district=True)
            magic_number = mid_number
            if len(addr) > magic_number:
                return addr[magic_number-13:magic_number]
        elif biased_group == 'ward':
            addr = clean(addr, is_ward=True)
            magic_number = mid_number
            if len(addr) > magic_number:
                return addr[0:magic_number-13]
        else:
            addr = clean_all_in_one(addr)
            magic_number = mid_number
            if len(addr) > magic_number:
                return addr[0:magic_number]
    return addr

def reduce_length_with_biased(addr: str, biased_group: str, magic_number=13, mid_number=27):
    if len(addr) > 0 and mid_number > magic_number:
        if biased_group == 'province':
            if len(addr) > magic_number:
                return addr[-magic_number:]
        elif biased_group == 'district':
            magic_number = mid_number
            if len(addr) > magic_number:
                return addr[magic_number-13:magic_number]
        elif biased_group == 'ward':
            magic_number = mid_number
            if len(addr) > magic_number:
                return addr[0:magic_number-13]
        else:
            magic_number = mid_number
            if len(addr) > magic_number:
                return addr[0:magic_number]
    return addr


def clean_alphanumeric_space(address: str):
    def only_alphanumeric_space(address: str):
        return re.sub(r'[^A-Za-z0-9,\s]', '', address)
    def _comma_to_space(address: str):
        return re.sub(',', ' ', address)
    try:
        result = unidecode(address)
        result = _comma_to_space(result)
        return only_alphanumeric_space(result).lower()
    except Exception as e:
        print(e)
def clean_and_split_into_words(addr: str):
    addr = clean_alphanumeric_space(addr)
    words = addr.split(' ')
    for i in range(len(words)):
        value = words[i].strip()
    if len(value) > 0:
        words[i] = value
    else:
        words[i] = None
    # Remove None
    result = [e for e in words if e]
    return result


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

    # Mapping values from address groups, address groups is assumpted to be smaller than groups keys
    result = dict()
    for i in range(len(groups)):
        result[group_keys[i]] = groups[i]
    return result


def add_zero_for_one_digit_number(num_as_string: str):
    # Add zero
    if len(num_as_string) > 2:
        if num_as_string[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9'] \
                and num_as_string[1] not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:
            result = '0' + num_as_string
            return result
    elif len(num_as_string) == 1:
        if num_as_string[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            result = '0' + num_as_string
            return result
    return num_as_string


def remove_leading_zero_for_one_digit_number(num_as_string: str):
    splits = num_as_string.split(' ')
    # print(splits)
    if len(splits) > 0:
        clean_list = [i.lstrip('0') for i in splits]
        result = ' '.join(clean_list)
        return result
    return num_as_string


def clean(address: str, is_city=False, is_district=False, is_ward=False):
    def only_alphanumeric(address: str):
        return re.sub(r'[^A-Za-z0-9]', '', address)

    def normalized_city(address: str):
        return re.sub(r'(tp\.)|(tp\s)|(^tinh\s)|(thanh\spho\s)', '', address, flags=re.IGNORECASE)
        # return re.sub(r'(tp\.)|(tp\s)|(thanh\spho\s)', '', address, flags=re.IGNORECASE)

    def normalized_district(address: str):
        return re.sub(r'(^huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(^quan\s)', '', address,
                      flags=re.IGNORECASE)
        # return re.sub(r'(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)', '', address, flags=re.IGNORECASE)

    def normalized_ward(address: str):
        return re.sub(r'(^xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(p\.)|([^a-z]+p\s+)|(^phuong\s)', '', address,
                      flags=re.IGNORECASE)
        # return re.sub(r'(thi\stran\s)|(tt\.)|(tt\s)', '', address, flags=re.IGNORECASE)

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


def clean_all_in_one(address: str):
    def only_alphanumeric(address: str):
        return re.sub(r'[^a-z0-9]', '', address)

    def normalized_city_district(address: str):
        # return re.sub(r'(tp\.)|(tp\s)|(^tinh\s)|(^huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(^quan\s)', '',address)
        return re.sub(r'(tp\.)|(tp\s)|(,tinh\s)|(,huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(,quan\s)', '',
                      address)
        # return re.sub(r'(tp\.)|(tp\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)', '',address)

    def normalized_ward(address: str):
        # return re.sub(r'(^xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(p\.)|([^a-z]+p\s+)|(^phuong\s)', '', address)
        return re.sub(r'(,xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(,phuong\s)', '', address)
        # return re.sub(r'(thi\stran\s)|(tt\.)|(tt\s)', '', address)

    try:
        result = unidecode(address)
        result = remove_leading_zero_for_one_digit_number(result)
        result = result.lower()
        result = normalized_city_district(result)
        result = normalized_ward(result)
        return only_alphanumeric(result)
    except Exception as e:
        print(e)


def clean_all_extra(address: str):
    def only_alphanumeric(address: str):
        return re.sub(r'[^a-z0-9]', '', address)

    def normalized_city_district(address: str):
        return re.sub(
            r'(tp\.)|(tp\s)|(,tinh\s)|(,huyen\s)|(thanh\spho\s)|(thi\sxa\s)|(tx\.)|(tx\s)|(,quan\s)|(tinh\s)|(huyen\s)|(quan\s)' \
            , '', address)

    def normalized_ward(address: str):
        return re.sub(
            r'(,xa\s)|(thi\stran\s)|(tt\.)|(tt\s)|(,phuong\s)|(p\.)|([^a-z]+p\s+)||(phuong\s)|(thon\s)|(xom\s)|(khom\s)|(xa\s)||(to\s)||(ap\s)',
            '', address)

    try:
        result = unidecode(address)
        result = remove_leading_zero_for_one_digit_number(result)
        result = result.lower()
        result = normalized_city_district(result)
        result = normalized_ward(result)
        return only_alphanumeric(result)
    except Exception as e:
        print(e)


def clean_all_test(address: str):
    def only_alphanumeric(address: str):
        return re.sub(r'[^a-z0-9]', '', address)

    try:
        result = unidecode(address)
        result = remove_leading_zero_for_one_digit_number(result)
        result = result.lower()
        return only_alphanumeric(result)
    except Exception as e:
        print(e)


def clean_alphanumeric_delimeter_upper(address: str):
    def only_alphanumeric(address: str):
        return re.sub(r'[^A-Za-z0-9,\s]', '', address, )

    def remove_vietnam(address: str):
        return re.sub(r'(vn\s)|(\svn)|(viet\snam)|(\svietnam)|(vietnam\s)', '', address,
                      flags=re.IGNORECASE)

    try:
        result = unidecode(address)
        result = remove_vietnam(result)
        return only_alphanumeric(result).upper()
    except Exception as e:
        print(e)
