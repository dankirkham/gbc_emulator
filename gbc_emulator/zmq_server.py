import json
import random
import threading
import zmq

class ZmqServer(threading.Thread):
    def __init__(self, gameboy):
        super().__init__()
        self.gameboy = gameboy
        # self.daemon = True

        # Set up ZeroMQ Server
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

    def run(self):
        while True:
            try:
                data = self.socket.recv(zmq.NOBLOCK)
                message = json.loads(data)
                print(message['type'])
            except zmq.error.Again:
                pass

            payload = {
                "number": random.randint(0, 256)
                }
            self.socket.send_string(json.dumps(payload))

if __name__ == "__main__":
    print("Starting standalone zmq server...")
    thread = ZmqServer(None)
    thread.start()
