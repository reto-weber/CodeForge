#include <iostream>
#include <string>
#include <vector>

int main() {
    std::cout << "Hello, World from C++!" << std::endl;
    std::cout << "======================" << std::endl << std::endl;
    
    // Variables and basic operations
    int a = 10, b = 5;
    std::cout << "Numbers: a = " << a << ", b = " << b << std::endl;
    std::cout << "a + b = " << (a + b) << std::endl;
    std::cout << "a - b = " << (a - b) << std::endl;
    std::cout << "a * b = " << (a * b) << std::endl;
    std::cout << "a / b = " << (a / b) << std::endl;
    
    // String operations
    std::string greeting = "Welcome to C++ programming!";
    std::cout << "\nString: " << greeting << std::endl;
    std::cout << "String length: " << greeting.length() << std::endl;
    
    // Vector demonstration
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    std::cout << "\nVector contents: ";
    for (int num : numbers) {
        std::cout << num << " ";
    }
    std::cout << std::endl;
    
    return 0;
}
