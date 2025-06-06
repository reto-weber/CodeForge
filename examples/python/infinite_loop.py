# Infinite loop test - use this to test the cancel functionality
import time

print("Starting infinite loop...")
print("Use the Cancel button to stop this!")

count = 0
while True:
    count += 1
    print(f"Loop iteration: {count}")
    time.sleep(1)  # Sleep for 1 second each iteration
