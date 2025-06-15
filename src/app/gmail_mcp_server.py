from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build

import app.oauth as oauth
mcp = FastMCP("GMail assistant", streamable_http_path="/")

import base64

def decode_message_body(message_body):
    if message_body['size'] != 0:
        return base64.urlsafe_b64decode(message_body['data']).decode('utf-8').strip()
    return None

def decode_message_multiple_parts(parts):
    contents = []
    for part in parts:
        if part.get('mimeType') == 'text/plain':
            contents.append(decode_message_body(part['body']))
        for nested_parts in part.get('parts', []):
            nested_content = decode_message_multiple_parts(nested_parts)
            contents.append(nested_content)
    return "".join([content for content in contents if content is not None])

def decode_message(message):
    message_body = message['payload']['body']
    message_parts = message['payload'].get('parts', [])
    if message_parts:
        return decode_message_multiple_parts(message_parts)
    return decode_message_body(message_body)

@mcp.resource("email://gmail/{mail_address}/{message_id}")
async def get_mail_conversation(mail_address: str, message_id: str):
    if not oauth.is_user_logged_in(mail_address):
        return f"""Login is required!
Open {oauth.generate_authorization_url(mail_address)} to login."""
    creds = oauth.get_user_credentials(mail_address)
    service = build("gmail", "v1", credentials=creds)
    message= service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()
    mail_from = next(h['value'] for h in message['payload']['headers'] if h['name'] == 'From')
    main_to = next(h['value'] for h in message['payload']['headers'] if h['name'] == 'To')
    body = decode_message(message)
    return {
        "from": mail_from,
        'to': main_to,
        'conversation': body,
    }

@mcp.tool()
async def search_mailbox(query: str, mail_address: str):
    """

    Args:
    query: The query used to search the mailbox, syntax is the same as for Gmail search.

    Returns:
    Exactly one message matching the query.
    """
    if not oauth.is_user_logged_in(mail_address):
        return f"""Login is required!
Open {oauth.generate_authorization_url(mail_address)} to login."""
    creds = oauth.get_user_credentials(mail_address)
    service = build("gmail", "v1", credentials=creds)
    messages = service.users().messages().list(
        userId='me',
        q=query,  # Gmail search query
        maxResults=1
    ).execute().get('messages',[])
    if not messages:
        raise Exception("No messages found.")
    if len(messages) != 1:
        raise Exception("More than one message found.")
    return {
        "id": messages[0]['id']
    }
