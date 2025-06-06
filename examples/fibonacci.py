# Fibonacci Sequence Generator
def fibonacci(n):
    """Generate Fibonacci sequence up to n terms"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence

# Generate and display Fibonacci sequence
n_terms = 10
print(f"Fibonacci sequence with {n_terms} terms:")
fib_sequence = fibonacci(n_terms)

for i, num in enumerate(fib_sequence):
    print(f"F({i}) = {num}")

print(f"\nThe sequence: {fib_sequence}")

# Calculate the golden ratio approximation
if len(fib_sequence) > 1:
    golden_ratio = fib_sequence[-1] / fib_sequence[-2]
    print(f"Golden ratio approximation: {golden_ratio:.6f}")
