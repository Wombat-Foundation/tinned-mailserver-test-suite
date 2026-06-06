import os
import smtplib
import pytest
from email.message import EmailMessage

PAYLOAD_DIR = os.path.join(os.path.dirname(__file__), "payload_files")

def read_payload(filename):
    path = os.path.join(PAYLOAD_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


def test_201_inbound_eicar_txt(mail_config, smtp_sender):
    """
    Test 201: Inbound message containing the EICAR test signature in a text attachment.
    Expects the mail server to reject the email with an SMTP error code (e.g. 550, 554).
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.TXT"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]    # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature in an attachment.\n"
        "It is expected to be rejected by the mail server's Anti-Virus filter.\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.TXT")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="octet-stream",
        filename="EICAR.TXT"
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
    # A rejection code should be 550, 554, or any error in SMTP block
    assert err.code in [550, 554, 501, 451, 452], f"Unexpected rejection SMTP code: {err.code}"


def test_202_inbound_gtube(mail_config, smtp_sender):
    """
    Test 202: Inbound message containing the GTUBE (Generic Test for Unsolicited Bulk Email) string.
    Expects the mail server to reject the email as spam.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound GTUBE"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]    # External sender

    # GTUBE string must be on a line by itself
    msg.set_content(
        "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"
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
    assert err.code in [550, 554, 501, 451, 452], f"Unexpected rejection SMTP code: {err.code}"


def test_203_inbound_eicar_zip(mail_config, smtp_sender):
    """
    Test 203: Inbound message containing the EICAR test signature inside a ZIP file.
    Expects the mail server to reject the email with an SMTP error code.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.COM-ZIP"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]    # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature in a ZIP attachment.\n"
        "It is expected to be rejected by the mail server's Anti-Virus filter.\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.COM-ZIP")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="zip",
        filename="EICAR.COM-ZIP.zip"
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
    assert err.code in [550, 554, 501, 451, 452], f"Unexpected rejection SMTP code: {err.code}"


def test_204_inbound_eicar_com(mail_config, smtp_sender):
    """
    Test 204: Inbound message containing the EICAR test signature as a raw .COM file attachment.
    Expects the mail server to reject the email with an SMTP error code.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.COM"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]    # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature as a raw .COM file.\n"
        "It is expected to be rejected by the mail server's Anti-Virus or File-Type filter.\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.COM")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="octet-stream",
        filename="EICAR.COM"
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
    assert err.code in [550, 554, 501, 451, 452], f"Unexpected rejection SMTP code: {err.code}"


def test_205_inbound_eicar_com2_zip(mail_config, smtp_sender):
    """
    Test 205: Inbound message containing the EICAR test signature inside a nested ZIP file (double compressed).
    Expects the mail server to reject the email if recursive scanning is enabled.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Inbound EICAR.COM2-ZIP"
    msg["To"] = mail_config["sender_main"]  # Local recipient
    msg["From"] = mail_config["recipient"]    # External sender
    msg.set_content(
        "Hi,\n\n"
        "This is a test email containing the EICAR test signature inside a nested ZIP file (double compressed).\n"
        "It is expected to be rejected by the mail server's Anti-Virus filter if recursive scanning is enabled.\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    payload_data = read_payload("EICAR.COM2-ZIP")
    msg.add_attachment(
        payload_data,
        maintype="application",
        subtype="zip",
        filename="EICAR.COM2-ZIP.zip"
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
    assert err.code in [550, 554, 501, 451, 452], f"Unexpected rejection SMTP code: {err.code}"
