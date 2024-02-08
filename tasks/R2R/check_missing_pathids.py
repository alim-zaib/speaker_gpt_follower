import json

# Load the final combined JSON file
with open('final_combined_output.json', 'r') as file:
    data = json.load(file)

# Extract the list of path_ids from the data
path_ids = [item['path_id'] for item in data]

# Specify the range of path_ids you expect
start_id = 1000000
end_id = 1178299

# Find the missing path_ids
missing_path_ids = [path_id for path_id in range(start_id, end_id + 1) if path_id not in path_ids]

# Check if there are missing path_ids and print the appropriate message
if missing_path_ids:
    print("Missing path_ids:", missing_path_ids)
    # Save the missing path_ids to a JSON file
    with open('missing_path_ids.json', 'w') as outfile:
        json.dump(missing_path_ids, outfile, indent=4)
    print("Missing path_ids saved to missing_path_ids.json")
else:
    print("No missing path_ids found. The dataset is complete.")

# Function to check if path_ids are in chronological order
def check_chronological_order(path_ids):
    out_of_order_indices = []
    for i in range(len(path_ids) - 1):
        if path_ids[i] > path_ids[i + 1]:
            out_of_order_indices.append((i, path_ids[i], path_ids[i + 1]))
    return out_of_order_indices

# Check chronological order and print detailed information if not
out_of_order = check_chronological_order(path_ids)
if not out_of_order:
    print("Path IDs are in chronological order.")
else:
    print("Path IDs are NOT in chronological order. Please check the dataset at the following indices and path_ids:")
    for index, current_id, next_id in out_of_order:
        print(f"Index {index}: {current_id} followed by {next_id}")

