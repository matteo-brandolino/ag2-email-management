import random
from typing import List, Union
from utils.email_utils import (
    create_draft,
    fetch_email_thread,
    group_emails_by_sender,
    mark_email_as_read,
    send_draft,
)
from autogen import UserProxyAgent, ConversableAgent
from autogen.agentchat.contrib.swarm_agent import (
    AfterWork,
    AfterWorkOption,
    initiate_swarm_chat,
    OnCondition,
    register_hand_off,
)

from utils.functions import fetch_all_emails, get_context, get_gmail_info, get_llm_config, sort_and_trim_emails

# handle thread id

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

context_variables = get_context(unread_emails)

print(context_variables)

# -------- Tools ----------


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


def mark_one_email_as_read(email_id: str) -> str:
    """ Marks a single email as read based on its id after user confirmation"""
    read_email_ids.append(email_id)
    if is_mock_read_email:
        return "Successfully marked email as read."
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


user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    is_termination_msg=lambda x: x.get(
        "content", "").rstrip().endswith("TERMINATE"),
)


triage_agent = ConversableAgent(
    name="triage_agent",
    llm_config=llm_config,
    system_message=f"""You are a triage agent for emails.
All emails with id, sender and subject will be provided to you through context variables: {context_variables['user_emails_context']}.

1. Classify ALL the emails into:
- "Mark as read": If you think the email could be marked as read based on subject, from and body's email. Explain why the mail was classified like this.
- "Read full email to decide": If you need to read the full email to decide. Explain why the mail was classified like this.

2. After full emails are retrieved, outline the key points in short, concise sentences for each email. Make it short and informative.

3. Please identify what sender's email are less important and can be marked as read in bulk.
Given your suggestions on what emails by sender can be marked as read and always ask the user for confirmation before marking them as read.

4. Identify if any email requires a response and suggest this action.

If no further actions are needed, please reply with TERMINATE.
""",
    functions=[mark_one_email_as_read, get_email_body],
)

writer_agent = ConversableAgent(
    name="writer_agent",
    llm_config=llm_config,
    system_message=f"""You are a professional email drafting assistant dedicated to helping users create precise, effective, and polished email communications.

Your core responsibilities include:

1. Drafting Email Responses:
- Thoroughly analyze the context and tone of incoming emails
- Craft clear, concise, and professionally worded drafts
- Align responses with the user’s communication intent, considering the email’s context and recipient

2. Email Drafting Workflow:
a) Request specific guidance from the user about:
   - Desired tone (e.g., formal, friendly, direct)
   - Key points to include
   - Any special instructions or nuances
b) Offer multiple draft options if the user desires
c) Support iterative refinement to perfect the drafts

3. Reviewing Email Drafts:
- Proofread and suggest improvements
- Check for grammar, professionalism, clarity, length, and structure

Special Considerations:
- Be sensitive to varying communication contexts (business, personal, professional)
- Adapt style to user preferences and recipient type
- Maintain a neutral, helpful tone focused on achieving the user’s communication goals

When drafting, always confirm with the user and be ready to revise until the email meets their exact needs.
If the user wants to draft a reply, use the function to retrieve the full email thread through THREAD ID, and discuss the draft accordingly.
To reply, use the THREAD ID to preserve email history.
Always ask for the user’s intention before drafting a response.
Please format all email drafts within triple backticks as plain text (```txt```).
Use the send function only if the user confirms sending the reply.

If no further actions are needed, respond with TERMINATE.
""",
    functions=[get_full_thread, write_draft, send],
)


# Register hand-offs
register_hand_off(
    agent=triage_agent,
    hand_to=[
        OnCondition(writer_agent, "To write a draft"),
    ],
)

initiate_swarm_chat(
    triage_agent,
    agents=[triage_agent, writer_agent],
    messages='Handle my emails',
    user_agent=user_proxy,
    after_work=AfterWork(AfterWorkOption.REVERT_TO_USER),
    context_variables=context_variables
)
