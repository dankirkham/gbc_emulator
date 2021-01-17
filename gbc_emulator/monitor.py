import time
from math import floor
from gbc_emulator.mqtt import Mqtt

CLOCK_FREQUENCY = 1048576

class bcolors:
    GREEN = '\u001b[38;5;2m'
    ENDC = '\033[0m'

def print_monitor(monitor):
    # print("\033[1;1H" + time.asctime())
    print("\033[1;1H\u001b[2J" + time.asctime())
    print("Emulation Speed: {}%".format(floor(monitor["rate"] / CLOCK_FREQUENCY * 100.0)))

    print("\nRegisters:")
    for register, value in monitor["registers"].items():
        print("  {}: 0x{}".format(register, value))

    print("\nStack:")
    sp = monitor["registers"]["SP"]
    for address, value in monitor["stack"]:
        if sp == address:
            print(bcolors.GREEN + "  0x{}: 0x{}".format(address, value) + bcolors.ENDC)
        else:
            print("  0x{}: 0x{}".format(address, value))

mqtt = Mqtt("127.0.0.1")
mqtt.on("monitor", print_monitor)

print("\033[1;1H\u001b[2J" + time.asctime())

# MQTT in main thread
mqtt.run()
