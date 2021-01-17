import time
from gbc_emulator.mqtt import Mqtt

class bcolors:
    GREEN = '\u001b[38;5;2m'
    ENDC = '\033[0m'

def control(command):
    if command == "reset":
        print("\n" + time.asctime(), flush=True)


def print_byte(data):
    if data == "\n":
        print(bcolors.GREEN + "<LF>" + bcolors.ENDC, end='', flush=True)
    print(data, end='', flush=True)

print("\033[1;1H\u001b[2J" + time.asctime())

mqtt = Mqtt("127.0.0.1")
mqtt.on("serial/control", control)
mqtt.on("serial/out", print_byte)

# MQTT in main thread
mqtt.run()
