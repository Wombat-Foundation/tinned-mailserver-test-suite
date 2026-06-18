# pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements,invalid-name,redefined-outer-name,missing-module-docstring,missing-function-docstring,broad-exception-caught,unused-argument,unused-variable,unspecified-encoding,raise-missing-from,duplicate-code  # noqa: E501
import datetime
import imaplib
import os
import re
import smtplib
import socket
import ssl
import sys
import time

import pytest
from dotenv import load_dotenv

# Path to the vars.conf file at the root for backwards compatibility
VARS_CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vars.conf")


def load_config() -> None:
    # Try loading from .env if present
    load_dotenv()

    # Try loading from smtp-tests/vars.conf manually (handles 'export KEY=val')
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

_connectivity_cache: dict[tuple[str, int], bool] = {}
_AUTH_STATUS: dict[str, bool | None] = {
    "smtp": None,
    "imap": None,
    "smtp_submission": None,
}


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
    if _AUTH_STATUS["smtp"] is False:
        pytest.skip("SMTP authentication is not working/unconfigured.")
    if _AUTH_STATUS["smtp"] is True:
        return

    server = mail_config["server_name"]
    helo = mail_config["helo_name"]
    user = mail_config["auth_user"]
    password = mail_config["auth_pass"]

    if not user or not password:
        _AUTH_STATUS["smtp"] = False
        pytest.skip("SMTP credentials not configured.")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with smtplib.SMTP_SSL(
            server, 465, context=context, local_hostname=helo, timeout=3.0
        ) as client:
            client.set_debuglevel(int(os.environ.get("SMTP_DEBUG", "2")))
            # pylint: disable=protected-access
            client._print_debug = lambda *args: custom_print_debug(client, *args)
            client.login(user, password)
            _AUTH_STATUS["smtp"] = True
    except Exception as e:
        _AUTH_STATUS["smtp"] = False
        pytest.skip(f"SMTP login failed with credentials in .env: {e}")


@pytest.fixture(scope="session")
def imap_authenticated(mail_config, imap_connected):
    """Skips tests if IMAP authentication fails."""
    if _AUTH_STATUS["imap"] is False:
        pytest.skip("IMAP authentication is not working/unconfigured.")
    if _AUTH_STATUS["imap"] is True:
        return

    server = mail_config["server_name"]
    user = mail_config["auth_user"]
    password = mail_config["auth_pass"]

    if not user or not password:
        _AUTH_STATUS["imap"] = False
        pytest.skip("IMAP credentials not configured.")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with imaplib.IMAP4_SSL(server, 993, ssl_context=context) as client:
            client.login(user, password)
            _AUTH_STATUS["imap"] = True
    except Exception as e:
        _AUTH_STATUS["imap"] = False
        pytest.skip(f"IMAP login failed with credentials in .env: {e}")


@pytest.mark.usefixtures("smtp_submission_connected")
@pytest.fixture(scope="session")
def smtp_submission_authenticated(mail_config):
    """Skips tests if SMTP Submission authentication fails."""
    if _AUTH_STATUS["smtp_submission"] is False:
        pytest.skip("SMTP Submission authentication is not working/unconfigured.")
    if _AUTH_STATUS["smtp_submission"] is True:
        return

    server = mail_config["server_name"]
    helo = mail_config["helo_name"]
    user = mail_config["auth_user"]
    password = mail_config["auth_pass"]

    if not user or not password:
        _AUTH_STATUS["smtp_submission"] = False
        pytest.skip("SMTP credentials not configured.")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with smtplib.SMTP(server, 587, local_hostname=helo, timeout=3.0) as client:
            client.set_debuglevel(int(os.environ.get("SMTP_DEBUG", "2")))
            # pylint: disable=protected-access
            client._print_debug = lambda *args: custom_print_debug(client, *args)
            client.starttls(context=context)
            client.ehlo(helo)
            client.login(user, password)
            _AUTH_STATUS["smtp_submission"] = True
    except Exception as e:
        _AUTH_STATUS["smtp_submission"] = False
        pytest.skip(f"SMTP Submission login failed with credentials in .env: {e}")


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
        "sender_mailinglist": os.environ.get(
            "SENDER_MAILLINGLIST", "maillinglist@example.net"
        ),
        "sender_mailinglist_origin": os.environ.get(
            "SENDER_MAILLINGLIST_ORIGIN", "sender@example.org"
        ),
        "recipient": os.environ.get("RECIPIENT_ADDRESS", "test@example.com"),
    }


def custom_print_debug(_client, *args):
    """Formats and colorizes SMTP debug logs beautifully."""
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    if len(args) >= 2:
        prefix = str(args[0]).strip()
        payload = " ".join(str(x) for x in args[1:])

        # Clean up the payload representation
        cleaned_payload = payload
        if payload.startswith("b'") or payload.startswith('b"'):
            try:
                inner = payload[2:-1]
                cleaned_payload = inner.encode("utf-8").decode("unicode_escape")
            except Exception:
                cleaned_payload = payload
        elif payload.startswith("'") or payload.startswith('"'):
            try:
                inner = payload[1:-1]
                cleaned_payload = inner.encode("utf-8").decode("unicode_escape")
            except Exception:
                cleaned_payload = payload

        # Strip trailing newlines/carriage returns
        cleaned_payload = cleaned_payload.rstrip("\r\n").rstrip("\n")

        if prefix == "send:":
            # Client outgoing message
            formatted = f"{CYAN}➜ CLIENT:{RESET} {BOLD}{cleaned_payload}{RESET}"
        elif prefix == "reply:":
            # Server incoming message (check response code)
            code_match = re.match(r"^(\d{3})", cleaned_payload)
            if code_match:
                code = int(code_match.group(1))
                color = GREEN if code < 400 else RED
            elif "retcode" in cleaned_payload:
                color = GRAY
            else:
                color = GREEN
            formatted = f"{color}⬅ SERVER:{RESET} {cleaned_payload}"
        elif prefix == "data:":
            formatted = f"{YELLOW}✉ DATA:{RESET} {cleaned_payload}"
        else:
            formatted = f"{prefix} {cleaned_payload}"

        print(f"{GRAY}[{timestamp}]{RESET} {formatted}", file=sys.stderr)
    else:
        payload = " ".join(str(x) for x in args)
        print(f"{GRAY}[{timestamp}]{RESET} {payload}", file=sys.stderr)


def _send_smtp_message(
    config,
    envelope_from,
    envelope_to,
    message,
    use_ssl=True,
    use_starttls=False,
    authenticate=True,
    port=None,
    auth_method=None,
):
    """
    Sends an SMTP message using the provided configuration with transient retries.
    """
    server = config["server_name"]
    helo = config["helo_name"]

    # SSL Context with certificate verification relaxed for testing
    # environments (e.g. self-signed certs)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    max_attempts = 3
    for attempt in range(max_attempts):
        if port is not None:
            actual_port = port
        elif use_ssl:
            actual_port = 465
        else:
            actual_port = 25

        if use_ssl and actual_port == 465:
            client = smtplib.SMTP_SSL(
                server, actual_port, context=context, local_hostname=helo, timeout=15.0
            )
        else:
            client = smtplib.SMTP(server, actual_port, local_hostname=helo, timeout=5.0)
            if use_starttls:
                client.starttls(context=context)
                client.ehlo(helo)

        # Set SMTP debugging level to show exact protocol transaction on stderr
        client.set_debuglevel(int(os.environ.get("SMTP_DEBUG", "2")))
        # pylint: disable=protected-access,cell-var-from-loop
        client._print_debug = lambda *args: custom_print_debug(client, *args)

        try:
            if authenticate and config["auth_user"] and config["auth_pass"]:
                user = config["auth_user"]
                password = config["auth_pass"]
                if auth_method in ("PLAIN", "LOGIN"):
                    client.user = user
                    client.password = password
                    client.auth(
                        auth_method, getattr(client, "auth_" + auth_method.lower())
                    )
                else:
                    client.login(user, password)

            # Send mail with explicit envelope values
            refused = client.send_message(
                message, from_addr=envelope_from, to_addrs=envelope_to
            )
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)

            return 250, "Message accepted"

        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPResponseException) as e:
            code = None
            msg = ""
            if isinstance(e, smtplib.SMTPRecipientsRefused):
                for rcpt, err in e.recipients.items():
                    code, msg_bytes = err
                    if isinstance(msg_bytes, bytes):
                        msg = msg_bytes.decode("utf-8", errors="ignore")
                    else:
                        msg = str(msg_bytes)
                    break
            else:
                code = e.smtp_code
                if isinstance(e.smtp_error, bytes):
                    msg = e.smtp_error.decode("utf-8", errors="ignore")
                else:
                    msg = str(e.smtp_error)

            # Check if this is a transient/rate-limiting error
            is_transient = (
                (code is not None and (400 <= code <= 499))
                or "rate limit" in msg.lower()
                or "try again later" in msg.lower()
            )

            if is_transient and attempt < max_attempts - 1:
                time.sleep(3.0)
                continue

            if is_transient:
                pytest.skip(
                    f"Skipping test due to temporary SMTP rate limit: {code} {msg}"
                )

            raise
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


def pytest_addoption(parser):
    parser.addoption(
        "--smtp-debug",
        action="store",
        default="2",
        help="SMTP debug level (0=none, 1=standard, 2=with timestamps)",
    )


def pytest_configure(config):
    # Set the environment variable so all helper functions can access it
    os.environ["SMTP_DEBUG"] = str(config.getoption("--smtp-debug"))
