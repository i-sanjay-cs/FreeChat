# app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite for simplicity
db = SQLAlchemy(app)
socketio = SocketIO(app)
rooms = {}  # Dictionary to store room information

import sqlite3

conn = sqlite3.connect('site.db')
cursor = conn.cursor()

# Now you can execute SQL queries, e.g., cursor.execute("SELECT * FROM chat_room;")

class ChatRoom(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    expiration_time = db.Column(db.DateTime, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']

        # Check if the room code exists and is not expired
        room = ChatRoom.query.filter_by(id=code).first()
        if room and room.expiration_time > datetime.utcnow():
            return redirect(url_for('chat', name=name, code=code))
        else:
            return render_template('index.html', error='Invalid or expired code. Please try again.')

    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@socketio.on('join')
def handle_join(data):
    name = data['name']
    code = data['code']

    print(f"Join request received: {name}, {code}")

    # Check if the room code exists and is not expired
    room = ChatRoom.query.filter_by(id=code).first()
    if room and room.expiration_time > datetime.utcnow():
        join_room(code)  # Use join_room to add the user to the room
        rooms[request.sid] = code  # Update rooms dictionary with user's room
        print("User joined successfully.")
        emit('chat', {'message': f'{name} has joined the chat', 'name': 'System'}, room=code)
    else:
        # Create a new ChatRoom record with a future expiration time
        expiration_time = datetime.utcnow() + timedelta(days=1)
        new_room = ChatRoom(id=code, expiration_time=expiration_time)
        db.session.add(new_room)
        db.session.commit()

        # Inform the user about the successful join
        join_room(code)
        rooms[request.sid] = code
        print("User joined successfully.")
        emit('chat', {'message': f'{name} has joined the chat', 'name': 'System'}, room=code)




@socketio.on('message')
def handle_message(data):
    name = data['name']
    message = data['message']

    # Check if the user is in a room
    if request.sid in rooms:
        code = rooms[request.sid]
        emit('chat', {'message': message, 'name': name}, room=code)
    else:
        print(f"User {name} is not in a room. Ignoring message.")


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in rooms:
        code = rooms[sid]
        del rooms[sid]
        emit('chat', {'message': 'A user has left the chat', 'name': 'System'}, room=code)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
