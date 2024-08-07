# speaker_GPT_follower

## Project Overview

This section of my third-year university project, titled **"Exploring the Versatility of GPT in Vision-and-Language Navigation and in Minecraft,"** investigates how OpenAI's GPT models can enhance navigation instructions generated by the "Speaker Follower Models for Vision and Language Navigation." The goal is to determine if integrating GPT can improve the clarity and effectiveness of these instructions, thereby enhancing the performance of follower models in Vision and Language Navigation (VLN) scenarios.

The project involves experimenting with various GPT prompts and models to assess their impact on the quality of navigation instructions. By refining these instructions, the project aims to demonstrate the potential of GPT models in improving navigation tasks that require understanding and processing both visual and linguistic information. Through rigorous testing and evaluation, this research seeks to provide insights into how GPT can be effectively applied to complex, multi-modal applications.


## Scripts and Dataset

The main components of this project, which consist of the scripts created to improve instructions through GPT models, can be found in the `tasks/R2R` folder. Therefore, only this specific directory has been included in the code submission. You can locate a link to the repository at the end of this document. These scripts play a role in creating and perfecting navigation instructions, forming the foundation of how the project operates.

### Script Location

- **Directory Path**: `tasks/R2R`
  -  Within this directory are all the scripts utilised to enhance navigation instructions. It serves as the central storage location for the project's code related to integrating Speaker-Follower models and refining instruction processes.

### Dataset

- **Dataset File**: `tasks/R2R/data/R2R_GPT_enhanced_speaker_data_paths.json`
  -  The dataset generated by these scripts is essential for comprehending the improvements made to navigation instructions. It captures the results of using GPT models to fine-tune output from the speaker model, providing a picture of how this project impacts navigation accuracy in VLN scenarios.

## Features
- **Instruction Refinement**: Using OpenAI's GPT models to refine navigation instructions from the speaker model for clarity and ease of navigation.
- **Parallel Processing**: Implementing multithreading for refinement processes ensuring effective handling of large instruction sets.
- **Navigation Performance Evaluation**: Assesses the follower model's performance using both the original and GPT-refined instructions to determine the impact of instruction refinement on navigation accuracy in VLN scenarios.
- **Error Handling and Logging**: Establishing robust error handling mechanisms and detailed logging procedures to monitor the refinement process and maintain data integrity.

## Usage
This project involves a series of steps where initial instructions are generated by the speaker model, refined using GPT, and evaluated using the follower model. The main script manages the process based on GPT and is adaptable for testing various GPT models and prompts.

## Technologies and Learning

- **OpenAI API**: Key in incorporating GPT models for refining instructions.
- **Python**: The main programming language used for developing scripts focused on instruction refinement, ensuring correct formatting, and managing various data processing tasks related to the project.
- **Concurrent Futures**: Supports multithreading to enhance the efficiency of the GPT refinement process.
- **Anaconda**: Used for managing project environments and dependencies, facilitating development and testing across varied computational setups.
- **Computational Shared Facility**: Used the university's computational resources for processing large datasets and running intensive models.
- **PyTorch Documentation**: Explored and utilised PyTorch-related libraries for updating and managing model-related code.
- **OpenCV Documentation**:  Explored the library to update outdated functions causing problems.
- **Logging**: Utilised for tracking the process flow and identifying potential issues during the instruction refinement stage.
- **JSON**: Employed for handling the instruction data, enabling seamless integration between the speaker model, GPT refinement, and follower model.


## Acknowledgments
- Ronghang Hu and contributors for the foundational "Speaker-Follower Models for Vision-and-Language Navigation" repository (https://github.com/ronghanghu/speaker_follower).
