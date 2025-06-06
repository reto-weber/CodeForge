public class Calculator {
    private double num1, num2;

    public Calculator(double a, double b) {
        this.num1 = a;
        this.num2 = b;
    }

    public double add() {
        return num1 + num2;
    }

    public double subtract() {
        return num1 - num2;
    }

    public double multiply() {
        return num1 * num2;
    }

    public double divide() {
        if (num2 != 0) {
            return num1 / num2;
        } else {
            System.out.println("Error: Division by zero!");
            return 0.0;
        }
    }

    public void displayResults() {
        System.out.printf("Numbers: %.2f and %.2f%n%n", num1, num2);
        System.out.printf("Addition: %.2f + %.2f = %.2f%n", num1, num2, add());
        System.out.printf("Subtraction: %.2f - %.2f = %.2f%n", num1, num2, subtract());
        System.out.printf("Multiplication: %.2f * %.2f = %.2f%n", num1, num2, multiply());
        System.out.printf("Division: %.2f / %.2f = %.2f%n", num1, num2, divide());
    }

    public static void main(String[] args) {
        System.out.println("Object-Oriented Calculator in Java");
        System.out.println("==================================");
        System.out.println();

        Calculator calc = new Calculator(15.5, 4.2);
        calc.displayResults();

        System.out.println("\nTesting division by zero:");
        Calculator calc2 = new Calculator(10.0, 0.0);
        System.out.printf("Result: %.2f%n", calc2.divide());
    }
}
