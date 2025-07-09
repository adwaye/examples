# noqa D101
from __future__ import annotations

import base64
import logging
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, List, Tuple

from auth.auth import authenticate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# from twisted.words.protocols.jabber.jstrports import client
logging.basicConfig(level=logging.INFO)


class GmailApi:
    """Class to interact with Gmail API."""

    def __init__(self):
        """Initiate the GmailApi class."""
        creds = authenticate()
        self.service = build("gmail", "v1", credentials=creds)

    def find_email_id_by_sender(self, sender: str) -> List[Dict[str, str]]:
        """Find all emails from a given sender.

        Parameters
        ----------
        sender : str
            Email address of sender

        Returns
        -------
        List[Dict[str, str]]
            List of email ids example:
            [{'id': '197ee83ece9d9bfa', 'threadId': '197ee83ece9d9bfa'},]
        """
        logging.info("\n=============== Find Emails: start ===============")
        request = (
            self.service.users()
            .messages()
            .list(userId="me", q=f"from:{sender}", maxResults=200)
        )

        result = self._execute_request(request)
        try:
            messages = result["messages"]
            logging.info(
                f"Retrieved messages matching the {sender} query: {messages}",
            )
        except KeyError:
            logging.info(f"No messages found for the sender {sender}")
            messages = []
        logging.info(f"found {len(messages)} emails for sender {sender}")
        logging.info("=============== Find Emails: end ===============")

        return messages

    def get_email_full(
        self,
        email_id: str,
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Retrieve the full details of an email by its ID.

        Parameters
        ----------
        email_id : str
            Would be the 'id' key of the output of ``find_email_id_by_sender``

        Returns
        -------
        Tuple[Dict[str, str], Dict[str, str]]
            [simple_dict,meta_dict]
            Simple dict contains the 'date', 'read' and 'message'.
            Meta dict contains all other keys of the 'message' object.
        """
        logging.info("\n=============== Get Email: start ===============")

        result = self._get_email_raw(email_id)
        logging.info(f"Retrieved email with email_id={email_id}: {result}")
        logging.info(f"Email payload keys: {result['payload'].keys()}")
        try:
            content = result["payload"]["parts"][0]["body"]["data"]
        except KeyError:
            # If the email is not multipart,
            # the content will be in the body directly
            content = result["payload"]["body"]["data"]
        content = content.replace("-", "+").replace("_", "/")
        decoded = base64.b64decode(content).decode("utf-8")

        logging.info(f"Retrieved email with email_id={email_id}: {result}")
        logging.info("=============== Get Email: end ===============")
        res_list = result["payload"]["headers"]
        metadata = [f for f in res_list if f["name"] == "Date"]
        date_str = metadata[0]["value"]
        datetime_object = datetime.strptime(
            date_str,
            "%a, %d %b %Y %H:%M:%S %z",
        )

        read = "UNREAD" in result[-1][1]["labelIds"]
        return {
            "date": datetime_object,
            "message": decoded,
            "read": read,
        }, result

    def _get_email_raw(self, email_id):
        # todo: only get unread emails, and only get emails in the inbox folder
        request = self.service.users().messages().get(userId="me", id=email_id)
        result = self._execute_request(request)
        return result

    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)

    def create_reply(
        self,
        sender: str,
        to: str,
        original_message_id: str,
        thread_id: str,
        subject: str,
        body: str,
    ) -> Dict[str, str]:
        """Create a reply to an email.

        Parameters
        ----------
        sender : str
            Email from which the reply is sent from, usually same as the
            gmail address of the user.
        to : str
            Receiver of the reply.
        original_message_id : str
            email id, usually 'id' field of the output of
            ``find_email_id_by_sender``
        thread_id : str
            thread id, usually
            'threadId' field of the output of ``find_email_id_by_sender``
        subject : str
            Title of the reply
        body : str
            body of the email

        Returns
        -------
        Dict[str,str]
            {
            'raw': raw,
            'threadId': thread_id,
            } to be fed to ``send_reply``
        """
        message = MIMEText(body)
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject
        message["In-Reply-To"] = original_message_id
        message["References"] = original_message_id
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {
            "raw": raw,
            "threadId": thread_id,
        }

    def send_reply(
        self,
        user_id: str,
        message: Dict[str, str],
    ) -> None | Dict[str, str]:
        """Reply to an email.

        Parameters
        ----------
        user_id : str
            _description_
        message : Dict[str,str]
            Keys are 'raw' and 'threadId', with 'raw' containing an encoded
            message to be send.

        Returns
        -------
        Union[None,Dict[str,str]]
            None if there is an error, else a dict with the following keys:
                -   raw: the encoded message
                -   threadId: the ID of the thread that this message is part
                    of
        """
        try:
            message = (
                self.service.users()
                .messages()
                .send(userId=user_id, body=message)
                .execute()
            )
            print("Message Id: %s" % message["id"])
            return message
        except Exception as error:
            print(f"An error occurred: {error}")
            return None


if __name__ == "__main__":
    client = GmailApi()

    sender = "adwayerambojun@gmail.com"
    emails = client.find_email_id_by_sender(sender)
    email_ids = [email["id"] for email in emails]
    contents = [client.get_email_full(email_id) for email_id in email_ids]
    contents = sorted(contents, key=lambda item: item[0]["date"])
    content = contents[-1]

    original_text = content[1]["payload"]["parts"][0]["body"]["data"]
    original_text = original_text.replace("-", "+").replace("_", "/")
    decoded = base64.b64decode(original_text).decode("utf-8")

    raw_messages = [f[1] for f in contents]

    sender = "adwayeaiagent@gmail.com"
    original_id = raw_messages[0]["id"]
    thread_id = raw_messages[0]["threadId"]
    raw_message_list = raw_messages[0]["payload"]["headers"]
    recipient_email = [f for f in raw_message_list if f["name"] == "From"]
    recipient_email = recipient_email[0]["value"]
    reply_subject = [f for f in raw_message_list if f["name"] == "Subject"]
    reply_subject = reply_subject[0]["value"]
    reply_body = "hi there"

    # from ollama import chat
    # from ollama import ChatResponse

    # response: ChatResponse = chat(model='llama3.2', messages=[
    #     {
    #         'role': 'user',
    #         'content': f'{decoded}',
    #     },
    # ])

    # reply_message = client.create_reply(sender, recipient_email,
    #                              original_id, thread_id, reply_subject,
    #                              response.message.content)
    # client.send_reply(user_id='me',message=reply_message)
