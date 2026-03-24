#include <stdio.h>
#include <stdlib.h>

long read_int(void) {
    long value = 0;
    if (scanf("%ld", &value) != 1) {
        fprintf(stderr, "failed to read integer\n");
        exit(1);
    }
    return value;
}

void print_int(long value) {
    printf("%ld\n", value);
}
