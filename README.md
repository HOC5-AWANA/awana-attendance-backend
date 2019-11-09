# Attendance Backend (Python) - AWANA@HOC5
Backend API used to receive, store, and retrieve attendance info in JSON format for easy export.

Setup:
 - Verify that `bcrypt`, `flask`, `flask_cors`, and `pytz` are installed
 - Start the WS by running `python api.py`

Authentication for Accounts:
 - Authentication data, including a template account can be found in `auth_data.json`
 - Possible Permissions are as follows: `create_attendee_report`, `create_attendee`, `remove_attendee_specific`, `remove_record_specific`, `update_notes_specific`, `list_records_specific`, `list_records_weekly`, `list_records_all`, `list_attendee_info_all`
  - To grant all permissions, use `*`
  - Passwords for accounts can be generated through the use of `bcrypt` (`bcrypt.hashpw('your_password'.encode('utf8'), bcrypt.gensalt())`)

Note: this code was only tested on Python 2.7
