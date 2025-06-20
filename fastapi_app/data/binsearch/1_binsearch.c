#include <stdio.h>
#include <stdlib.h>

//1 2 3 4 {5} 6 7 8 9 10
typedef struct {
    int *arr;
    int tam;
    int i_mid;
} list;

int bin_search(list *l, int elem) {
    int pivot = 0;
    int index = 0;
    // Control de parámetros
    if (l->arr == NULL || l->tam == 0) {
        return -1;
    }

    index = l->i_mid;
    pivot = l->arr[index];
    printf("Index = %d\n", index);
    printf("Pivot = %d\n", pivot);
    l->tam /= 2;
    // Caso Base
    if (pivot == elem) {
        return index;
    }else if (elem < pivot) {
        l->i_mid /= 2;
        index = bin_search(l, elem);
    }else {
        l->i_mid *= 2;
        index = bin_search(l, elem);
    }
}

int main() {
    int arr[10] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int tam = 10;
    int i_mid = 4, elem = 3;
    list *l;

    if ((l = malloc(sizeof(list))) == NULL) {
        return -1;
    }
    l->arr = arr; l->tam = tam; l->i_mid = i_mid;
    
    printf("El elemento %d se encuentra en la posición %d del array\n", elem, bin_search(l, elem));

    free(l);
    return 0;
}