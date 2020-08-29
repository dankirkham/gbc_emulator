# GBCPUman.pdf page 76
# Opcodes 0x01, 0x11, 0x21, 0x31
# Loads 16-bit immediate value into 16-bit register.

def ld_n_nn_bc(self, reg=None):
    self.B = self.memory[self.PC + 2]
    self.C = self.memory[self.PC + 1]

def ld_n_nn_de(self, reg=None):
    self.D = self.memory[self.PC + 2]
    self.E = self.memory[self.PC + 1]

def ld_n_nn_hl(self, reg=None):
    self.H = self.memory[self.PC + 2]
    self.L = self.memory[self.PC + 1]

def ld_n_nn_sp(self, reg=None):
    self.SP = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]

def ld_sp_hl(self):
    """GBCPUman.pdf page 76
    Opcode 0xF9
    Put HL into SP"""
    self.SP = (self.H << 8) | self.L

def ld_hl_sp_n(self):
    """GBCPUman.pdf page 77
    Opcode 0xF8
    Put SP + n into HL.
    n is a signed byte"""
    n = self.memory[self.PC + 1]
    if n & 0x80:
        # Negative, must convert with 2's complement
        n = -((~n & 0xFF) + 1)
    result = self.SP + n

    self.H = (result >> 8) & 0xFF
    self.L = result & 0xFF

    # TODO: Set C and H flags correctly.
    # https://stackoverflow.com/a/7261149
    # For now, just clear all flags
    self.F = 0

def ld_nn_sp(self):
    """GBCPUman.pdf page 78
    Opcode 0x08
    Put SP at address nn
    nn is two bytes."""
    nn = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
    self.memory[nn] = self.SP & 0xFF
    self.memory[nn + 1] = (self.SP >> 8) & 0xFF

# GBCPUman.pdf page 78
# Opcodes 0xC5, 0xD5, 0xE5, 0xF5
# Push register pair onto stack.
# Decrement SP twice.
# TODO: Keeping lower byte at lower address. Verify this is correct.

def push_nn_bc(self):
    self.SP -= 2
    self.memory[self.SP + 1] = self.B
    self.memory[self.SP] = self.C

def push_nn_de(self):
    self.SP -= 2
    self.memory[self.SP + 1] = self.D
    self.memory[self.SP] = self.E

def push_nn_hl(self):
    self.SP -= 2
    self.memory[self.SP + 1] = self.H
    self.memory[self.SP] = self.L

def push_nn_af(self):
    self.SP -= 2
    self.memory[self.SP + 1] = self.A
    self.memory[self.SP] = self.F

# GBCPUman.pdf page 79
# Opcodes 0xC1, 0xD1, 0xE1, 0xF1
# Pop two bytes off of stack into register pair
# Increment SP twice.

def pop_nn_bc(self):
    self.B = self.memory[self.SP + 1]
    self.C = self.memory[self.SP]
    self.SP += 2

def pop_nn_de(self):
    self.D = self.memory[self.SP + 1]
    self.E = self.memory[self.SP]
    self.SP += 2

def pop_nn_hl(self):
    self.H = self.memory[self.SP + 1]
    self.L = self.memory[self.SP]
    self.SP += 2

def pop_nn_af(self):
    self.A = self.memory[self.SP + 1]
    self.F = self.memory[self.SP] & 0xF0 # Lower 4 bytes of can never be 1
    self.SP += 2
