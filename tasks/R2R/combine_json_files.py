import json
import glob

# This file only needs to be used if instructions were processed in batches.

def combine_json_files(input_pattern, output_file):
    """
    Combines multiple JSON files into a single JSON file. 

    :param input_pattern: Glob pattern to match the input files.
    :param output_file: Path for the combined output JSON file.
    """
    combined_data = []
    
    # Use glob to find all files matching the input pattern
    for file_name in sorted(glob.glob(input_pattern)):
        with open(file_name, 'r') as file:
            data = json.load(file)
            combined_data.extend(data)
    
    with open(output_file, 'w') as file:
        json.dump(combined_data, file, indent=4)
    
    print(f"Combined JSON saved to {output_file}")


if __name__ == "__main__":
    input_pattern = '/home/alim/Desktop/speaker_gpt_follower/batch[0-9]*_[0-9]*_[0-9]*.json'  
    output_file = '/home/alim/Desktop/speaker_gpt_follower/combined_output.json'  
    combine_json_files(input_pattern, output_file)

