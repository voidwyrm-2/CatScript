fn fib_rec(n) {
    if n < 2 {
        return n
    }
    return fib_rec(n - 1) + fib_rec(n - 2)
}

if IsMain() {
    fib_rec(10)
}