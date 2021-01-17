import time
from gbc_emulator.mqtt import Mqtt
from gbc_emulator.lr35902 import LR35902

cpu = LR35902(None, None)

class bcolors:
    GREEN = '\u001b[38;5;2m'
    ENDC = '\033[0m'

def print_monitor(monitor):
    #print("\033[1;1H" + time.asctime())
    print("\033[1;1H\u001b[2J" + time.asctime())
    print("\nProgram:")
    pc = monitor["registers"]["PC"]
    for address, value in monitor["program"]:
        val_int = int(value, 16)
        mnemonic = "<Unknown>"
        if val_int == 0xCB:
            mnemonic = "<Bitwise Extension>"
        else:
            instruction = cpu.instructions[val_int]
            if instruction:
                mnemonic = instruction.mnemonic

        if pc == address:
            print(bcolors.GREEN + "  0x{}: 0x{} {}".format(address, value, mnemonic) + bcolors.ENDC)
        else:
            print("  0x{}: 0x{} {}".format(address, value, mnemonic))

mqtt = Mqtt("127.0.0.1")
mqtt.on("monitor", print_monitor)

print("\033[1;1H\u001b[2J" + time.asctime())

# MQTT in main thread
mqtt.run()
