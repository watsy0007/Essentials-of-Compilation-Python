#include <inttypes.h>
#include <stdlib.h>
#include <stdio.h>
#include "runtime.h"

// print an integer to stdout
void print_int(int64_t x) {
  printf("%" PRId64, x);
}
