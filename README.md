## Requirements/ Dependency

1. unidecode: to remove Vietnamese accents
2. fuzzywuzzy: for string approximation
3. vietnam-provinces(optional): the original data files come from this module. You may find it interesting in other tasks.
---

## Notes

There some folders and files you may neet to look:
1. data: containing files as json format. These file served as database for look-up and compare tasks.
    * "flat_divisions.json" and "nested_divisions.json": are used to make other files, these 02 files come from vietnam-provinces
    * Have  look in this folder and code when using with your own data files
2. address: some test data
3. load_data.py: containing logics to make files and load data files
4. evaluate.py: evaluating logics
5. address_extract.py: main functions in here
---

## Simple use

Group search
```python
from address_extract import AddressExtractor
extractor = AddressExtractor()

# Play
from time import time
t0 = time()
testw = ['phu','phuong','phuong 1',' phuong 10']
for e in testw:
    result = extractor.group_search(e,group_name='wards',top_n=5)
    final = [(r.get('ward_name'),r.get('rate')) for r in result]
    print(final)
t1 = time()
t = t1 - t0
t

#Output:
#[('Phường Phúc Xá', 90), ('Phường Vĩnh Phúc', 90), ('Phường Phúc Tân', 90), ('Phường Phú Thượng', 90), ('Phường Yên Phụ', 90)]
#[('Phường Phương Liên', 90), ('Phường Phương Mai', 90), ('Phường Phương Liệt', 90), ('Phường Xuân Phương', 90), ('Phường Phương Canh', 90)]
#[('Phường 1', 90), ('Phường 1', 90), ('Phường 1', 90), ('Phường 12', 90), ('Phường 1', 90)]
#[('Phường 10', 90), ('Phường 10', 90), ('Phường 10', 90), ('Phường 10', 90), ('Phường 10', 90)]
#3.125349998474121

# Default wards contains >10k records, so you may want pass it a custom list
custom_list = ('Phường Phương Liên', 'Phường Phương Mai', 'Phường Phương Liệt', 'Phường Xuân Phương', 'Phường Phương Canh','Phường 1','Phường 12','Phường 10')
t0 = time()
testw = ['phu','phuong','phuong 1',' phuong 10']
for e in testw:
    result = extractor.group_search(e,group_name='wards',top_n=3,custom_list=custom_list)
    final = [(r.get('original_value'),r.get('value'),r.get('rate')) for r in result]
    print(final)
t1 = time()
t = t1 - t0
t

#[('Tỉnh Thanh Hóa', 90), ('Tỉnh Thái Nguyên', 72), ('Tỉnh Khánh Hòa', 72), ('Tỉnh Ninh Thuận', 72), ('Tỉnh Bình Thuận', 72)]
#[('Tỉnh Thanh Hóa', 74), ('Tỉnh Khánh Hòa', 63), ('Tỉnh Bình Phước', 56), ('Thành phố Hà Nội', 53), ('Thành phố Hải Phòng', 53)]
#[('Tỉnh Hoà Bình', 90), ('Tỉnh Phú Thọ', 90), ('Thành phố Hải Phòng', 90), ('Tỉnh Thanh Hóa', 90), ('Tỉnh Khánh Hòa', 90)]
#[('Thành phố Hồ Chí Minh', 90), ('Tỉnh Lào Cai', 60), ('Tỉnh Hoà Bình', 60), ('Tỉnh Phú Thọ', 60), ('Tỉnh Vĩnh Phúc', 60)]
#0.016386747360229492

t0 = time()
testd = ['phu nhua','quan 11',' quan 11 ho','quan 11 ho ch','11',' quan 05']
for e in testd:
    result = extractor.group_search(e,group_name='districts',top_n=5)
    final = [(r.get('district_name'),r.get('rate')) for r in result]
    print(final)
t1 = time()
t = t1 - t0
t

#[('Quận Phú Nhuận', 90), ('Quận Thanh Xuân', 64), ('Huyện Thuận Châu', 64), ('Huyện Phú Bình', 64), ('Huyện Phù Ninh', 64)]
#[('Quận 11', 90), ('Huyện Văn Quan', 75), ('Quận 1', 75), ('Quận 12', 75), ('Quận 10', 75)]
#[('Quận 12', 67), ('Quận 10', 67), ('Quận 11', 67), ('Huyện Quan Hóa', 63), ('Quận 1', 59)]
#[('Quận 12', 60), ('Quận 10', 60), ('Quận 11', 60), ('Huyện Quan Hóa', 57), ('Quận 1', 53)]
#[('Huyện Than Uyên', 90), ('Huyện Tân Uyên', 90), ('Huyện Nậm Nhùn', 90), ('Thành phố Sơn La', 90), ('Huyện Quỳnh Nhai', 90)]
#[('Quận 5', 90), ('Huyện Quản Bạ', 72), ('Huyện Bắc Quang', 72), ('Huyện Quang Bình', 72), ('Huyện Hà Quảng', 72)]
#0.2439730167388916
```

# Assumption search / Brute force with assumptions: look in the code to know more
```python
# Load your data files and throw to it
# Expeact the whole combinations of 3 data file or default data will be loaded
from address_extract import AddressExtractor
from time import time
extractor = AddressExtractor()
ad1 = ", 111 Đoàn Văn Bơ , Phường 10, Quận 4, Thành phố Hồ Chí Minh"
ad2 = "111 Đoàn Văn Bơ Phường 10 Quận 4 Thành phố Hồ Chí Minh"
ad3 = " 111 Đoàn Văn Bơ, TP Hồ Chí Minh"
ad4 = " 111 Đoàn Văn Bơ, TP Hồ Chí Minh, phường 10, quận 4"
l = [ad1, ad2, ad3, ad4]
for addr in l:
    t2 = time()
    result = extractor.assumption_brute_force_search(address=addr)
    #result = extractor.assumption_search(address=addr)
    t3 = time()
    elapsed = t3 - t2
    print(result)
    print(elapsed)

#{time'street': '111 Đoàn Văn Bơ', 'ward': 'Phường 10', 'district': 'Quận 4', 'province': 'Thành phố Hồ Chí Minh', 'city_rate': 100, 'all_rate': 100, 'type': 'brute'}
#0.023527860641479492
#{'street': '111 Đoàn Văn Bơ Phường 10 Quận 4 Thành phố Hồ Chí Minh', 'ward': 'Phường 04', 'district': 'Quận 3', 'province': 'Thành phố Hồ Chí Minh', 'type': 'medium', 'city_rate': 72, 'all_rate': 67}
#0.05301403999328613
#{'street': '111 Đoàn Văn Bơ', 'ward': 'Phường Tân Định', 'district': 'Quận 1', 'province': 'Thành phố Hồ Chí Minh', 'type': 'fast', 'city_rate': 86, 'all_rate': 90}
#0.0262296199798584
#{'street': '111 Đoàn Văn Bơ', 'ward': 'Phường 10', 'district': 'Quận 4', 'province': 'Thành phố Hồ Chí Minh', 'city_rate': 100, 'all_rate': 100, 'type': 'brute'}
#0.019798994064331055

for addr in l:
    t2 = time()
    result = extractor.assumption_search(address=addr)
    t3 = time()
    elapsed = t3 - t2
    print(result)
    print(elapsed) 
#{'street': '111 Đoàn Văn Bơ', 'ward': 'Phường Tân Định', 'district': 'Quận 1', 'province': 'Thành phố Hồ Chí Minh', 'type': 'fast', 'city_rate': 86, 'all_rate': 68}
#0.031347036361694336
#{'street': '111 Đoàn Văn Bơ Phường 10 Quận 4 Thành phố Hồ Chí Minh', 'ward': 'Phường 04', 'district': 'Quận 3', 'province': 'Thành phố Hồ Chí Minh', 'type': 'medium', 'city_rate': 72, 'all_rate': 67}
#0.04418587684631348
#{'street': '111 Đoàn Văn Bơ', 'ward': 'Phường Tân Định', 'district': 'Quận 1', 'province': 'Thành phố Hồ Chí Minh', 'type': 'fast', 'city_rate': 86, 'all_rate': 90}
#0.019034862518310547
#{'street': '111 Đoàn Văn Bơ', 'ward': 'Thị trấn Vĩnh Lộc', 'district': 'Huyện Chiêm Hóa', 'province': 'Tỉnh Tuyên Quang', 'type': 'medium', 'city_rate': 72, 'all_rate': 52}
#0.032180070877075195
                 
```

Not too smart, hope it help :)