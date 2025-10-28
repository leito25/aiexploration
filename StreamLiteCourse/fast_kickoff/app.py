import base64
import os
import requests # You'll need to install this library: pip install requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

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
    st.success('Zendesk validation OK')
else:
    print('Issues with Zendesk Token Validation')
    st.error('Issues with Zendesk Token Validation')

# Assuming 'headers' is already defined from the authentication snippet above
base_url = "https://unity3d1757688765.zendesk.com" #unity3d.zendesk.com #https://unity3d1757688765.zendesk.com

st.title("Zendesk Tickets Dashboard")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📋 Fetch Tickets", "📊 Status Timeline", "📄 Tickets Status Details"])

# Tab 1: Fetch Tickets
with tab1:
    st.header("Fetch Tickets")

    # Number input for ticket count
    num_tickets = st.number_input('Enter number of tickets to fetch:', min_value=1, max_value=100, value=10, step=1)

    # Button to fetch tickets
    if st.button('Fetch Tickets'):
        st.write(f"Fetching {num_tickets} tickets...")

        # Construct URL with per_page parameter
        url = f"{base_url}/api/v2/tickets.json?per_page={num_tickets}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Raise an exception for HTTP errors
            tickets_data = response.json()

            if tickets_data and 'tickets' in tickets_data:
                tickets = tickets_data['tickets']

                # Prepare data for DataFrame
                ticket_list = []
                for ticket in tickets:
                    ticket_dict = {
                        'ID': ticket.get('id', 'N/A'),
                        'Subject': ticket.get('subject', 'N/A'),
                        'Status': ticket.get('status', 'N/A'),
                        'Requester': ticket.get('requester_id', 'N/A'),  # Will be ID for now
                        'Assignee': ticket.get('assignee_id', 'N/A'),    # Will be ID for now
                        'Type': ticket.get('type', 'N/A'),
                        'Due Date': ticket.get('due_at', 'N/A')
                    }
                    ticket_list.append(ticket_dict)

                # Create DataFrame
                df = pd.DataFrame(ticket_list)

                # Display DataFrame
                st.dataframe(df, use_container_width=True)

                st.success(f"Successfully fetched and displayed {len(tickets)} tickets.")

                # Store tickets in session state for chart tab
                st.session_state.tickets = tickets
                st.session_state.df = df

            else:
                st.warning("No tickets found or unexpected response format.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching tickets: {e}")

# Tab 2: Status Timeline
with tab2:
    st.header("Status Timeline Chart")

    # Check if tickets are available in session state
    if 'tickets' not in st.session_state:
        st.warning("Please fetch tickets first in the 'Fetch Tickets' tab.")
        st.stop()

    tickets = st.session_state.tickets

    # Date range controls
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        days_back = st.slider("Days back from today:", min_value=1, max_value=90, value=30)

    with col2:
        start_date = st.date_input("Start date:", value=datetime.now() - timedelta(days=30))

    with col3:
        end_date = st.date_input("End date:", value=datetime.now())

    # Use custom date range if selected, otherwise use days back
    if start_date and end_date and (start_date != datetime.now().date() - timedelta(days=30) or end_date != datetime.now().date()):
        date_range = (start_date, end_date)
    else:
        date_range = (datetime.now() - timedelta(days=days_back), datetime.now())

    # Ticket selection for chart
    ticket_options = [f"#{ticket['id']} - {ticket['subject'][:50]}..." for ticket in tickets]
    selected_tickets_display = st.multiselect("Select tickets to chart (max 5):", ticket_options, max_selections=5)

    if selected_tickets_display and st.button("Generate Status Chart"):
        # Extract ticket IDs from selection
        selected_ticket_ids = []
        for selection in selected_tickets_display:
            ticket_id = selection.split(' - ')[0].replace('#', '')
            selected_ticket_ids.append(int(ticket_id))

        st.write("Generating chart for tickets:", selected_ticket_ids)

        # Prepare data from current ticket status
        chart_data = []
        for ticket in tickets:
            if ticket['id'] in selected_ticket_ids:
                # Use creation date as the timeline point
                created_at = ticket.get('created_at', '')
                if created_at:
                    # Parse the date
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        # Calculate days from start of date range
                        days_from_start = (created_date.date() - date_range[0]).days

                        chart_data.append({
                            'ticket_id': ticket['id'],
                            'subject': ticket.get('subject', 'N/A')[:30],
                            'status': ticket.get('status', 'unknown'),
                            'created_date': created_date,
                            'days_from_start': max(0, days_from_start)  # Ensure non-negative
                        })
                    except:
                        continue

        if chart_data:
            # Create DataFrame for plotting
            chart_df = pd.DataFrame(chart_data)

            # Create scatter plot showing status distribution over time
            fig = px.scatter(chart_df, x='days_from_start', y='status',
                           color='status',
                           hover_data=['ticket_id', 'subject'],
                           title='Current Ticket Status Distribution Over Time',
                           labels={'days_from_start': 'Days from Start Date', 'status': 'Current Status'},
                           category_orders={'status': ['new', 'open', 'pending', 'solved', 'closed']})

            # Update y-axis to be categorical
            fig.update_yaxes(type='category')

            st.plotly_chart(fig, use_container_width=True)

            # Also show a summary table
            st.subheader("Status Summary")
            status_counts = chart_df['status'].value_counts()
            summary_df = pd.DataFrame({
                'Status': status_counts.index,
                'Count': status_counts.values
            })
            st.dataframe(summary_df, use_container_width=False)
        else:
            st.warning("No ticket data found for the selected tickets within the date range.")

# Tab 3: Tickets Status Details
with tab3:
    st.header("Ticket Status Details Comparison")

    # Check if tickets are available in session state
    if 'tickets' not in st.session_state:
        st.warning("Please fetch tickets first in the 'Fetch Tickets' tab.")
        st.stop()

    tickets = st.session_state.tickets

    # Ticket selection for comparison (minimum 2)
    ticket_options = [f"#{ticket['id']} - {ticket['subject'][:50]}..." for ticket in tickets]
    selected_tickets_display = st.multiselect(
        "Select tickets to compare (minimum 2):",
        ticket_options,
        max_selections=2
    )

    if len(selected_tickets_display) >= 2 and st.button("Compare Selected Tickets"):
        # Extract ticket IDs from selection
        selected_ticket_ids = []
        for selection in selected_tickets_display:
            ticket_id = selection.split(' - ')[0].replace('#', '')
            selected_ticket_ids.append(int(ticket_id))

        st.write(f"Comparing {len(selected_tickets_display)} tickets:")

        # Create comparison layout
        selected_tickets_data = []
        for ticket in tickets:
            if ticket['id'] in selected_ticket_ids:
                selected_tickets_data.append(ticket)

        # Display tickets in columns
        num_tickets = len(selected_tickets_data)
        cols = st.columns(min(num_tickets, 3))  # Max 3 columns

        for i, ticket in enumerate(selected_tickets_data):
            col_idx = i % 3
            with cols[col_idx]:
                # Status color mapping
                status_colors = {
                    'new': '🆕',
                    'open': '🔓',
                    'pending': '⏳',
                    'solved': '✅',
                    'closed': '🔒'
                }

                status_emoji = status_colors.get(ticket.get('status', 'unknown'), '❓')

                st.subheader(f"{status_emoji} Ticket #{ticket['id']}")

                # Key details
                st.write(f"**Subject:** {ticket.get('subject', 'N/A')}")
                st.write(f"**Status:** {ticket.get('status', 'N/A').title()}")
                st.write(f"**Type:** {ticket.get('type', 'N/A').title() if ticket.get('type') else 'N/A'}")
                st.write(f"**Priority:** {ticket.get('priority', 'N/A').title() if ticket.get('priority') else 'N/A'}")

                # Dates
                if ticket.get('created_at'):
                    created_date = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                    st.write(f"**Created:** {created_date.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.write("**Created:** N/A")

                if ticket.get('updated_at'):
                    updated_date = datetime.fromisoformat(ticket['updated_at'].replace('Z', '+00:00'))
                    st.write(f"**Updated:** {updated_date.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.write("**Updated:** N/A")

                if ticket.get('due_at'):
                    due_date = datetime.fromisoformat(ticket['due_at'].replace('Z', '+00:00'))
                    st.write(f"**Due Date:** {due_date.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.write("**Due Date:** N/A")

                # People
                st.write(f"**Requester ID:** {ticket.get('requester_id', 'N/A')}")
                st.write(f"**Assignee ID:** {ticket.get('assignee_id', 'N/A')}")

                # Description preview
                description = ticket.get('description', '')
                if description:
                    preview = description[:100] + "..." if len(description) > 100 else description
                    st.write(f"**Description:** {preview}")
                else:
                    st.write("**Description:** N/A")

                st.markdown("---")

        # Summary comparison table
        st.subheader("Comparison Summary")
        comparison_data = []
        for ticket in selected_tickets_data:
            comparison_data.append({
                'ID': ticket['id'],
                'Subject': ticket.get('subject', 'N/A')[:30] + "..." if len(ticket.get('subject', '')) > 30 else ticket.get('subject', 'N/A'),
                'Status': ticket.get('status', 'N/A').title(),
                'Type': ticket.get('type', 'N/A').title() if ticket.get('type') else 'N/A',
                'Priority': ticket.get('priority', 'N/A').title() if ticket.get('priority') else 'N/A',
                'Created': datetime.fromisoformat(ticket.get('created_at', '').replace('Z', '+00:00')).strftime('%Y-%m-%d') if ticket.get('created_at') else 'N/A',
                'Updated': datetime.fromisoformat(ticket.get('updated_at', '').replace('Z', '+00:00')).strftime('%Y-%m-%d') if ticket.get('updated_at') else 'N/A'
            })

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)

    elif len(selected_tickets_display) < 2:
        st.info("Please select at least 2 tickets to compare.")
