from googleapiclient.discovery import build

import oauth as oauth
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



def get_message(query, user_email="david.ng.pub@gmail.com"):
    """Get all messages in a thread given a message ID"""
    if not oauth.is_user_logged_in(user_email):
        raise Exception("User not logged in.")
    creds = oauth.get_user_credentials(user_email)
    service = build("gmail", "v1", credentials=creds)

    [message] = service.users().messages().list(
            userId='me',
            q=query,  # Gmail search query
            maxResults=1
        ).execute().get('messages',[])
    if not message:
        raise Exception("No messages found.")
    message= service.users().messages().get(
        userId='me',
        id=message['id'],
        format='full'
    ).execute()
    mail_from = next(h['value'] for h in message['payload']['headers'] if h['name'] == 'From')
    main_to = next(h['value'] for h in message['payload']['headers'] if h['name'] == 'To')
    body = decode_message(message)
    print({
        "from": mail_from,
        'to': main_to,
        'body': body,
    })



# Usage
thread_data = get_message('from:c.vandeursen@elsevier.com AND subject:laptop', "david.ng.pub@gmail.com")

