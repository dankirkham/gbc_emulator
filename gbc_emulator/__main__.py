#!/usr/bin/env python

from gbc_emulator.lr35902 import LR35902
from gbc_emulator.memory import Memory
from gbc_emulator.debugger import Debugger
from gbc_emulator.window import do_window
import argparse
import threading
import sys

parser = argparse.ArgumentParser()
parser.add_argument('rom')
args = parser.parse_args()

memory = Memory()
memory[Memory.REGISTER_BOOTLOADER_DISABLED] = 0xFF

ptr = 0
with open(args.rom, "rb") as f:
    byte = f.read(1)
    while byte:
        memory[ptr] = int.from_bytes(byte, byteorder='little')
        ptr += 1
        byte = f.read(1)

# memory.verbose = True

cpu = LR35902(memory)
# cpu.verbose = True

cpu.A = 0x01
cpu.F = 0xB0
cpu.B = 0x00
cpu.C = 0x13
cpu.D = 0x00
cpu.E = 0xD8
cpu.H = 0x01
cpu.L = 0x4D
cpu.SP = 0xFFFE
cpu.PC = 0x100

debugger = Debugger(cpu)

def done():
    debugger.onecmd("EOF")
    sys.exit()

debugger_thread = threading.Thread(target=debugger.cmdloop)
debugger_thread.start()

do_window(cpu, done)

# while True:
#     cpu.clock()
#
# f = open('out.bin', 'wb')
# for byte in memory:
#     f.write(bytes(byte))
# f.close()
