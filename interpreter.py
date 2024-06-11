from typing import Any
from random import randint
import time
import cat_funcs



def split_str_by_index(string: str, index: int, error_if_index_to_big: bool = True) -> tuple[str, str, str]:
    '''Returns the part of the string leading up to, the character at, and the string after, the index\n
    If `error_if_index_to_big` is `False`, returns the original string, else raises an IndexError'''
    #if index < 0: index += len(string)
    if index > len(string) - 1 or index < 0:
        if error_if_index_to_big:
            raise IndexError(f"index {index} is out of range of string(len {len(string)})")
        return string, '', ''
    return string[:index], string[index], string[index+1:]


def concat_dict(old_dict: dict[Any, Any], new_kv_pairs: tuple[Any, Any] | list[tuple[Any, Any]] | dict[Any, Any]) -> dict[Any, Any]:
    out = old_dict.copy()
    if isinstance(new_kv_pairs, dict):
        if len(new_kv_pairs) == 1: out[list(new_kv_pairs)[0]] = new_kv_pairs[list(new_kv_pairs)[0]]
        else:
            for k, v in new_kv_pairs:
                out[k] = v
    elif isinstance(new_kv_pairs, tuple):
        out[new_kv_pairs[0]] = new_kv_pairs[1]
    else:
        if len(new_kv_pairs) == 1: out[new_kv_pairs[0][0]] = new_kv_pairs[0][1]
        for kv in new_kv_pairs:
            out[kv[0]] = kv[1]
    return out


def generate_dict(entries: list[tuple[Any, set[Any]]]) -> dict[Any, Any]:
    out: dict[Any, Any] = {}
    for e in entries:
        v = e[0]
        if isinstance(e, (list, tuple, set, dict)):
            for k in e[1]: out[k] = v
        else: out[k] = v
    return out


CATSCRIPT_TYPES = generate_dict([ ('Int', ['int', 'integer']), ('Float', 'float'), ('String', ['string', 'str']), ('List', 'list'), ('Tuple', 'tuple'), ('Dict', ['dict', 'dictionary']), ('Set', 'set'), ('Null', ['null', 'nil', 'none', 'nonetype']) ])
def to_catscript_type(t: str) -> str:
    return CATSCRIPT_TYPES.get(t.casefold(), t.casefold().capitalize())



class Error:
    "This class usually causes the interpreter to call `error()` on the class and print the result, then return an error code of `-1`"
    def __init__(self, _type: str | None = None, details: str | None = None, ln: int | tuple[int, int] | tuple[int, int, int] | None = None) -> None:
        self.__type: str = _type if _type else 'Error'
        self.__details: str = details
        self.__ln: int | tuple[int, int] | None = ln
    
    def type(self) -> str: return self.__type

    def ln(self) -> int | tuple[int, int] | tuple[int, int, int] | None: return self.__ln

    def setln(self, new_ln: int): self.__ln = new_ln

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
    
    def SyntaxErr(details: str, linenum: int):
        return Error('SyntaxError', details, linenum)

    def ExprErr(details: str, linenum: str):
        return Error('ExpressionError', details, linenum)
    
    def EvalErr(details: str, linenum: str):
        return Error('EvaluationError', details, linenum)
    
    def TypeErr(details: str, linenum: str):
        return Error('TypeError', details, linenum)
    
    def NoPrint(linenum: int):
        "This error causes the interpreter to act as if there is an error, but not print it's details"
        return Error('NoPrint', "This error causes the interpreter to act as if there is an error, but not print it's details", linenum)

    # flag errors that makes the interpreter do things
    def LineJump(linenum: tuple[int, int]):
        "This error causes the interpreter to jump to the line stored in the second index of `ln`"
        return Error('LineJump', "This error causes the interpreter to jump to the line stored in the second index of `ln`", linenum)
    
    def ScheduledLineJump(linenum: tuple[int, int, int]):
        "This error causes the interpreter to jump to the line stored in the second index of `ln` when at the line stored in the third index of `ln`"
        return Error('ScheduledLineJump', "This error causes the interpreter to jump to the line stored in the second index of `ln` when at the line stored in the third index of `ln`", linenum)
    
    def Exit(linenum: int):
        "This error causes the interpreter to exit without an error, and an error code of `1`"
        return Error('Exit', "This error causes the interpreter to exit without an error, and an error code of `1`", linenum)
    
    def Return(linenum: int):
        "This error causes the interpreter to return the eval result of the current line, and an error code of `2`"
        return Error('Return', "This error causes the interpreter to return the eval result of the current line, and an error code of `2`", linenum)



class ArgNotGiven:
    def __repr__(self) -> str: return 'ArgNotGiven'

class Func:
    def __init__(self, name: str, code: list[str], args: list[tuple[str, bool, Any | None]] = [], desciption: str = '[no description]') -> None:
        self.__name: str = name
        self.__desc: str = desciption
        self.__code: list[str] = code
        self.__args: list[tuple[str, bool]] = args
    
    def name(self) -> str: return self.__name

    def desc(self) -> str: return self.__desc

    def run(self, vars: dict[str, Any], funcs: dict[str, tuple[bool, Any]], lines: list[str], used_stack: list[str], ln: int, inputs: list[Any]) -> tuple[int, tuple[dict[str, Any], dict[str, object], Any] | None, Error | None]:
        #print(self.__args)
        #print(inputs)
        if len(inputs) > len(self.__args):
            return -1, None, Error('FuncError', f"expected {len(self.__args)} arguments, but {len(inputs)} were given", ln)
        
        formatted_inputs = []

        for n, i in enumerate(inputs):
            formatted_inputs.append((self.__args[n][0], i))
        if len(formatted_inputs) < len(self.__args):
            if not self.__args[len(formatted_inputs)][1]:
                return -1, None, Error('FuncError', f"expected {len(self.__args)} arguments, but {len(formatted_inputs)} were given", ln)
            else:
                for a in self.__args[len(formatted_inputs):]:
                    formatted_inputs.append((a[0], a[2]))
        
        run_res = run_code(self.__code, used_stack, True, injected_vars=concat_dict(vars, formatted_inputs), injected_funcs=funcs.copy())
        return (*run_res, None)


def process_args(args: list[str], vars: dict[str, Any], funcs: dict[str, tuple[bool, Func | Any]], lines: list[str], used_stack: list[str], ln: int) -> tuple[list[tuple[str, bool, Any | None]], Error | None]:
    out: list[tuple[str, bool, Any | None]] = []
    for a in args:
        if '=' in a:
            argname, arg_default = a.split('=', 1)
            c_arg_default, arg_def_err = evaluate(vars, funcs, arg_default.strip(), lines, used_stack, ln)
            if arg_def_err: return None, arg_def_err
            out.append((argname.strip(), True, c_arg_default))
        else: out.append((a, False, None))
    return out, None



def get_char_not_in_str(string: str, char: str, quote_char: str = '"', nth_char_to_get: int = 1, respect_escapes: bool = True) -> int:
    '''Returns the index of `char` in the given string
    Returns `-1` if the char is not found'''
    if char not in string: return -1
    in_str = False
    ignore_quote = 0
    char_count = 0 if nth_char_to_get - 1 < 0 else nth_char_to_get - 1
    for cn, c in enumerate(string):
        if c == quote_char and not ignore_quote:
            in_str = not in_str
        elif c == '\\' and respect_escapes and in_str: ignore_quote = 2
        elif c == char and not in_str:
            if char_count: char_count -= 1
            else: return cn
        if ignore_quote: ignore_quote -= 1
    return -1


def split_by_chars_not_in_str(string: str, char: str, strip_splits: bool = False, quote_char: str = '"', respect_escapes: bool = True) -> list[str]:
    if char not in string: return [string]
    out: list[str] = []
    current = string
    while char in current:
        char_index = get_char_not_in_str(current, char, quote_char, 1, respect_escapes)
        if char_index == -1: out.append(current); return out
        o, _, next = split_str_by_index(current, char_index)
        if strip_splits: out.append(o.strip())
        else: out.append(o)
        current = next
    if strip_splits: out.append(current.strip())
    else: out.append(current)
    return out


def collect_until_token(lines: list[str], ln: int, closing_token: str = '}', opening_token: str = '{') -> tuple[list[str], Error | None]:
    out = []
    nest = 0
    for l in lines:
        if l == closing_token:
            if nest: out.append(l); nest -= 1
            else: return out, None
        else:
            if l.endswith(opening_token) and not l.startswith(closing_token): nest += 1
            out.append(l)
    return None, Error.SyntaxErr(f"expected '{closing_token}', but found end of file", ln)


def get_index_of_next_token_if(lines: list[str], ln: int, endcode: int = 0) -> tuple[int, Error | None]: # , tokens: str | tuple[str] = '}'):
    '''`endcode`:
    <= 0: `}`\n
    1: `else`
    >= 2: `elseif`
    '''
    #if isinstance(tokens, str): tokens = tuple([tokens])
    nest: list[bool] = []
    for n, l in enumerate(lines):
        #print(n, endcode, nest, f"'{l}'")
        if l.endswith('{') and not l.startswith('}'):
            if l.startswith('if '): nest.append(True)
            else: nest.append(False)
        elif l == '}':
            if len(nest): nest.pop()
            elif endcode <= 0: return (n + 1) + ln, None
            else: return -1, None
        elif l in ('} else {', '}else {', '} else{', '}else{'):
            if endcode == 1:
                if len(nest):
                    if not nest[-1]:
                        return None, Error.SyntaxErr("unexpected else", ln)
                else: return (n + 1) + ln, None
        elif l.startswith(('} elseif ', '}elseif ')) and l.endswith('{'):
            if endcode >= 2:
                if len(nest):
                    if not nest[-1]:
                        return None, Error.SyntaxErr("unexpected elseif", ln)
                else: return (n + 1) + ln, None
    return None, Error.SyntaxErr("expected '}', '} else {', or '} elseif {', but found end of file", ln)


def evaluate(vars: dict[str, Any], funcs: dict[str, tuple[bool, Func | Any]], input: str, lines: list[str], used_stack: list[str], ln: int) -> tuple[Any, Error | None]:
    #print(funcs)
    #print([f + '(' for f in list(funcs)])
    #print(f"'{input}'")

    singlequote_index = get_char_not_in_str(input, "'")
    if singlequote_index != -1:
        return None, Error.SyntaxErr("unexpected \"'\"", ln)
    del singlequote_index

    if input.startswith(tuple([f + '(' for f in list(funcs)])) and input.endswith(')'):
        funcname, fargs = input.removesuffix(')').split('(', 1)
        op_count = fargs.count('(')
        cl_count = fargs.count(')')
        
        if op_count > cl_count:
            fargs += (')' * (op_count - cl_count))
        elif op_count < cl_count:
            fargs = ('(' * (cl_count - op_count)) + fargs
            
        if fargs.strip() != '':
            func_inputs, err = evaluate(vars, funcs, fargs.strip(), lines, used_stack, ln)
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
            if not isinstance(func_inputs, (list, tuple, set, dict)): func_inputs = [func_inputs]
            func_errcode, func_res, func_err = funcs[funcname][1].run(vars, funcs, lines, used_stack, ln, func_inputs)
            if func_err: return None, func_err
            if func_errcode < 0:
                return None, Error.NoPrint(ln)
            elif func_errcode == 1:
                return None, Error.Exit(ln)
            else:
                new_vars, new_funcs, func_returned = func_res
                for varkey in new_vars:
                    if varkey in list(vars): vars[varkey] = new_vars[varkey]
                for funckey in new_funcs:
                    if funckey in list(funcs): funcs[funckey] = new_funcs[funckey]
                
                if func_errcode == 2:
                    return func_returned, None
                else: return None, None
        #return None, None

    elif input.startswith('fn ') and '(' in input and input.endswith((') {', '){')):
        funcname, args_raw = input.removeprefix('fn ').removesuffix(') {').removesuffix('){').split('(', 1)
        funcname, args_raw = funcname.strip(), args_raw.strip()

        args_raw_split = split_by_chars_not_in_str(args_raw, ',', True)

        processed_args, p_args_err = process_args(args_raw_split, vars, funcs, lines, used_stack, ln)
        if p_args_err: return None, p_args_err
        
        func_lines, func_lines_err = collect_until_token(lines[ln:], ln)
        if func_lines_err: return None, func_lines_err
        
        funcs[funcname] = (False, Func(funcname, func_lines, processed_args))
        return None, Error.LineJump((ln, (ln + len(func_lines)) + 2))

    elif input.startswith('lt ') and '=' in input:
        varname, val = input.removeprefix('lt ').split('=', 1)
        varname = varname.strip()
        if varname in list(vars): return None, Error('VariableError', f"cannot create variable '{varname}', already exists", ln)
        c_val, err = evaluate(vars, funcs, val.strip(), lines, used_stack, ln)
        if err: return None, err
        vars[varname] = c_val
        return None, None

    elif input.startswith(tuple([v + '=' for v in list(vars)]) + tuple([v + ' =' for v in list(vars)])) and not input.startswith(tuple([v + '==' for v in list(vars)]) + tuple([v + ' ==' for v in list(vars)])):
        varname, val = input.split('=', 1)
        varname = varname.strip()
        if varname not in list(vars): return None, Error('VariableError', f"variable '{varname}' does not exist", ln)
        c_val, err = evaluate(vars, funcs, val.strip(), lines, used_stack, ln)
        if err: return None, err
        vars[varname] = c_val
        return None, None
    
    elif input.startswith('for ') and input.endswith('{'):
        invalid_for_expr = lambda expr, reason = '': Error.ExprErr(f"invalid for loop expression '{expr}'{f'({reason})' if reason else ''}", ln)
        for_expr = input.removeprefix('for ').removesuffix('{').strip()
        if '=' in for_expr and ',' in for_expr:
            assign_index = get_char_not_in_str(for_expr, '=')
            if assign_index == -1:
                return None, invalid_for_expr(for_expr, "expected format `[varname] = [start], [end]` but missing `=`")
            
            floop_varname, _, floop_range = split_str_by_index(for_expr, assign_index)
            floop_varname, floop_range = floop_varname.strip(), floop_range.strip()

            comma_index = get_char_not_in_str(floop_range, ',')
            if comma_index == -1:
                return None, invalid_for_expr(for_expr, "expected format `[varname] = [start], [end]` but missing `,`")
            
            start, _, end = split_str_by_index(floop_range, comma_index)
            
            c_start, start_err = evaluate(vars, funcs, start, lines, used_stack, ln)
            if start_err: return None, start_err
            if not isinstance(c_start, int):
                return None, Error('TypeError', f"expected Int for range start, but {to_catscript_type(type(c_start).__name__)} was given instead")
            
            c_end, end_err = evaluate(vars, funcs, end, lines, used_stack, ln)
            if end_err: return None, end_err
            if not isinstance(c_start, int):
                return None, Error('TypeError', f"expected Int for range end, but {to_catscript_type(type(c_start).__name__)} was given instead")

            floop_lines, floop_lines_err = collect_until_token(lines[ln:], ln)
            if floop_lines_err: return None, floop_lines_err

            for floop_iter_index in range(c_start, c_end):
                floop_errcode, floop_res = run_code(floop_lines, used_stack, True, vars.copy() if floop_varname == '_' else concat_dict(vars, (floop_varname, floop_iter_index)), funcs.copy())
                if floop_errcode < 0:
                    return None, Error.NoPrint(ln)
                elif floop_errcode == 1:
                    return 1, None
                elif floop_errcode == 0:
                    for varkey in floop_res[0]:
                        if varkey in list(vars): vars[varkey] = floop_res[0][varkey]
                    for funckey in floop_res[1]:
                        if funckey in list(funcs): funcs[funckey] = floop_res[1][funckey]
            return None, Error.LineJump((ln, (ln + len(floop_lines)) + 2))
        else:
            return None, invalid_for_expr(for_expr)
        
    elif input.startswith(('if ', '} elseif ', '}elseif ')) and input.endswith('{'):
        if_res, if_err = evaluate(vars, funcs,
                                  input.removeprefix('if ').removeprefix('} elseif ').removeprefix('}elseif ').removesuffix('{').strip(),
                                  lines, used_stack, ln)
        if if_err: return None, if_err

        next_if, next_if_err = get_index_of_next_token_if(lines[ln:], ln, 2)
        if next_if_err: return None, next_if_err
        if next_if == -1:
            next_if, next_if_err2 = get_index_of_next_token_if(lines[ln:], ln, 1)
            if next_if_err2: return None, next_if_err2
        end_of_if, end_of_if_err = get_index_of_next_token_if(lines[ln:], ln, 0)
        if end_of_if_err: return None, end_of_if_err

        if if_res:
            #print(next_if, end_of_if)
            if next_if == -1: return None, Error.ScheduledLineJump((ln, end_of_if, end_of_if+1))
            return None, Error.ScheduledLineJump((ln, next_if, end_of_if+1))
        else:
            if next_if == -1: return None, Error.LineJump((ln, end_of_if+1))
            return None, Error.LineJump((ln, next_if))
    
    elif input in ('} else {', '}else {', '} else{', '}else{'):
        end_of_if, end_of_if_err = get_index_of_next_token_if(lines[ln:], ln, 0)
        if end_of_if_err: return None, end_of_if_err
        return None, Error.ScheduledLineJump((ln, end_of_if, end_of_if+1))

    elif input.startswith('goto '):
        e_linenum, err = evaluate(vars, funcs, input.removeprefix('goto '), lines, used_stack, ln)
        if err: return err
        if not isinstance(e_linenum, int):
            return None, Error.ValueErr('goto', 'Int', e_linenum, ln)
        if e_linenum == ln:
            return None, Error('OutOfIndexError', f"cannot use goto to jump to the same line", ln)
        elif e_linenum < 1 or e_linenum > len(lines)+1:
            return None, Error('OutOfIndexError', f"{e_linenum} is not a valid line", ln)
        return None, Error.LineJump((ln, e_linenum))

    #print(f"'{input}'")

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


def run_code(text: str | list[str], used_stack: list[str] = [], return_values: bool = False, injected_vars: dict[str, Any] | None = None, injected_funcs: dict[str, Func | Any] | None = None) -> tuple[int, tuple[dict[str, Any], dict[str, Func]] | None]:
    lines: list[str] = [clean_line(l) for l in text.replace('null', 'None').replace('true', 'True').replace('false', 'False').splitlines()] if isinstance(text, str) else list(text)

    vars: dict[str, Any] = injected_vars if isinstance(injected_vars, dict) else {}

    # if `True`, then it should be run like a python function, otherwise use `.run()`
    funcs: dict[str, tuple[bool, Func | Any]] = injected_funcs if isinstance(injected_funcs, dict) else {
        'Println': (True, lambda ln, *values: (print(*values), None)),

        'Printf': (True, lambda ln, string, *insertions: (cat_funcs.printf(string, *insertions), None)),

        'GetText': (True, lambda ln, message: (input(message), None) if isinstance(message, str) else (None, Error.ValueErr('GetText', 'string', message, ln)) ),

        'Lower': (True, lambda ln, value: (value.casefold(), None) if isinstance(value, str) else (None, Error.ValueErr('Casefold', 'string', value, ln)) ),

        'Rand': (True, lambda ln, min, max: ((randint(min, max), None) if min <= max else (None, Error('ValueError', f"arg 'min' cannot be higher than arg 'max' of Rand", ln))) if isinstance(min, int) and isinstance(max, int) else (None, Error('ValueError', f"invalid value '{min}' for arg 'min' of Rand, expected Int", ln)) if not isinstance(min, int) and isinstance(max, int) else (None, Error('ValueError', f"invalid value '{max}' for arg 'max' of Rand, expected Int", ln)) if isinstance(min, int) and not isinstance(max, int) else (None, Error('ValueError', f"invalid value '{min}' for arg 'min' and '{max}' for arg 'max' of Rand, expected Int and Int", ln))),

        'IsMain': (True, lambda ln: (not len(used_stack), None)),

        'Sleep': (True, lambda ln, seconds: (time.sleep(seconds), None) if isinstance(seconds, (int, float)) else (None, Error.ValueErr('Sleep', 'Float or Int', seconds, ln)) ),

        'Exit': (True, lambda ln: (None, Error.Exit(ln))),

        'Len': (True, lambda ln, obj: (len(obj), None) if cat_funcs.can_get_length(obj) else (None, Error.TypeErr(f"'{to_catscript_type(type(obj).__name__)}' does not have a length", ln)))

        #'NotGiven': (True, lambda ln, arg: (isinstance(arg, ArgNotGiven), None)),

        #'Help': (True, lambda ln, x: print(f"help for function '{x.name()}':\n{x.desc()}") if isinstance(x, Func) else help(x)),
    }


    #printing_vars = vars.copy()
    #try: printing_vars.pop('__builtins__')
    #except KeyError: pass
    #print(printing_vars)

    ln = 0
    scheduled_ln: list[tuple[int, int, int]] = []
    while ln < len(lines):
        #print(ln, scheduled_ln)
        if len(scheduled_ln):
            if ln == scheduled_ln[-1][1]:
                ln = scheduled_ln[-1][2]
                scheduled_ln.pop()
                continue
        l = lines[ln]
        if not l: ln += 1; continue
        #print(l)
        line_res, err = evaluate(vars, funcs, l, lines, used_stack, ln+1)
        if err:
            match err.type():
                case 'LineJump':
                    _, new_ln = err.ln()
                    ln = new_ln - 1
                    rm = []
                    for i, sln in enumerate(scheduled_ln):
                        if sln[0] >= ln: rm.append(i)
                    #print('rm:', rm)
                    rm.reverse()
                    for r in rm: del scheduled_ln[r]
                    continue
                case 'ScheduledLineJump':
                    orig_ln, jump_at, jump_to = err.ln()
                    scheduled_ln.append((orig_ln, jump_at - 1, jump_to - 1))
                case 'Exit':
                    if return_values: return 1, (vars, funcs)
                    return 1, None
                case 'Return':
                    return 2, (vars, funcs, line_res)
                case 'NoPrint':
                    return -1, None
                case other:
                    print(err.error())
                    return -1, None
        ln += 1
    
    if return_values: return 0, (vars, funcs, None)
    return 0, None



#['()', '[1, 2, 3, 4, 5]', '"AHHHH"', "` wow would you look at that it's a comment"]

#run_code(['Print("Hello, Catdog!")', 'Print(Casefold("ABCD"))', 'lt x = 10', 'lt y = x / 2', 'Print(x, y)', 'Print(Rand(1, 10))', 'Print(IsMain())', 'x = "WHAT"', 'print(x)'])

#run_code(['lt x = 1', 'print("AHHHH")', 'Sleep(1)', 'x = x + 1', 'goto x'])

#run_code(['lt x = "times"', 'Printf("That happened {} {}!\\n", 10, x)'])

#run_code(
#'''lt x = 0
#lt y = 42
#for i = x, y {
#    Println(i)
#}''')

#run_code('''lt x = 14
#if x == 10 {
#    Println("hi!")
#} elseif x == 11 {
#    Println("no thank you")
#} elseif x == 12 {
#    Println("AHHHH")
#} else {
#    Println("go away!")
#}''')

#run_code('''fn TestPrint(str, end = "") {
#    Println(str + end)
#}
#
#TestPrint("Hello!")
#
#TestPrint("Hello", " there.")''')