#include <iostream>
#include <iomanip>

class Calculator {
private:
    double num1, num2;

public:
    Calculator(double a, double b) : num1(a), num2(b) {}
    
    double add() { return num1 + num2; }
    double subtract() { return num1 - num2; }
    double multiply() { return num1 * num2; }
    
    double divide() {
        if (num2 != 0) {
            return num1 / num2;
        } else {
            std::cout << "Error: Division by zero!" << std::endl;
            return 0.0;
        }
    }
    
    void displayResults() {
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Numbers: " << num1 << " and " << num2 << std::endl << std::endl;
        std::cout << "Addition: " << num1 << " + " << num2 << " = " << add() << std::endl;
        std::cout << "Subtraction: " << num1 << " - " << num2 << " = " << subtract() << std::endl;
        std::cout << "Multiplication: " << num1 << " * " << num2 << " = " << multiply() << std::endl;
        std::cout << "Division: " << num1 << " / " << num2 << " = " << divide() << std::endl;
    }
};

int main() {
    std::cout << "Object-Oriented Calculator in C++" << std::endl;
    std::cout << "==================================" << std::endl << std::endl;
    
    Calculator calc(15.5, 4.2);
    calc.displayResults();
    
    std::cout << std::endl << "Testing division by zero:" << std::endl;
    Calculator calc2(10.0, 0.0);
    std::cout << "Result: " << calc2.divide() << std::endl;
    
    return 0;
}
