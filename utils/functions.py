
import re
from autogen import config_list_from_json

from utils.email_utils import fetch_emails, get_gmail_service, get_user_email, parse_email_data


def get_llm_config():
    config_list = config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={"model": ["gpt-4o-mini"]},
    )
    llm_config = {"config_list": config_list, "timeout": 60}
    return llm_config


def get_gmail_info():
    # -------------- Connect to Google Email --------------
    # Get the Gmail service (this will prompt you to authenticate if needed)
    gmail_service = get_gmail_service()
    print(f"Got gmail_service: {gmail_service}")

    # Get the logged-in user's email address
    user_email = get_user_email(gmail_service)
    print(f"Logged in as: {user_email}")

    return user_email, gmail_service


def fetch_all_emails(gmail_service, max_unread_emails_limit):
    # Loop through pages to fetch all unread emails
    unread_emails = []
    page_token = None

    while True:
        messages, page_token = fetch_emails(
            gmail_service, page_token, filter_by=['UNREAD', 'INBOX']
        )
        print(f"messages {messages}")
        if not messages:
            break

        for msg in messages:
            email_data = parse_email_data(gmail_service, msg)
            if email_data:
                unread_emails.append(email_data)
            if len(unread_emails) >= max_unread_emails_limit:
                break
        if not page_token or len(unread_emails) >= max_unread_emails_limit:
            break
    print(f"Unread emails: {unread_emails}")
    return unread_emails


def sort_and_trim_emails(grouped_emails):
    sorted_grouped_emails_tuple = sorted(
        grouped_emails.items(), key=lambda x: len(x[1]), reverse=True
    )

    email_regex = re.compile(r'<([^>]+)>')

    sorted_grouped_emails = {}

    for sender, emails in sorted_grouped_emails_tuple:
        match = email_regex.search(sender)
        stripped_sender = match.group(1) if match else sender
        sorted_grouped_emails[stripped_sender] = emails

    print(f"Sorted_grouped_emails: {sorted_grouped_emails}")

    return sorted_grouped_emails


def get_context(unread_emails):
    context = ""
    for email in unread_emails:
        context += f"Email ID: {email['message_id']}\n"
        context += f"Thread ID: {email['thread_id']}\n"
        context += f"From: {email['from']}\n"
        context += f"Subject: {email['subject']}\n"
        context += "\n"
    context_variables = {
        "user_emails_context": f"""Here is what you know about the user's email details: {context}
    """}
    return context_variables
