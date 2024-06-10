from typing import Any
from random import randint
import pb_funcs



class Error:
    def __init__(self, _type: str | None = None, details: str | None = None, ln: int | None = None) -> None:
        self.__type: str = _type if _type else 'Error'
        self.__details: str = details
        self.__ln: int | None = ln
    
    def type(self) -> str: return self.__type

    def error(self) -> str:
        err = str(self.__type)
        if self.__ln: err += f" on line {self.__ln}"
        if self.__details: err += f": {self.__details}"
        return err
    
    def __repr__(self) -> str: return self.error()



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


class DoNotPrint: pass
def evaluate(vars: dict[str, Any], funcs: dict[str, tuple[bool, Func | Any]], input: str, ln: int) -> tuple[Any, Error | None]:
    #print(funcs)
    #print([f + '(' for f in list(funcs)])
    #print(f"'{input}'")
    if input.startswith(tuple([f + '(' for f in list(funcs)])) and input.endswith(')'):
        s_in = input.removesuffix(')').split('(', 1)
        op_count = s_in[1].count('(')
        cl_count = s_in[1].count(')')
        
        if op_count > cl_count:
            s_in[1] += (')' * (op_count - cl_count))
        elif op_count < cl_count:
            s_in[1] = ('(' * (cl_count - op_count)) + s_in[1]
            
        if s_in[1].strip() != '':
            func_inputs, err = evaluate(vars, funcs, s_in[1].strip(), ln)
        else: func_inputs, err = [], None
        if err: return None, err
        
        if funcs[s_in[0]][0]:
            try:
                if not isinstance(func_inputs, (list, tuple, set, dict)): func_inputs = [func_inputs]
                #print(f"finp: '{func_inputs}'")
                return funcs[s_in[0]][1](ln, *func_inputs)
            except Exception as e:
                return None, Error('FuncError', e, ln)
        else:
            return funcs[s_in[0]][1].run(func_inputs, ln)
        #return DoNotPrint(), None

    elif input.startswith('lt ') and '=' in input:
        varname, val = input.removeprefix('lt ').split('=', 1)
        varname = varname.strip()
        if varname in list(vars): return None, Error('VariableError', f"cannot create variable '{varname}', already exists", ln)
        c_val, err = evaluate(vars, funcs, val.strip(), ln)
        if err: return err
        vars[varname] = c_val
        return DoNotPrint(), None

    elif input.startswith(tuple([v + '=' for v in list(vars)]) + tuple([v + ' =' for v in list(vars)])):
        varname, val = input.split('=', 1)
        varname = varname.strip()
        if varname not in list(vars): return None, Error('VariableError', f"cannot reassign variable '{varname}', doesn't exists", ln)
        c_val, err = evaluate(vars, funcs, val.strip(), ln)
        if err: return err
        vars[varname] = c_val
        return DoNotPrint(), None

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

    if_to_end: dict[int, tuple[bool, bool, int]] = {}
    if_to_elseifs: dict[int, list[int]] = {}
    if_to_else: dict[int, int] = {}
    else_to_end: dict[int, int] = {}

    for_to_end: dict[int, int] = {}
    end_to_for: dict[int, int] = {}

    func_to_end: dict[int, int] = {}
    end_to_func: dict[int, int] = {}

    ifstack = []
    elseifstack = []
    elsestack = []
    forstack = []
    funcstack = []
    latest = None
    for n, l in enumerate(lines):
        if l.startswith('if ') and l.endswith('{'):
            ifstack.append([n, 0, False])
            latest = 'if'
        elif l.startswith('} elseif ') and l.endswith('{'):
            if latest != 'if': print(Error('SyntaxError', "unexpected 'elseif'", ln).error()); return
            ifstack[-1][1].append(n)
        elif l == '} else {':
            if latest != 'if': print(Error('SyntaxError', "unexpected 'else'", ln).error()); return
            ifstack[-1][2] = True
        elif l.startswith('for ') and l.endswith('{'):
            forstack.append(n)
            latest = 'for'
        elif l.startswith('fn ') and l.endswith('{'):
            funcstack.append(n)
            latest = 'func'
        elif l == '}':
            if latest == 'for':
                f = forstack.pop()
                for_to_end[f] = n
                end_to_for[n] = f
            elif latest == 'func':
                f = funcstack.pop()
                func_to_end[f] = n
                end_to_func[n] = f
            elif len(ifstack):
                fn, elseifs, el = ifstack.pop()
                if_to_end[fn] = bool(len(elseifs)), el, n
                if_to_elseifs[fn] = elseifs
            else:
                print(Error('SyntaxError', "unexpected '}'", ln).error()); return


    vars: dict[str, Any] = {}

    # if `True`, then it should be run like a python function, otherwise use `.run()`
    funcs: dict[str, tuple[bool, Func | Any]] = {
        'Print': (True, lambda ln, *x: (print(*x), None)),

        'GetText': (True, lambda ln, message: (input(message), None)),

        'Casefold': (True, lambda ln, value: (value.casefold(), None) if isinstance(value, str) else (None, Error('ValueError', f"invalid value for Casefold '{value}', expected string", ln)) ),

        'Rand': (True, lambda ln, min, max: ((randint(min, max), None) if min <= max else (None, Error('ValueError', f"arg 'min' cannot be higher than arg 'max' of Rand", ln))) if isinstance(min, int) and isinstance(max, int) else (None, Error('ValueError', f"invalid value '{min}' for arg 'min' of Rand, expected int", ln)) if not isinstance(min, int) and isinstance(max, int) else (None, Error('ValueError', f"invalid value '{max}' for arg 'max' of Rand, expected int", ln)) if isinstance(min, int) and not isinstance(max, int) else (None, Error('ValueError', f"invalid value '{min}' for arg 'min' and '{max}' for arg 'max' of Rand, expected int and int", ln))),

        'IsMain': (True, lambda ln: (not len(used_stack), None))
    }

    ln = 0
    while ln < len(lines):
        l = lines[ln].split('`', 1)[0].strip() if '`' in lines[ln] else lines[ln]
        if not l: ln += 1; continue
        _, err = evaluate(vars, funcs, l, ln+1)
        if err: print(err.error()); return -1, None
        ln += 1
    
    if return_values: return 0, vars, funcs
    return 0, None



#['()', '[1, 2, 3, 4, 5]', '"AHHHH"', "` wow would you look at that it's a comment"]

#run_code(['Print("Hello, Catdog!")', 'Print(Casefold("ABCD"))', 'lt x = 10', 'lt y = x / 2', 'Print(x, y)', 'Print(Rand(1, 10))', 'Print(IsMain())', 'x = "WHAT"', 'print(x)'])
