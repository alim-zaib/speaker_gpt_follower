## Script Overview

In this section, we'll go over the custom scripts created specifically for this project. These scripts are essential for improving the navigation guidance and handling the dataset. Each script serves a purpose in the project's workflow, starting from data organisation to final instruction fine-tuning and dataset creation.

### Scripts

- `reformat_instructions.py`: Reformats instructions refined by GPT into a format suitable for the follower model.
- `process_with_gpt.py`: Processes instructions using the OpenAI API. This script allows the setting of the model and specific prompts. It also utilizes concurrent futures/multithreading to speed up the process, enabling batch processing.
- `merge_and_sort.py`: Merges and sorts specified batches/datasets to ensure all instructions are included in the dataset and are in the correct order, as multithreading can affect sequencing.
- `combine_json_files.py`: Combines dataset batches into a single file.
- `check_missing_pathids.py`: Checks that all path IDs/objects have been processed and are included in the refined dataset.

### Generated Dataset

The mentioned scripts have been used to produce a dataset labelled `R2R_GPT_enhanced_speaker_data_paths.json` located in `tasks/R2R/data`. This dataset contains navigation instructions that have been enhanced using GPT models to enhance clarity and precision. The structure of this dataset is crucial for evaluating how instruction refinement impacts navigation performance in VLN scenarios.

### Evaluation of the Follower Model Using Refined Instructions

With the `R2R_GPT_enhanced_speaker_data_paths.json` dataset now generated, the focus shifts to evaluating the follower model's performance. Guided by the GPT-refined instructions, its effectiveness is set to be assessed in comparison to its operation with the original instructions. This critical analysis seeks to underscore the enhancements in navigation accuracy and efficiency within VLN scenarios, demonstrating the value added by refining instructions through GPT models.
