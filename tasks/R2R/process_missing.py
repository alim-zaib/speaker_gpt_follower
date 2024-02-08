import argparse
import json
import requests
import os
import time
import logging
import concurrent.futures

from reformat_instructions import format_instruction

# Setup basic logging
logging.basicConfig(filename='missing_processing.log', level=logging.INFO,
                    format='%(asctime)s | %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def call_chatgpt(prompt, api_key, max_retries=3):
    """
    Function to call the ChatGPT API with retries.
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo-instruct',
        'prompt': prompt,
        'max_tokens': 100
    }
    for _ in range(max_retries):
        response = requests.post('https://api.openai.com/v1/completions',
                                 headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['text'].strip()
        else:
            logging.warning(f'Retry due to API error: {response.text}')
            time.sleep(2)  # Wait before retrying
    raise Exception(f'Failed after {max_retries} retries.')

def refine_instruction(instruction, api_key):
    """
    Refine a single instruction using ChatGPT and format it.
    """
    if instruction.strip():  # Only process non-empty instructions
        # THE PROMPT!!!
        prompt = f"Refine this instruction: {instruction}"
        refined_instruction = call_chatgpt(prompt, api_key)
        return format_instruction(refined_instruction)
    else:
        return instruction  # Return as-is if empty

def process_instruction(item, api_key):
    """
    Refine instructions for a single item using ChatGPT.
    """
    # Assuming each item has 'instructions' as a list of strings.
    for i, original_instruction in enumerate(item['instructions']):
        if original_instruction:
            refined_instruction = refine_instruction(original_instruction, api_key)
            item['instructions'][i] = refined_instruction
    return item

def process_batch(data, api_key, max_workers=10):
    processed_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_instruction, item, api_key) for item in data]
        for future in concurrent.futures.as_completed(futures):
            try:
                processed_item = future.result()
                processed_items.append(processed_item)
                logging.info(f'Item processed: {processed_item.get("path_id", "Unknown ID")}')
            except Exception as exc:
                logging.error(f'Processing error: {exc}')
    return processed_items

def process_missing_items(input_file, output_file, api_key, missing_path_ids):
    with open(input_file, 'r') as file:
        data = json.load(file)

    items_to_process = [item for item in data if item['path_id'] in missing_path_ids]

    processed_items = process_batch(items_to_process, api_key)

    with open(output_file, 'w') as file:
        json.dump(processed_items, file, indent=4)
    logging.info(f'Processed items saved to {output_file}')

def main():
    parser = argparse.ArgumentParser(description="Refine missing instructions with ChatGPT.")
    parser.add_argument('input_file', type=str, help='Input JSON file path')
    parser.add_argument('output_file', type=str, help='Output JSON file path')
    args = parser.parse_args()

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not set in environment variables")

    # Load the missing path_ids
    with open('missing_path_ids.json', 'r') as file:
        missing_path_ids = json.load(file)

    logging.info("Starting processing of missing items.")
    start_time = time.time()

    process_missing_items(args.input_file, args.output_file, api_key, missing_path_ids)

    elapsed_time = time.time() - start_time
    print(f"Processing complete. It took {elapsed_time:.2f} seconds.")
    logging.info(f"Processing complete. It took {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()