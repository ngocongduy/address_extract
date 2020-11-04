import re
from unidecode import unidecode


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
