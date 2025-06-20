#include <stdio.h>

typedef unsigned long long F;

F fibonacci(F n);

int main()
{
    int n, i, j;

    printf("--- Fibonacci series program ---\n");
    printf("Enter a number:");
    scanf("%d",&n);

    printf("\nFibonacci series:\n");
    j = 0;
    for ( i = 1 ; i <= n ; i++ )
    {
        printf("%d ", fibonacci(j));
        j++;
    }
}

F fibonacci(F n)
{
    int i;
    F f1 = 0;
    F f2 = 1;
    F fi;

    if(n == 0)
        return 0;
    if(n == 1)
        return 1;

    for(i = 2 ; i <= n ; i++ )
    {
        fi = f1 + f2;
        f1 = f2;
        f2 = fi;
    }
    return fi;
}