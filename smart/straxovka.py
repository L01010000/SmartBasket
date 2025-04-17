books = [
    ("Thus Spoke Zarathustra", "9785389085015", 2500),
    ("Lolita", "9780241996492", 3400),
    ("120 Days of Sodom", "9785171119577", 2700),
    ("Critique of Practical Reason", "9785171157012", 1900),
    ("Metamorphosis", "9785171013110", 3800)
]

def get_book_by_index(index):
    if 1 <= index <= len(books):
        book = books[index - 1]  # Adjust for 0-based indexing
        return f"{index} - {book[0]}"
    else:
        return "Invalid index. Please enter a number between 1 and 5."

# Main loop
while True:
    try:
        user_input = int(input("Enter a number (1-5): "))
        print(get_book_by_index(user_input))
    except ValueError:
        print("Please enter a valid integer.")
