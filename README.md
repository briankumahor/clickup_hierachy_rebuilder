# ClickUp Task Hierarchy Status Recreator

This Python script is a utility for editing tasks and subtasks
in ClickUp, a project management tool. The script uses the ClickUp API to fetch and update tasks, 
lists, and folders within a ClickUp space.

The script's main functionality includes processing tasks and deciding if a task should be a subtask of another task 
based on certain conditions. It also finds parent tasks and updates task details on the server. 
The script uses logging to track its operations and outputs logs to a file named output_clickup_recreator.log. 
The script also handles environment variables for storing sensitive data like API keys, 
which are loaded from a .env file.

## Features

- Processes tasks and decides if a task should be a subtask based on certain conditions.
- Finds parent tasks and updates task details on the server.
- Handles environment variables for storing sensitive data like API keys, which are loaded from a .env file.
- Logs its operations and outputs logs to a file named `output_clickup_recreator.log`.

## Setup

1. Clone this repository to your local machine.
2. Install the required Python packages with `pip install -r requirements.txt`
3. (you should create this file with all the dependencies of your project).
4. Create a `.env` file in the project root and add your ClickUp API key, team ID, and space URLs.
5. Make sure to separate multiple space URLs with commas. Here's an example:

```env
CLICKUP_API_KEY=your_api_key
CLICKUP_TEAM_ID=your_team_id
CLICKUP_SPACE_URLS=url1,url2,url3
Run the script with python Clickup_Task_Hierachy_Status_Recreator_Doc.py.
Usage
This script is intended to be run from the command line.
It does not take any command line arguments. All configuration is done through the .env file.

Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
