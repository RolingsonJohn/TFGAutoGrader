#include <stdio.h>

/**
 * Recursive function to print the fibonacci series
 * @param n: fibonacci's number to print
 * @param prev_1: first previous number of the sequence
 * @param prev_2: second previous number of the sequence
 * 
 */
void fib(int n, int prev1, int prev2) {
    // Caso base
    if (n < 3) {
        return;
    }
    
    int curr = prev1 + prev2;
    printf("%d ", curr);
  
    return fib(n - 1, prev2, curr);
}

/**
 * Function that prints the fibonacci's number
 * @param n: fibonacci's numbers to print
 */
void printFib(int n) {
    //Control de parametro
    if (n < 1)
        printf("Invalid number of terms\n");
    else if (n == 1)
        printf("%d ", 0);
    else if (n == 2)
        printf("%d %d", 0, 1);
    else {
        printf("%d %d ", 0, 1);
        fib(n, 0, 1);
    }

    return;
}

int main() {
    int n = 0;
    printf("Introduzca el número de rondas de fibonacci: ");
    if (scanf("%d", &n) != -1) 
        printFib(n);

    return 0;
}
