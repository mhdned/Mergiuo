# Mergiuo

A Python script I built to stop wasting time creating merge requests one by one. Instead of clicking through GitLab's UI for every project, this tool lets me batch-create MRs across multiple repositories with just a few prompts.

## Overview

This interactive console application connects to your GitLab instance and walks you through creating merge requests for multiple projects at once. You can filter projects by category (like "backend" or "frontend"), pick which ones you want, set your branches, choose an assignee, and let it run. It handles all the API calls, checks if branches exist, skips projects that already have open MRs, and gives you a clean summary at the end.

## Technologies

<p align="left">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=python,gitlab" />
  </a>
</p>

## Features

- **Interactive Setup**: Prompts for GitLab URL, access token, and authenticates before starting
- **Smart Filtering**: Filter projects by category keywords (searches in project paths and names)
- **Flexible Selection**: Choose specific projects by number or select all filtered results
- **Branch Validation**: Automatically checks if source and target branches exist before creating MRs
- **Duplicate Detection**: Skips projects that already have an open MR between the specified branches
- **Assignee Options**: Assign to yourself, pick from project members, or leave unassigned
- **Visual Feedback**: Clear success/warning/error indicators with MR URLs for quick access
- **Batch Processing**: Create dozens of MRs in seconds instead of minutes

## Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd <repository-name>
pip install -r requirements.txt
```
Or install the only dependency directly:

```bash
pip install requests
```
## Usage

Run the script:

```bash
python gitlab_mr_creator.py
```

Follow the interactive prompts:

1. Enter your GitLab instance URL (e.g., `https://gitlab.com`)
2. Provide your private access token
3. Enter a category keyword to filter projects (e.g., `backend`)
4. Select projects by entering numbers separated by commas, or type `all`
5. Specify source and target branch names
6. Choose assignee option (yourself, project member, or none)
7. Watch as MRs are created across all selected projects

## Requirements

- Python 3.6+
- `requests` library
- GitLab private access token with API access
- Appropriate permissions on target projects

## License

MIT License  
Use it, break it, fix it, share it. Just don't blame me if it creates 100 MRs in the wrong projects. 💥

## Author

```python
Print("mhdned")
```