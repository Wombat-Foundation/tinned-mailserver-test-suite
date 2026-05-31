# mailserver-test-suite

A suite of mailserver tests based on [Swaks - Swiss Army Knife for SMTP](https://jetmore.org/john/code/swaks/).

With this project, testing a new mailserver configuration should be made easier. The repository contains a number of tests that can be configured to connect to the mailserver to test and attempt a series of test cases. Some of them are intended to be rejected by the mail server, others are expected to be received and delivered.

## How to use

### Local execution (e.g., on Arch Linux)

If you are running on Arch Linux, you can install the required tools with:

```bash
sudo pacman -S swaks gettext
```

Then follow these steps:

1. Enter the `smtp-tests` directory:
   ```bash
   cd smtp-tests
   ```
2. Copy the example configuration:
   ```bash
   cp vars.example.conf vars.conf
   ```
3. Edit `vars.conf` and fill in your mailserver details and credentials.
4. Run the tests:
   ```bash
   bash run.sh
   ```

### GitHub Actions

This repository includes a GitHub Action workflow to automate these tests. To make this work, you need to configure your environment in GitHub (**Settings** > **Secrets and variables** > **Actions**):

#### 1. Variables (Plaintext)

Add these under the **Variables** tab for non-sensitive configuration:

- `MAILSERVER_NAME`
- `SENDER_AUTH_USER`
- `SENDER_ADDRESS_MAIN`
- `SENDER_ADDRESS_ALIAS`
- `SENDER_ADDRESS_MAIN_TAG`
- `SENDER_ADDRESS_ALIAS_TAG`
- `SENDER_ADDRESS_DENIED`
- `SENDER_ADDRESS_FORGED`
- `SENDER_ADDRESS_FORGED2`
- `RECIPIENT_ADDRESS`

#### 2. Secrets (Encrypted)

Add these under the **Secrets** tab for sensitive data:

- `SENDER_AUTH_PASSWORD`

The list of test cases can be found in the [Testcases](Testcases.md) documentation.
