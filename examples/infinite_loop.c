// Infinite loop test - use this to test the cancel functionality
#include <stdio.h>
#include <unistd.h>

int main() {
    printf("Starting infinite loop...\n");
    printf("Use the Cancel button to stop this!\n");
    fflush(stdout);
    
    int count = 0;
    while (1) {
        count++;
        printf("Loop iteration: %d\n", count);
        fflush(stdout);
        sleep(1);  // Sleep for 1 second each iteration
    }
    
    return 0;
}
