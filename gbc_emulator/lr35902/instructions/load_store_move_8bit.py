# GBCPUman.pdf page 65
# Opcodes 0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E
# Put 8-bit immediate value into 8-bit register.
# NOTE: This is also implements 0x3E from LD A, # from page 68.
def ld_nn_n_a(self):
    self.A = self.memory[self.PC + 1]

def ld_nn_n_b(self):
    self.B = self.memory[self.PC + 1]

def ld_nn_n_c(self):
    self.C = self.memory[self.PC + 1]

def ld_nn_n_d(self):
    self.D = self.memory[self.PC + 1]

def ld_nn_n_e(self):
    self.E = self.memory[self.PC + 1]

def ld_nn_n_h(self):
    self.H = self.memory[self.PC + 1]

def ld_nn_n_l(self):
    self.L = self.memory[self.PC + 1]

# GBCPUman.pdf page 66
# Opcodes
# A - 0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D
# B - 0x40, 0x41, 0x42, 0x43, 0x44, 0x45
# C - 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D
# D - 0x50, 0x51, 0x52, 0x53, 0x54, 0x55
# E - 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D
# H - 0x60, 0x61, 0x62, 0x63, 0x64, 0x65
# L - 0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D
# Put value of r2 into r1
# r2 = src register
# r1 = dst register
# Note: A is not a valid source for this function. It is documented in
# ld_n_a page 69.
def ld_a_b_between_registers(self):
    """0x78"""
    self.A = self.B

def ld_a_c_between_registers(self):
    """0x79"""
    self.A = self.C

def ld_a_d_between_registers(self):
    """0x7A"""
    self.A = self.D

def ld_a_e_between_registers(self):
    """0x7B"""
    self.A = self.E

def ld_a_h_between_registers(self):
    """0x7C"""
    self.A = self.H

def ld_a_l_between_registers(self):
    """0x7D"""
    self.A = self.L

def ld_b_c_between_registers(self):
    """0x41"""
    self.B = self.C

def ld_b_d_between_registers(self):
    """0x42"""
    self.B = self.D

def ld_b_e_between_registers(self):
    """0x43"""
    self.B = self.E

def ld_b_h_between_registers(self):
    """0x44"""
    self.B = self.H

def ld_b_l_between_registers(self):
    """0x45"""
    self.B = self.L

def ld_c_b_between_registers(self):
    """0x48"""
    self.C = self.B

def ld_c_d_between_registers(self):
    """0x4A"""
    self.C = self.D

def ld_c_e_between_registers(self):
    """0x4B"""
    self.C = self.E

def ld_c_h_between_registers(self):
    """0x4C"""
    self.C = self.H

def ld_c_l_between_registers(self):
    """0x4D"""
    self.C = self.L

def ld_d_b_between_registers(self):
    """0x50"""
    self.D = self.B

def ld_d_c_between_registers(self):
    """0x51"""
    self.D = self.C

def ld_d_e_between_registers(self):
    """0x53"""
    self.D = self.E

def ld_d_h_between_registers(self):
    """0x54"""
    self.D = self.H

def ld_d_l_between_registers(self):
    """0x55"""
    self.D = self.L

def ld_e_b_between_registers(self):
    """0x58"""
    self.E = self.B

def ld_e_c_between_registers(self):
    """0x59"""
    self.E = self.C

def ld_e_d_between_registers(self):
    """0x5A"""
    self.E = self.D

def ld_e_h_between_registers(self):
    """0x5C"""
    self.E = self.H

def ld_e_l_between_registers(self):
    """0x5D"""
    self.E = self.L

def ld_h_b_between_registers(self):
    """0x60"""
    self.H = self.B

def ld_h_c_between_registers(self):
    """0x61"""
    self.H = self.C

def ld_h_d_between_registers(self):
    """0x62"""
    self.H = self.D

def ld_h_e_between_registers(self):
    """0x63"""
    self.H = self.E

def ld_h_l_between_registers(self):
    """0x65"""
    self.H = self.L

def ld_l_b_between_registers(self):
    """0x68"""
    self.L = self.B

def ld_l_c_between_registers(self):
    """0x69"""
    self.L = self.C

def ld_l_d_between_registers(self):
    """0x6A"""
    self.L = self.D

def ld_l_e_between_registers(self):
    """0x6B"""
    self.L = self.E

def ld_l_h_between_registers(self):
    """0x6C"""
    self.L = self.H

# GBCPUman.pdf page 66
# Opcodes 0x46, 0x4E, 0x56, 0x5E, 0x66, 0x6E
# Put value of memory at r2 into r1
# r2 = src register pointing to memory
# r1 = dst register
def ld_hl_b_from_memory(self, dst=None):
    """0x46"""
    ptr = (self.H << 8) | self.L
    self.B = self.memory[ptr]

def ld_hl_c_from_memory(self, dst=None):
    """0x4E"""
    ptr = (self.H << 8) | self.L
    self.C = self.memory[ptr]

def ld_hl_d_from_memory(self, dst=None):
    """0x56"""
    ptr = (self.H << 8) | self.L
    self.D = self.memory[ptr]

def ld_hl_e_from_memory(self, dst=None):
    """0x5E"""
    ptr = (self.H << 8) | self.L
    self.E = self.memory[ptr]

def ld_hl_h_from_memory(self, dst=None):
    """0x66"""
    ptr = (self.H << 8) | self.L
    self.H = self.memory[ptr]

def ld_hl_l_from_memory(self, dst=None):
    """0x6E"""
    ptr = (self.H << 8) | self.L
    self.L = self.memory[ptr]

# GBCPUman.pdf page 66
# Opcodes 0x70, 0x71, 0x72, 0x73, 0x74, 0x75
# Put value of r2 into memory at r1
# r2 = src register
# r1 = dst register pointing to memory
def ld_hl_b_to_memory(self, src=None):
    """0x70"""
    self.memory[(self.H << 8) | self.L] = self.B

def ld_hl_c_to_memory(self, src=None):
    """0x71"""
    self.memory[(self.H << 8) | self.L] = self.C

def ld_hl_d_to_memory(self, src=None):
    """0x72"""
    self.memory[(self.H << 8) | self.L] = self.D

def ld_hl_e_to_memory(self, src=None):
    """0x73"""
    self.memory[(self.H << 8) | self.L] = self.E

def ld_hl_h_to_memory(self, src=None):
    """0x74"""
    self.memory[(self.H << 8) | self.L] = self.H

def ld_hl_l_to_memory(self, src=None):
    """0x75"""
    self.memory[(self.H << 8) | self.L] = self.L

def ld_r1_r2_immediate_to_memory(self):
    """"GBCPUman.pdf page 66
    Opcode 0x36
    Put value of r2 into memory at r1
    r1 = dst register pointing to memory
    r2 = immediate 8-bit value
    """
    self.memory[(self.H << 8) | self.L] = self.memory[self.PC + 1]

# GBCPUman.pdf page 68
# Opcodes 0x0A, 0x1A, 0x7E
# Put value of n into A
# src = source register pointing to memory
def ld_a_bc_from_memory(self):
    """0x0A"""
    ptr = (self.B << 8) | self.C
    self.A = self.memory[ptr]

def ld_a_de_from_memory(self):
    """0x1A"""
    ptr = (self.D << 8) | self.E
    self.A = self.memory[ptr]

def ld_a_hl_from_memory(self):
    """0x78"""
    ptr = (self.H << 8) | self.L
    self.A = self.memory[ptr]

def ld_a_n_from_memory_immediate(self):
    """"GBCPUman.pdf page 68
    Opcode 0xFA
    Put value memory at nn into A
    nn - two byte immediate value
    """
    ptr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
    self.A = self.memory[ptr]

# GBCPUman.pdf page 69
# Opcodes 0x47, 0x4F, 0x57, 0x5F, 0x67, 0x6F, 0x7F
# Put value of A into register
# dst - source register
def ld_b_a(self):
    """0x47"""
    self.B = self.A

def ld_c_a(self):
    """0x4F"""
    self.C = self.A

def ld_d_a(self):
    """0x57"""
    self.D = self.A

def ld_e_a(self):
    """0x5F"""
    self.E = self.A

def ld_h_a(self):
    """0x67"""
    self.H = self.A

def ld_l_a(self):
    """0x6F"""
    self.L = self.A

# GBCPUman.pdf page 69
# Opcodes 0x02, 0x12, 0x77
# Put value of A into memory at register pointer
# dst - source register
def ld_bc_a_pointer(self):
    """0x02"""
    addr = (self.B << 8) | self.C
    self.memory[addr] = self.A

def ld_de_a_pointer(self):
    """0x12"""
    addr = (self.D << 8) | self.E
    self.memory[addr] = self.A

def ld_hl_a_pointer(self):
    """0x77"""
    addr = (self.H << 8) | self.L
    self.memory[addr] = self.A

def ld_n_a_immediate(self):
    """"GBCPUman.pdf page 69
    Opcodes 0xEA
    Put value of A into memory at immediate 16-bit address
    """
    addr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]

    self.memory[addr] = self.A

def ld_a_c(self):
    """"GBCPUman.pdf page 70
    Opcode 0xF2
    Put value at address 0xFF00 + C into register A
    """
    addr = 0xFF00 + self.C
    self.A = self.memory[addr]

def ld_c_a(self):
    """"GBCPUman.pdf page 70
    Opcode 0xE2
    Put value of register A into memory at address 0xFF00 + C.
    """
    addr = 0xFF00 + self.C
    self.memory[addr] = self.A

def ld_a_hl_decrement(self):
    """"GBCPUman.pdf page 71
    Opcode 0x3A
    Put value at address HL into A. Decrement HL.
    """
    addr = (self.H << 8) | self.L
    self.A = self.memory[addr]

    addr -= 1
    self.H = ((addr & 0xFF00) >> 8) & 0xFF
    self.L = addr & 0xFF

def ld_hl_a_decrement(self):
    """"GBCPUman.pdf page 72
    Opcode 0x32
    Put value at A into memory at address HL. Decrement HL.
    """
    addr = (self.H << 8) | self.L
    self.memory[addr] = self.A

    addr -= 1
    self.H = ((addr & 0xFF00) >> 8) & 0xFF
    self.L = addr & 0xFF

def ld_a_hl_increment(self):
    """"GBCPUman.pdf page 73
    Opcode 0x2A
    Put value at address HL into A. Increment HL.
    """
    addr = (self.H << 8) | self.L
    self.A = self.memory[addr]

    addr += 1
    self.H = ((addr & 0xFF00) >> 8) & 0xFF
    self.L = addr & 0xFF

def ld_hl_a_increment(self):
    """"GBCPUman.pdf page 74
    Opcode 0x22
    Put value at A into memory at address HL. Increment HL.
    """
    addr = (self.H << 8) | self.L
    self.memory[addr] = self.A

    addr += 1
    self.H = ((addr & 0xFF00) >> 8) & 0xFF
    self.L = addr & 0xFF

def ldh_n_a(self):
    """"GBCPUman.pdf page 75
    Opcode 0xE0
    Put value at A into memory at address n + 0xFF00
    n is an immediate byte
    """
    addr = self.memory[self.PC + 1] + 0xFF00
    self.memory[addr] = self.A

def ldh_a_n(self):
    """"GBCPUman.pdf page 75
    Opcode 0xF0
    Put value at address n + 0xFF00 into register A
    n is an immediate byte
    """
    addr = self.memory[self.PC + 1] + 0xFF00
    self.A = self.memory[addr]
