import subprocess
import argparse
import json
import yaml
import logging
import uuid
import os

logging.basicConfig(level=logging.INFO)

def run_git_command(command: str) -> list:
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True, shell=True)
    return result.stdout.strip().split('\n')

def set_output(name: str, value: any) -> None:
    logging.info(f"Setting output {name}")
    logging.info(f"Setting value {value}") # magnus debug line
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)

def read_yaml(folder: str, file_name: str, keyword: str) -> dict:
    file_path = f"{folder}/{file_name}"
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return data.get(keyword, {})
    except FileNotFoundError:
        logging.error(f"File {file_path} not found")
        return {}
    except yaml.YAMLError as exc:
        logging.error(f"Error in configuration file: {exc}")
        return {}

# Function to get the default (primary) branch name
def get_default_branch() -> str:
    try:
        default_branch = subprocess.run("git remote show origin | grep 'HEAD branch' | sed 's/  HEAD branch: //'", stdout=subprocess.PIPE, text=True, shell=True).stdout.strip()
        return default_branch
    except Exception as e:
        logging.error(f"An error occurred while determining the default branch: {e}")
        return 'main'  # Fallback to 'main' as a last resort

# Parse arguments
parser = argparse.ArgumentParser(description='Process Git diff and sort folders.')
parser.add_argument('--meta_file_name', type=str, help='Name of the YAML metadata file', default=None)
parser.add_argument('--keyword', type=str, help='Keyword to look for in the YAML file', default=None)
parser.add_argument('--comparing_branch', type=str, help='Branch to compare with', default=get_default_branch())

args = parser.parse_args()

yaml_meta_file_name = args.meta_file_name
keyword = args.keyword
comparing_branch = args.comparing_branch

# Initialize metadata dictionary
metadata = {}

# Get Git Diff
git_diff_output = run_git_command(f"git diff {comparing_branch} --name-only")
print(f"git_diff_output: {git_diff_output}")

# Extract distinct folders and files
distinct_folders = list(set([str(path).rsplit('/')[0] for path in git_diff_output]))
distinct_files = list(set(git_diff_output))

# Populate metadata dictionary by reading YAML files in each folder
for folder in distinct_folders:
    metadata.update(read_yaml(folder, yaml_meta_file_name, keyword))

# Filter folders based on metadata availability
folders_with_metadata = [folder for folder in distinct_folders if folder in metadata]
folders_without_metadata = [folder for folder in distinct_folders if folder not in metadata]

# Sort folders alphabetically
folders_sorted_alpha_inc = sorted(distinct_folders)
folders_sorted_alpha_dec = sorted(distinct_folders, reverse=True)

# Sort folders with metadata based on metadata
folders_sorted_meta_inc = sorted(folders_with_metadata, key=lambda x: metadata.get(x, 0))
folders_sorted_meta_dec = sorted(folders_with_metadata, key=lambda x: metadata.get(x, 0), reverse=True)

# Set Outputs
set_output("distinct_folders", distinct_folders)
set_output("folders_without_metadata", folders_without_metadata)
set_output("folders_sorted_alpha_inc", folders_sorted_alpha_inc)
set_output("folders_sorted_alpha_dec", folders_sorted_alpha_dec)
set_output("folders_sorted_meta_inc", folders_sorted_meta_inc)
set_output("folders_sorted_meta_dec", folders_sorted_meta_dec)

# Convert lists to JSON
json_output = json.dumps({
    "distinct_folders": distinct_folders,
    "folders_without_metadata": folders_without_metadata,
    "folders_sorted_alpha_inc": folders_sorted_alpha_inc,
    "folders_sorted_alpha_dec": folders_sorted_alpha_dec,
    "folders_sorted_meta_inc": folders_sorted_meta_inc,
    "folders_sorted_meta_dec": folders_sorted_meta_dec
})

# Set output as JSON
set_output("json_output", json_output)

# debug line
set_output("magnus_debug", "debugvaloneline")

