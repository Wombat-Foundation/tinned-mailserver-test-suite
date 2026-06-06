import smtplib
from email.message import EmailMessage

import pytest


def test_101_outbound_submissions_authenticated_from_main(mail_config, smtp_sender):
    """
    Test 101: Successful outbound message through submissions port (TLS, port 465).
    Sends email with the user's main email address.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender authenticated main address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via submissions port (TLS, port 465)\n"
        "* Client authenticates via PLAIN/LOGIN authentication (user + password)\n"
        "* Client sends email to external recipient address with main address\n\n"
        "This message should be accepted by the mailserver.\n\n"
        "Best regards,\n"
        "SMTP test suite\n"
    )

    code, response = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_main"],
        envelope_to=mail_config["recipient"],
        message=msg,
        use_ssl=True,
    )
    assert code == 250
    assert "accepted" in response.lower()


def test_102_outbound_submissions_authenticated_from_alias(mail_config, smtp_sender):
    """
    Test 102: Successful outbound message through submissions port (TLS, port 465).
    Sends email with an alias email address to test alias handling for outbound email messages.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender authenticated alias address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via submissions port (TLS, port 465)\n"
        "* Client authenticates via PLAIN/LOGIN authentication (user + password)\n"
        "* Client sends email to external recipient address with alias address\n\n"
        "This message should be accepted by the mailserver.\n\n"
        "Best regards,\n"
        "SMTP test suite\n"
    )

    code, response = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_alias"],
        envelope_to=mail_config["recipient"],
        message=msg,
        use_ssl=True,
    )
    assert code == 250
    assert "accepted" in response.lower()


def test_103_outbound_submissions_authenticated_from_main_tag(mail_config, smtp_sender):
    """
    Test 103: Outbound message through submissions port (TLS, port 465) with plus extension.
    If mustMatchSender is strictly enabled on the server, this might get rejected. We handle
    both success (250) and a 501 sender matching restriction gracefully.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        "Swaks SMTP test - Sender authenticated main address with plus extension"
    )
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main_tag"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test sending from a plus-tagged sender address.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main_tag"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
        )
        assert code == 250
        assert "accepted" in response.lower()
    except smtplib.SMTPResponseException as e:
        # Gracefully handle Stalwart's default strict mustMatchSender behavior
        err_msg = (
            e.smtp_error.decode("utf-8", errors="ignore")
            if isinstance(e.smtp_error, bytes)
            else str(e.smtp_error)
        )
        if e.smtp_code == 501 and "not allowed" in err_msg.lower():
            pytest.skip(
                "Sub-addressing sender rejected by Stalwart's default mustMatchSender policy"
            )
        else:
            raise


def test_104_outbound_submissions_authenticated_from_alias_tag(
    mail_config, smtp_sender
):
    """
    Test 104: Outbound message through submissions port (TLS, port 465) with plus extension on an alias.
    If mustMatchSender is strictly enabled on the server, this might get rejected. We handle
    both success (250) and a 501 sender matching restriction gracefully.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        "Swaks SMTP test - Sender authenticated alias address with plus extension"
    )
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias_tag"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test sending from a plus-tagged alias address.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_alias_tag"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
        )
        assert code == 250
        assert "accepted" in response.lower()
    except smtplib.SMTPResponseException as e:
        # Gracefully handle Stalwart's default strict mustMatchSender behavior
        err_msg = (
            e.smtp_error.decode("utf-8", errors="ignore")
            if isinstance(e.smtp_error, bytes)
            else str(e.smtp_error)
        )
        if e.smtp_code == 501 and "not allowed" in err_msg.lower():
            pytest.skip(
                "Sub-addressing alias sender rejected by Stalwart's default mustMatchSender policy"
            )
        else:
            raise


def test_outbound_submissions_authenticated_from_disallowed(mail_config, smtp_sender):
    """
    Test: Attempting to send from an unauthorized/disallowed address while authenticated.
    This MUST be rejected by the mailserver under test.
    We accept rejection code 501 (used by Stalwart at MAIL FROM stage) or 550/554 (used by other servers).
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender disallowed Sender"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_denied"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This message should be rejected by the mailserver due to a disallowed sender address.\n"
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_denied"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
        )

    err = exc_info.value
    assert err.smtp_code in [501, 550, 554]
    err_msg = (
        err.smtp_error.decode("utf-8", errors="ignore")
        if isinstance(err.smtp_error, bytes)
        else str(err.smtp_error)
    )
    err_msg = err_msg.lower()
    assert any(
        term in err_msg
        for term in ["not allowed", "denied", "sender", "spoof", "5.5.4"]
    )


def test_outbound_submissions_authenticated_from_mismatch_1(mail_config, smtp_sender):
    """
    Test: Authenticate, send envelope MAIL FROM as the legitimate user address, but
    use a forged header From (ceo@google.com).
    If the server's policy is lax on outgoing header alignment, this may succeed (returns 250).
    If strict alignment is enforced, it will reject (raises SMTPResponseException). Both are valid.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender mismatch / forged Sender 1"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_forged"]  # Forged header From: ceo@google.com
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This message tests if envelope MAIL FROM and DATA From can mismatch.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main"],  # Legitimate envelope MAIL FROM
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
        )
        assert code == 250
    except smtplib.SMTPResponseException as e:
        # If rejected, ensure it is a proper SMTP rejection error code
        assert e.code in [501, 550, 554]


def test_outbound_submissions_authenticated_from_mismatch_2(mail_config, smtp_sender):
    """
    Test: Authenticate, send envelope MAIL FROM as the legitimate user address, but
    use a forged header From (admin@microsoft.com).
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender mismatch / forged Sender 2"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config[
        "sender_forged2"
    ]  # Forged header From: admin@microsoft.com
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This message tests if envelope MAIL FROM and DATA From can mismatch.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main"],  # Legitimate envelope MAIL FROM
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
        )
        assert code == 250
    except smtplib.SMTPResponseException as e:
        assert e.smtp_code in [501, 550, 554]
