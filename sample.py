import fitz  # PyMuPDF
import re  # Regular expression module

def remove_or_change_special_characters(input_pdf_filename: str, output_txt_filename: str, replacement_char: str = ''):
    """
    Extract text from the given PDF file, remove or replace special characters, and save to a new text file.

    :param input_pdf_filename: The path to the input PDF file.
    :param output_txt_filename: The path to the output text file.
    :param replacement_char: The character to replace special characters (default is empty string to remove).
    """
    try:
        # Open the PDF file
        doc = fitz.open(input_pdf_filename)
        text = ""

        # Loop through each page in the PDF and extract the text
        for page in doc:
            text += page.get_text()

        # Define a pattern to match special characters (e.g., accented characters, symbols, etc.)
        # This pattern can be customized based on the characters you want to target
        pattern = r'[^\x00-\x7F]'  # Matches non-ASCII characters (everything above ASCII range)

        # Replace or remove special characters
        if replacement_char:
            text = re.sub(pattern, replacement_char, text)  # Replace with specified character
        else:
            text = re.sub(pattern, '', text)  # Remove special characters

        # Save the cleaned text to an output file
        with open(output_txt_filename, 'w', encoding='utf-8') as file:
            file.write(text)

        print(f"[+] PDF '{input_pdf_filename}' processed and saved as '{output_txt_filename}'.")

    except Exception as e:
        print(f"[-] An error occurred: {e}")

# Example usage
remove_or_change_special_characters("1.pdf", "output_file.txt", replacement_char=' ')  # Replaces special chars with space
