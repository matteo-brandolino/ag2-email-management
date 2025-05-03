# Email Management Assistant

An intelligent email management tool that leverages AG2’s swarm agents to help you quickly triage, filter, and respond to your emails. This application connects to Gmail, groups unread emails by sender, and offers two steps of automated assistance:

- **Mark as read in Batch:** Identify and mark groups of non-critical emails from the same sender as read.
- **Individual actions:** Read, summarize, and assist in drafting replies for emails requiring your attention.

## Detailed Description

This project streamlines your email workflow by performing the following tasks:

- **Connecting to Gmail:** Securely authenticates and retrieves unread emails.
- **Grouping Emails:** Organizes emails by sender and provides summaries (including subject lines and excerpts from the email body) for rapid review.
- **Bulk Filtering:** Utilizes a swarm agent (_filter_agent_) to analyze email groups, suggesting which sender groups can be marked as read, and then confirms with the user before executing the bulk action.
- **Individual Email Assistance:** Deploys another swarm agent (_email_assistant_) to classify each email, determining whether an email should be marked as read directly or read in full for further review. The agent also assists in summarizing key points and drafting responses when needed.

## AG2 Features

This project demonstrates several key AG2 features:

- **[Swarm Agent](https://docs.ag2.ai/docs/user-guide/advanced-concepts/swarm/deep-dive):** Multiple agents work together to manage different aspects of email processing.
- **[Tool using](https://docs.ag2.ai/docs/user-guide/basic-concepts/tools):** Agents trigger Python functions (e.g., marking emails as read, retrieving email threads) based on real-time context.

For further details on these features, please refer to the [AG2 Documentation](https://docs.ag2.ai/docs/Home).

## TAGS

TAGS: swarm, function-call, tool-use, email management, automation, gmail integration, email triage, workflow optimization, ai assistant

## Installation

### 1. Start by cloning the repository:

```bash
git clone https://github.com/ag2ai/build-with-ag2.git
cd email-management
```

### 2. Then, install the required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

First, You need to obtain API keys from OpenAI. Sign up for OpenAI [here](https://platform.openai.com/).
Then, create a `OAI_CONFIG_LIST` file based on the provided `OAI_CONFIG_LIST_sample`:

```bash
cp OAI_CONFIG_LIST_sample OAI_CONFIG_LIST
```

You also need to set up google credentials to access Gmail API. Search for "Gmail API" in the Google Cloud Console and enable the API.
Follow the instructions [here](https://developers.google.com/workspace/guides/create-credentials) to set up the credentials and download the `credentials.json` file. Place the `credentials.json` file in the root directory of the project.
You get the credentials.json from the `OAuth 2.0-Client-IDs` auth option, other options will not work.

## Running the Code

1. **Settings**

   In `main.py`, set the `max_unread_emails_limit` to be the maximum number of unread emails to fetch at each run. By default, it is set to 20. By default, `is_mock_read_email` is set to `True` to mock the read email action. If set to `True`, emails in your Gmail account will be marked as read. Please be careful to modify this setting.

2. **Execute the Main Script:**
   Run the primary script to start the assistant:
   ```bash
   python main.py
   ```
   The script will prompt you to authenticate your Gmail account and authorize the application to access your emails. A `token.json` file will be generated to store the authentication token for future use.
   Then you can interact with the manager to triage your emails.

## Contact

For more information or any questions, please refer to the documentation or reach out to us!

- AG2 Documentation: https://docs.ag2.ai/docs/Home
- AG2 GitHub: https://github.com/ag2ai/ag2
- Discord: https://discord.gg/pAbnFJrkgZ

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) for details.
