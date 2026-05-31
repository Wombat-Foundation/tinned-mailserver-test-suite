# Test cases

The following list contains the test cases and the configuration settings used in them.

## Basic concept

The test cases listed here use configuration parameters to configure the test cases before they are executed. 
This documentation shows the specific configuration variables used in each of the test cases. 

The configuration specifies a number of email addresses and user/password combination. The credentials are used to authenticate against the mailserver under test. Email addresses for external email accounts used as receivers for outbound emails are also specified for some tests.


### Terms used

| Term                  | Description                                                                              |
| ---                   | ---                                                                                      |
| mailserver under test | The mailserver that should be tested by running the test cases.                          |
| outbound              | Messages sent from the mailserver under test out to a different emailserver              |
| inbound               | Messages coming from another emailserver to the mailserver under test for local delivery |
| address extension     | Allow to add an extension to the email addresses local-part                              |
|                       | Address extension is also know sub-addressing, plus addressing, tagged addressing.       |
| alias address         | Additional email addresses associated to a user account to receive messages on.          |


## 101 outbound_submissions_authenticated_from_main

### Variables

| Variable               | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| MAILSERVER_NAME        | The name or IP address of the mailserver                     |
| SENDER_AUTH_USER       | User on the mailserver to send outbound emails               |
| SENDER_AUTH_PASSWORD   | Password for the user on the mailserver                      |
| SENDER_ADDRESS_MAIN    | The main email address of the user on the mailserver         |
| RECIPIENT_ADDRESS      | Recipient email address not on the mailserver                |

### Description

This test email is intended to test a successfull outbound massage through the mailserver under test.
The email is sent with an users main email address.

* connects via submissions port (TLS, port 465)
* authenticates via PLAIN authentication (user + password)
* sends email to external recipient address with main address

### Pass criteria

This test is considered passed when the email is **successfully accepted for sending**.


## 102 outbound_submissions_authenticated_from_alias

### Variables

| Variable               | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| MAILSERVER_NAME        | The name or IP address of the mailserver                     |
| SENDER_AUTH_USER       | User on the mailserver to send outbound emails               |
| SENDER_AUTH_PASSWORD   | Password for the user on the mailserver                      |
| SENDER_ADDRESS_ALIAS   | The email alias address of the user on the mailserver        |
| RECIPIENT_ADDRESS      | Recipient email address not on the mailserver                |

### Description

This test email is intended to test a successful outbound massage through the mailserver under test.
The email is sent with an alias address to test alias handling for outbound email messages.

* connects via submissions port (TLS, port 465)
* authenticates via PLAIN authentication (user + password)
* sends email to external recipient address with main address

### Pass criteria

This test is considered passed when the email is **successfully accepted for sending**.


## 103 outbound_submissions_authenticated_from_main+ext

### Variables

| Variable                | Description                                                                     |
| ----------------------  | ------------------------------------------------------------------------------- |
| MAILSERVER_NAME         | The name or IP address of the mailserver                                        |
| SENDER_AUTH_USER        | User on the mailserver to send outbound emails                                  |
| SENDER_AUTH_PASSWORD    | Password for the user on the mailserver                                         |
| SENDER_ADDRESS_MAIN_TAG | The main email address of the user on the mailserver with an address extension  |
| RECIPIENT_ADDRESS       | Recipient email address not on the mailserver                                   |

### Description

This test email is intended to test a successful outbound massage through the mailserver under test.
The email is sent with an users main email address with an address extension.

* connects via submissions port (TLS, port 465)
* authenticates via PLAIN authentication (user + password)
* sends email to external recipient address with main address

### Pass criteria

This test is considered passed when the email is **successfully accepted for sending**.


## 104 outbound_submissions_authenticated_from_alias+ext

### Variables

| Variable                 | Description                                                                     |
| ----------------------   | ------------------------------------------------------------------------------- |
| MAILSERVER_NAME          | The name or IP address of the mailserver                                        |
| SENDER_AUTH_USER         | User on the mailserver to send outbound emails                                  |
| SENDER_AUTH_PASSWORD     | Password for the user on the mailserver                                         |
| SENDER_ADDRESS_ALIAS_TAG | The alias email address of the user on the mailserver with an address extension |
| RECIPIENT_ADDRESS        | Recipient email address not on the mailserver                                   |

### Description

This test email is intended to test a successful outbound massage through the mailserver under test.
The email is sent with an alias email address with an address extension.

* connects via submissions port (TLS, port 465)
* authenticates via PLAIN authentication (user + password)
* sends email to external recipient address with main address

### Pass criteria

This test is considered passed when the email is **successfully accepted for sending**.


## 201 inbound_eicar_txt

### Variables

| Variable               | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| MAILSERVER_NAME        | The name or IP address of the mailserver                     |
| SENDER_ADDRESS_MAIN    | The email address of the local user to receive the test mail |
| RECIPIENT_ADDRESS      | The external email address sending the test mail             |
| PAYLOAD_PATH           | Path to the EICAR.TXT file                                   |

### Description

This test email contains the EICAR test signature in an attachment. It is sent as an inbound message to the mailserver under test.

* connects via SMTP port (port 25)
* uses STARTTLS
* sends email with EICAR.TXT attachment

### Pass criteria

This test is considered passed when the email is **successfully rejected** (Swaks exit code 24).


## 202 inbound_gtube

### Variables

| Variable               | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| MAILSERVER_NAME        | The name or IP address of the mailserver                     |
| SENDER_ADDRESS_MAIN    | The email address of the local user to receive the test mail |
| RECIPIENT_ADDRESS      | The external email address sending the test mail             |

### Description

This test email contains the GTUBE (Generic Test for Unsolicited Bulk Email) string in the body. It is sent as an inbound message to the mailserver under test.

* connects via SMTP port (port 25)
* uses STARTTLS
* sends email with GTUBE string in the body

### Pass criteria

This test is considered passed when the email is **successfully rejected** (Swaks exit code 24).


## ToDo

### Outgoing
* outbound submissions authenticated-plain
	* test auth method PLAIN on port 465
	* test auth method PLAIN on port 587
* outbound submissions authenticated-login
	* test auth method LOGIN on port 465
	* test auth method LOGIN on port 587
* outbound smtp (port 25) authenticated-plain
	* this message should be rejected
* outbound smtp (port 25) authenticated-login
 	* this message should be rejected
* outbound submission authenticated fake sender address
	* port 465 authenticated
	* port 587 authenticated
* outbound submission authenticated fake sender address with address extension
	* port 465 authenticated
	* port 587 authenticated

### INBOUND
* inbound smtp (port 25) starttls local recipient


### INBOUND AV-TEST
* inbound smtp (port 25) starttls EICAR test pattern
	* EICAR.TXT as file attachment
	* EICAR.COM as file attachment
	* EICAR.COM-ZIP as file attachment
	* EICAR.COM2-ZIP as file attachment
* inbound smtp (port 25) starttls GTUBE test pattern
	* GTUBE "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"
		* string must be alone in a line
* inbound smtp (port 25) starttls NAItube test pattern
	* NAItube Medium "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-MXL09*C.34X"
		* string must be alone in a line
	* NAItube High "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-MXL10*C.34X"
		* string must be alone in a line
	* NAItube Critical "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-MXL11*C.34X"
		* string must be alone in a line

