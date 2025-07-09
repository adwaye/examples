"""Runs the reply email app."""

from __future__ import annotations

import time

from client import GmailApi
from ollama import chat
from ollama import ChatResponse


def main():
    """App that replies to emails."""
    client = GmailApi()

    sender = "adwayerambojun@gmail.com"
    num_emails = 0
    while True:
        emails = client.find_email_id_by_sender(sender)
        email_ids = [email["id"] for email in emails]
        contents = [client.get_email_full(email_id) for email_id in email_ids]
        sorted_dict = sorted(contents, key=lambda item: item[0]["date"])
        # contents = [f for f in contents if 'UNREAD' in f[0]['labelIdS']]
        print("------------------------------------------------")
        print(sorted_dict[-1])
        print(len(sorted_dict[-1]))
        print(sorted_dict[-1][1]["labelIds"])
        # break

        # print(f"Content of the emails matching sender '{sender}':")
        _num_emails = len(contents)
        if _num_emails > num_emails:

            # sorted_dict = {k,v for k,v in sorted_dict if }
            content = sorted_dict[-1]
            # for content in contents:
            print(content)
            response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "user",
                        "content": f'{content[0]["message"]}',
                    },
                ],
            )
            # print(response.message.content)
            sender = "adwayeaiagent@gmail.com"
            raw_message = content[1]
            original_id = raw_message["id"]
            thread_id = raw_message["threadId"]
            raw_message_list = raw_message["payload"]["headers"]
            # fmt: off
            recipient_email = [
                f for f in raw_message_list if f["name"] == "From"
            ]
            # fmt: on
            recipient_email = recipient_email[0]["value"]
            # fmt: off
            reply_subject = [
                f for f in raw_message_list if f["name"] == "Subject"
            ]
            # fmt: on
            reply_subject = reply_subject[0]["value"]
            reply_body = "hi there"
            reply_message = client.create_reply(
                sender,
                recipient_email,
                original_id,
                thread_id,
                reply_subject,
                response.message.content,
            )
            print(reply_body)
            print(reply_message)
            num_emails = _num_emails

        time.sleep(30)


if __name__ == "__main__":
    main()
