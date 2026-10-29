#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    char *end = NULL;
    long long limit = strtoll(argv[1], &end, 10);
    if (!end || *end || limit < 0) return 2;

    long long total = 0;
    for (long long number = 1; number <= limit; ++number) total += number;
    printf("%lld\n", total);
    return 0;
}
