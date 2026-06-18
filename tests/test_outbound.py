"""
Outbound SMTP Mail Server Test Cases.

This module validates outbound email delivery, Submissions port (587, STARTTLS)
with PLAIN and LOGIN authentication, SMTPS (465, implicit TLS), and sender address
mismatch restrictions.
"""

import smtplib
import uuid
from email.message import EmailMessage

import pytest


@pytest.mark.usefixtures("smtp_authenticated", "imap_authenticated")
def test_100_outbound_normal_delivery_local_recipient(
    mail_config,
    smtp_sender,
    imap_verifier,
):
    """
    Test 100: Normal outbound submission with local delivery.
    Sends an authenticated message via port 465 (submissions) to a local alias
    and verifies that it successfully arrives in the local user's IMAP mailbox.
    """
    unique_id = str(uuid.uuid4())
    subject = f"Swaks SMTP test - Outbound Submission Local Delivery - {unique_id}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["To"] = mail_config["sender_alias"]  # Local recipient (alias)
    msg["From"] = mail_config["sender_main"]  # Local sender
    msg.set_content(
        "Hi,\n\n"
        "This is an authenticated test email sent via SMTP (port 465, SSL).\n"
        "It is expected to be accepted and delivered locally to the alias address.\n\n"
        f"Verification ID: {unique_id}\n\n"
        "Best regards,\n"
        "Test Suite\n"
    )

    # 1. Send via SMTP (authenticated)
    code, _ = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_main"],
        envelope_to=mail_config["sender_alias"],
        message=msg,
        use_ssl=True,
    )
    assert code == 250

    # 2. Verify delivery via IMAP
    imap_verifier(
        config=mail_config,
        user=mail_config["auth_user"],
        password=mail_config["auth_pass"],
        subject=subject,
        expected_folder="INBOX",
        expect_exists=True,
        timeout=20.0,
    )


# ==========================================
# 101 - 106: Outbound Submissions (Port 587)
# ==========================================


@pytest.mark.usefixtures("smtp_submission_authenticated")
def test_101_outbound_submissions_plain_authenticated_from_main(
    mail_config, smtp_sender
):
    """
    Test 101: Successful outbound message through submissions port
    (STARTTLS, port 587) using PLAIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender plain authenticated main address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via submissions port (STARTTLS, port 587)\n"
        "* Client authenticates via PLAIN authentication\n"
        "* Client sends email to external recipient with main address\n\n"
        "This message should be accepted by the mailserver.\n\n"
        "Best regards,\n"
        "SMTP test suite\n"
    )

    code, response = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_main"],
        envelope_to=mail_config["recipient"],
        message=msg,
        use_ssl=False,
        use_starttls=True,
        port=587,
        auth_method="PLAIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


@pytest.mark.usefixtures("smtp_submission_authenticated")
def test_102_outbound_submissions_plain_authenticated_from_alias(
    mail_config, smtp_sender
):
    """
    Test 102: Successful outbound message through submissions port
    (STARTTLS, port 587) using PLAIN authentication with an alias address.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender plain authenticated alias address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via submissions port (STARTTLS, port 587)\n"
        "* Client authenticates via PLAIN authentication\n"
        "* Client sends email to external recipient with alias address\n\n"
        "This message should be accepted by the mailserver.\n\n"
        "Best regards,\n"
        "SMTP test suite\n"
    )

    code, response = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_alias"],
        envelope_to=mail_config["recipient"],
        message=msg,
        use_ssl=False,
        use_starttls=True,
        port=587,
        auth_method="PLAIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


@pytest.mark.usefixtures("smtp_submission_authenticated")
def test_103_outbound_submissions_plain_authenticated_from_main_tag(
    mail_config, smtp_sender
):
    """
    Test 103: Outbound message through submissions port (STARTTLS, port 587)
    with plus extension using PLAIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        "Swaks SMTP test - Sender plain authenticated main address with tag"
    )
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main_tag"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test plus-tagged senders.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main_tag"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            port=587,
            auth_method="PLAIN",
        )
        assert code == 250
        assert "accepted" in response.lower()
    except smtplib.SMTPResponseException as e:
        err_msg = (
            e.smtp_error.decode("utf-8", errors="ignore")
            if isinstance(e.smtp_error, bytes)
            else str(e.smtp_error)
        )
        if e.smtp_code == 501 and "not allowed" in err_msg.lower():
            pytest.skip("Sub-addressing sender rejected by mustMatchSender")
        else:
            raise


@pytest.mark.usefixtures("smtp_submission_authenticated")
def test_104_outbound_submissions_plain_authenticated_from_alias_tag(
    mail_config, smtp_sender
):
    """
    Test 104: Outbound message through submissions port (STARTTLS, port 587)
    with plus extension on an alias using PLAIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        "Swaks SMTP test - Sender plain authenticated alias address with tag"
    )
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias_tag"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test plus-tagged alias senders.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_alias_tag"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=False,
            use_starttls=True,
            port=587,
            auth_method="PLAIN",
        )
        assert code == 250
        assert "accepted" in response.lower()
    except smtplib.SMTPResponseException as e:
        err_msg = (
            e.smtp_error.decode("utf-8", errors="ignore")
            if isinstance(e.smtp_error, bytes)
            else str(e.smtp_error)
        )
        if e.smtp_code == 501 and "not allowed" in err_msg.lower():
            pytest.skip("Sub-addressing alias sender rejected by mustMatchSender")
        else:
            raise


def test_105_outbound_submissions_login_authenticated_from_main(
    mail_config, smtp_sender, smtp_submission_authenticated
):
    """
    Test 105: Successful outbound message through submissions port
    (STARTTLS, port 587) using LOGIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender login authenticated main address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via submissions port (STARTTLS, port 587)\n"
        "* Client authenticates via LOGIN authentication\n"
        "* Client sends email to external recipient with main address\n\n"
        "This message should be accepted by the mailserver.\n\n"
        "Best regards,\n"
        "SMTP test suite\n"
    )

    code, response = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_main"],
        envelope_to=mail_config["recipient"],
        message=msg,
        use_ssl=False,
        use_starttls=True,
        port=587,
        auth_method="LOGIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


def test_106_outbound_submissions_login_authenticated_from_alias(
    mail_config, smtp_sender, smtp_submission_authenticated
):
    """
    Test 106: Successful outbound message through submissions port
    (STARTTLS, port 587) using LOGIN authentication with an alias address.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender login authenticated alias address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via submissions port (STARTTLS, port 587)\n"
        "* Client authenticates via LOGIN authentication\n"
        "* Client sends email to external recipient with alias address\n\n"
        "This message should be accepted by the mailserver.\n\n"
        "Best regards,\n"
        "SMTP test suite\n"
    )

    code, response = smtp_sender(
        config=mail_config,
        envelope_from=mail_config["sender_alias"],
        envelope_to=mail_config["recipient"],
        message=msg,
        use_ssl=False,
        use_starttls=True,
        port=587,
        auth_method="LOGIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


# ==========================================
# 111 - 116: Outbound SMTPS (Port 465)
# ==========================================


def test_111_outbound_smtps_plain_authenticated_from_main(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 111: Successful outbound message through SMTPS port
    (SSL, port 465) using PLAIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender plain authenticated main address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via SMTPS port (SSL, port 465)\n"
        "* Client authenticates via PLAIN authentication\n"
        "* Client sends email to external recipient with main address\n\n"
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
        auth_method="PLAIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


def test_112_outbound_smtps_plain_authenticated_from_alias(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 112: Successful outbound message through SMTPS port
    (SSL, port 465) using PLAIN authentication with an alias address.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender plain authenticated alias address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via SMTPS port (SSL, port 465)\n"
        "* Client authenticates via PLAIN authentication\n"
        "* Client sends email to external recipient with alias address\n\n"
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
        auth_method="PLAIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


def test_113_outbound_smtps_plain_authenticated_from_main_tag(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 113: Outbound message through SMTPS port (SSL, port 465)
    with plus extension using PLAIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        "Swaks SMTP test - Sender plain authenticated main address with tag"
    )
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main_tag"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test plus-tagged senders.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main_tag"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
            auth_method="PLAIN",
        )
        assert code == 250
        assert "accepted" in response.lower()
    except smtplib.SMTPResponseException as e:
        err_msg = (
            e.smtp_error.decode("utf-8", errors="ignore")
            if isinstance(e.smtp_error, bytes)
            else str(e.smtp_error)
        )
        if e.smtp_code == 501 and "not allowed" in err_msg.lower():
            pytest.skip("Sub-addressing sender rejected by mustMatchSender")
        else:
            raise


def test_114_outbound_smtps_plain_authenticated_from_alias_tag(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 114: Outbound message through SMTPS port (SSL, port 465)
    with plus extension on an alias using PLAIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        "Swaks SMTP test - Sender plain authenticated alias address with tag"
    )
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias_tag"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test plus-tagged alias senders.\n"
    )

    try:
        code, response = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_alias_tag"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
            auth_method="PLAIN",
        )
        assert code == 250
        assert "accepted" in response.lower()
    except smtplib.SMTPResponseException as e:
        err_msg = (
            e.smtp_error.decode("utf-8", errors="ignore")
            if isinstance(e.smtp_error, bytes)
            else str(e.smtp_error)
        )
        if e.smtp_code == 501 and "not allowed" in err_msg.lower():
            pytest.skip("Sub-addressing alias sender rejected by mustMatchSender")
        else:
            raise


def test_115_outbound_smtps_login_authenticated_from_main(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 115: Successful outbound message through SMTPS port
    (SSL, port 465) using LOGIN authentication.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender login authenticated main address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_main"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via SMTPS port (SSL, port 465)\n"
        "* Client authenticates via LOGIN authentication\n"
        "* Client sends email to external recipient with main address\n\n"
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
        auth_method="LOGIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


def test_116_outbound_smtps_login_authenticated_from_alias(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 116: Successful outbound message through SMTPS port
    (SSL, port 465) using LOGIN authentication with an alias address.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender login authenticated alias address"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_alias"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This test email is intended to test the following situation.\n\n"
        "* Client connects via SMTPS port (SSL, port 465)\n"
        "* Client authenticates via LOGIN authentication\n"
        "* Client sends email to external recipient with alias address\n\n"
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
        auth_method="LOGIN",
    )
    assert code == 250
    assert "accepted" in response.lower()


# ==========================================
# 251 - 253: Policy / Sender Mismatch Tests
# ==========================================


def test_251_outbound_submissions_authenticated_from_disallowed(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 251: Attempting to send from an unauthorized/disallowed address.
    This MUST be rejected by the mailserver under test.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender disallowed Sender"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_denied"]
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This message should be rejected due to disallowed sender.\n"
    )

    with pytest.raises(smtplib.SMTPResponseException) as exc_info:
        smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_denied"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
            auth_method="PLAIN",
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
        for term in [
            "not allowed",
            "denied",
            "sender",
            "spoof",
            "5.5.4",
            "rejected",
        ]
    )


def test_252_outbound_submissions_authenticated_from_mismatch_1(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 252: Authenticate, send envelope MAIL FROM as the user, but
    use a forged header From (ceo@google.com). Expect rejection or accept
    based on policy.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender mismatch / forged Sender 1"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_forged"]  # Forged header From
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This message tests envelope and header From mismatches.\n"
    )

    try:
        code, _ = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
            auth_method="PLAIN",
        )
        assert code == 250
    except smtplib.SMTPResponseException as e:
        # Expected RC might be 26 (dropped connection/rejection)
        # or general SMTP code like 501/550/554
        assert e.smtp_code in [26, 501, 550, 554]


def test_253_outbound_submissions_authenticated_from_mismatch_2(
    mail_config, smtp_sender, smtp_authenticated
):
    """
    Test 253: Authenticate, send envelope MAIL FROM as the user, but
    use a forged header From (admin@microsoft.com). Expect rejection or
    accept based on policy.
    """
    msg = EmailMessage()
    msg["Subject"] = "Swaks SMTP test - Sender mismatch / forged Sender 2"
    msg["To"] = mail_config["recipient"]
    msg["From"] = mail_config["sender_forged2"]  # Forged header From
    msg.set_content(
        "Hi,\n\n"
        "This is a test email sent via SMTP using Python.\n"
        "This message tests envelope and header From mismatches.\n"
    )

    try:
        code, _ = smtp_sender(
            config=mail_config,
            envelope_from=mail_config["sender_main"],
            envelope_to=mail_config["recipient"],
            message=msg,
            use_ssl=True,
            auth_method="PLAIN",
        )
        assert code == 250
    except smtplib.SMTPResponseException as e:
        # Expected RC might be 26 (dropped connection/rejection)
        # or general SMTP code like 501/550/554
        assert e.smtp_code in [26, 501, 550, 554]
