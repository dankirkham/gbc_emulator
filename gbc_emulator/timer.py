from gbc_emulator.memory import Memory
from gbc_emulator.lr35902 import LR35902

class Timer:
    DIVIDER = 64

    SPEEDS = [
        256, # 00b
        4, # 01b
        16, # 10b
        64, # 11b
    ]

    def __init__(self, memory):
        self.memory = memory

        self.divider_wait = 0
        self.counter_wait = 0

    def clock(self):
        if self.memory[Memory.REGISTER_TAC] & 0x4: # Running
            self.divider_wait += 1
            self.counter_wait += 1

            # Divider counts up at a fixed 16384 Hz.
            if self.divider_wait >= Timer.DIVIDER:
                self.divider_wait = 0
                self.memory[Memory.REGISTER_DIV] = (self.memory[Memory.REGISTER_DIV] + 1) & 0xFF

            speed = Timer.SPEEDS[self.memory[Memory.REGISTER_TAC] & 0x03]
            if self.counter_wait >= speed:
                self.counter_wait = 0
                self.memory[Memory.REGISTER_TIMA] = (self.memory[Memory.REGISTER_TIMA] + 1) & 0xFF
                if self.memory[Memory.REGISTER_TIMA] == 0:
                    # Trigger interrupt on wrap
                    self.memory[Memory.REGISTER_IF] |= (1 << LR35902.INTERRUPT_TIMER)
                    # Reset to modulo
                    self.memory[Memory.REGISTER_TIMA] = self.memory[Memory.REGISTER_TMA]
