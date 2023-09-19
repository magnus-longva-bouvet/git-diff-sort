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
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)

def read_yaml(folder: str, file_name: str) -> dict:
    file_path = os.path.join(folder, file_name)
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return data
    except FileNotFoundError:
        logging.error(f"File {file_path} not found")
        return {}
    except yaml.YAMLError as exc:
        logging.error(f"Error in configuration file: {exc}")
        return {}

# Initialize metadata dictionary
metadata = {}

# Parse arguments
parser = argparse.ArgumentParser(description='Process Git diff and sort folders.')
parser.add_argument('--meta_file_name', type=str, help='Name of the YAML metadata file', default=None)
parser.add_argument('--keyword', type=str, help='Keyword to look for in the YAML file', default=None)
parser.add_argument('--comparing_branch', type=str, help='Branch to compare with', default='main')

args = parser.parse_args()

# Get Git Diff
try:
    working_directory = os.environ['GITHUB_WORKSPACE']
    print(f"working directory {working_directory}")
    print(f"current working dir {os.getcwd()}")
    git_diff_output = run_git_command(f"git -git-dir {working_directory}/.git --work-tree {working_directory} diff {args.comparing_branch} --name-only")
    print(f"git diff output {git_diff_output}")
except Exception as e:
    logging.error(f"An error occurred while running the git command: {e}")
    git_diff_output = []

# Extract distinct folders
distinct_folders = list(set([os.path.dirname(path) for path in git_diff_output if path]))

# Populate metadata dictionary by reading YAML files in each folder
folders_with_metadata = []
folders_without_metadata = []

for folder in distinct_folders:
    try:
        sorting_key = read_yaml(folder, args.meta_file_name).get(args.keyword)
        if sorting_key:
            metadata[folder] = sorting_key
            folders_with_metadata.append(folder)
        else:
            folders_without_metadata.append(folder)
    except Exception as e:
        logging.error(f"An error occurred while reading YAML for folder {folder}: {e}")


# Sort folders
folders_sorted_alpha_inc = sorted(distinct_folders)
folders_sorted_alpha_dec = sorted(distinct_folders, reverse=True)
folders_sorted_meta_inc = sorted(folders_with_metadata, key=lambda x: metadata[x])
folders_sorted_meta_dec = sorted(folders_with_metadata, key=lambda x: metadata[x], reverse=True)

# Set Outputs
set_output("distinct_folders", distinct_folders)
set_output("folders_with_metadata", folders_with_metadata)
set_output("folders_without_metadata", folders_without_metadata)
set_output("folders_sorted_alpha_inc", folders_sorted_alpha_inc)
set_output("folders_sorted_alpha_dec", folders_sorted_alpha_dec)
set_output("folders_sorted_meta_inc", folders_sorted_meta_inc)
set_output("folders_sorted_meta_dec", folders_sorted_meta_dec)

# Convert lists to JSON
json_output = json.dumps({
    "distinct_folders": distinct_folders,
    "folders_with_metadata": folders_with_metadata,
    "folders_without_metadata": folders_without_metadata,
    "folders_sorted_alpha_inc": folders_sorted_alpha_inc,
    "folders_sorted_alpha_dec": folders_sorted_alpha_dec,
    "folders_sorted_meta_inc": folders_sorted_meta_inc,
    "folders_sorted_meta_dec": folders_sorted_meta_dec
})

# Set output as JSON
set_output("json_output", json_output)
