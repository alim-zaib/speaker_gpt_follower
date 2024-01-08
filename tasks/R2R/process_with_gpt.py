import argparse
import json
import requests
import os

def call_chatgpt(prompt, api_key):
    """
    Function to call the ChatGPT API.
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo-instruct',  # Specify the model
        'prompt': prompt,
        'max_tokens': 100  # Adjust as needed
    }
    # Ensure the endpoint matches the model you're using
    response = requests.post('https://api.openai.com/v1/completions', 
                             headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()
    else:
        response_text = response.text  # Get the detailed error message
        raise Exception(f'ChatGPT API request failed with status code {response.status_code}, response: {response_text}')

def format_instruction(instruction):
    """
    Format the instruction to lowercase and adjust punctuation spacing to match the dataset,
    and remove escaped characters.
    """
    # Convert to lowercase
    instruction = instruction.lower()

    # Replace periods and commas to have space on both sides
    instruction = instruction.replace('.', ' . ')
    instruction = instruction.replace(',', ' , ')

    # Remove backslashes used for escaping and strip quotes
    instruction = instruction.replace('\\', '')

    # Remove any extra spaces, including potential double spaces from the replacements
    instruction = ' '.join(instruction.split())

    return instruction.strip('"')



def refine_instruction(instruction, api_key):
    """
    Refine a single instruction using ChatGPT and format it.
    """
    if instruction.strip():  # Only process non-empty instructions
        prompt = f"Refine this instruction: {instruction}"
        refined_instruction = call_chatgpt(prompt, api_key)
        return format_instruction(refined_instruction)
    else:
        return instruction  # Return as-is if empty

def process_file(input_file, output_file, api_key, num_items=100):
    """
    Process the input file with ChatGPT to refine instructions and save the output.
    """
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Process the first `num_items` items
    for item in data[:num_items]:
        for i, original_instruction in enumerate(item['instructions']):
            if original_instruction:
                refined_instruction = refine_instruction(original_instruction, api_key)
                item['instructions'][i] = refined_instruction

    # Save the output for the processed items
    with open(output_file, 'w') as file:
        json.dump(data[:num_items], file, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Process R2R data augmentation with ChatGPT.")
    parser.add_argument('input_file', type=str, help='Input JSON file path')
    parser.add_argument('output_file', type=str, help='Output JSON file path')
    args = parser.parse_args()

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not set in environment variables")

    process_file(args.input_file, args.output_file, api_key)

if __name__ == "__main__":
    main()
