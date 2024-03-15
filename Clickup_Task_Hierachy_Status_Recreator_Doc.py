# File: Clickup_Task_Hierachy_Status_Recreator_Doc.py
''' 
This Python script Clickup_Task_Hierachy_Status_Recreator_Doc.py is a utility for managing tasks 
in ClickUp, a project management tool. The script uses the ClickUp API to fetch and update tasks, 
lists, and folders within a ClickUp space.

The script's main functionality includes processing tasks and deciding if a task should be a subtask 
based on certain conditions. It also finds parent tasks and updates task details on the server. 
The script uses logging to track its operations and outputs logs to a file named output_clickup_recreator.log. 
The script also handles environment variables for storing sensitive data like API keys, 
which are loaded from a .env file.
'''
import requests
import sys
import time
import webbrowser

import logging

import os
from dotenv import load_dotenv


#Add .env to your .gitignore file: This prevents the .env file from 
# being committed to your version control system.
#.env

#Add .env.example to your repository: This is a copy of your .env file,
# but it contains default values for each variable. This is useful for
# helping other developers set up your project, as well as for providing
# default values for your own development environment. Your .env file
# should be listed in your .gitignore file so nobody accidentally commits
# it with their own credentials.
#.env.example

# Load the .env file
load_dotenv()

# Now you can access the variables
api_key = os.getenv('CLICKUP_API_KEY')
team_id = os.getenv('CLICKUP_TEAM_ID')
space_urls_with_labels = os.getenv('CLICKUP_SPACE_URLS').split(',')

# Split the labels and URLs and create a space_urls without labels
space_urls = {}
for url_with_label in space_urls_with_labels:
    label, url = url_with_label.split('|')
    space_urls[label] = url


    
# Set the headers for the API requests
headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}


BASE_URL = "https://api.clickup.com/api/v2"


"""
This code sets up a logger named 'my_logger' that logs messages of level INFO and 
above to a file named 'output_clickup_recreator.log'. The format of the log messages 
is 'timestamp - logger name - log level - message'. For more details on the logging 
library and the format string, please refer to the Python logging library documentation. 
"""

# Create a logger
logger = logging.getLogger('my_logger')

# Set the level of this logger. Only logs of this level or above will be tracked.
# Possible levels are DEBUG, INFO, WARNING, ERROR, CRITICAL eg. logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# Create a file handler for output file
handler = logging.FileHandler('output_clickup_recreator.log')

# Define the format for log mesaages
# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set the formatter for this handler to the formatter we just created
handler.setFormatter(formatter)
 

# Add the handler to the logger
logger.addHandler(handler)

# Now you can log messages!
# logger.debug('This is a debug message')
# logger.info('This is an informational message')
# logger.warning('This is a warning')
# logger.error('This is an error message')
# logger.critical('This is a critical error message')

# Create a stream handler for debugging
# Comment out the stream handler when done debugging
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def get_space_id(space_url):
    return space_url.split('/')[-1]

def get_folders_url(space_id):
    return f"{BASE_URL}/space/{space_id}/folder"

def get_lists_url(folder_id):
    return f"{BASE_URL}/folder/{folder_id}/list"

def get_tasks_url(list_id):
    return f"{BASE_URL}/list/{list_id}/task"


def handle_api_request(url, headers, params=None, is_get_tasks=False):
    # sourcery skip: remove-unnecessary-else, swap-if-else-branches
    if params is None:
        params = {}
    params['include_closed'] = 'true'
    all_data = []
    page = 0

    while True:
        if is_get_tasks:
            params['page'] = page

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            logger.info("Rate limit reached. Waiting for 60 seconds before retrying.")
            time.sleep(60)
            continue
        elif response.status_code == 500:
            logger.info(f"Internal server error when requesting {url}. Please try again later.")
            return None
        elif response.status_code != 200:
            raise Exception(f"Request to {url} returned status code {response.status_code}")

        data = response.json()

        if is_get_tasks:
            all_data.extend(data.get('tasks', []))
            if 'last_page' not in data or data['last_page']:
                break
            page += 1
            time.sleep(0.6)
        else:
            return data

    return all_data


def get_data_from_url(url, headers, params=None):
    if params is None:
        params = {}
    params = {'include_closed': 'true'}
    return handle_api_request(url, headers, params)
   
        

def get_data_from_tasks_url(url, headers, params=None):

    if params is None:
        params = {}
    params['include_closed'] = 'true'
    # params['subtasks'] = 'true'  # Include subtasks in the request
    return handle_api_request(url, headers, params)



def get_a_task_details_from_url(url, headers):

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception if the request failed
    return response.json()


def get_parent_task(parent_task_id):
    parent_task_url = f"{BASE_URL}/task/{parent_task_id}"
    return get_data_from_url(parent_task_url, headers).get('task')



def delete_list(url, headers, folder_id):

    # Fetch the list details
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        logger.info("Rate limit reached. Waiting for 60 seconds before retrying.")
        time.sleep(60)  # Wait for 60 seconds before retrying
    elif response.status_code != 200:
        logger.info(f"Error fetching the list details: {response.status_code}, {response.text} for listurl ==> {url}")
        return False

    list_details = response.json()
    if list_details['folder']['id'] != folder_id:
        logger.info(f"Error: The list for listurl ==> {url} is not in the expected folder.")
        return False

    # Delete the list
    response = requests.delete(url, headers=headers)
    """Function to delete a list in a folder

    Returns:
        [type]: [description]
    """
    if response.status_code == 429:
        logger.info("Rate limit reached. Waiting for 60 seconds before retrying.")
        time.sleep(60)  # Wait for 60 seconds before retrying
    elif response.status_code == 200:    
        logger.info(f"Successfully deleted the list in folder {folder_id}. for listurl ==> {url}")
        return True
    else:
        logger.info(f"Error deleting the list details:response_status_code==> {response.status_code}, {response.text} for listurl ==> {url} in folder {folder_id}")
        return False



def update_task_on_server(task_id, parent_task, parent_list, headers):

    update_url = f"https://api.clickup.com/api/v2/task/{task_id}"
    update_data = {
        'parent': str(parent_task['id']),  # Convert parent id to string
        'list_id': int(parent_list['id'])  # Convert list id to integer
    }
    #logger.info(f"*** Updating task ==> {task_id} with parent ==> {parent_task['id']} aka {parent_task['name']}  in list ==> {parent_list['name']}")
    update_response = requests.put(update_url, headers=headers, json=update_data)
    return update_response.status_code == 200



def process_space(space_url, headers):
    # Processes a Space in ClickUp.
    # Extract the space_id from the space_url
    # Make a GET request to the ClickUp API to retrieve all folders in the Space
    # Iterate over each folder and make another GET request to retrieve all lists in the folder
    logger.info(f"Processing ==> {space_url}")
    space_id = get_space_id(space_url)
    folders_url = get_folders_url(space_id)
    response = get_data_from_url(folders_url, headers)
    folders = response.get('folders', [])
    for folder in folders:
        #logger.info(f"Processing Folder id ==> {folder['id'] }")
        #process_folder(folder, headers)
        # 
        hier_update_folder(folder, headers)

    # try:
    #     folders = response['folders']
    # except KeyError:
    #     folders = []
    # Iterate over each folder and make another GET request to retrieve all lists in the folder
    #for folder in folders:
        


def process_folder(folder, headers):  # sourcery skip: use-named-expression
    """Processes a Folder in a Space ."""
    logger.info(f"Processing foldername ==> {folder['name']}")
    lists_url = get_lists_url(folder['id'])
    response = get_data_from_url(lists_url, headers)
    lists_in_folder_only = response.get('lists', [])

    # Extract the lists from the response
    #lists = response.get('lists', [])

    for subtask_level in range(11, 4, -1): #decrement from 11 to 5 inclusive
            logger.info(f"Processing Folder id ==> {folder['id'] } and subtask_level ==> {subtask_level}") if subtask_level == 5 else None

            # Iterate over each list and make yet another GET request to retrieve all tasks in the list
            for list in lists_in_folder_only:
                #logger.info(f"Processing List id ==> {list['id'] } and subtask_level ==> {subtask_level}")
                should_delete = False
                should_delete = process_list(list, headers, lists_in_folder_only, subtask_level)
                if should_delete:

                    logger.info(f"***Confirmed for deletion. No tasks found for list ==> {list['id']} and {list['name']} in Foldername ==> {folder['name']} ***")
                    list_details_url = f"https://api.clickup.com/api/v2/list/{list['id']}"
                    success = delete_list(list_details_url, headers, folder['id'])
                    if not success:
                        logger.info(f"Exiting due to error - unsuccessful at deleting list ==> {list['id']} and {list['name']} in Foldername ==> {folder['name']}.")
                        #sys.exit(1)
                        #continue
                        return  # Return to the calling function to process the next list
                    else:
                        # Fetch the lists for the folder again since we deleted one
                        lists_url = f"https://api.clickup.com/api/v2/folder/{folder['id']}/list"
                        response = get_data_from_url(lists_url, headers)

                        # Extract the lists from the response
                        lists_in_folder_only = response.get('lists', [])
                    #sys.stdout = open('output.txt', 'a', encoding='utf-8')                       


def process_list(list, headers, lists_in_folder_only, subtask_level):

    logger.info(f"Processing ==> {list['name']} in Foldername ==> {list['folder']['name']}")
    tasks_url = get_tasks_url(list['id']) 
    params = {"include_closed": "true", "subtasks": "false"}
    try:
        if list['name'].count('\\') == 3 and list['name'] == "\\\\\\" and subtask_level > 5:
            #avoid the Continue command if the list name is \\\\\\, which is the default name for the root list 
            #don't process the root list if subtask_level is greater than 5
            logger.info(f"skipping root list when subtask_level ==> {subtask_level}")
            return False  # Return to the calling function to process the next list
        else:
            tasks = get_data_from_tasks_url(tasks_url, headers, params)

    except Exception as e:
        #sys.stdout.close()
        #sys.stdout = original_stdout
        logger.info(f"***Error: Exception occurred while fetching tasks for list ==> {list['id']} and {list['name']}***")
        tasks = []
    if not tasks:
        #logger.info(f"***Candidate for deletion. No tasks found for list ==> {list['id']} and {list['name']} in Foldername ==> {folder['name']} ***")
        #if list['name'].count('\\') <= 3:
        if not (4 <= list['name'].count('\\') <= 7):
            logger.info(f"***Candidate for deletion. No tasks found for list ==> {list['id']} and {list['name']} ***")
            if list['name'].count('\\') == 3 and list['name'] != "\\\\\\":
                #avoid the Continue command if the list name is \\\\\\, which is the default name for the root list 
                logger.info("has 3 backslashes, but is not the root list. delete it.")
            else:
                logger.info(f"***But the list name for listurl ==> {tasks_url} does not contain count(backslashes) between 4 and 7 inclusive. don't delete skip to next list in loop")       
                #continue  # Skip to the next iteration of the loop
                return False  # Return to the calling function to process the next list                        
        # Fetch the tasks for the list again with subtasks included
        params["subtasks"] = "true"
        tasks = get_data_from_tasks_url(tasks_url, headers, params)
        if not tasks:               
           return True  # Return to the calling function to delete the list                            
    else:

        for task in tasks:
            process_task(task, headers, lists_in_folder_only, subtask_level)
    return False  # Return to the calling function to not delete the list
        
              
def process_task(task, headers, lists_in_folder_only, subtask_level):
    # sourcery skip: use-named-expression
    logger.info(f"Processing taskname ==> {task['name']} in list ==> {task['list']['name']} with subtask_level ==> {subtask_level}")

    # Check if the task already has a parent
    if 'parent' in task and task['parent']:
        logger.info(f"Task {task['id']} already has a parent ==> {task['parent']} . Checking next task in this list.")

        return  # Return to the calling function to process the next task
    potential_subtask_id, parent_task, parent_list = decide_if_making_it_subtask(task, lists_in_folder_only, headers, subtask_level)
    if potential_subtask_id is None or parent_task is None or parent_list is None:
        logger.info(f"Could not classify as potential subtask or find parent task for task {task['id']} aka {task['name']} with existinglist ==> {task['list']}")

        return  # Return to the calling function to process the next task
    # Use potential_subtask_id, parent_task, parent_list here
    if potential_subtask_id and parent_task:
        success = update_task_on_server(potential_subtask_id, parent_task, parent_list, headers)
        if success:
            logger.info(f"*** Successfully updated potential subtask ==> {potential_subtask_id} ***")
        else:
            logger.info(f"*** Failed to update potential subtask ==> {potential_subtask_id} ***")


def decide_if_making_it_subtask(task, lists, headers, subtask_level):
    """Determine if a task should be a subtask .

    Args:
        task ([type]): [description]
        lists ([type]): [description]
        headers ([type]): [description]
        subtask_level ([type]): [description]

    Returns:
        [type]: [description]
    """
   # Determine if the task should be a subtask
   # If the task has a custom field called "M Path Depth 2" and the value is equal to the current subtask_level, then it should be a subtask
    # If the task has a custom field called "M Path Depth 2" and the value is not equal to the current subtask_level, then it should not be a subtask
    # If the task does not have a custom field called "M Path Depth 2", then it should not be a subtask

    parent_task_level = subtask_level - 1
    for field in task['custom_fields']:
        if field['name'] == 'M Path Depth 2' and 'value' in field and field['value'] == str(subtask_level):
            potential_subtask_id = task['id']
            #logger.info(f"Task {task['id']} matches the current listlevel search of ==> {subtask_level}. Finding it a parent now")

            split_count = 2 if subtask_level >= 7 else (8 - subtask_level)+1
            parts = task['list']['name'].rsplit('\\', split_count)
            parent_task_name = parts[0] if subtask_level == 5 else parts[1]
            extra_backslash = False
            split_increment = 0

            if parent_task_name.strip() == '':
                split_count += 1  # Assume an additional backslash and it's escape character
                extra_backslash = True
                logger.info(f"Parent task name is empty. Trying to split with {split_count} backslashes")
            parts = task['list']['name'].rsplit('\\', split_count)
            parent_task_name = parts[0] if subtask_level == 5 else parts[1]


            while subtask_level > 4:
                if len(parts) < 3:
                    #logger.info(f"List name {task['list']['name']} does not contain enough backslashes to find a parent task.")
                    return None, None, None

                split_count = (2 if subtask_level >= 7 else (8 - subtask_level)+1) + split_increment
                if extra_backslash:
                    split_count += 1
                parts = task['list']['name'].rsplit('\\', split_count)
                if subtask_level == 5:
                    parent_list_name = '\\\\\\'
                    # grandparent_task_name = parts[3] if len(parts) > 4 else None
                    # if grandparent_task_name == parent_task_name:
                    #     grandparent_task_name = parts[2]
                    grandparent_task_name = parts[len(parts)-4] if extra_backslash else parts[len(parts)-3]
                else:
                    parent_list_name = parts[0] + '\\'
                    grandparent_task_name = None                

                #parent_list_name = '\\\\\\' if subtask_level == 5 else parts[0] + '\\'
                #grandparent_task_name = parts[4] if subtask_level == 5 else None

                if subtask_level > 5 and subtask_level < 8:
                    parent_list_name += '\\' * (8 - subtask_level)  # Add (8 - subtask_level) backslashes
                #elif subtask_level >= 8:
                #    parent_list_name += '\\'

                parent_task, parent_list = find_parent_task(parent_list_name, parent_task_name, lists, headers, parent_task_level, grandparent_task_name)
                if parent_task:
                    return potential_subtask_id, parent_task, parent_list

                # If no parent task is found and subtask_level is >= 8, try again with an additional backslash
                if subtask_level >= 8:
                    parent_list_name += '\\'
                    parent_task, parent_list = find_parent_task(parent_list_name, parent_task_name, lists, headers, parent_task_level)
                    if parent_task:
                        return potential_subtask_id, parent_task, parent_list
        
                # If no parent task is found, decrement subtask_level and repeat the process
                split_increment += 1  # Increment split_increment by 1 for the next iteration
                #logger.info(f"Checking for grandparent and higher ancestors in ==> {subtask_level-1} of {parent_list_name} .")
                subtask_level -= 1
                    
        else:
            logger.info(f"The MPathDepth2 value for Task {task['id']} does not match current subtask_level ==> {subtask_level}. Skipping.")   
    return None, None, None


def find_parent_task(parent_list_name, parent_task_name, lists, headers, parent_task_level, grandparent_task_name=None):
    """Find a task in clickup .
    Args:
        parent_list_name ([type]): [description]
        parent_task_name ([type]): [description]
        lists ([type]): [description]
        headers ([type]): [description]
        parent_task_level ([type]): [description]
        grandparent_task_name ([type], optional): [description]. Defaults to None.

    Returns:
        [type]: [description]
    """
    for potential_parent_list in lists:
        if potential_parent_list['name'].strip() == parent_list_name.strip():
            tasks_url = f"https://api.clickup.com/api/v2/list/{potential_parent_list['id']}/task"
            params = {"subtasks": "true"}
            try:
                tasks = get_data_from_tasks_url(tasks_url, headers, params)
            except Exception as e:  
                logger.info(f"KeyError: No tasks found for list ==> {potential_parent_list['id']} and {potential_parent_list['name']}")
                tasks = []
            for potential_parent_task in tasks:
                if parent_task_name.strip() in potential_parent_task['name'].strip():
                    for parent_field in potential_parent_task['custom_fields']:
                        #if  parent_field['value'] == str(parent_task_level):
                        if 'value' in parent_field and parent_field['value'] == str(parent_task_level):                           
                            if grandparent_task_name is None:
                                return potential_parent_task, potential_parent_list
                            #elseif parent_list_name.strip() == '\\\\\\':
                            else: # if parent_list_name.strip() == '\\\\\\':
                                potential_grandparent_id = potential_parent_task['parent']
                                potential_grandparent_url = f"https://api.clickup.com/api/v2/task/{potential_grandparent_id}"
                                potential_grandparent = get_a_task_details_from_url(potential_grandparent_url, headers)
                                #potential_grandparent_tasks = get_data_from_tasks_url(potential_grandparent_url, headers, params)
                                if potential_grandparent['name'].strip() == grandparent_task_name.strip():
                                    return potential_parent_task, potential_parent_list
                                # for potential_grandparent_task in potential_grandparent_tasks:
                                #     if potential_grandparent_task['name'].strip() == grandparent_task_name.strip():
                                #         return potential_parent_task, potential_parent_list
                                #     else:
                                #         logger.info(f"Potential Grandparent task name {potential_grandparent_task['name']} does not match expected name {grandparent_task_name}.")
                                #         #skip to next potential_parent_task
                                #         continue
                                
                                else:
                                    #logger.info(f"Grandparent task name {potential_grandparent['name']} does not match expected name {grandparent_task_name}.")
                                    #skip to next potential_parent_task
                                    continue
    logger.info(f"Parent task name {parent_task_name} does not exist in list {parent_list_name}.")    
    return None, None


def get_a_task_details_from_url(url, headers):
    """Fetch a single task from ClickUp using its URL.

    Args:
        url (str): The URL of the task.
        headers (dict): The headers to use when making the request.

    Returns:
        dict: The JSON response from the request.
    """
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception if the request failed
    return response.json()



def hier_update_folder(folder, headers):
    """Processes a Folder in a Space."""
    lists_url = get_lists_url(folder['id'])
    response = get_data_from_url(lists_url, headers)
    lists_in_folder_only = response.get('lists', [])

    logger.info(f"Processing Folder id ==> {folder['id'] } foldername ==> {folder['name']}") 

    # Iterate over each list and make yet another GET request to retrieve all tasks in the list
    for list_to_update in lists_in_folder_only:
        #logger.info(f"Processing List id ==> {list['id'] }")
        #hier_process_list(lists_in_folder_only, headers)
        hier_update_list(list_to_update, headers)
   
        #sys.stdout = open('output.txt', 'a', encoding='utf-8')        



def get_custom_fields(task):
    return {field['name']: field.get('value') for field in task.get('custom_fields', [])}



def hier_update_list(list, headers):
    """
    This function updates the status of tasks and subtasks in ClickUp based on their custom fields. The process is as follows:

    Fetch all tasks and subtasks: Retrieves all tasks and subtasks from a specified list in ClickUp, regardless of their status.

    Initial processing based on 'M Date Completed': If this field is populated, the function updates 'Date Closed' and 'Date Done' fields with this date and sets the task's status to 'COMPLETE' unless it's already marked as such.

    Secondary processing for open tasks and subtasks: After the initial processing, the function fetches tasks and subtasks that are still open, excluding those marked as 'COMPLETE' in the previous step.

    Detailed processing for open tasks and subtasks: The function updates the status of each open task and subtask to match 'M Project Status', prefixes the task name with "[Prj]" if 'M Is Project' is 'Y', and changes the status to "REJECTED" if 'M Hide In To Do' is 'Y'.

    Ignored Fields: Certain fields like 'M flag', 'M Folder', 'M Task Effort', 'M Importance', 'M Urgency', and 'M Starred' are either ignored and deleted or ignored but retained.

    For more details, refer to the ClickUp API documentation
    """
    logger.info(f"Processing ==> {list['name']} in Foldername ==> {list['folder']['name']}")
    tasks_url = get_tasks_url(list['id']) 
    params = {"include_closed": "true", "subtasks": "true"}
    try:
        tasks = get_data_from_tasks_url(tasks_url, headers, params)
    except Exception as e:
        #sys.stdout.close()
        #sys.stdout = original_stdout
        logger.info(f"***Error: Exception occurred while fetching tasks for list ==> {list['id']} and {list['name']}***")
        tasks = []
    if not tasks:               
        return  # Return to the calling function to process the next list                            
    else:
        # Initial processing based on 'M Date Completed'
        # Refetch tasks and subtasks with a status of 'Open'
        # Exclude tasks that have been newly marked as 'COMPLETE' in the initial processing.
        # Detailed processing for open tasks and subtasks
        # Ignored fields
        logger.info(f"Processing ==> {list['name']} in Foldername ==> {list['folder']['name']}")

        for task in tasks:
            task_details = {}
            custom_fields = get_custom_fields(task)

            m_date_completed = custom_fields.get('M Date Completed')
            if m_date_completed is not None:
                task_details['Date Closed'] = m_date_completed
                task_details['Date Done'] = m_date_completed
                m_recurrence = custom_fields.get('M Recurrence')
                if task['status'] != 'COMPLETE' and (m_recurrence is None or m_recurrence == ''):
                    task_details['status'] = 'COMPLETE'
            if task_details:
                update_task_details(task['id'], task_details, headers)

        # Secondary processing for open tasks and subtasks
        # Refetch tasks with a status of 'Open'
        params = {"include_closed": "false", "subtasks": "true"}
        try:
            tasks = get_data_from_tasks_url(tasks_url, headers, params)
        except Exception as e:
            logger.info(f"***Error: Exception occurred while fetching tasks for list ==> {list['id']} and {list['name']}***")
            tasks = []
        if not tasks:               
            return  # Return to the calling function to process the next list                            
        else:
            # Detailed processing for open tasks and subtasks
            for task in tasks:
                task_details = {}
                custom_fields = get_custom_fields(task)

                m_project_status = custom_fields.get('M Project Status')
                if m_project_status == 'Completed':
                    m_recurrence = custom_fields.get('M Recurrence')
                    if m_recurrence is not None and m_recurrence != '':
                        task_details['comments'] = m_recurrence
                    else:
                        task_details['status'] = 'COMPLETE'
                elif m_project_status == 'In Progress':
                    task_details['status'] = 'IN PROGRESS'
                elif m_project_status == 'Suspended':
                    task_details['status'] = 'SUSPENDED'

                if custom_fields.get('M Is Project') == 1:
                    task_details['name'] = '[Prj] ' + task['name']
                if custom_fields.get('M Hide In To Do') == 'Y':
                    task_details['status'] = 'REJECTED'
                m_recurrence = custom_fields.get('M Recurrence')
                if m_recurrence is not None and m_recurrence != '':
                    task_details['comments'] = m_recurrence
                if custom_fields.get('M Starred') == 'Y':
                    task_details['priority'] = 1
                m_date_modified = custom_fields.get('M Date Modified')
                if m_date_modified is not None:
                    task['date_updated'] = m_date_modified

                if task_details:
                    update_task_details(task['id'], task_details, headers)

        
        # Logging
        logging.info('Finished updating tasks and subtasks') 


    return  # Return to the calling function


def update_task_details(task_id, task_details, headers):
    """Update task details on Clickup server

    Args:
        task_id ([type]): [description]
        task_details (dict): Dictionary containing task details to be updated
        headers ([type]): [description]

    Returns:
        bool: True if update was successful, False otherwise
    """
    update_url = f"https://api.clickup.com/api/v2/task/{task_id}"
    
    # Send the update request
    update_response = requests.put(update_url, headers=headers, json=task_details)
    
    return update_response.status_code == 200

space_url = None
try:
    # Prompt the user for the URL of their ClickUp Space
    # space_url = input("Enter the URL of your ClickUp Space: ")
    # or get a list of all spaces from the env file


    for space_url in space_urls:
    # Make a GET request to the ClickUp API to retrieve each Space
    # Iterate over each Space and make another GET request to retrieve all folders in the space
        process_space(space_url, headers)
        
except Exception as e:
    logger.info(f"An error occurred while processing {space_url}: {e}")
    logger.info("Local variables:", locals())
finally:
    logger.info(f"Finished processing {space_url}")

