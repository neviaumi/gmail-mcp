from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build
import base64

import app.oauth as oauth

mcp = FastMCP("GMail assistant", streamable_http_path="/")


def decode_message_body(message_body):
    """Decodes the body of a Gmail message from base64 to readable text.

    Args:
        message_body: A dictionary containing the message body data from Gmail API

    Returns:
        The decoded message text as a string, or None if the message body is empty
    """
    if message_body["size"] != 0:
        return base64.urlsafe_b64decode(message_body["data"]).decode("utf-8").strip()
    return None


def decode_message_multiple_parts(parts):
    """Decodes multipart Gmail message content recursively.

    This function handles messages with multiple parts (e.g., HTML and plain text)
    and recursively processes nested parts to extract all text content.

    Args:
        parts: A list of message part dictionaries from the Gmail API

    Returns:
        A string containing all the concatenated text content from the message parts
    """
    contents = []
    for part in parts:
        if part.get("mimeType") == "text/plain":
            contents.append(decode_message_body(part["body"]))
        for nested_parts in part.get("parts", []):
            nested_content = decode_message_multiple_parts(nested_parts)
            contents.append(nested_content)
    return "".join([content for content in contents if content is not None])


def decode_message(message):
    """Decodes a Gmail message to extract its text content.

    This function serves as the main entry point for message decoding. It determines
    whether the message has a simple body or multiple parts and calls the appropriate
    decoding function.

    Args:
        message: A complete message object from the Gmail API

    Returns:
        A string containing the decoded text content of the message
    """
    message_body = message["payload"]["body"]
    message_parts = message["payload"].get("parts", [])
    if message_parts:
        return decode_message_multiple_parts(message_parts)
    return decode_message_body(message_body)


@mcp.resource("email://gmail/{mail_address}/{message_id}")
@mcp.tool(
    "get_mail_conversation",
    "Get mail conversation by given mail address and message id",
)
async def get_mail_conversation(mail_address: str, message_id: str):
    """Retrieves a specific email conversation from Gmail.

    This function fetches a specific email message from the user's Gmail account
    using the provided message ID and decodes its content.

    Args:
        mail_address: Mail address to search
        message_id: Message Id inside mailbox

    Returns:
        A dictionary containing:
            - from: The sender's email address
            - to: The recipient's email address
            - conversation: The decoded content of the email
    """
    if not oauth.is_user_logged_in(mail_address):
        raise oauth.LoginRequiredException(mail_address)
    creds = oauth.get_user_credentials(mail_address)
    service = build("gmail", "v1", credentials=creds)
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    mail_from = next(
        h["value"] for h in message["payload"]["headers"] if h["name"] == "From"
    )
    main_to = next(
        h["value"] for h in message["payload"]["headers"] if h["name"] == "To"
    )
    body = decode_message(message)
    return {
        "from": mail_from,
        "to": main_to,
        "conversation": body,
    }


@mcp.tool("search_mailbox", "Search Gmail mailbox with a specific query")
async def search_mailbox(query: str, mail_address: str):
    """Searches a Gmail mailbox using a specific query and returns a single matching message.

    This function searches the user's Gmail mailbox using the provided query string
    and returns the ID of the first matching message. It will raise an exception if
    no messages are found or if multiple messages match the query.

    Args:
        query: The query used to search the mailbox, syntax is the same as for Gmail search.
        mail_address: The mail address to search inside

    Returns:
        A dictionary containing:
            - id: The ID of the matching message

    Raises:
        Exception: If no messages are found or if more than one message is found.
        LoginRequiredException: If the user is not logged in.
    """
    if not oauth.is_user_logged_in(mail_address):
        raise oauth.LoginRequiredException(mail_address)
    creds = oauth.get_user_credentials(mail_address)
    service = build("gmail", "v1", credentials=creds)
    messages = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,  # Gmail search query
            maxResults=1,
        )
        .execute()
        .get("messages", [])
    )
    if not messages:
        raise Exception("No messages found.")
    if len(messages) != 1:
        raise Exception("More than one message found.")
    return {"id": messages[0]["id"]}
