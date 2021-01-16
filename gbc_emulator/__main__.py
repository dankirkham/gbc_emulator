#!/usr/bin/env python

import argparse
import threading
import sys
from gbc_emulator.gameboy import Gameboy
from gbc_emulator.window import do_window

parser = argparse.ArgumentParser()
parser.add_argument('rom')
args = parser.parse_args()

gameboy = Gameboy(attach_debugger=True, bootloader_enabled=False)
ptr = 0
with open(args.rom, "rb") as f:
    byte = f.read(1)
    while byte:
        gameboy.memory.cpu_port[ptr] = int.from_bytes(byte, byteorder='little')
        ptr += 1
        byte = f.read(1)

def done():
    gameboy.debugger.onecmd("EOF")
    sys.exit()

debugger_thread = threading.Thread(target=gameboy.debugger.cmdloop)
debugger_thread.start()

# do_window(gameboy, done)
