import os
import smtplib
import socket
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv

# Load variables
VARS_CONF_PATH = "vars.conf"
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
                os.environ[key] = val
else:
    load_dotenv()

# Server configurations
SERVER = os.environ.get("MAILSERVER_NAME", "mail.example.com")
HELO = os.environ.get("HELO_NAME", "localhost")
USER = os.environ.get("SENDER_AUTH_USER", "test1@example.com")
PASS = os.environ.get("SENDER_AUTH_PASSWORD", "TestPassword")
MAIN_ADDR = os.environ.get("SENDER_ADDRESS_MAIN", "test1@example.com")
EXT_ADDR = os.environ.get("SENDER_ADDRESS_MAIN_TAG", "test1+extension@example.com")
EXT_RECIPIENT = os.environ.get("RECIPIENT_ADDRESS", "test@example.com")


def safe_str(val):
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="ignore")
    return str(val)


print("=" * 70)
print(f"DIAGNOSTIC REPORT FOR MAIL SERVER: {SERVER}")
print("=" * 70)

# Create relaxed SSL Context
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# -------------------------------------------------------------------------
# PROBE 1: Port 465 (Outbound Submissions with implicit SSL)
# -------------------------------------------------------------------------
print("\n[PROBE 1] Outbound Submissions Port (Port 465 - Implicit TLS)")
print("-" * 50)
try:
    print(f"Connecting to {SERVER}:465 with 15s timeout...")
    client: smtplib.SMTP = smtplib.SMTP_SSL(
        SERVER, 465, context=context, local_hostname=HELO, timeout=15.0
    )
    print("✓ Successfully connected to Port 465.")

    # EHLO Capabilities
    ehlo_resp = client.ehlo(HELO)
    print("✓ EHLO successful. Server capabilities advertised:")
    for cap in client.esmtp_features:
        print(f"  - {cap.upper()}")

    # Test Login
    if USER and PASS:
        try:
            client.login(USER, PASS)
            print(f"✓ Authentication with user '{USER}' succeeded.")

            # Outbound Plus Address Probe
            print(
                "Probing outbound plus-addressing support "
                f"(MAIL FROM: <{EXT_ADDR}>)..."
            )
            try:
                # Issue MAIL FROM
                code, resp = client.mail(EXT_ADDR)
                print(f"  -> Server response: {code} {safe_str(resp)}")
                print(
                    "✓ Outbound plus-addressing (sub-addressing) "
                    "is ALLOWED by the mail server."
                )
            except smtplib.SMTPResponseException as e:
                print("  ✗ Outbound plus-addressing is REJECTED " "by the mail server.")
                print(f"    Reason: {e.smtp_code} {safe_str(e.smtp_error)}")

        except smtplib.SMTPResponseException as e:
            print(
                f"  ✗ Authentication failed: {e.smtp_code} " f"{safe_str(e.smtp_error)}"
            )
    else:
        print(
            "  - No SENDER_AUTH_USER and SENDER_AUTH_PASSWORD "
            "defined for login check."
        )

    client.quit()
except socket.timeout:
    print(
        "✗ Connection to Port 465 TIMED OUT "
        "(Blocked by local firewall, ISP, or offline server)."
    )
except Exception as e:
    print(f"✗ Connection to Port 465 failed: {e}")

# -------------------------------------------------------------------------
# PROBE 2: Port 25 (Inbound SMTP / MX Delivery)
# -------------------------------------------------------------------------
print("\n[PROBE 2] Inbound SMTP Port (Port 25 - STARTTLS)")
print("-" * 50)
try:
    print(f"Connecting to {SERVER}:25 with 5s timeout...")
    client = smtplib.SMTP(SERVER, 25, local_hostname=HELO, timeout=5.0)
    print("✓ Successfully connected to Port 25.")

    client.starttls(context=context)
    client.ehlo(HELO)
    print("✓ Negotiated STARTTLS & EHLO successful.")

    # Inbound Plus Address Probe
    test_rcpt = f"{MAIN_ADDR.split('@')[0]}+testprobe@{MAIN_ADDR.split('@')[1]}"
    print(f"Probing inbound plus-addressing support (RCPT TO: <{test_rcpt}>)...")
    try:
        client.mail(EXT_RECIPIENT)  # External sender
        code, resp = client.rcpt(test_rcpt)  # Plus-addressed local recipient
        print(f"  -> Server response to RCPT TO: {code} {safe_str(resp)}")
        if code == 250:
            print(
                "✓ Inbound plus-addressing (sub-addressing) "
                "is SUPPORTED for local delivery!"
            )
        else:
            print(
                "✗ Inbound plus-addressing is REJECTED "
                "or not supported by the mail server."
            )
    except smtplib.SMTPResponseException as e:
        print(
            f"✗ Inbound plus-addressing check failed: "
            f"{e.smtp_code} {safe_str(e.smtp_error)}"
        )

    # AV / Anti-Spam Rejection Probe
    print(
        "Probing if inbound Anti-Virus/Anti-Spam "
        "actively rejects signature payloads..."
    )
    # Attempt to send GTUBE
    try:
        msg = EmailMessage()
        msg["Subject"] = "Diagnostics probe - GTUBE"
        msg["To"] = MAIN_ADDR
        msg["From"] = EXT_RECIPIENT
        msg.set_content(
            "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"
        )

        # Reset transaction
        client.rset()
        client.mail(EXT_RECIPIENT)
        client.rcpt(MAIN_ADDR)
        # Try sending DATA
        code, resp = client.data(msg.as_bytes())
        print(f"  -> GTUBE sent. Server response: {code} {safe_str(resp)}")
        if code == 250:
            print(
                "  ℹ Inbound GTUBE (Spam) was ACCEPTED (No active session "
                "rejection, or filters are inactive/deliver-to-junk)."
            )
        else:
            print("  ✓ Inbound GTUBE (Spam) was REJECTED during transaction.")
    except smtplib.SMTPResponseException as e:
        print(
            "  ✓ Inbound GTUBE (Spam) was REJECTED during transaction: "
            f"{e.smtp_code} {safe_str(e.smtp_error)}"
        )

    client.quit()
except socket.timeout:
    print("✗ Connection to Port 25 TIMED OUT.")
    print(
        "  ℹ Note: Port 25 is heavily blocked by residential ISPs "
        "and cloud providers (like AWS, Azure, Google Cloud)."
    )
    print(
        "  ℹ If running this locally or in a restricted VM, please "
        "ensure outbound SMTP port 25 is allowed."
    )
except Exception as e:
    print(f"✗ Connection to Port 25 failed: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTICS COMPLETE.")
print("=" * 70)
