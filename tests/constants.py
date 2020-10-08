ADDRESSES = {
    "vi": " 123 đường , phường , quận , thành phố ",
    "en": " 123 street , ward , district , city ",
}
EXPECTED_ADDRESSES_AS_GROUP = {
    "vi": {'street': "123 đường", "ward": "phường", "district": "quận", "city": "thành phố"},
    "en": {'street': "123 street", "ward": "ward", "district": "district", "city": "city"},
}
ADDRESSES_ONE_TWO_THREE = {
    "one": " 123 street ward district city ",
    "two": " 123 street ward district , city ",
    "three": " 123 street ward , district , city ",
}
EXPECTED_ADDRESSES_ONE_TWO_THREE = {
    "one": {'street': "123 street ward district city"},
    "two": {'street': "123 street ward district", "ward": "city"},
    "three": {'street': "123 street ward", "ward": "district", "district": "city"},
}
ADDRESSES_FIVE_SIX_EMPTY = {
    "five": " 1 , 2 , 3 ,4,5 ",
    "six": " 1 , 2 , 3 ,4,5,6 ",
    "empty": ",,3,4,5,6",
}
EXPECTED_ADDRESSES_FIVE_SIX_EMPTY = {
    "five": {"street": "1 2", "ward": "3", "district": "4", "city": "5"},
    "six": {"street": "1 2 3", "ward": "4", "district": "5", "city": "6"},
    "empty": {"street": "3", "ward": "4", "district": "5", "city": "6"}
}



