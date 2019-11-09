###Permissions###
#create_attendee_report
#create_attendee
#remove_attendee_specific
#remove_record_specific
#update_notes_specific
#list_records_specific
#list_records_weekly
#list_records_all
#list_attendee_info_all
#*

import bcrypt

class Auth:
    def __init__(self, data_class):
        #Data Class
        self.data = data_class
        #Authentication Data
        self.auth_data = data_class.get_from_json_file('auth_data.json')
        print('Authentication class initialized')

    def is_username_valid(self, username):
        return username in self.auth_data

    def are_credentials_valid(self, username, password):
        return username in self.auth_data and bcrypt.checkpw(password.encode('utf8'), self.auth_data[username]['password_hash'].encode('utf8'))

    def has_permission(self, username, permissions_list=[]):
        if username in self.auth_data:
            if '*' in self.auth_data[username]['permissions']:
                return True
            permitted = True
            for permission in permissions_list:
                if permission not in self.auth_data[username]['permissions']:
                    permitted = False
                    break
            return permitted
        return False

    def add_user(self, username, password, permissions, comments):
        self.auth_data[username] = {
            'password_hash': bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()),
            'permissions': permissions,
            'comments': comments
        }
        self.data.write_to_json_file('auth_data.json', self.auth_data)
