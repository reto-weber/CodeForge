#include <stdio.h>

// Function prototypes
int add(int x, int y);
int subtract(int x, int y);
int multiply(int x, int y);
float divide(int x, int y);

int main() {
    printf("Simple Calculator in C\n");
    printf("=====================\n\n");
    
    int num1 = 15;
    int num2 = 4;
    
    printf("Numbers: %d and %d\n\n", num1, num2);
    
    printf("Addition: %d + %d = %d\n", num1, num2, add(num1, num2));
    printf("Subtraction: %d - %d = %d\n", num1, num2, subtract(num1, num2));
    printf("Multiplication: %d * %d = %d\n", num1, num2, multiply(num1, num2));
    printf("Division: %d / %d = %.2f\n", num1, num2, divide(num1, num2));
    
    // Test division by zero
    printf("Division by zero: %d / %d = %.2f\n", num1, 0, divide(num1, 0));
    
    return 0;
}

// Function implementations
int add(int x, int y) {
    return x + y;
}

int subtract(int x, int y) {
    return x - y;
}

int multiply(int x, int y) {
    return x * y;
}

float divide(int x, int y) {
    if (y != 0) {
        return (float)x / y;
    } else {
        printf("Error: Division by zero!\n");
        return 0.0;
    }
}
