from typing import Any



def printf(string: str, *insertions: Any):
    if len(insertions) != string.count('{}'):
        raise Exception(f"expected {string.count('{}')} {'argument' if string.count('{}') == 1 else 'arguments'}, but {len(insertions)} were given")
    
    for i in insertions:
        string = string.replace('{}', str(i), 1)
    
    print(string, end='')


def split_str_by_index(string: str, index: int, error_if_index_to_big: bool = True) -> tuple[str, str, str]:
    '''Returns the part of the string leading up to, the character at, and the string after, the index\n
    If `error_if_index_to_big` is `False`, returns the original string, else raises an IndexError'''
    #if index < 0: index += len(string)
    if index > len(string) - 1 or index < 0:
        if error_if_index_to_big:
            raise IndexError(f"index {index} is out of range of string(len {len(string)})")
        return string, '', ''
    return string[:index+1], string[index], string[index+1:]


def can_get_length(thing: Any):
    try:
        len(thing)
        return True
    except Exception:
        return False