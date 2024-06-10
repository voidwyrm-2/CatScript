from typing import Any



def printf(string: str, *insertions: Any):
    if len(insertions) != string.count('{}'):
        raise Exception(f"expected {string.count('{}')} {'argument' if string.count('{}') == 1 else 'arguments'}, but {len(insertions)} were given")
    
    for i in insertions:
        string = string.replace('{}', str(i), 1)
    
    print(string, end='')
