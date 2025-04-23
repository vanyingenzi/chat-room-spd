from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from collections import defaultdict
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
socketio = SocketIO(app)

# Track users per room: { room: { sid: { 'username': ..., 'ip': ... } } }
rooms = defaultdict(dict)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat')
def chat():
    username = request.args.get('username')
    room = request.args.get('room')
    if not username or not room:
        return redirect(url_for('index'))
    return render_template('chat.html', username=username, room=room)


def get_ip_info(ip):
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}')
        geo = resp.json()
        return jsonify({
            "country": resp.get('country'),
            "region": resp.get('regionName'),
            "city": resp.get('city'),
            "ip": ip
        })
    except requests.RequestException:
        return {}


@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data['username']
    sid = request.sid
    # TODO : Get the user's IP address
    # TODO: Get IP address of user
    join_room(room)
    rooms[room][sid] = {'username': username}
    # Notify all clients in room of updated user list
    users = list(rooms[room].values())
    emit('user_list', {'users': users}, room=room)
    emit('message', {'username': 'System',
         'msg': f'{username} has entered the room.'}, room=room)


@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    sid = request.sid
    user = rooms[room].get(sid)
    if user:
        emit('message', {'username': user['username'], 'msg': msg}, room=room)


@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    username = data['username']
    sid = request.sid
    leave_room(room)
    rooms[room].pop(sid, None)
    emit('message', {'username': 'System',
         'msg': f'{username} has left the room.'}, room=room)
    users = list(rooms[room].values())
    emit('user_list', {'users': users}, room=room)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5050)
