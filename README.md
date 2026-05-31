# mailserver-test-suite

A suite of mailserver tests based on [Swaks - Swiss Army Knife for SMTP](https://jetmore.org/john/code/swaks/).

With this project, testing a new mailserver configuration should be made easier. The reporitory contains a number of tests that can be configured to connect to the mailserver to test and attemt a series of test cases. Some of them are intended to be rejected by the mail server, others are expected to be received and delivered.

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

This repository includes a GitHub Action workflow to automate these tests. You will need to configure the following secrets in your GitHub repository:

- `MAILSERVER_NAME`
- `SENDER_AUTH_USER`
- `SENDER_AUTH_PASSWORD`
- `SENDER_ADDRESS_MAIN`
- `SENDER_ADDRESS_ALIAS`
- `SENDER_ADDRESS_MAIN_TAG`
- `SENDER_ADDRESS_ALIAS_TAG`
- `SENDER_ADDRESS_DENIED`
- `SENDER_ADDRESS_FORGED`
- `SENDER_ADDRESS_FORGED2`
- `RECIPIENT_ADDRESS` (defaults to `services@nutra.tk` if not set)

The list of test cases can be found in the [Testcases](Testcases.md) documentation.
