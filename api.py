from flask import Flask, jsonify, request, abort, session
from flask_cors import CORS
from datetime import datetime, timedelta
from utils.auth import Auth
from utils.data import Data
import hashlib
import pytz
import time
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

data = Data()
auth = Auth(data)

tz = pytz.timezone('America/Los_Angeles')
pst_now = datetime.now(tz)

general_data = {}

last_checkin_date = pst_now.date().strftime("%m/%d/%Y")



###Misc Functions###

def startup():
    global last_checkin_date
    general_data = data.general_data
    if len(general_data['logged_weeks']) == 0:
        general_data['logged_weeks'].append(pst_now.date().strftime("%m/%d/%Y"))
    last_checkin_date = general_data['logged_weeks'][len(general_data['logged_weeks']) - 1]

def update_checkin_date():
    global last_checkin_date
    last_checkin_date = pst_now.date().strftime("%m/%d/%Y")
    if last_checkin_date not in data.general_data['logged_weeks']:
        data.weekly_summary_cache = {'checked_in': {}}
        data.general_data['logged_weeks'].append(last_checkin_date)
        data.sync_all_data()



###Authentication###

@app.before_request
def check_token_validation():
    if request.path != '/api/v3/auth/login' and request.method == 'POST':
        username = session.get('username', 'none')
        if not auth.is_username_valid(username):
            abort(401)

@app.route('/api/v3/auth/login', methods=['POST'])
def auth_login():
    json = request.get_json(force=True)
    d = {}
    if auth.are_credentials_valid(json.get('username', 'none'), json.get('password', 'none')):
        d['error'] = 'none'
        d['is_authed'] = True
        session['username'] = json['username']
    else:
        d['error'] = 'invalidCredentials'
        d['is_authed'] = False
    return jsonify(d)

@app.route('/api/v3/auth/create_user', methods=['POST'])
def auth_create_user():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['create_user']):
        username_new = json.get('username')
        password_new = json.get('password')
        permissions = json.get('permissions')
        comments = json.get('comments', '')
        if username_new and password_new and type(permissions) == type([]):
            if not auth.is_username_valid(username_new):
                if '*' not in permissions:
                    auth.add_user(username_new, password_new, permissions, comments)
                    d['error'] = 'none'
                    d['success'] = True
                else:
                    d['error'] = 'permissionNotPossible'
                    d['success'] = False
            else:
                d['error'] = 'userExists'
                d['success'] = False
        else:
            d['error'] = 'argsMissing'
            d['success'] = False
    else:
        d['error'] = 'noPermission'
        d['success'] = False
    return jsonify(d)



###Attendance Submission###

@app.route('/api/v3/checkin_client/submit_record', methods=['POST'])
def checkin_client_submit_record():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['create_attendee_report']):
        user_hash = json.get('user_hash') #md5: first_name-last_name-designation
        checkin_ts = json.get('checkin_ts')
        marked_sunday_school = json.get('marked_sunday_school')
        if data.attendee_exists(user_hash):
            update_checkin_date()
            data.add_attendee_record(user_hash, checkin_ts, marked_sunday_school, last_checkin_date)
            d['error'] = 'none'
            d['success'] = True
        else:
            d['error'] = 'noSuchAttendee'
            d['success'] = False
    else:
        d['error'] = 'noPermission'
        d['success'] = False
    return jsonify(d)

@app.route('/api/v3/checkin_client/create_attendee', methods=['POST'])
def checkin_client_create_attendee():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['create_attendee']):
        first_name = json.get('first_name')
        last_name = json.get('last_name')
        designation = json.get('designation')
        role = json.get('role')
        user_hash = json.get('user_hash', hashlib.md5(first_name + '-' + last_name + '-' + designation).hexdigest()) #md5: first_name-last_name-designation
        if not data.attendee_exists(user_hash):
            data.add_attendee(first_name, last_name, designation, role, user_hash)
            d['error'] = 'none'
            d['success'] = True
        else:
            d['error'] = 'noSuchAttendee'
            d['success'] = False
    else:
        d['error'] = 'noPermission'
        d['success'] = False
    return jsonify(d)



###Attendance Management###

@app.route('/api/v3/management/remove_attendee', methods=['POST'])
def management_remove_attendee():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['remove_attendee_specific']):
        user_hash = json.get('user_hash') #md5: first_name-last_name-designation
        if data.attendee_exists(user_hash):
            data.remove_attendee(user_hash)
            d['error'] = 'none'
            d['success'] = True
        else:
            d['error'] = 'noSuchAttendee'
            d['success'] = False
    else:
        d['error'] = 'noPermission'
        d['success'] = False
    return jsonify(d)

@app.route('/api/v3/management/remove_record', methods=['POST'])
def management_remove_record():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['remove_record_specific']):
        user_hash = json.get('user_hash') #md5: first_name-last_name-designation
        record_hash = json.get('record_hash') #md5: first_name-last_name-designation-datestr
        if data.attendee_exists(user_hash):
            if data.attendee_record_exists(user_hash, record_hash):
                data.remove_attendee_record(user_hash, record_hash)
                d['error'] = 'none'
                d['success'] = True
            else:
                d['error'] = 'noSuchRecord'
                d['success'] = False
        else:
            d['error'] = 'noSuchAttendee'
            d['success'] = False
    else:
        d['error'] = 'noPermission'
        d['success'] = False
    return jsonify(d)

@app.route('/api/v3/management/update_attendee_notes', methods=['POST'])
def management_update_attendee_notes():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['update_notes_specific']):
        user_hash = json.get('user_hash') #md5: first_name-last_name-designation
        notes = json.get('notes')
        if data.attendee_exists(user_hash):
            data.update_attendee_notes(user_hash, notes)
            d['error'] = 'none'
            d['success'] = True
        else:
            d['error'] = 'noSuchAttendee'
            d['success'] = False
    else:
        d['error'] = 'noPermission'
        d['success'] = False
    return jsonify(d)



###Attendance Information###

@app.route('/api/v3/data/attendee_data', methods=['POST'])
def data_attendee_data():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['list_records_specific']):
        user_hash = json.get('user_hash') #md5: first_name-last_name-designation
        if data.attendee_exists(user_hash):
            d['error'] = 'none'
            d['success'] = True
            d['data'] = data.get_attendee_data(user_hash)
        else:
            d['error'] = 'noSuchAttendee'
            d['success'] = False
            d['data'] = {}
    else:
        d['error'] = 'noPermission'
        d['success'] = False
        d['data'] = {}
    return jsonify(d)

@app.route('/api/v3/data/search_attendees', methods=['POST'])
def data_search_attendees():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['list_attendee_info_all']):
        characters = request.json.get('characters')
        d['error'] = 'none'
        d['success'] = True
        d['matching_attendees'] = data.search_attendees(characters)
    else:
        d['error'] = 'noPermission'
        d['success'] = False
        d['matching_attendees'] = {}
    return jsonify(d)

@app.route('/api/v3/data/attendees_info', methods=['POST'])
def data_attendees_info():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['list_attendee_info_all']):
        d['error'] = 'none'
        d['success'] = True
        d['info'] = data.attendees_info()
    else:
        d['error'] = 'noPermission'
        d['success'] = False
        d['matching_attendees'] = {}
    return jsonify(d)

@app.route('/api/v3/data/weekly_summary', methods=['POST'])
def data_weekly_summary():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['list_records_weekly']):
        #date = request.json.get('date', None)
        d['error'] = 'none'
        d['success'] = True
        d['summary'] = data.get_weekly_summary()
    else:
        d['error'] = 'noPermission'
        d['success'] = False
        d['summary'] = {}
    return jsonify(d)

@app.route('/api/v3/data/full_data', methods=['POST'])
def data_full_data():
    json = request.get_json(force=True)
    d = {}
    username = session['username']
    if auth.has_permission(username, ['list_records_all']):
        d['error'] = 'none'
        d['success'] = True
        d['data'] = data.get_all_data()
    else:
        d['error'] = 'noPermission'
        d['success'] = False
        d['data'] = {}
    return jsonify(d)



###Default Page###

@app.route('/', methods=['GET', 'POST'])
def main_domain():
    return '', 200

@app.route('/api/v3/auth/check', methods=['POST'])
def auth_check():
    return '', 200

if __name__ == '__main__':
    startup()
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
