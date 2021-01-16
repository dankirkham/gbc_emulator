from gbc_emulator.memory import Memory
from gbc_emulator.lr35902 import LR35902

class PPU:
    MODE_HBLANK = 0
    MODE_VBLANK = 1
    MODE_OAM_SEARCH = 2
    MODE_ACTIVE_PICTURE = 3

    def __init__(self, memory):
        self.memory = memory
        self.mode = PPU.MODE_OAM_SEARCH
        self.wait = 0
        self.line = 0
        self.frame = [(0, 0, 0)] * 160 * 144

        self.DEBUG_last_mode = self.mode
        self.DEBUG_cycles = 0

    def clock(self):
        self.wait += 1

        self.DEBUG_cycles += 1
        if self.DEBUG_last_mode != self.mode:
            # print(self.DEBUG_last_mode, self.line, self.DEBUG_cycles)
            self.DEBUG_last_mode = self.mode

        if self.mode == PPU.MODE_HBLANK:
            if self.wait == 204:
                self.wait = 0
                self.line += 1

                if self.line >= 143:
                    # print('VBLANK')
                    if self.memory[Memory.REGISTER_IE] << LR35902.INTERRUPT_VBLANK:
                        # print('VBLANK INTERRUPT')
                        self.memory[Memory.REGISTER_IF] |= (1 << LR35902.INTERRUPT_VBLANK)
                    self.mode = PPU.MODE_VBLANK
                else:
                    self.mode = PPU.MODE_ACTIVE_PICTURE
        elif self.mode == PPU.MODE_VBLANK:
            if self.wait == 4560:
                self.wait = 0
                self.line = 0
                self.mode = PPU.MODE_OAM_SEARCH
        elif self.mode == PPU.MODE_OAM_SEARCH:
            if self.wait == 80:
                self.wait = 0
                self.mode = PPU.MODE_ACTIVE_PICTURE
        elif self.mode == PPU.MODE_ACTIVE_PICTURE:
            if self.wait == 172:
                self.wait = 0
                # Render a line
                # y = self.line - 1
                # for x_bytes in range(160 * 2):
                #

                self.mode = PPU.MODE_HBLANK
