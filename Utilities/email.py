"""
Script Name - email.py (part of Utilities package).

Activation - Any script that imports the following - from Utilities.email import Email.
Moreover, initiate the email object using the call,
email = Email(sender_details=<sender_details_dict>, recipients=<list_of_recipients>, subject=<subject_string>)

Purpose - Emails are a convenient way to receive a report on the automation results. In general, there should be some
company email dedicated for automation.

Created by - Michael Samelsohn, 12/04/2024
"""

# Imports #
import os
import re
import smtplib
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Settings.settings import log


class Email:
    def __init__(self, sender_address: str, sender_password: str, recipients: list, subject: str,
                 server_host="smtp.gmail.com", server_port=587, body="", attachments=None):
        """
        Email class used to send an email.

        TODO: Probably need to set some default value for the sender details.
        :param server_host: The server host/domain (example - email.celeno.com).
        :param server_port: The port of the server host/domain.
        :param sender_address: The sender email address.
        :param sender_password: The password of the sender email address.
        Note - Important: To create an app password, you need 2-Step Verification on your Google Account:
            1) Go to your Google Account.
            2) Select Security.
            3) Under "How you sign in to Google," select 2-Step Verification.
            4) At the bottom of the page, select App passwords.
            5) Enter a name that helps you remember where you’ll use the app password.
            6) Select Generate.
            7) To enter the app password, follow the instructions on your screen. The app password is the 16-character
               code that generates on your device.
            8) Select Done.

        :param subject: The subject of the email.
        :param body: The body of the email.
        :param attachments: List of attachments to be added to the email.
        :param recipients: List of recipients to receive the email.

        TODO: Add usage examples.
        """

        self.server_host = server_host
        self.server_port = server_port
        self.sender_address = sender_address
        self.sender_password = sender_password

        self.subject = subject
        self.body = body
        self.attachments = attachments
        self.recipients = recipients

    def send(self) -> bool:
        """
        Send an email.

        :return: True if email sent successfully, False otherwise.
        """

        if self.__check_essential_parameters():
            log.debug("Configuring main email parameters")
            msg = MIMEMultipart()
            # Define the sender.
            msg["From"] = self.sender_address
            # Define the recipients (separated with a ';').
            msg["To"] = ' ;'.join(self.recipients)
            # Define the subject.
            msg["Subject"] = self.subject
            # Define the body.
            msg.attach(MIMEText(self.body, "html"))

            # Handling the attachments.
            if self.attachments is not None:
                log.debug("Adding attachments to the email")
                for attachment in self.attachments:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(open(attachment, "rb").read())
                    encoders.encode_base64(part)
                    part.add_header('content-disposition', 'attachment', filename=os.path.basename(attachment))
                    msg.attach(part)

            log.debug("Attempting to send the email")
            server = None
            try:
                server = smtplib.SMTP(host=self.server_host, port=self.server_port)
                server.ehlo()
                server.starttls()
                server.login(self.sender_address, self.sender_password)
                server.sendmail(self.sender_address, self.recipients, msg.as_string())
                log.info("Email sent successfully")
                return True
            except smtplib.SMTPSenderRefused:
                log.error("Client not authorized to send email")
                log.print_data(traceback.format_exc(), log_level="error")
            except smtplib.SMTPAuthenticationError:
                log.error("Client not authenticated (bad address or password)")
                log.print_data(traceback.format_exc(), log_level="error")
            finally:
                try:
                    server.quit()
                except smtplib.SMTPServerDisconnected:
                    return False
        else:
            log.error("Unable to send email due to one of the required parameters is missing or set incorrectly, "
                      "see errors above")
            return False

    def __check_essential_parameters(self) -> bool:
        """
        Assertion method for essential email parameters.
        The following checks are performed:
            * Sender email is valid.
            * Recipient email list is not empty and includes only valid Gmail domains.
            * TODO: Add a check that server is valid.
            * Server port is a non-negative integer.
            * TODO: Add a check for an empty subject? Is there a case where we need an empty subject?

        :return: True if all required parameters are defined correctly.
        """

        log.debug("Asserting that the server port is a non-negative integer")
        if self.server_port <= 0:
            log.error(f"Negative server port - {self.server_port}")
            return False

        log.debug("Asserting that sender email address is valid")
        if not self.__check_email_address_validity(email_address=self.sender_address) or self.sender_address == "":
            log.error(f"Invalid sender email address - {self.sender_address}")
            return False

        log.debug("Asserting that recipient list is valid")
        if not self.recipients:
            log.error("The recipients list is empty")
            return False
        else:
            # Recipient list is not empty.
            bad_emails = []  # Initializing a list of all bad emails.
            for email_address in self.recipients:
                if not self.__check_email_address_validity(email_address=email_address):
                    bad_emails.append(email_address)

            if bad_emails:
                log.error("Below are the invalid email addresses provided in the recipient list:")
                log.print_data(data=bad_emails, log_level="error")
                return False

        log.debug("Essential email parameters verified")
        return True

    @staticmethod
    def __check_email_address_validity(email_address: str) -> bool:
        """
        Assertion method for email address correctness.
        The regular expression that does the check, checks for the validity of the email address (no illegal sequences,
        see below) and that the Gmail domain (gmail.com) is the only approved. Here are some examples:
        Valid email addresses,
            niceandsimple@gmail.com - True
            very.common@gmail.com - True
            disposable.style.email.with+symbol@gmail.com - True
            other.email-with-dash@gmail.com - True
        Invalid email addresses,
            invalid..email@gmail.com - False (two dots in a row).
            -invalid-email@gmail.com - False (starts with a dash).
            invalid--email@gmail.com - False (two dashes in a row).
            niceandsimple@other.com - False (not Gmail domain).

        :param email_address: The email address under assertion.

        :return: True if email address is within the defined standard, False otherwise.
        """

        if not re.search(r"^[a-z0-9]+(?!.*(?:\+{2,}|\-{2,}|\.{2,}))(?:[\.+\-]{0,1}[a-z0-9])*@gmail\.com$",
                         email_address):
            return False

        # If we got to this point, the email is valid.
        return True

    def _email_parameters(self):
        """Used for debug, to understand what are the set email parameters"""
        log.info(f"Server details - {self.server_host}:{self.server_port}")
        log.info(f"Sender address - {self.sender_address}")
        log.info(f"List of recipients - {self.recipients}")
        log.info(f"Email subject - {self.subject}")
        log.info(f"Email body contains any context - {False if self.body is None else True}")
        log.info(f"Email attachments list - {self.attachments}")
