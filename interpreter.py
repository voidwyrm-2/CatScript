from typing import Any
from random import randint
import time
import cat_funcs



class Error:
    "This class usually causes the interpreter to call `error()` on the class and print the result, then return an error code of `-1`"
    def __init__(self, _type: str | None = None, details: str | None = None, ln: int | tuple[int, int] | None = None) -> None:
        self.__type: str = _type if _type else 'Error'
        self.__details: str = details
        self.__ln: int | tuple[int, int] | None = ln
    
    def type(self) -> str: return self.__type

    def ln(self) -> int | tuple[int, int] | None: return self.__ln

    def error(self) -> str:
        err = str(self.__type)
        if self.__ln: err += f" on line {self.__ln}"
        if self.__details: err += f": {self.__details}"
        return err
    
    def __repr__(self) -> str: return self.error()

    def copy(self): return Error(self.__type, self.__details, self.__ln)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Error):
            return value.type() == self.__type
        return False
    
    def __ne__(self, value: object) -> bool:
        if isinstance(value, Error):
            return value.type() != self.__type
        return True

    # stuff I can call so I don't have to write the same thing over and over again,
    # I just have to call one method and give it the line number

    #def TypeErr(usedfor: str, expected: str, actual: type, linenum: int):
    #    return Error('TypeError', f"type '{actual.__name__.casefold()}' is not valid for {usedfor}, expected type '{expected}'", linenum)
    
    def ValueErr(usedfor: str, expected: str, actual: Any, linenum: int):
        return Error('ValueError', f"invalid value for {usedfor} '{actual}', expected {expected}", linenum)

    # flagging errors that makes the interpreter do things
    def LineJump(linenum: int) -> Any:
        "This error causes the interpreter to jump to the line stored in `ln`"
        return Error('LineJump', "This error causes the interpreter to jump to the line stored in the second index of `ln`", linenum)
    
    def Exit(linenum: int) -> Any:
        "This error causes the interpreter to exit without an error, and an error code of `1`"
        return Error('Exit', "This error causes the interpreter to exit without an error, and an error code of `1`", linenum)
    
    def Return(linenum: int) -> Any:
        "This error causes the interpreter to return the eval result of the current line, and an error code of `2`"
        return Error('Return', "This error causes the interpreter to return the eval result of the current line, and an error code of `2`", linenum)



class ArgNotGiven:
    def __repr__(self) -> str: return 'ArgNotGiven'

class Func:
    def __init__(self, name: str, code: list[str], args: list[tuple[str, bool]]) -> None:
        self.__name: str = name
        self.__code: list[str] = code
        self.__args: list[tuple[str, bool]] = args
    
    def name(self) -> str: return self.__name

    def run(self, inputs: list[Any], ln: int) -> tuple[int, tuple[dict[str, Any], dict[str, object]]] | tuple[int, Any]:
        pass



def evaluate(vars: dict[str, Any], funcs: dict[str, tuple[bool, Func | Any]], input: str, ln: int) -> tuple[Any, Error | None]:
    #print(funcs)
    #print([f + '(' for f in list(funcs)])
    #print(f"'{input}'")
    if input.startswith(tuple([f + '(' for f in list(funcs)])) and input.endswith(')'):
        funcname, fargs = input.removesuffix(')').split('(', 1)
        op_count = fargs.count('(')
        cl_count = fargs.count(')')
        
        if op_count > cl_count:
            fargs += (')' * (op_count - cl_count))
        elif op_count < cl_count:
            fargs = ('(' * (cl_count - op_count)) + fargs
            
        if fargs.strip() != '':
            func_inputs, err = evaluate(vars, funcs, fargs.strip(), ln)
        else: func_inputs, err = [], None
        if err: return None, err
        
        if funcs[funcname][0]:
            try:
                if not isinstance(func_inputs, (list, tuple, set, dict)): func_inputs = [func_inputs]
                #print(f"finp: '{func_inputs}'")
                return funcs[funcname][1](ln, *func_inputs)
            except Exception as e:
                return None, Error('FuncError', e, ln)
        else:
            return funcs[funcname][1].run(func_inputs, ln)
        #return None, None

    elif input.startswith('lt ') and '=' in input:
        varname, val = input.removeprefix('lt ').split('=', 1)
        varname = varname.strip()
        if varname in list(vars): return None, Error('VariableError', f"cannot create variable '{varname}', already exists", ln)
        c_val, err = evaluate(vars, funcs, val.strip(), ln)
        if err: return err
        vars[varname] = c_val
        return None, None

    elif input.startswith(tuple([v + '=' for v in list(vars)]) + tuple([v + ' =' for v in list(vars)])):
        varname, val = input.split('=', 1)
        varname = varname.strip()
        if varname not in list(vars): return None, Error('VariableError', f"cannot reassign variable '{varname}', doesn't exist", ln)
        c_val, err = evaluate(vars, funcs, val.strip(), ln)
        if err: return err
        vars[varname] = c_val
        return None, None
    
    elif input.startswith('for ') and input.endswith('{'):
        if '=' in input and ',' in input:
            pass
        else:
            return None, Error
    
    elif input.startswith('goto '):
        e_linenum, err = evaluate(vars, funcs, input.removeprefix('goto '), ln)
        if err: return err
        if not isinstance(e_linenum, int):
            return None, Error.ValueErr('goto', 'int', e_linenum, ln)
        if e_linenum == ln:
            return None, Error('OutOfIndexError', f"cannot use goto to jump to the same line", ln)
        return None, Error.LineJump((ln, e_linenum))

    try: return eval(input, vars), None
    except Exception as e:
        return None, Error('EvalError', e, ln)



def clean_line(line: str):
    line = line.strip()
    if '//' not in line: return line
    in_str = 0
    ignore_quote = False
    for cn, c in enumerate(line):
        if c == '"' and not ignore_quote:
            in_str = not in_str
        elif c == '\\': in_str = 2
        elif c == '/' and not in_str:
            try:
                if line[cn + 1] == '/':
                    return line[:len(line)-(cn)].strip()
            except IndexError:
                return line
        if in_str: in_str -= 1
    return line


def run_code(text: str | list[str], used_stack: list[str] = [], return_values: bool = False, injected_vars: dict[str, Any] | None = None, injected_funcs: dict[str, Func | Any] | None = None) -> tuple[int, tuple[dict[str, Any], dict[str, Func]] | Any | None]:
    lines: list[str] = [clean_line(l) for l in text.replace('null', 'None').splitlines()] if isinstance(text, str) else list(text)

    vars: dict[str, Any] = {}

    # if `True`, then it should be run like a python function, otherwise use `.run()`
    funcs: dict[str, tuple[bool, Func | Any]] = {
        'Println': (True, lambda ln, *values: (print(*values), None)),

        'Printf': (True, lambda ln, string, *insertions: (cat_funcs.printf(string, *insertions), None)),

        'GetText': (True, lambda ln, message: (input(message), None) if isinstance(message, str) else (None, Error.ValueErr('GetText', 'string', message, ln)) ),

        'Lower': (True, lambda ln, value: (value.casefold(), None) if isinstance(value, str) else (None, Error.ValueErr('Casefold', 'string', value, ln)) ),

        'Rand': (True, lambda ln, min, max: ((randint(min, max), None) if min <= max else (None, Error('ValueError', f"arg 'min' cannot be higher than arg 'max' of Rand", ln))) if isinstance(min, int) and isinstance(max, int) else (None, Error('ValueError', f"invalid value '{min}' for arg 'min' of Rand, expected int", ln)) if not isinstance(min, int) and isinstance(max, int) else (None, Error('ValueError', f"invalid value '{max}' for arg 'max' of Rand, expected int", ln)) if isinstance(min, int) and not isinstance(max, int) else (None, Error('ValueError', f"invalid value '{min}' for arg 'min' and '{max}' for arg 'max' of Rand, expected int and int", ln))),

        'IsMain': (True, lambda ln: (not len(used_stack), None)),

        'Sleep': (True, lambda ln, seconds: (time.sleep(seconds), None) if isinstance(seconds, (int, float)) else (None, Error.ValueErr('Sleep', 'float or int', seconds, ln)) ),

        'NotGiven': (True, lambda ln, arg: (isinstance(arg, ArgNotGiven), None))
    }

    ln = 0
    while ln < len(lines):
        l = lines[ln]
        if not l: ln += 1; continue
        line_res, err = evaluate(vars, funcs, l, ln+1)
        if err:
            match err.type():
                case 'LineJump':
                    orig_ln, new_ln = err.ln()
                    if new_ln < 1 or new_ln > len(lines):
                        print(Error('OutOfIndexError', f"{new_ln} is not a valid line", orig_ln).error())
                        return -1, None
                    ln = new_ln - 1
                    continue
                case 'Exit':
                    if return_values: return 1, vars, funcs
                    return 1, None
                case 'Return':
                    return 2, line_res
                case other:
                    print(err.error())
                    return -1, None
        ln += 1
    
    if return_values: return 0, vars, funcs
    return 0, None



#['()', '[1, 2, 3, 4, 5]', '"AHHHH"', "` wow would you look at that it's a comment"]

#run_code(['Print("Hello, Catdog!")', 'Print(Casefold("ABCD"))', 'lt x = 10', 'lt y = x / 2', 'Print(x, y)', 'Print(Rand(1, 10))', 'Print(IsMain())', 'x = "WHAT"', 'print(x)'])

#run_code(['lt x = 1', 'print("AHHHH")', 'Sleep(1)', 'x = x + 1', 'goto x'])

run_code(['lt x = "times"', 'Printf("That happened {} {}!\\n", 10, x)'])