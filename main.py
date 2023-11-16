from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, emit


app = Flask(__name__)
socketio = SocketIO(app, async_mode="gevent")  # Set async_mode to "gevent" for Gunicorn
rooms = {}  # Dictionary to store room information

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        return redirect(url_for('chat', name=name, code=code))

    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@socketio.on('join')
def handle_join(data):
    name = data['name']
    code = data['code']

    print(f"Join request received: {name}, {code}")

    join_room(code)  # Use join_room to add the user to the room
    rooms[request.sid] = code  # Update rooms dictionary with the user's room
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
        print(f"User {name} is not in a room. Ignoring the message.")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in rooms:
        code = rooms[sid]
        del rooms[sid]
        emit('chat', {'message': 'A user has left the chat', 'name': 'System'}, room=code)

if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()

    from gunicorn import pywsgi

    # Assuming your SocketIO instance is named socketio and your Flask app is named app
    gunicorn_app = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=socketio.server.GeventWebSocketHandler)
    gunicorn_app.serve_forever()
