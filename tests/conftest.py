import imaplib
import os
import smtplib
import socket
import ssl
import time

import pytest
from dotenv import load_dotenv

# Path to the vars.conf file at the root for backwards compatibility
VARS_CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vars.conf")


def load_config():
    # 1. Try loading from .env if present
    load_dotenv()

    # 2. Try loading from smtp-tests/vars.conf manually (handles 'export KEY=val')
    if os.path.exists(VARS_CONF_PATH):
        with open(VARS_CONF_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    n_exports = len("export ")
                    line = line[n_exports:]
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Set it in environment if not already set (env takes precedence)
                    if key not in os.environ:
                        os.environ[key] = val


# Load configurations at module import time
load_config()

_connectivity_cache = {}
_smtp_auth_working = None
_imap_auth_working = None


def check_port_open(host, port, timeout=1.0):
    cache_key = (host, port)
    if cache_key in _connectivity_cache:
        return _connectivity_cache[cache_key]

    try:
        with socket.create_connection((host, port), timeout=timeout):
            _connectivity_cache[cache_key] = True
            return True
    except Exception:
        _connectivity_cache[cache_key] = False
        return False


@pytest.fixture(scope="session")
def smtp_inbound_connected(mail_config):
    """Skips tests if SMTP Inbound (port 25) is unreachable."""
    server = mail_config["server_name"]
    if not check_port_open(server, 25, timeout=1.5):
        pytest.skip(f"SMTP Inbound port 25 on {server} is unreachable.")


@pytest.fixture(scope="session")
def smtp_outbound_connected(mail_config):
    """Skips tests if SMTP Outbound (port 465) is unreachable."""
    server = mail_config["server_name"]
    if not check_port_open(server, 465, timeout=1.5):
        pytest.skip(f"SMTP Outbound port 465 on {server} is unreachable.")


@pytest.fixture(scope="session")
def imap_connected(mail_config):
    """Skips tests if IMAP (port 993) is unreachable."""
    server = mail_config["server_name"]
    if not check_port_open(server, 993, timeout=1.5):
        pytest.skip(f"IMAP port 993 on {server} is unreachable.")


@pytest.fixture(scope="session")
def smtp_authenticated(mail_config, smtp_outbound_connected):
    """Skips tests if SMTP authentication fails."""
    global _smtp_auth_working
    if _smtp_auth_working is False:
        pytest.skip("SMTP authentication is not working/unconfigured.")
    if _smtp_auth_working is True:
        return

    server = mail_config["server_name"]
    helo = mail_config["helo_name"]
    user = mail_config["auth_user"]
    password = mail_config["auth_pass"]

    if not user or not password:
        _smtp_auth_working = False
        pytest.skip("SMTP credentials not configured.")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with smtplib.SMTP_SSL(
            server, 465, context=context, local_hostname=helo, timeout=3.0
        ) as client:
            client.login(user, password)
            _smtp_auth_working = True
    except Exception as e:
        _smtp_auth_working = False
        pytest.skip(f"SMTP login failed with credentials in .env: {e}")


@pytest.fixture(scope="session")
def imap_authenticated(mail_config, imap_connected):
    """Skips tests if IMAP authentication fails."""
    global _imap_auth_working
    if _imap_auth_working is False:
        pytest.skip("IMAP authentication is not working/unconfigured.")
    if _imap_auth_working is True:
        return

    server = mail_config["server_name"]
    user = mail_config["auth_user"]
    password = mail_config["auth_pass"]

    if not user or not password:
        _imap_auth_working = False
        pytest.skip("IMAP credentials not configured.")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with imaplib.IMAP4_SSL(server, 993, ssl_context=context) as client:
            client.login(user, password)
            _imap_auth_working = True
    except Exception as e:
        _imap_auth_working = False
        pytest.skip(f"IMAP login failed with credentials in .env: {e}")


@pytest.fixture(scope="session")
def mail_config():
    """Provides configuration parameters for SMTP mail server testing."""
    return {
        "server_name": os.environ.get("MAILSERVER_NAME", "mail.example.com"),
        "helo_name": os.environ.get("HELO_NAME", "localhost"),
        "auth_user": os.environ.get("SENDER_AUTH_USER", "test1@example.com"),
        "auth_pass": os.environ.get("SENDER_AUTH_PASSWORD", "TestPassword"),
        "sender_main": os.environ.get("SENDER_ADDRESS_MAIN", "test1@example.com"),
        "sender_alias": os.environ.get("SENDER_ADDRESS_ALIAS", "test2@example.com"),
        "sender_main_tag": os.environ.get(
            "SENDER_ADDRESS_MAIN_TAG", "test1+extension@example.com"
        ),
        "sender_alias_tag": os.environ.get(
            "SENDER_ADDRESS_ALIAS_TAG", "test2+tag02@example.com"
        ),
        "sender_denied": os.environ.get("SENDER_ADDRESS_DENIED", "test3@example.com"),
        "sender_forged": os.environ.get("SENDER_ADDRESS_FORGED", "forged@example.com"),
        "sender_forged2": os.environ.get(
            "SENDER_ADDRESS_FORGED2", "forged@example.net"
        ),
        "recipient": os.environ.get("RECIPIENT_ADDRESS", "test@example.com"),
    }


def _send_smtp_message(
    config,
    envelope_from,
    envelope_to,
    message,
    use_ssl=True,
    use_starttls=False,
    authenticate=True,
):
    """
    Sends an SMTP message using the provided configuration.
    """
    server = config["server_name"]
    helo = config["helo_name"]

    # SSL Context with certificate verification relaxed for testing
    # environments (e.g. self-signed certs)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    if use_ssl:
        port = 465
        client = smtplib.SMTP_SSL(
            server, port, context=context, local_hostname=helo, timeout=15.0
        )
    else:
        port = 25
        client = smtplib.SMTP(server, port, local_hostname=helo, timeout=5.0)
        if use_starttls:
            client.starttls(context=context)
            client.ehlo(helo)

    try:
        if authenticate and config["auth_user"] and config["auth_pass"]:
            client.login(config["auth_user"], config["auth_pass"])

        # Send mail with explicit envelope values
        refused = client.send_message(
            message, from_addr=envelope_from, to_addrs=envelope_to
        )
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)

        return 250, "Message accepted"
    finally:
        try:
            client.quit()
        except Exception:
            pass


@pytest.fixture(scope="session")
def smtp_sender():
    """Fixture returning the raw SMTP sender helper function."""
    return _send_smtp_message


def _verify_imap_delivery(
    config,
    user,
    password,
    subject,
    expected_folder="INBOX",
    expect_exists=True,
    timeout=15.0,
):
    """
    Connects to the IMAP server and polls to verify delivery of an email.
    """
    server = config["server_name"]
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    start_time = time.time()
    while True:
        try:
            client = imaplib.IMAP4_SSL(server, 993, ssl_context=context)
        except Exception as e:
            if time.time() - start_time > timeout:
                raise RuntimeError(f"Failed to connect to IMAP server {server}: {e}")
            time.sleep(2.0)
            continue

        try:
            client.login(user, password)

            # Select folder. Handles variant folder names (e.g. Spam/Junk)
            folder_selected = False
            for folder in [
                expected_folder,
                expected_folder.lower(),
                expected_folder.capitalize(),
                "Spam",
                "Junk",
            ]:
                try:
                    client.select(folder)
                    folder_selected = True
                    break
                except imaplib.IMAP4.error:
                    continue

            if not folder_selected:
                try:
                    client.select("INBOX")
                except imaplib.IMAP4.error:
                    pass

            # Search by subject
            typ, data = client.search(None, "SUBJECT", f'"{subject}"')
            if typ == "OK":
                msg_ids = data[0].split()
                found = len(msg_ids) > 0

                if expect_exists and found:
                    return True
                if not expect_exists and found:
                    raise AssertionError(
                        f"Email '{subject}' found, but expected blocked."
                    )

            client.logout()
        except Exception as e:
            if isinstance(e, AssertionError):
                raise
            pass

        if time.time() - start_time > timeout:
            if expect_exists:
                raise AssertionError(
                    f"Email '{subject}' not found in IMAP within {timeout}s."
                )
            else:
                return True

        time.sleep(3.0)


@pytest.fixture(scope="session")
def imap_verifier():
    """Fixture returning the IMAP delivery verification helper function."""
    return _verify_imap_delivery
