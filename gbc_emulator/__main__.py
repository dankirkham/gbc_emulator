from gbc_emulator.lr35902 import LR35902
from gbc_emulator.memory import Memory
from gbc_emulator.debugger import Debugger
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('rom')
args = parser.parse_args()

memory = Memory()
memory.bootloader_enabled = False

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
cpu.PC = 0x100
cpu.SP = 0xFFFE
# cpu.A = 0x11 # GBC
cpu.F = 0x80
cpu.D = 0xFF
cpu.E = 0x56
cpu.L = 0x0D

debugger = Debugger(cpu)

debugger.cmdloop()

# while True:
#     cpu.clock()
#
# f = open('out.bin', 'wb')
# for byte in memory:
#     f.write(bytes(byte))
# f.close()
