fn fib_loop(n) {
    lt a = 0
    lt b = 1
    lt c = 0
    for i = 0, n {
        print(a)
        c = a + b
        b = a
        a = c
    }
}


fib_loop(10)