import argparse
import json
import requests
import os
import time
import logging
import concurrent.futures

from reformat_instructions import format_instruction

# Setup basic logging
logging.basicConfig(filename='processing.log', level=logging.INFO,
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
        'model': 'gpt-3.5-turbo-instruct', # !!! MODEL !!!
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
    if instruction.strip():  
        # THE PROMPT!!!
        prompt = f"Refine this instruction: {instruction}"
        refined_instruction = call_chatgpt(prompt, api_key)
        return format_instruction(refined_instruction)
    else:
        return instruction  
    
def process_instruction(item, api_key):
    for j, original_instruction in enumerate(item['instructions']):
        if original_instruction:
            refined_instruction = refine_instruction(original_instruction, api_key)
            item['instructions'][j] = refined_instruction
    return item
    
def process_batch(data, start_index, end_index, api_key, max_workers=10):    # max_workers = amount of threads
    #print(f"Processing items at indices: {list(range(start_index, end_index))}")
    processed_items = [None] * (end_index - start_index)  # Preallocate list with None to maintain order
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(process_instruction, data[i], api_key): i for i in range(start_index, end_index)}
        
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                processed_item = future.result()
                # Calculate relative index to place processed item correctly
                relative_index = index - start_index
                processed_items[relative_index] = processed_item  # Place item in correct order
                logging.info(f'Item processed: {index}')
            except Exception as exc:
                logging.error(f'Item {index} generated an exception: {exc}')
    
    # Filter out None values if any task failed, or ensure all tasks succeeded before this step
    processed_items = [item for item in processed_items if item is not None]
    return processed_items



def process_file(input_file, output_file, api_key, start_index=0, num_items=100, batch_size=100):  # Implemented refinining in batches, optional usage
    #print(f"DEBUG in process_file: Start Index: {start_index}, Num Items: {num_items}, Batch Size: {batch_size}")  # Debugging print
    with open(input_file, 'r') as file:
        data = json.load(file)

    all_processed_items = []  # Collect all processed items if needed

    for current_start in range(start_index, min(start_index + num_items, len(data)), batch_size):
        current_end = min(current_start + batch_size, start_index + num_items, len(data))
        batch_data = process_batch(data, current_start, current_end, api_key)
        
        # Directly use batch_data as it now correctly contains only the processed items for the current batch
        batch_file = f'{output_file}_{current_start}_{current_end}.json'
        with open(batch_file, 'w') as file:
            json.dump(batch_data, file, indent=4)  # Write batch_data directly
        logging.info(f'Saved batch {current_start}-{current_end} to {batch_file}')
        
        all_processed_items.extend(batch_data)  





def main():
    parser = argparse.ArgumentParser(description="Process R2R data augmentation with ChatGPT.")
    parser.add_argument('input_file', type=str, help='Input JSON file path')
    parser.add_argument('output_file', type=str, help='Output JSON file path without extension')
    parser.add_argument('--start_index', type=int, default=0, help='Starting index for processing instructions')
    parser.add_argument('--num_items', type=int, default=100, help='Number of items to process')
    parser.add_argument('--batch_size', type=int, default=100, help='Number of items per batch') # Implemented refinining in batches, optional usage
    args = parser.parse_args()
    
    print(f"DEBUG: Start Index: {args.start_index}, Num Items: {args.num_items}, Batch Size: {args.batch_size}")


    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not set in environment variables")

    logging.info(f'Starting processing from index {args.start_index} for {args.input_file}')
    start_time = time.time()
    try:
        process_file(args.input_file, args.output_file, api_key, args.start_index, args.num_items, args.batch_size)
    except Exception as e:
        logging.exception(f'An error occurred: {e}')
    else:
        elapsed_time = time.time() - start_time
        print(f"Processing complete. It took {elapsed_time:.2f} seconds to refine {args.num_items} instructions.")
        logging.info(f"Processing complete. It took {elapsed_time:.2f} seconds to refine {args.num_items} instructions.")
    finally:
        logging.info('Processing finished.')

if __name__ == "__main__":
    main()
