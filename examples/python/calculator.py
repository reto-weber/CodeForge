# Simple Calculator Example
def add(x, y):
    return x + y


def subtract(x, y):
    return x - y


def multiply(x, y):
    return x * y


def divide(x, y):
    if y != 0:
        return x / y
    else:
        return "Error: Division by zero!"


# Test the calculator
print("Simple Calculator")
print("=================")

num1 = 15
num2 = 4

print(f"Numbers: {num1} and {num2}")
print(f"Addition: {num1} + {num2} = {add(num1, num2)}")
print(f"Subtraction: {num1} - {num2} = {subtract(num1, num2)}")
print(f"Multiplication: {num1} * {num2} = {multiply(num1, num2)}")
print(f"Division: {num1} / {num2} = {divide(num1, num2)}")

# Test division by zero
print(f"Division by zero: {divide(num1, 0)}")
