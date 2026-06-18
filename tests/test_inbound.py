"""
Inbound SMTP Mail Server Test Cases.

This module validates inbound email delivery features, spam/AV blocking
(EICAR signatures, GTUBE patterns), and envelope-mismatch policies.
"""

import os
import smtplib
from email.message import EmailMessage

import pytest
from conftest import execute_delivery_test

PAYLOAD_DIR = os.path.join(os.path.dirname(__file__), "payload_files")

pytestmark = pytest.mark.usefixtures("smtp_inbound_connected")


def read_payload(filename: str) -> bytes:
    """Reads a binary virus or spam payload from the payload_files directory."""
    path = os.path.join(PAYLOAD_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


@pytest.mark.usefixtures("imap_authenticated")
def test_200_inbound_normal_delivery(
    mail_config,
    smtp_sender,
    imap_verifier,
) -> None:
    """
    Test 200: Normal inbound message delivery to local recipient.
    Sends a clean email from an external sender (port 25, STARTTLS)
    and verifies that it successfully arrives in the local user's IMAP INBOX.
    """
    execute_delivery_test(
        mail_config,
        smtp_sender,
        imap_verifier,
        subject_prefix="Swaks SMTP test - Inbound Normal Delivery",
        body_text=(
            "This is a normal test email sent via SMTP (port 25, STARTTLS).\n"
            "It is expected to be accepted and delivered to the INBOX."
        ),
        envelope_from=mail_config["recipient"],
        envelope_to=mail_config["sender_main"],
        msg_from=mail_config["recipient"],
        msg_to=mail_config["sender_main"],
        use_ssl=False,
        use_starttls=True,
        authenticate=False,
    )


def test_201_inbound_eicar_txt(mail_config, smtp_sender):
    """
    Test 201: Inbound message containing the EICAR test signature
    in a text attachment. Expects the mail server to reject the email.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.TXT"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]  # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature "
        "in an attachment.\n"
        "It is expected to be rejected by the mail server's Anti-Virus filter."
        "\n\nBest regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.TXT")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="octet-stream",
        filename="EICAR.TXT",
    )

    # Inbound tests: port 25, STARTTLS, no authentication
    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_202_inbound_gtube(mail_config, smtp_sender):
    """
    Test 202: Inbound message containing the GTUBE string.
    Expects the mail server to reject the email as spam.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound GTUBE"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]  # External sender

    # GTUBE string must be on a line by itself
    gtube = "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"
    msg.set_content(gtube)

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_203_inbound_eicar_zip(mail_config, smtp_sender):
    """
    Test 203: Inbound message containing the EICAR test signature
    inside a ZIP file. Expects the mail server to reject the email.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.COM-ZIP"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]  # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature "
        "in a ZIP attachment.\n"
        "It is expected to be rejected by the mail server's Anti-Virus filter."
        "\n\nBest regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.COM-ZIP")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="zip",
        filename="EICAR.COM-ZIP.zip",
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_204_inbound_eicar_com(mail_config, smtp_sender):
    """
    Test 204: Inbound message containing the EICAR test signature
    as a raw .COM file attachment. Expects the mail server to reject.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.COM"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]  # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature "
        "as a raw .COM file.\n"
        "It is expected to be rejected by the mail server's "
        "Anti-Virus or File-Type filter.\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.COM")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="octet-stream",
        filename="EICAR.COM",
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_205_inbound_eicar_com2_zip(mail_config, smtp_sender):
    """
    Test 205: Inbound message containing the EICAR test signature
    inside a nested ZIP file (double compressed). Expects rejection.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.COM2-ZIP"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]  # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature "
        "inside a nested ZIP file (double compressed).\n"
        "It is expected to be rejected by the mail server's "
        "Anti-Virus filter if recursive scanning is enabled.\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.COM2-ZIP")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="zip",
        filename="EICAR.COM2-ZIP.zip",
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_206_inbound_naitube_medium(mail_config, smtp_sender):
    """
    Test 206: Inbound message containing the NAItube Medium spam pattern.
    Expects the mail server to reject the email as spam.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound NAItube Medium"
    msg["To"] = mail_config["sender_main"]
    msg["From"] = mail_config["recipient"]
    msg.set_content(
        "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-MXL09*C.34X"
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_207_inbound_naitube_high(mail_config, smtp_sender):
    """
    Test 207: Inbound message containing the NAItube High spam pattern.
    Expects the mail server to reject the email as spam.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound NAItube High"
    msg["To"] = mail_config["sender_main"]
    msg["From"] = mail_config["recipient"]
    msg.set_content(
        "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-MXL10*C.34X"
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_208_inbound_naitube_critical(mail_config, smtp_sender):
    """
    Test 208: Inbound message containing the NAItube Critical spam pattern.
    Expects the mail server to reject the email as spam.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound NAItube Critical"
    msg["To"] = mail_config["sender_main"]
    msg["From"] = mail_config["recipient"]
    msg.set_content(
        "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-MXL11*C.34X"
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["recipient"],
            envelope_to=mail_config["sender_main"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            authenticate=False,
        )

    err = exc_info.value
    assert err.smtp_code in [
        550,
        554,
        501,
        451,
        452,
    ], f"Unexpected rejection SMTP code: {err.smtp_code}"


def test_254_inbound_mailinglist_from_mismatch_1(
    mail_config,
    smtp_sender,
):
    """
    Test 254: Inbound mailing list sender mismatch test.
    Ensures that mail is accepted when envelope MAIL FROM matches the mailing list
    but Header From contains the original sender address (typical mailing list
    behavior).
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender mismatch / mailinglist inbound"
    msg["To"] = mail_config["sender_main"]
    msg["From"] = mail_config["sender_mailinglist_origin"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test mailing list sender mismatch scenario.\n"
    )

    code, _ = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_mailinglist"],
        envelope_to=mail_config["sender_main"],
        message=msg,
        use_ssl=False,
        use_starttls=True,
        authenticate=False,
    )
    assert code == 250
