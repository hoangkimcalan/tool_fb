from flask import Flask, request
from flask_socketio import SocketIO, emit
import eventlet
from threading import Lock
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


app = Flask(__name__)
socketio = SocketIO(app)

clients_lock = Lock()
connected_clients = []

@socketio.on('connect')
def handle_connect():
    print('client connected')
    client_id = request.sid
    with clients_lock:
        connected_clients.append(client_id)
    emit('check_new_messenger', {'message': 'server received'})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    with clients_lock:
        if client_id in connected_clients:
            connected_clients.remove(client_id)
    print(f"client disconnected")

@socketio.on('client_response')
def handle_client_response(data):
    print(f"received from client: {data}")

def periodic_task():
    while True:
        print('check message')
        with clients_lock:
            if not connected_clients:
                print("no connected clients")
            else:
                for client_id in connected_clients:
                    print("start check messenger:", client_id)
                    # socketio.emit('check_new_messenger', {'messenger':'send your data'}, to=client_id)
                    print("check done")
                    # socketio.sleep(3)
                    socketio.emit('auto_send_mess', {"id_fb": "61555051976616", "id_chat":"100025284053087", "content":"tuyệt vời quá"}, to=client_id)
                    print('reply done')
        socketio.sleep(300)


if __name__ == '__main__':
    socketio.start_background_task(periodic_task)
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)