import telebot
import requests
import time
from telebot import types

bot = telebot.TeleBot('7825809842:AAFa9WPFg-qHBMJAabi5XVyz0Yn7RwuPwg8')
TELEGRAM_BOT_TOKEN = '7825809842:AAFa9WPFg-qHBMJAabi5XVyz0Yn7RwuPwg8'

# ServiceNow instance details
SNOW_INSTANCE = 'https://dev247149.service-now.com/'
SNOW_USER = 't_user3'
SNOW_PASSWORD = 'BotTest123!@#'

# Define states for conversation flow
STATE_DESCRIPTION, STATE_SHORT_DESCRIPTION, STATE_CUSTOMER, STATE_CATEGORY, STATE_SUBCATEGORY, STATE_URGENCY = range(6)

# Dictionary to store user input for each step
user_data = {}

# Sample categories and urgency lists (These can be fetched dynamically from ServiceNow if needed)
companies = ["ACME EMEA", "Boxeo", "Tesla"]
categories = ["Network", "Hardware", "Software", "Inquiry", "Database"]
subcategories = {
    "Network": ["VPN", "DNS", "Wireless", "DHCP", "IP Address"],
    "Hardware": ["Disk", "Monitor", "CPU", "Keybord", "Memory", "Mouse"],
    "Software": ["Operating System", "Email"],
    "Inquiry": ["Antivirus", "Email", "Internal Application"],
    "Database": ["DB2", "Oracle", "MS SQL Server"]
}
urgency_levels = ["Low", "Medium", "High"]


# Function to fetch incident details
def fetch_incident(number):
    url = f'https://dev247149.service-now.com/api/now/table/incident'
    params = {'sysparm_query': f'number={number}', 'sysparm_limit': 1}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.get(url, headers=headers, params=params, auth=(SNOW_USER, SNOW_PASSWORD))

    if response.status_code == 200:
        result = response.json()
        if result['result']:
            incident = result['result'][0]
            return incident
        else:
            return None
    else:
        return None


# Function to update incident with PATCH request
def update_incident(number, field, new_value):
    # URL to access the ServiceNow API for incidents
    url = f'https://dev247149.service-now.com/api/now/table/incident'

    # Retrieve the incident first to get its sys_id
    incident = fetch_incident(number)

    if incident:
        sys_id = incident['sys_id']  # Get the sys_id of the incident

        # Prepare the data to update the incident
        update_url = f'{url}/{sys_id}'
        update_data = {
            field: new_value  # Update the specified field with the new value
        }
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        update_response = requests.patch(update_url, headers=headers, json=update_data, auth=(SNOW_USER, SNOW_PASSWORD))

        if update_response.status_code == 200:
            return f"Incident {number} updated successfully: {field} changed to {new_value}"
        else:
            return f"Error updating incident: {update_response.status_code} - {update_response.text}"
    else:
        return f"No incident found with number {number}"


@bot.message_handler(commands=['check_incident'])
def check_incident(message):
    incident_number = message.text.strip()  # Get the incident number from user message
    incident = fetch_incident(incident_number)  # Fetch the incident details

    if incident:  # Check if the incident exists
        # Format the incident details
        incident_details = (
            f"**Incident Number:** {incident.get('number', 'N/A')}\n"
            f"**Short Description:** {incident.get('short_description', 'N/A')}\n"
            f"**State:** {incident.get('state', 'N/A')}\n"
            f"**Category:** {incident.get('category', 'N/A')}\n"
            f"**Subcategory:** {incident.get('subcategory', 'N/A')}\n"
            f"**Urgency:** {incident.get('urgency', 'N/A')}\n"
            f"**Impact:** {incident.get('impact', 'N/A')}\n"
            f"**Priority:** {incident.get('priority', 'N/A')}\n"
            f"**Assignment Group:** {incident.get('assignment_group', 'N/A')}\n"
            f"**Assigned To:** {incident.get('assigned_to', 'N/A')}\n"
            f"**Created On:** {incident.get('sys_created_on', 'N/A')}\n"
            f"**Updated On:** {incident.get('sys_updated_on', 'N/A')}\n"
            f"**Description:** {incident.get('description', 'N/A')}\n"
            f"**Comments:** {incident.get('comments', 'N/A')}\n"
        )
        # Send the incident details to the user
        bot.send_message(message.chat.id, incident_details, parse_mode='Markdown')
    else:
        # If the incident is not found, notify the user
        bot.send_message(message.chat.id, "No incident found with that number. Please check the number and try again.")


# Start process to receive incident number
@bot.message_handler(commands=['update_incident'])
def process_incident_number(message):
    incident_number = message.text.strip()
    incident = fetch_incident(incident_number)

    if incident:
        # Display incident details
        details = (
            f"Incident Number: {incident['number']}\n"
            f"Short Description: {incident['short_description']}\n"
            f"State: {incident['state']}\n"
            f"Category: {incident['category']}\n"
            f"Subcategory: {incident.get('subcategory', 'N/A')}\n"
            f"Urgency: {incident.get('urgency', 'N/A')}\n"
            f"Description: {incident['description']}\n"
        )
        bot.send_message(message.chat.id, f"Incident Details:\n{details}")

        # Ask what the user wants to change
        fields_options = ("Which field do you want to change?"
                          "\n1. Category\n2. Subcategory\n3. State\n4. Urgency\n5. Description")
        bot.send_message(message.chat.id, fields_options)
        bot.register_next_step_handler(message, process_field, incident_number)
    else:
        bot.send_message(message.chat.id, "No incident found with that number. Please try again.")
        update_incident(message)


def process_field(message, incident_number):
    field_mapping = {
        "1": "category",
        "2": "subcategory",
        "3": "state",
        "4": "urgency",
        "5": "description"
    }

    field_choice = message.text.strip()
    if field_choice in field_mapping:
        user_data['incident_number'] = incident_number
        user_data['field'] = field_mapping[field_choice]
        bot.send_message(message.chat.id,
                         f"You want to change the field: {field_mapping[field_choice]}. Please enter the new value:")
        bot.register_next_step_handler(message, process_new_value)
    else:
        bot.send_message(message.chat.id, "Invalid choice. Please choose a valid field number.")
        process_incident_number(message)


def process_new_value(message):
    incident_number = user_data.get('incident_number')
    field = user_data.get('field')
    new_value = message.text


# Call the update incident function
    result_message = update_incident(incident_number, field, new_value)
    bot.send_message(message.chat.id, result_message)


# Function to create a new incident in ServiceNow
def create_incident(data):
    url = f'https://dev247149.service-now.com/api/now/table/incident'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

    # Payload for creating an incident
    payload = {
        'short_description': data['short_description'],
        'description': data['description'],
        'company': data['company'],  # Customer information
        'category': data['category'],
        'subcategory': data['subcategory'],
        'urgency': data['urgency'],
        'contact_type': 'Chat'  # Auto-fill contact type as "chat"
    }
    response = requests.post(url, headers=headers, json=payload, auth=(SNOW_USER, SNOW_PASSWORD))

    if response.status_code == 201:
        incident = response.json()['result']
        return f"Incident created successfully! Number: {incident['number']}"
    else:
        return f"Error creating incident: {response.status_code}"


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a custom keyboard
    print("Start command received")
    markup = types.InlineKeyboardMarkup()
    itembtn1 = types.InlineKeyboardButton('Check Incident', callback_data='check_incident')
    itembtn2 = types.InlineKeyboardButton('Update Incident', callback_data='update_incident')
    itembtn3 = types.InlineKeyboardButton('Create Incident', callback_data='create_incident')
    markup.add(itembtn1, itembtn2, itembtn3)

    # Send a welcome message with options
    bot.send_message(message.chat.id,
                     "Hi, my name is InciBot. I can check, update and create incidents. What do you want to do?",
                     reply_markup=markup)


# Handle text messages to decide between checking or creating an incident
@bot.callback_query_handler(func=lambda message: True)
def handle_query(call):
    if call.data == 'check_incident':
        bot.send_message(call.message.chat.id, "Please enter the incident number:")
        bot.register_next_step_handler(call.message, check_incident)
    elif call.data == 'update_incident':
        bot.send_message(call.message.chat.id, "Please enter the incident number:")
        bot.register_next_step_handler(call.message, process_incident_number)
    elif call.data == 'create_incident':
        bot.send_message(call.message.chat.id, "Please describe the issue:")
        bot.register_next_step_handler(call.message, process_description)
    else:
        bot.send_message(call.message.chat.id, "Please choose an option from the menu.")


# Step 2: Handle creating an incident - Start with Description
def process_description(message):
    user_data['description'] = message.text
    bot.send_message(message.chat.id, "Did you have a Short Keyword for that?")
    bot.register_next_step_handler(message, process_short_description)


# Step 3: Ask for short description
def process_short_description(message):
    user_data['short_description'] = message.text
    # Present companies for selection
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for company in companies:
        markup.add(company)

    bot.send_message(message.chat.id, "For which customer do you create the Incident?", reply_markup=markup)
    bot.register_next_step_handler(message, process_customer)


# Step 4: Ask for customer
def process_customer(message):
    user_data['company'] = message.text

    # Present categories for selection
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for category in categories:
        markup.add(category)

    bot.send_message(message.chat.id, "In which Incident Category can you sort it? \n"
                                      "Hardware, Software, Network, Inquiry, Database", reply_markup=markup)
    bot.register_next_step_handler(message, process_category)


# Step 5: Ask for category
def process_category(message):
    user_data['category'] = message.text

    # Present subcategories based on the selected category
    selected_category = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)

    # Check if the selected category exists and retrieve subcategories
    subcategory_list = subcategories.get(selected_category, [])

    # If there are no subcategories for the selected category
    if not subcategory_list:
        bot.send_message(message.chat.id, "No subcategories available for this category.")
        return

    # Create a string of subcategories to display
    subcategory_options = "\n".join(subcategory_list)

    # Inform the user about the available subcategories
    bot.send_message(
        message.chat.id,
        f"In which subcategory can you sort it? Here are your options:\n{subcategory_options}",
        reply_markup=markup)
    bot.register_next_step_handler(message, process_subcategory)


# Step 6: Ask for subcategory
def process_subcategory(message):
    user_data['subcategory'] = message.text

    # Present urgency levels for selection
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)

    # Define urgency levels
    for urgency in urgency_levels:
        markup.add(urgency)

    bot.send_message(message.chat.id, "How is the Urgency? \n Low, Medium, High.", reply_markup=markup)
    bot.register_next_step_handler(message, process_urgency)


# Step 7: Ask for urgency and finalize incident creation
def process_urgency(message):
    user_data['urgency'] = message.text

    # Create the incident in ServiceNow with the collected data
    result = create_incident(user_data)
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['help'])
def send_help(message):
    # Create a custom keyboard
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Update Incident')
    itembtn2 = types.KeyboardButton('Create Incident')
    markup.add(itembtn1, itembtn2)

    # Send a welcome message with options
    bot.send_message(message.chat.id,
                     "Hi, my name is InciBot. What do you need help with?",
                     reply_markup=markup)


# Handle text messages to decide between checking or creating an incident
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == 'Update Incident':
        bot.send_message(message.chat.id, "If you want to check information about incident, "
                                          "please enter the incident number:")
        bot.register_next_step_handler(message, update_incident)
    elif message.text == 'Create Incident':
        bot.send_message(message.chat.id, "If you want to create a new incident you need to "
                                          "provide me some information. Please describe the issue:")
        bot.register_next_step_handler(message, process_description)
    else:
        bot.send_message(message.chat.id, "Please choose an option from the menu.")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "I don't get you, write /help.")


bot.polling(none_stop=True)
