
from typing import List, Union
from utils.email_utils import create_draft, fetch_email_thread, group_emails_by_sender, mark_email_as_read, send_draft
from utils.functions import fetch_all_emails, get_gmail_info, sort_and_trim_emails

read_email_ids = []
unread_emails = []
user_email, gmail_service = get_gmail_info()


def fetch_unread_emails():
    global unread_emails
    emails = fetch_all_emails(gmail_service, 20)
    unread_emails = emails
    return emails


def mark_all_from_sender_as_read(sender: str) -> str:
    """ Marks email as read n bulk based on sender"""

    try:
        grouped_emails = group_emails_by_sender(unread_emails)

        sorted_grouped_emails = sort_and_trim_emails(grouped_emails)
        emails = sorted_grouped_emails[sender]
    except KeyError:
        return f"No emails found from {sender}."
    # print warning message: sender, first 10 email subjects and random 3 email bodies
    print("*" * 100)
    print("*" * 100)
    print(f"WARNING: Marking all emails as read from {sender}")
    for email in emails[:25]:
        print(f"Selected Email Subject: {email['subject']}")
    print("*" * 100)
    print("*" * 100)
    user_input = input("Do you want to continue? (yes/no): ")
    if user_input.lower() == "yes" or user_input.lower() == "y":
        print("Marking all emails as read...")
        # mark all emails as read
        for email in emails:
            read_email_ids.append(email["message_id"])
            mark_email_as_read(gmail_service, email["message_id"])
        return "All emails marked as read successfully!"
    else:
        return "Operation cancelled by user."


def mark_one_email_as_read(email_id: str) -> str:
    """ Marks a single email as read based on its id after user confirmation"""
    read_email_ids.append(email_id)
    return mark_email_as_read(
        gmail_service, email_id
    )


def get_email_body(email_id: str) -> str:
    """Get the body of an email by email id"""
    for email in unread_emails:
        if email["message_id"] == email_id:
            return email["body"]
    return "Email not found."


def get_full_thread(email_thread_id: str) -> str:
    """Get the full thread of an email."""
    return fetch_email_thread(gmail_service, email_thread_id)


def write_draft(to: str, subject: str, body: str, cc: Union[str, List[str]] = None,
                bcc: Union[str, List[str]] = None, attachment_paths: List[str] = None,
                thread_id: str = None) -> str:
    """ Create a draft email
    Args:
        to: Email address(es) of the recipient(s)
        subject: Email subject
        body: Plain text body of the email
        cc: Email address(es) to CC
        bcc: Email address(es) to BCC
        attachment_paths: List of file paths to attach
        thread_id: Thread ID to add this draft to (for replies)
    Returns:
        String with draft creation result
    """
    return create_draft(gmail_service, to, subject, body, cc, bcc, attachment_paths, thread_id)


def send(draft_id: str) -> str:
    """ Send a draft by draft id """
    return send_draft(gmail_service, draft_id)
