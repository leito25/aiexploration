import base64
import os
import requests # You'll need to install this library: pip install requests
import streamlit as st

# Replace with your actual Zendesk email and API key
email = "leonardo.quinones@unity3d.com"
# It's best practice to store your API token securely, e.g., as an environment variable
# For this example, we'll use a placeholder, but in a real application, use os.getenv()
api_token = os.getenv("ZENDESK_API_KEY", "MY_ZENDESK_KEY")

# Construct the combined string
combined_str = f"{email}/token:{api_token}"

# Encode the string in Base64
encoded_bytes = base64.b64encode(combined_str.encode("utf-8"))
zd_base64_encoded_str = encoded_bytes.decode("utf-8")

# Prepare the Authorization header
headers = {
    "Authorization": f"Basic {zd_base64_encoded_str}",
    "Content-Type": "application/json"
}

# Example validation (optional)
if len(zd_base64_encoded_str) == 92:
    print('Zendesk validation OK')
    st.text('Zendesk validation OK')
else:
    print('Issues with Zendesk Token Validation')
    st.text('Issues with Zendesk Token Validation')

# Assuming 'headers' is already defined from the authentication snippet above
base_url = "https://unity3d1757688765.zendesk.com" #unity3d.zendesk.com #https://unity3d1757688765.zendesk.com
endpoint = "/api/v2/tickets.json"
url = base_url + endpoint

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status() # Raise an exception for HTTP errors
    tickets_data = response.json()
    print("Successfully retrieved tickets:")
    # print(json.dumps(tickets_data, indent=2)) # Uncomment to see full JSON response
    if tickets_data and 'tickets' in tickets_data:
        for ticket in tickets_data['tickets'][:300]: # Print first 3 tickets for brevity
            print(f"  ID: {ticket['id']}, Subject: {ticket['subject']}, Status: {ticket['status']}")
    else:
        print("No tickets found or unexpected response format.")
except requests.exceptions.RequestException as e:
    print(f"Error listing tickets: {e}")



# Replace '3' with an actual ticket ID you want to retrieve
ticket_id = st.number_input('Enter Ticket ID to retrieve:', min_value=1)
endpoint = f"/api/v2/tickets/{ticket_id}.json"
url = base_url + endpoint

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    single_ticket_data = response.json()
    print(f"\nSuccessfully retrieved details for Ticket ID {ticket_id}:")
    if single_ticket_data and 'ticket' in single_ticket_data:
        ticket = single_ticket_data['ticket']
        print(f"  Subject: {ticket['subject']}")
        st.text(f"  Subject: {ticket['subject']}")
        st.text(f"  Status: {ticket['status']}")
        st.text(f"  Description: {ticket['description'][:100]}...") # Print first 100 chars
    else:
        st.text("No data found for this ticket or unexpected response format.")
except requests.exceptions.RequestException as e:
    st.text(f"Error getting single ticket: {e}")
