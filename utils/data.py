import json
import hashlib
import time

class Data:
    def __init__(self):
        print('Data class initialized')
        self.attendee_data = self.get_from_json_file('attendee_data.json')
        self.general_data = self.get_from_json_file('general_data.json')
        self.weekly_summary_cache = {'checked_in': {}}
        self.get_weekly_summary_data()

    def write_to_json_file(self, file, dict):
        with open(file, 'w') as f:
            json.dump(dict, f, ensure_ascii=False, sort_keys=True, indent=4)

    def get_from_json_file(self, file):
        with open(file) as f:
            dict = json.load(f)
        return dict

    def get_weekly_summary_data(self):
        for user_hash in self.attendee_data:
            for record_hash in self.attendee_data[user_hash]['attendance_record']:
                if self.attendee_data[user_hash]['attendance_record'][record_hash]['ts'] in range(int(time.time()) - 432000, int(time.time()) + 432000):
                    record_copy = dict(self.attendee_data[user_hash]['attendance_record'][record_hash])
                    record_copy['record_hash'] = record_hash
                    self.weekly_summary_cache['checked_in'][user_hash] = record_copy

    def sync_all_data(self):
        self.write_to_json_file('attendee_data.json', self.attendee_data)
        self.write_to_json_file('general_data.json', self.general_data)

    def attendee_exists(self, user_hash):
        return user_hash in self.attendee_data

    def attendee_record_exists(self, user_hash, record_hash):
        return user_hash in self.attendee_data and record_hash in self.attendee_data[user_hash]['attendance_record']

    def add_attendee(self, first_name, last_name, designation, role, user_hash):
        if user_hash not in self.attendee_data:
            self.attendee_data[user_hash] = {
                'attendance_record': {},
                'first_name': first_name,
                'last_name': last_name,
                'designation': designation,
                'role': role,
                'user_hash': user_hash,
                'notes': ''
            }
            self.sync_all_data()

    def add_attendee_record(self, user_hash, checkin_ts, marked_sunday_school, date_str):
        if user_hash in self.attendee_data:
            record_hash = hashlib.md5(self.attendee_data[user_hash]['first_name'] + '-' + self.attendee_data[user_hash]['last_name'] + '-' + self.attendee_data[user_hash]['designation'] + '-' + date_str).hexdigest()
            if record_hash not in self.attendee_data[user_hash]['attendance_record']:
                self.attendee_data[user_hash]['attendance_record'][record_hash] = {
                    'ts': checkin_ts,
                    'marked_sunday_school': marked_sunday_school
                }
                self.sync_all_data()
            if user_hash not in self.weekly_summary_cache['checked_in']:
                self.weekly_summary_cache['checked_in'][user_hash] = {
                    'record_hash': record_hash,
                    'ts': checkin_ts,
                    'marked_sunday_school': marked_sunday_school
                }

    def remove_attendee(self, user_hash):
        if user_hash in self.attendee_data:
            del self.attendee_data[user_hash]
            self.sync_all_data()

    def remove_attendee_record(self, user_hash, record_hash):
        if user_hash in self.attendee_data and record_hash in self.attendee_data[user_hash]['attendance_record']:
            del self.attendee_data[user_hash]['attendance_record'][record_hash]
            self.sync_all_data()

    def update_attendee_notes(self, user_hash, notes):
        if user_hash in self.attendee_data:
            self.attendee_data[user_hash]['notes'] = str(notes)
            self.sync_all_data()

    def get_attendee_data(self, user_hash=None, basic=False, name_only=False):
        if user_hash in self.attendee_data:
            if name_only:
                return {
                    'first_name': self.attendee_data[user_hash]['first_name'],
                    'last_name': self.attendee_data[user_hash]['last_name']
                }
            elif basic:
                return {
                    'first_name': self.attendee_data[user_hash]['first_name'],
                    'last_name': self.attendee_data[user_hash]['last_name'],
                    'designation': self.attendee_data[user_hash]['designation'],
                    'role': self.attendee_data[user_hash]['role'],
                    'user_hash': user_hash,
                    'notes': self.attendee_data[user_hash]['notes']
                }
            else:
                return self.attendee_data[user_hash]
        return {}

    def get_weekly_summary(self):
        weekly_summary_copy = dict(self.weekly_summary_cache)
        weekly_summary_copy['logged_weeks'] = self.general_data['logged_weeks']
        return weekly_summary_copy

    def get_all_data(self):
        return {
            'attendee_data': self.attendee_data,
            'general_data': self.general_data
        }

    def search_attendees(self, characters):
        found_names = []
        if not characters:
            for user_hash in self.attendee_data:
                found_names.append(self.get_attendee_data(user_hash, name_only=True))
        else:
            split_name = characters.split(' ')
            if len(split_name) == 2:
                for user_hash in self.attendee_data:
                    user_name = self.get_attendee_data(user_hash, name_only=True)
                    if split_name[0].lower() in user_name['first_name'].lower() and split_name[1].lower() in user_name['last_name'].lower():
                        found_names.append(user_name)
            else:
                for user_hash in self.attendee_data:
                    user_name = self.get_attendee_data(user_hash, name_only=True)
                    if characters.lower() in user_name['first_name'].lower() or characters.lower() in user_name['last_name'].lower():
                        found_names.append(user_name)
        return found_names

    def attendees_info(self):
        attendees = []
        for user_hash in self.attendee_data:
            attendees.append(self.get_attendee_data(user_hash, basic=True))
        return attendees
