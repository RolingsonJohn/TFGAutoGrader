#include <stdio.h>
#include <stdlib.h>


int fibonacci(int n, int prev_1, int prev_2) {
    int next_num = prev_1 + prev_2;
    if (n < 3)
        return 0;
    
    printf("%d ", next_num);
    return fibonacci(n - 1, prev_2, next_num);
}

int main(int argc, char *argv[]) {
    int rounds = 0;

    printf("Introduzca el número de rondas de fibonacci: ");
    scanf("%d", &rounds);

    printf("0 1 1");
    fibonacci(rounds, 1, 1);
    printf("\n");

    return 0;

}