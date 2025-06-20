#include <stdio.h>

#define MAX 100

int fibonacci(int n, int *fib) {
    int i;
    for (i = 2; i <= n; i++) {
        fib[i] = fib[i - 1] + fib[i - 2];
    }
    return fib[n];
}

int main(int argc, char *argv[]) {

    int fib[MAX], i, result = 0, n;
    char exit = '\0';

    fib[0] = 0;
    fib[1] = 1;

    do {
        printf("Enter the value of n: ");
        scanf("%d", &n);
    
        if (n < 0 || n >= MAX) {
            printf("Please enter a value between 0 and %d\n", MAX - 1);
        }else {
            result = fibonacci(n, fib);
            printf("Fibonacci number at position %d is %d\n", n, result);
        }

        printf("If you want to quit, press q: ");
        scanf("%c", &exit);

    }while(exit != 'q');

    return 0;
}