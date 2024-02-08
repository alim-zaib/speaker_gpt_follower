import json

def merge_and_sort(original_file, missing_file, output_file):
    # Load the original combined output
    with open(original_file, 'r') as file:
        original_data = json.load(file)
    
    # Load the missing objects
    with open(missing_file, 'r') as file:
        missing_data = json.load(file)
    
    # Combine the two datasets
    combined_data = original_data + missing_data
    
    # Sort the combined dataset by path_id
    combined_data_sorted = sorted(combined_data, key=lambda x: x['path_id'])
    
    # Save the sorted combined dataset
    with open(output_file, 'w') as file:
        json.dump(combined_data_sorted, file, indent=4)

    print(f"Data merged and sorted. Output saved to {output_file}")

if __name__ == "__main__":
    original_file = 'combined_output.json'
    missing_file = 'missing_objects.json'
    output_file = 'final_combined_output.json'
    
    merge_and_sort(original_file, missing_file, output_file)
