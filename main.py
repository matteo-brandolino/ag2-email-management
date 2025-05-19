from autogen import UserProxyAgent, ConversableAgent
from autogen.agentchat.contrib.swarm_agent import (
    AfterWork,
    AfterWorkOption,
    initiate_swarm_chat,
    OnCondition,
    register_hand_off,
)

from utils.functions import get_llm_config
from utils.tools import fetch_unread_emails, get_email_body, get_full_thread, mark_all_from_sender_as_read, mark_one_email_as_read, send, write_draft


llm_config = get_llm_config()

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
    system_message=f""""You are a triage agent for emails.
To get information about unread emails, you must call the fetch_unread_emails tool first, which will provide you with emails containing id, sender, and subject information.
All emails retrieved from fetch_unread_emails will be available for your analysis and triage.
1. Classify ALL the emails into:
- "Mark as read": If you think the email could be marked as read based on subject, from and body's email. Explain why the mail was classified like this.
- "Read full email to decide": If you need to read the full email to decide. Explain why the mail was classified like this.
2. After full emails are retrieved, outline the key points in short, concise sentences for each email. Make it short and informative.
3. Please identify what sender's email are less important and can be marked as read in bulk.
Given your suggestions on what emails by sender can be marked as read and always ask the user for confirmation before marking them as read.
4. Identify if any email requires a response and suggest this action.
If no further actions are needed, please reply with TERMINATE.
""",
    functions=[fetch_unread_emails, mark_one_email_as_read,
               mark_all_from_sender_as_read, get_email_body],
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
)
