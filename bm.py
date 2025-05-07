import random
from collections import OrderedDict
import time
import os

class MobileNumberGenerator:
    def __init__(self):
        self.generated_numbers = OrderedDict()
        self.default_filename = "mobile_numbers.txt"
    
    def generate_number(self, pattern):
        """
        Generate a mobile number based on the pattern
        Pattern example: "+91976^^^^^^" where ^ represents a random digit
        """
        number = []
        for char in pattern:
            if char == '^':
                number.append(str(random.randint(0, 9)))
            else:
                number.append(char)
        return ''.join(number)
    
    def generate_unique_numbers(self, pattern, count, filename=None):
        """
        Generate unique mobile numbers and save to file
        """
        if filename is None:
            filename = self.default_filename
        
        if '^' not in pattern:
            print("Pattern must contain '^' symbols for random digits")
            return
        
        # Calculate total possible unique numbers for this pattern
        digits_needed = pattern.count('^')
        total_possible = 10 ** digits_needed
        
        if count > total_possible:
            print(f"Warning: Only {total_possible} unique combinations possible for this pattern")
            count = total_possible
        
        start_time = time.time()
        generated = 0
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'a') as file:  # Append mode to avoid overwriting
            while generated < count:
                num = self.generate_number(pattern)
                if num not in self.generated_numbers:
                    self.generated_numbers[num] = True
                    file.write(num + '\n')
                    generated += 1
                    
                    # Progress reporting
                    if generated % 1000 == 0:
                        print(f"Generated {generated}/{count} numbers for pattern {pattern}...")
        
        end_time = time.time()
        print(f"\nSuccessfully generated {generated} unique numbers for pattern {pattern}")
        print(f"Time taken: {end_time-start_time:.2f} seconds")
        print(f"Saved to {filename}\n")

def display_banner():
    print("\n" + "="*50)
    print("MOBILE NUMBER GENERATOR BOT".center(50))
    print("="*50)
    print("\nCommands:")
    print("/gen +91976^^^^^^ 1000 - Generate 1000 numbers starting with +91976")
    print("/gen +91754^^^^^^ 500  - Generate 500 numbers starting with +91754")
    print("/list                 - Show all generated patterns and counts")
    print("/clear                - Clear all generated numbers from memory")
    print("/exit                 - Exit the program")
    print("\nNote: Each '^' in pattern will be replaced with random digit")
    print("Example: +91976^^^^^^ creates 10-digit numbers (+91976 + 5 random digits)\n")

def main():
    generator = MobileNumberGenerator()
    display_banner()
    
    while True:
        user_input = input("\nEnter command: ").strip()
        
        if user_input.lower() == 'exit':
            print("Exiting Mobile Number Generator Bot...")
            break
        
        elif user_input.lower() == '/list':
            print("\nGenerated Numbers Summary:")
            if not generator.generated_numbers:
                print("No numbers generated yet")
            else:
                patterns = {}
                for num in generator.generated_numbers:
                    prefix = num[:7]  # Get the base pattern (+91976 or +91754 etc.)
                    patterns[prefix] = patterns.get(prefix, 0) + 1
                
                for pattern, count in patterns.items():
                    print(f"{pattern}******: {count} numbers")
            continue
        
        elif user_input.lower() == '/clear':
            generator.generated_numbers.clear()
            print("All generated numbers cleared from memory (file remains unchanged)")
            continue
        
        elif user_input.startswith('/gen'):
            try:
                parts = user_input.split()
                if len(parts) != 3:
                    raise ValueError
                
                pattern = parts[1]
                count = int(parts[2])
                
                if count <= 0:
                    print("Count must be positive")
                    continue
                
                # Validate pattern
                if not pattern.startswith('+') or '^' not in pattern:
                    print("Invalid pattern. Must start with '+' and contain '^' for random digits")
                    continue
                
                # For 10-digit Indian numbers (including +91)
                if len(pattern.replace('^', '0')) != 12 or pattern.count('^') != 10 - (len(pattern) - pattern.count('^') - 3):
                    print("Note: Pattern should result in 10-digit Indian numbers (+91 followed by 10 digits)")
                
                generator.generate_unique_numbers(pattern, count)
                
            except (IndexError, ValueError):
                print("Invalid command format. Use: /gen +91976^^^^^^ 1000")
        else:
            print("Unknown command. Type '/help' for available commands")

if __name__ == "__main__":
    main()
