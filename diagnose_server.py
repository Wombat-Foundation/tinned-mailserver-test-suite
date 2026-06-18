"""
SMTP Server Diagnostics Tool.

This module probes mail server ports (25 and 465) to verify connectivity,
SSL/TLS negotiation, authentication, sub-addressing (plus-addressing)
support, and inbound security filtering capability.
"""

import os
import smtplib
import socket
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv

# Load variables
VARS_CONF_PATH = "vars.conf"
if os.path.exists(VARS_CONF_PATH):
    with open(VARS_CONF_PATH, "r", encoding="utf-8") as f:
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


def safe_str(val_obj: object) -> str:
    """Safely decodes bytes to string or converts an object to string."""
    if isinstance(val_obj, bytes):
        return val_obj.decode("utf-8", errors="ignore")
    return str(val_obj)


def main() -> None:
    """Main execution entrypoint for mail server diagnostics."""
    # Server configurations
    server = os.environ.get("MAILSERVER_NAME", "mail.example.com")
    helo = os.environ.get("HELO_NAME", "localhost")
    user = os.environ.get("SENDER_AUTH_USER", "test1@example.com")
    password = os.environ.get("SENDER_AUTH_PASSWORD", "TestPassword")
    main_addr = os.environ.get("SENDER_ADDRESS_MAIN", "test1@example.com")
    ext_addr = os.environ.get("SENDER_ADDRESS_MAIN_TAG", "test1+extension@example.com")
    ext_recipient = os.environ.get("RECIPIENT_ADDRESS", "test@example.com")

    print("=" * 70)
    print(f"DIAGNOSTIC REPORT FOR MAIL SERVER: {server}")
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
        print(f"Connecting to {server}:465 with 15s timeout...")
        ssl_client = smtplib.SMTP_SSL(
            server, 465, context=context, local_hostname=helo, timeout=15.0
        )
        print("✓ Successfully connected to Port 465.")

        # EHLO Capabilities
        ssl_client.ehlo(helo)
        print("✓ EHLO successful. Server capabilities advertised:")
        for cap in ssl_client.esmtp_features:
            print(f"  - {cap.upper()}")

        # Test Login
        if user and password:
            try:
                ssl_client.login(user, password)
                print(f"✓ Authentication with user '{user}' succeeded.")

                # Outbound Plus Address Probe
                print(
                    "Probing outbound plus-addressing support "
                    f"(MAIL FROM: <{ext_addr}>)..."
                )
                try:
                    # Issue MAIL FROM
                    code, resp = ssl_client.mail(ext_addr)
                    print(f"  -> Server response: {code} {safe_str(resp)}")
                    print(
                        "✓ Outbound plus-addressing (sub-addressing) "
                        "is ALLOWED by the mail server."
                    )
                except smtplib.SMTPResponseException as e:
                    print(
                        "  ✗ Outbound plus-addressing is REJECTED "
                        "by the mail server."
                    )
                    print(f"    Reason: {e.smtp_code} {safe_str(e.smtp_error)}")

            except smtplib.SMTPResponseException as e:
                print(
                    f"  ✗ Authentication failed: {e.smtp_code} "
                    f"{safe_str(e.smtp_error)}"
                )
        else:
            print(
                "  - No SENDER_AUTH_USER and SENDER_AUTH_PASSWORD "
                "defined for login check."
            )

        ssl_client.quit()
    except socket.timeout:
        print(
            "✗ Connection to Port 465 TIMED OUT "
            "(Blocked by local firewall, ISP, or offline server)."
        )
    except (socket.error, smtplib.SMTPException, ssl.SSLError) as e:
        print(f"✗ Connection to Port 465 failed: {e}")

    # -------------------------------------------------------------------------
    # PROBE 2: Port 25 (Inbound SMTP / MX Delivery)
    # -------------------------------------------------------------------------
    print("\n[PROBE 2] Inbound SMTP Port (Port 25 - STARTTLS)")
    print("-" * 50)
    try:
        print(f"Connecting to {server}:25 with 5s timeout...")
        smtp_client = smtplib.SMTP(server, 25, local_hostname=helo, timeout=5.0)
        print("✓ Successfully connected to Port 25.")

        smtp_client.starttls(context=context)
        smtp_client.ehlo(helo)
        print("✓ Negotiated STARTTLS & EHLO successful.")

        # Inbound Plus Address Probe
        test_rcpt = f"{main_addr.split('@')[0]}+testprobe@{main_addr.split('@')[1]}"
        print("Probing inbound plus-addressing support " f"(RCPT TO: <{test_rcpt}>)...")
        try:
            smtp_client.mail(ext_recipient)  # External sender
            code, resp = smtp_client.rcpt(test_rcpt)  # Local recipient
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
            msg["To"] = main_addr
            msg["From"] = ext_recipient
            msg.set_content(
                "XJS*C4JDBQADN1.NSBN3*2IDNEN*"
                "GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"
            )

            # Reset transaction
            smtp_client.rset()
            smtp_client.mail(ext_recipient)
            smtp_client.rcpt(main_addr)
            # Try sending DATA
            code, resp = smtp_client.data(msg.as_bytes())
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

        smtp_client.quit()
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
    except (socket.error, smtplib.SMTPException, ssl.SSLError) as e:
        print(f"✗ Connection to Port 25 failed: {e}")

    print("\n" + "=" * 70)
    print("DIAGNOSTICS COMPLETE.")
    print("=" * 70)


if __name__ == "__main__":
    main()
