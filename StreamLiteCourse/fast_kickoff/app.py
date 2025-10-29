import base64
import os
import requests # You'll need to install this library: pip install requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Try to use NLTK VADER, fallback to simple sentiment analysis if not available
try:
    import ssl
    # Disable SSL verification for NLTK downloads (workaround)
    ssl._create_default_https_context = ssl._create_unverified_context

    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer

    # Set NLTK data path to a writable location
    nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)
    nltk.data.path.insert(0, nltk_data_dir)

    # Try to load VADER, download if needed
    try:
        nltk.data.find('vader_lexicon')
        sia = SentimentIntensityAnalyzer()
        USE_NLTK = True
    except LookupError:
        try:
            nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
            sia = SentimentIntensityAnalyzer()
            USE_NLTK = True
        except:
            USE_NLTK = False
            sia = None

except ImportError:
    USE_NLTK = False
    sia = None
    nltk = None

def analyze_sentiment_simple(text):
    """Simple sentiment analysis fallback when NLTK is not available"""
    if not text:
        return 0.0, []

    text_lower = text.lower()

    # Simple positive/negative word lists
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'awesome', 'love', 'best', 'happy', 'satisfied', 'resolved', 'fixed', 'thank', 'thanks', 'appreciate', 'helpful']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'angry', 'frustrated', 'issue', 'problem', 'error', 'bug', 'broken', 'fail', 'failed', 'crash', 'stuck', 'slow', 'delay', 'waiting']

    words = text_lower.split()
    positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
    negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))

    # Calculate simple polarity score
    total_words = len(words)
    if total_words == 0:
        return 0.0, []

    polarity = (positive_count - negative_count) / max(total_words, 1)
    polarity = max(-1.0, min(1.0, polarity))  # Clamp between -1 and 1

    # Extract key words
    key_words = []
    for word in words:
        if any(pos in word for pos in positive_words) or any(neg in word for neg in negative_words):
            key_words.append(word)

    return polarity, list(set(key_words))[:5]  # Return unique words, max 5

# Replace with your actual Zendesk email and API key
email = "leonardo.quinones@unity3d.com"
# It's best practice to store your API token securely, e.g., as an environment variable
# For this example, we'll use a placeholder, but in a real application, use os.getenv()
# FROm Streamlit cloud 
api_token = st.secrets.get("ZENDESK_API_KEY", os.getenv("ZENDESK_API_KEY", "MY_ZENDESK_KEY"))
# api_token = os.getenv("ZENDESK_API_KEY", "MY_ZENDESK_KEY")

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
tab1, tab2, tab3, tab4 = st.tabs(["📋 Fetch Tickets", "📊 Status Timeline", "📄 Tickets Status Details", "🤖 Sentiment Analysis"])

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
            
                # Download NLTK data for sentiment analysis
                try:
                    nltk.data.find('vader_lexicon')
                except LookupError:
                    nltk.download('vader_lexicon')
                try:
                    nltk.data.find('punkt')
                except LookupError:
                    nltk.download('punkt')

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
        ticket_options
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
    
        if len(selected_tickets_display) < 2:
            st.info("Please select at least 2 tickets to compare.")
    
    # Tab 4: Sentiment Analysis
    with tab4:
        st.header("Sentiment Analysis of Ticket Subjects")
    
        # Check if tickets are available in session state
        if 'tickets' not in st.session_state:
            st.warning("Please fetch tickets first in the 'Fetch Tickets' tab.")
            st.stop()
    
        tickets = st.session_state.tickets
    
        # Display sentiment analysis status
        if USE_NLTK and sia:
            st.success("✅ Using NLTK VADER for sentiment analysis")
        else:
            st.warning("⚠️ Using simple sentiment analysis (NLTK not available)")
            st.info("For better accuracy, install NLTK: pip install nltk")

        # Analyze sentiment button
        if st.button("Analyze Sentiment of All Tickets"):
            if sia is None:
                st.error("Sentiment analysis not available. NLTK data could not be loaded.")
            else:
                st.write("Analyzing sentiment for all ticket subjects...")

                # Perform sentiment analysis
                sentiment_data = []
                for ticket in tickets:
                    subject = ticket.get('subject', '')
                    if subject:
                        # Use NLTK VADER for sentiment analysis (more reliable than TextBlob for short texts)
                        sentiment_scores = sia.polarity_scores(subject)
                        polarity = sentiment_scores['compound']  # Overall sentiment score

                        # Determine sentiment category based on compound score
                        if polarity > 0.05:
                            sentiment = "Positive"
                            emoji = "😊"
                        elif polarity < -0.05:
                            sentiment = "Negative"
                            emoji = "😞"
                        else:
                            sentiment = "Neutral"
                            emoji = "😐"

                        # Extract key words that contribute to sentiment using VADER
                        words = subject.split()
                        word_sentiments = []
                        for word in words:
                            word_scores = sia.polarity_scores(word)
                            word_sentiments.append((word, word_scores['compound']))

                        # Sort by absolute compound score and take top 3
                        top_words = sorted(word_sentiments, key=lambda x: abs(x[1]), reverse=True)[:3]
                        key_words = [word for word, score in top_words if abs(score) > 0.1]

                        # Calculate subjectivity (simplified approach using VADER)
                        subjectivity = sentiment_scores.get('neu', 0.5)  # Neutral score as subjectivity proxy
    
                    sentiment_data.append({
                        'ticket_id': ticket['id'],
                        'subject': subject,
                        'sentiment': sentiment,
                        'emoji': emoji,
                        'polarity': round(polarity, 3),
                        'subjectivity': round(subjectivity, 3),
                        'key_words': ', '.join(key_words) if key_words else 'N/A',
                        'created_date': ticket.get('created_at', '')[:10] if ticket.get('created_at') else 'N/A'
                    })
    
            if sentiment_data:
                sentiment_df = pd.DataFrame(sentiment_data)
    
                # Sentiment Distribution Chart
                st.subheader("Sentiment Distribution")
                sentiment_counts = sentiment_df['sentiment'].value_counts()
    
                fig = px.pie(sentiment_counts,
                            values=sentiment_counts.values,
                            names=sentiment_counts.index,
                            title="Overall Sentiment Distribution",
                            color=sentiment_counts.index,
                            color_discrete_map={
                                'Positive': 'green',
                                'Negative': 'red',
                                'Neutral': 'gray'
                            })
                st.plotly_chart(fig, use_container_width=True)
    
                # Sentiment Over Time
                st.subheader("Sentiment Over Time")
                if sentiment_df['created_date'].str.contains('-').any():
                    # Convert to datetime for plotting
                    sentiment_df['date'] = pd.to_datetime(sentiment_df['created_date'], errors='coerce')
                    sentiment_df = sentiment_df.dropna(subset=['date'])
    
                    # Group by date and sentiment
                    time_sentiment = sentiment_df.groupby([sentiment_df['date'].dt.date, 'sentiment']).size().unstack(fill_value=0)
    
                    if not time_sentiment.empty:
                        fig_time = px.bar(time_sentiment,
                                        title="Sentiment Trends Over Time",
                                        labels={'value': 'Number of Tickets', 'date': 'Date'},
                                        color_discrete_map={
                                            'Positive': 'green',
                                            'Negative': 'red',
                                            'Neutral': 'gray'
                                        })
                        st.plotly_chart(fig_time, use_container_width=True)
    
                # Detailed Sentiment Table
                st.subheader("Detailed Sentiment Analysis")
    
                # Color code the dataframe based on sentiment
                def color_sentiment(val):
                    if val == 'Positive':
                        return 'background-color: lightgreen'
                    elif val == 'Negative':
                        return 'background-color: lightcoral'
                    else:
                        return 'background-color: lightgray'
    
                styled_df = sentiment_df[['ticket_id', 'subject', 'sentiment', 'polarity', 'subjectivity', 'key_words']].style.applymap(
                    color_sentiment, subset=['sentiment']
                )
    
                st.dataframe(styled_df, use_container_width=True)
    
                # Sentiment Statistics
                st.subheader("Sentiment Statistics")
                col1, col2, col3 = st.columns(3)
    
                with col1:
                    avg_polarity = sentiment_df['polarity'].mean()
                    st.metric("Average Polarity", "+.3f", delta=None)
    
                with col2:
                    avg_subjectivity = sentiment_df['subjectivity'].mean()
                    st.metric("Average Subjectivity", "+.3f")
    
                with col3:
                    most_common = sentiment_df['sentiment'].mode().iloc[0]
                    st.metric("Most Common Sentiment", most_common)
    
                # Download sentiment analysis results
                csv = sentiment_df.to_csv(index=False)
                st.download_button(
                    label="Download Sentiment Analysis CSV",
                    data=csv,
                    file_name="ticket_sentiment_analysis.csv",
                    mime="text/csv",
                    key="sentiment_download"
                )
    
            else:
                st.warning("No valid ticket subjects found for analysis.")
