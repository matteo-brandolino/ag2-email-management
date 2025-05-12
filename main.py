import random
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
    """ Marks a single email as read based on its id """
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


def write_draft(to: str, subject: str, body: str) -> str:
    """ Create a draft """
    return create_draft(gmail_service, to, subject, body)


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
- "Mark as read": If you think the email could be marked as read based on subject, from and body's email .
- "Read full email to decide": If you need to read the full email to decide.

2. After full emails are retrieved, outline the key points in short, concise sentences for each email. Make it short and informative.

3. Please identify what sender's email are less important and can be marked as read in bulk.
Given your suggestions on what emails by sender can be marked as read and ask the user for confirmation before marking them as read.

4. Identify if any email requires a response and suggest this action.

If no further actions are needed, please reply with TERMINATE.
""",
    functions=[mark_one_email_as_read, get_email_body],
)

writer_agent = ConversableAgent(
    name="writer_agent",
    llm_config=llm_config,
    system_message=f"""You are a professional email draft writer assistant designed to help users craft precise, effective email communications.
Your core responsibilities include:

1. Draft Email Responses:
- Carefully analyze the context and tone of incoming emails
- Create draft responses that are clear and concise, professionally worded, aligned with the user's communication intent, appropriate to the email's context and sender


2. Email Draft Workflow
a) Request specific guidance from the user about:
- Desired tone (formal, friendly, direct)
- Key points to include
- Any specific instructions or nuances
b) Provide multiple draft versions if the user wants options
c) Allow for iterative refinement of email drafts

3. Email Draft Review
- Proofread and suggest improvements to drafted emails
- Check for: grammatical correctness, professional language,clarity of message, appropriate length and structure


Special Considerations

- Be sensitive to different communication contexts (business, personal, professional)
- Adapt writing style based on user preferences and email recipient
- Maintain a neutral, helpful tone while supporting the user's communication goals

When drafting, always ask for user confirmation and be prepared to make multiple revisions to ensure the email meets the user's exact requirements
If user want to draft a response to the email, call the function to get the full thread of the email and discuss with the user to draft a response. 
You should ask the user's intention and draft a response accordingly. Please put the email in ```txt``` format.
Call the function send if user wants to send a repy message.

If no further actions are needed, please reply with TERMINATE.
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
