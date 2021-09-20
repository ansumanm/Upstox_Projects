#!/usr/bin/env python3

my_dict = {
        'key_1': 'value_1',
        'key_2': 'value_2',
        'key_3': 'value_3',
        'key_4': 'value_4',
        }

def print_keyval(key):
    val = my_dict[key]

    print(val)

def main():

    for key, val in my_dict.items():
        print_keyval(key)


main()
