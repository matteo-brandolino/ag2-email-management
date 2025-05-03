import random
import re
from utils.email_utils import (
    fetch_emails,
    parse_email_data,
    group_emails_by_sender,
    mark_email_as_read,
    fetch_email_thread,
)
from autogen import UserProxyAgent, ConversableAgent
from autogen.agentchat.contrib.swarm_agent import (
    AfterWork,
    AfterWorkOption,
    initiate_swarm_chat,
    OnCondition,
    OnContextCondition,
    register_hand_off,
    SwarmAgent,
    SwarmResult,
)

from utils.functions import fetch_all_emails, get_gmail_info, get_llm_config, sort_and_trim_emails

llm_config = get_llm_config()
user_email, gmail_service = get_gmail_info()
max_unread_emails_limit = 20
is_mock_read_email = False

# Fetch unread emails
unread_emails = fetch_all_emails(gmail_service, max_unread_emails_limit)

# group_by_sender
grouped_emails = group_emails_by_sender(unread_emails)
sorted_grouped_emails = sort_and_trim_emails(grouped_emails)

read_email_ids = []

# -------- First, sort emails by sender. Provide the option to mark all emails from a specific sender as read. --------


def mark_all_from_sender_as_read(sender: str) -> str:
    try:
        emails = sorted_grouped_emails[sender]
    except KeyError:
        return f"No emails found from {sender}."
    # print warning message: sender, first 10 email subjects and random 3 email bodies
    print("*" * 100)
    print("*" * 100)
    print(f"WARNING: Marking all emails as read from {sender}")
    for email in emails[:10]:
        print(f"Selected Email Subject: {email['subject']}")

    random_emails = random.sample(emails, 1)
    for email in random_emails:
        print(f"Selected Email Body: {email['body']}")

    print("*" * 100)
    print("*" * 100)
    user_input = input("Do you want to continue? (yes/no): ")
    if user_input.lower() == "yes" or user_input.lower() == "y":
        print("Marking all emails as read...")
        # mark all emails as read
        for email in emails:
            read_email_ids.append(email["message_id"])
            if not is_mock_read_email:
                mark_email_as_read(gmail_service, email["message_id"])
        return "All emails marked as read successfully!"
    else:
        return "Operation cancelled by user."


user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    is_termination_msg=lambda x: x.get(
        "content", "").rstrip().endswith("TERMINATE"),
)

# construct input string
input_str = ""
for sender, emails in sorted_grouped_emails.items():
    # if len(emails) <= 1:
    #     continue
    input_str += f"{sender}: {len(emails)} emails\n"
    input_str += "First 5 email subjects:\n"
    for i, email in enumerate(emails[:10]):
        input_str += f"{i}. {email['subject']}\n"
    input_str += "\n"
    print("-" * 100)
    print("\n")

context_variables = {
    "user_emails_context": f"""Here is what you know about the user's email details: {sorted_grouped_emails}
"""}

filter_agent = ConversableAgent(
    name="filter_agent",
    llm_config=llm_config,
    system_message="""You are helping the user to read emails and mark them as read.
You will be given a list of senders with the number of emails from each sender.
Please identify what sender's email are less important and can be marked as read in bulk.
Given your suggestions on what emails by sender can be marked as read and ask the user for confirmation before marking them as read.

If you believe no further actions are needed,  ask user if they want to mark more emails as read.
If no further actions are needed, please reply with TERMINATE.""",
    functions=[mark_all_from_sender_as_read],
)

initiate_swarm_chat(
    filter_agent,
    agents=[filter_agent],
    messages=input_str,
    user_agent=user_proxy,
    after_work=AfterWork(AfterWorkOption.REVERT_TO_USER),
    context_variables=context_variables
)
# remove read emails from unread_emails
read_ids_set = set(read_email_ids)
unread_emails = [
    email for email in unread_emails if email["message_id"] not in read_ids_set]

# -------------- Part 2: Email Assistant to help with reading emails one by one, marking as read, and drafting responses --------------
# def mark_one_email_as_read(email_id: str) -> str:
#     read_email_ids.append(email_id)
#     if is_mock_read_email:
#         return "Successfully marked email as read."
#     return mark_email_as_read(
#         gmail_service, email_id
#     )  # send request to mark email as read


# def get_email_body(email_id: str) -> str:
#     for email in unread_emails:
#         if email["message_id"] == email_id:
#             return email["body"]
#     return "Email not found."


# def get_full_thread(email_thread_id: str) -> str:
#     """Get the full thread of an email."""
#     return fetch_email_thread(gmail_service, email_thread_id)


# email_assistant = ConversableAgent(
#     name="email_assistant",
#     llm_config=llm_config,
#     system_message="""You are an email assistant.
# All email with id, sender and subject will be provided to you.

# 1. Classify ALL the emails into:
# - "Mark as read": If you think the email can be marked as read directly.
# - "Read full email to decide": If you need to read the full email to decide.
# Confirm with the user and call corresponding functions.

# 2. After full emails are retrieved, outline the key points in short, concise sentences for each email. Make it short and informative.

# 3. Identify if any email requires a response. If so, ask the user if they want to draft a response to the email.
# call the function to get the full thread of the email and discuss with the user to draft a response. You should ask the user's intention and draft a response accordingly. Please put the email in ```txt``` format.
# """,
#     functions=[mark_one_email_as_read, get_email_body, get_full_thread],
# )

# # construct input string
# email_str = ""
# for email in unread_emails:
#     email_str += f"Email ID: {email['message_id']}\n"
#     email_str += f"Thread ID: {email['thread_id']}\n"
#     email_str += f"From: {email['from']}\n"
#     email_str += f"Subject: {email['subject']}\n"
#     email_str += "\n"


# initiate_swarm_chat(
#     email_assistant,
#     agents=[email_assistant],
#     messages=email_str,
#     user_agent=user_proxy,
#     after_work=AfterWork(AfterWorkOption.REVERT_TO_USER),
# )
