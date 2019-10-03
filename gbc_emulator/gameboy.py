from gbc_emulator.lr35902 import LR35902
from gbc_emulator.memory import Memory
from gbc_emulator.debugger import Debugger
from gbc_emulator.timer import Timer
from enum import Enum
from time import time, sleep

class Gameboy:
    CLOCK_PERIOD = 1 / 1048576

    def __init__(self, attach_debugger=False, bootloader_enabled=True):
        self.memory = Memory()
        self.cpu = LR35902(self.memory.cpu_port)
        self.timer = Timer(self.memory.timer_port)

        if attach_debugger:
            self.debugger = Debugger(self)

        if not bootloader_enabled:
            # Disable bootloader and skip it.
            self.memory.cpu_port[Memory.REGISTER_BOOTLOADER_DISABLED] = 0xFF
            self.cpu.PC = 0x100

        self.running = False

    def cycle(self):
        self.timer.clock()
        return self.cpu.clock()

    def run(self):
        last_time = time()
        self.running = True
        while self.running:
            now = time()
            if not (now >= (last_time + Gameboy.CLOCK_PERIOD)):
                sleep(0) # Release the GIL
            else:
                last_time = now
                cpu_result = self.cycle()

                if self.debugger:
                    if cpu_result == LR35902.BREAKPOINT_HIT:
                        self.running = False

                    if self.debugger.stop:
                        self.running = False

    def step(self):
        while self.cpu.wait != 0:
            self.cycle()

        return self.cycle()
