import streamlit as st
from autogen import UserProxyAgent, ConversableAgent, run_swarm
from autogen.agentchat.contrib.swarm_agent import (
    AfterWork, AfterWorkOption, initiate_swarm_chat, OnCondition, register_hand_off
)
from autogen.io.run_response import RunResponseProtocol
from utils.functions import get_llm_config
from utils.tools import (
    fetch_unread_emails, get_email_body, get_full_thread,
    mark_all_from_sender_as_read, mark_one_email_as_read,
    send, write_draft
)

st.set_page_config(page_title="Email Triage Assistant")

# --- Session State Defaults ---
st.session_state.setdefault("messages", [])
st.session_state.setdefault("run_response", None)
st.session_state.setdefault("awaiting_input", False)
st.session_state.setdefault(
    "input_prompt", "Say something to the email assistant!")
st.session_state.setdefault("response_hook", None)

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- LLM and Agents Setup ---


def run_swarm_chat(initial_input) -> RunResponseProtocol:
    llm_config = get_llm_config()

    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=1,
        code_execution_config=False,
        is_termination_msg=lambda x: x.get(
            "content", "").rstrip().endswith("TERMINATE"),
    )

    triage_agent = ConversableAgent(
        name="triage_agent",
        llm_config=llm_config,
        system_message="""You are a triage agent for emails...""",  # abbreviazione per leggibilità
        functions=[
            fetch_unread_emails, mark_one_email_as_read,
            mark_all_from_sender_as_read, get_email_body
        ],
    )

    writer_agent = ConversableAgent(
        name="writer_agent",
        llm_config=llm_config,
        system_message="""You are a professional email drafting assistant...""",
        functions=[get_full_thread, write_draft, send],
    )

    register_hand_off(
        agent=triage_agent,
        hand_to=[OnCondition(writer_agent, "To write a draft")],
    )

    return run_swarm(
        triage_agent,
        agents=[triage_agent, writer_agent],
        messages=initial_input,
        user_agent=user_proxy,
        after_work=AfterWork(AfterWorkOption.REVERT_TO_USER),
    )


# --- Gestione dell’input dell’utente in attesa ---
if st.session_state.awaiting_input:
    prompt = st.chat_input(st.session_state.input_prompt)
    if prompt:
        st.session_state.response_hook(prompt)
        st.session_state.awaiting_input = False
        st.session_state.response_hook = None
        st.rerun()

# --- Gestione di eventi attivi ---
elif st.session_state.run_response:
    for event in st.session_state.run_response.events:
        print('+++++++' * 10)
        print(event)
        print('+++++++' * 10)
        if event.type == "text":
            st.session_state.messages.append({
                "role": event.content.sender,
                "content": event.content.content
            })
            st.rerun()
        elif event.type == "input_request":
            st.session_state.awaiting_input = True
            st.session_state.input_prompt = event.content.prompt
            st.session_state.response_hook = event.content.respond
            st.rerun()

    with st.chat_message("System"):
        summary = st.session_state.run_response.summary or "*The session has ended.*"
        st.markdown(f"**[Summary]** {summary}")
    st.stop()

# --- Nuova conversazione ---
else:
    prompt = st.chat_input("Say something to the email assistant!")
    if prompt:
        st.session_state.run_response = run_swarm_chat(prompt)
        st.rerun()
