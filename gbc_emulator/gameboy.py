from time import time, sleep
from gbc_emulator.lr35902 import LR35902
from gbc_emulator.memory import Memory
from gbc_emulator.debugger import Debugger
from gbc_emulator.timer import Timer
from gbc_emulator.ppu import PPU

class Gameboy:
    CLOCK_PERIOD = 1 / 1048576
    CLOCKS_PER_CHECK = 10485 # 10 ms

    def __init__(self, pubsub, attach_debugger=False, bootloader_enabled=True):
        self.memory = Memory(pubsub)
        self.cpu = LR35902(self.memory.cpu_port, pubsub)
        self.timer = Timer(self.memory.timer_port)
        self.ppu = PPU(self.memory.ppu_port)
        self.rate = 0
        self.clocks = 0

        if attach_debugger:
            self.debugger = Debugger(self)

        if not bootloader_enabled:
            # Disable bootloader and skip it.
            self.memory.cpu_port[Memory.REGISTER_BOOTLOADER_DISABLED] = 0xFF
            self.cpu.PC = 0x100

        self.running = False

    def cycle(self):
        self.ppu.clock()
        self.ppu.clock()
        self.ppu.clock()
        self.ppu.clock()
        self.timer.clock()

        return self.cpu.clock()

    def run(self):
        last_time = time()
        self.running = True
        while self.running:
            now = time()
            if (
                    self.clocks < Gameboy.CLOCKS_PER_CHECK or
                    now >= (last_time + (Gameboy.CLOCK_PERIOD * Gameboy.CLOCKS_PER_CHECK))
                ):
                self.clocks += 1
                if self.clocks >= Gameboy.CLOCKS_PER_CHECK:
                    self.clocks = 0
                    self.rate = 0.5 * self.rate + 0.5 * (Gameboy.CLOCKS_PER_CHECK / (now - last_time))
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
