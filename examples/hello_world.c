#include <stdio.h>
#include <string.h>

int main() {
    printf("Hello, World from C!\n");
    printf("===================\n\n");
    
    // Variables and basic operations
    int a = 10, b = 5;
    printf("Numbers: a = %d, b = %d\n", a, b);
    printf("a + b = %d\n", a + b);
    printf("a - b = %d\n", a - b);
    printf("a * b = %d\n", a * b);
    printf("a / b = %d\n", a / b);
    
    // String operations
    char greeting[] = "Welcome to C programming!";
    printf("\nString: %s\n", greeting);
    printf("String length: %zu\n", strlen(greeting));
    
    // Character array
    char name[] = "C Language";
    printf("Programming language: %s\n", name);
    
    return 0;
}
