from interpreter import run_code
import os



def showhelp():
    print("'exit/quit': exits the program")
    print("'help': shows this message")
    print("'run [file path]': runs the given file")


def main(extension: str = '.cat'):
    while True:
        inp = input('> ').strip()
        if inp.casefold() in ('exit', 'quit'):
            break
        elif inp.casefold() == 'help':
            showhelp()
        elif inp.startswith('run '):
            f = inp.removeprefix('run ').strip()
            sf = list(os.path.splitext(f))
            if sf[-1] == '':
                f += extension
                sf[-1] = extension
            if not os.path.exists(f):
                print(f"path '{f}' does not exist")
                continue
            elif not os.path.isfile(f):
                print(f"path '{f}' is not a file")
                continue
            elif sf[-1].casefold() != extension:
                print(f"file '{f}' is not a CatScript file")
                continue
            with open(f, 'rt') as fi:
                content = fi.read()
            run_code(content)



if __name__ == '__main__':
    main()
