import json
import argparse

def format_instruction(instruction):
    """
    Format the instruction to match the dataset's punctuation spacing and remove escaped characters.
    """
    instruction = instruction.lower()  # Convert to lowercase
    instruction = instruction.replace('.', ' . ')  # Space before and after period
    instruction = instruction.replace(',', ' , ')  # Space before and after comma
    instruction = ' '.join(instruction.split())  # Remove extra spaces
    instruction = instruction.replace('\\', '')  # Remove backslashes used for escaping
    return instruction.strip('"')  # Remove leading and trailing quotes

def reformat_instructions(file_path):
    """
    Read the JSON file, reformat the instructions, and overwrite the same file.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)

    for item in data:
        item['instructions'] = [format_instruction(instr) for instr in item['instructions']]

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Reformat R2R dataset instructions.")
    parser.add_argument('file_path', type=str, help='JSON file path to reformat in place')
    args = parser.parse_args()

    reformat_instructions(args.file_path)

if __name__ == "__main__":
    main()
