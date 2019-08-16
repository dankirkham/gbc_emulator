from gbc_emulator.lr35902 import LR35902
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('rom')
args = parser.parse_args()

memory = [0] * 2**16
ptr = 0
with open(args.rom, "rb") as f:
    byte = f.read(1)
    while byte:
        memory[ptr] = int.from_bytes(byte, byteorder='little')
        ptr += 1
        byte = f.read(1)

cpu = LR35902(memory)

cycle = 0
while True:
    print("Cycle: {}; PC: {}; Instruction: {}".format(cycle, cpu.PC, hex(memory[cpu.PC])))
    cpu.clock()
    cycle += 1
