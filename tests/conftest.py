import os
import smtplib
import ssl

import pytest
from dotenv import load_dotenv

# Path to the old vars.conf file for backwards compatibility
VARS_CONF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "smtp-tests", "vars.conf"
)


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
