from collections import namedtuple

class LR35902:
    """Sharp LR35902 emulation. This is the CPU used in the Gameboy and Gameboy Color."""

    # Register map for F register
    FLAG_Z = 7 # Zero Flag
    FLAG_N = 6 # Subtract Flag
    FLAG_H = 5 # Half Carry Flag
    FLAG_C = 4 # Carry Flag

    # Register map
    REGISTER_NONE = 0
    REGISTER_A = 1
    REGISTER_B = 2
    REGISTER_C = 3
    REGISTER_D = 4
    REGISTER_E = 5
    REGISTER_F = 6
    REGISTER_H = 7
    REGISTER_L = 8
    REGISTER_BC = 9
    REGISTER_DE = 10
    REGISTER_HL = 11
    REGISTER_SP = 12
    REGISTER_AF = 13

    Instruction = namedtuple('Instruction', ['function', 'length_in_bytes', 'duration_in_cycles', 'mnemonic'])

    def __init__(self, memory):
        self.memory = memory

        # 8-bit registers
        self.A = 0x00 # Accumulator
        self.B = 0x00
        self.C = 0x00
        self.D = 0x00
        self.E = 0x00
        self.F = 0x00 # Flags register
        self.H = 0x00
        self.L = 0x00

        # 16-bit registers
        self.SP = 0x0000
        self.PC = 0x0000

        # How long to wait for instruction to complete
        self.wait = 0

        # Instruction map
        self.instructions = [
            LR35902.Instruction(function=None, length_in_bytes=1, duration_in_cycles=4, mnemonic='NOP'), # 0x00
            LR35902.Instruction(function=lambda s: ld_n_nn(s, LR35902.REGISTER_BC), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD BC,d16'), # 0x01
        ]

    def clock(self):
        if self.wait > 0:
            self.wait -= 1
        else:
            pass

        # Fetch

        # Decode

        # Execute

    # 8-bit load/store/move instructions
    def ld_nn_n(self, reg=None):
        """GBCPUman.pdf page 65

        Put 8-bit immediate value into 8-bit register.

        NOTE: This is also implements 0x3E from LD A, # from page 68.
        """

        if reg == LR35902.REGISTER_A: # (0x3E)
            self.A = self.memory[self.PC + 1]
        elif reg == LR35902.REGISTER_B:
            self.B = self.memory[self.PC + 1]
        elif reg == LR35902.REGISTER_C:
            self.C = self.memory[self.PC + 1]
        elif reg == LR35902.REGISTER_D:
            self.D = self.memory[self.PC + 1]
        elif reg == LR35902.REGISTER_E:
            self.E = self.memory[self.PC + 1]
        elif reg == LR35902.REGISTER_H:
            self.H = self.memory[self.PC + 1]
        elif reg == LR35902.REGISTER_L:
            self.L = self.memory[self.PC + 1]
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    def ld_r1_r2_between_registers(self, src=None, dst=None):
        """"GBCPUman.pdf page 66

        Put value of r2 into r1

        r2 = src register
        r1 = dst register
        """
        if src == LR35902.REGISTER_A: # (0x3E)
            val = self.A
        elif src == LR35902.REGISTER_B:
            val = self.B
        elif src == LR35902.REGISTER_C:
            val = self.C
        elif src == LR35902.REGISTER_D:
            val = self.D
        elif src == LR35902.REGISTER_E:
            val = self.E
        elif src == LR35902.REGISTER_H:
            val = self.H
        elif src == LR35902.REGISTER_L:
            val = self.L
        else:
            raise RuntimeError('Invalid source register "{}" specified!'.format(src))

        if dst == LR35902.REGISTER_A: # (0x3E)
            self.A = val
        elif dst == LR35902.REGISTER_B:
            self.B = val
        elif dst == LR35902.REGISTER_C:
            self.C = val
        elif dst == LR35902.REGISTER_D:
            self.D = val
        elif dst == LR35902.REGISTER_E:
            self.E = val
        elif dst == LR35902.REGISTER_H:
            self.H = val
        elif dst == LR35902.REGISTER_L:
            self.L = val
        else:
            raise RuntimeError('Invalid destination register "{}" specified!'.format(dst))

    def ld_r1_r2_from_memory(self, src=None, dst=None):
        """"GBCPUman.pdf page 66

        Put value of memory at r2 into r1

        r2 = src register pointing to memory
        r1 = dst register
        """
        if src == LR35902.REGISTER_HL:
            ptr = (self.H << 8) | self.L
        else:
            raise RuntimeError('Invalid source register "{}" specified!'.format(src))

        if dst == LR35902.REGISTER_A: # (0x7E)
            self.A = self.memory[ptr]
        elif dst == LR35902.REGISTER_B:
            self.B = self.memory[ptr]
        elif dst == LR35902.REGISTER_C:
            self.C = self.memory[ptr]
        elif dst == LR35902.REGISTER_D:
            self.D = self.memory[ptr]
        elif dst == LR35902.REGISTER_E:
            self.E = self.memory[ptr]
        elif dst == LR35902.REGISTER_H:
            self.H = self.memory[ptr]
        elif dst == LR35902.REGISTER_L:
            self.L = self.memory[ptr]
        else:
            raise RuntimeError('Invalid destination register "{}" specified!'.format(dst))

    def ld_r1_r2_to_memory(self, src=None, dst=None):
        """"GBCPUman.pdf page 66

        Put value of r2 into memory at r1

        r2 = src register
        r1 = dst register pointing to memory
        """
        if src == LR35902.REGISTER_B:
            val = self.B
        elif src == LR35902.REGISTER_C:
            val = self.C
        elif src == LR35902.REGISTER_D:
            val = self.D
        elif src == LR35902.REGISTER_E:
            val = self.E
        elif src == LR35902.REGISTER_H:
            val = self.H
        elif src == LR35902.REGISTER_L:
            val = self.L
        else:
            raise RuntimeError('Invalid source register "{}" specified!'.format(src))

        if dst == LR35902.REGISTER_HL:
            self.memory[(self.H << 8) | self.L] = val
        else:
            raise RuntimeError('Invalid destination register "{}" specified!'.format(dst))

    def ld_r1_r2_immediate_to_memory(self, dst=None):
        """"GBCPUman.pdf page 66

        Put value of r2 into memory at r1

        r1 = dst register pointing to memory
        r2 = immediate 8-bit value
        """
        if dst == LR35902.REGISTER_HL:
            self.memory[(self.H << 8) | self.L] = self.memory[self.PC + 1]
        else:
            raise RuntimeError('Invalid destination register "{}" specified!'.format(dst))

    def ld_a_n_from_memory(self, src=None):
        """"GBCPUman.pdf page 68

        Put value of n into A

        src = source register pointing to memory
        """
        if src == LR35902.REGISTER_BC:
            ptr = (self.B << 8) | self.C
        elif src == LR35902.REGISTER_DE:
            ptr = (self.D << 8) | self.E
        elif src == LR35902.REGISTER_HL:
            ptr = (self.H << 8) | self.L
        else:
            raise RuntimeError('Invalid source register "{}" specified!'.format(src))

        self.A = self.memory[ptr]

    def ld_a_n_from_memory_immediate(self):
        """"GBCPUman.pdf page 68

        Put value memory at nn into A

        nn - two byte immediate value
        """
        ptr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
        self.A = self.memory[ptr]

    def ld_n_a(self, src):
        """"GBCPUman.pdf page 69

        Put value of register into A.

        src - source register
        """
        if src == LR35902.REGISTER_A:
            val = self.A
        elif src == LR35902.REGISTER_B:
            val = self.B
        elif src == LR35902.REGISTER_C:
            val = self.C
        elif src == LR35902.REGISTER_D:
            val = self.D
        elif src == LR35902.REGISTER_E:
            val = self.E
        elif src == LR35902.REGISTER_H:
            val = self.H
        elif src == LR35902.REGISTER_L:
            val = self.L
        else:
            raise RuntimeError('Invalid source register "{}" specified!'.format(src))

        self.A = val

    def ld_a_c(self):
        """"GBCPUman.pdf page 70

        Put value at address 0xFF00 + C into register A
        """
        addr = 0xFF00 + self.C
        self.A = self.memory[addr]

    def ld_c_a(self):
        """"GBCPUman.pdf page 70

        Put value of register A into memory at address 0xFF00 + C.
        """
        addr = 0xFF00 + self.C
        self.memory[addr] = self.A

    def ld_a_hl_decrement(self):
        """"GBCPUman.pdf page 71

        Put value at address HL into A. Decrement HL.
        """
        addr = (self.H << 8) | self.L
        self.A = self.memory[addr]

        addr -= 1
        self.H = ((addr & 0xFF00) >> 8) & 0xFF
        self.L = addr & 0xFF

    def ld_hl_a_decrement(self):
        """"GBCPUman.pdf page 72

        Put value at A into memory at address HL. Decrement HL.
        """
        addr = (self.H << 8) | self.L
        self.memory[addr] = self.A

        addr -= 1
        self.H = ((addr & 0xFF00) >> 8) & 0xFF
        self.L = addr & 0xFF

    def ld_a_hl_increment(self):
        """"GBCPUman.pdf page 73

        Put value at address HL into A. Increment HL.
        """
        addr = (self.H << 8) | self.L
        self.A = self.memory[addr]

        addr += 1
        self.H = ((addr & 0xFF00) >> 8) & 0xFF
        self.L = addr & 0xFF

    def ld_hl_a_increment(self):
        """"GBCPUman.pdf page 74

        Put value at A into memory at address HL. Increment HL.
        """
        addr = (self.H << 8) | self.L
        self.memory[addr] = self.A

        addr += 1
        self.H = ((addr & 0xFF00) >> 8) & 0xFF
        self.L = addr & 0xFF

    def ldh_n_a(self):
        """"GBCPUman.pdf page 75

        Put value at A into memory at address n + 0xFF00

        n is an immediate byte
        """
        addr = self.memory[self.PC + 1] + 0xFF00
        self.memory[addr] = self.A

    def ldh_n_a(self):
        """"GBCPUman.pdf page 75

        Put value at address n + 0xFF00 into register A

        n is an immediate byte
        """
        addr = self.memory[self.PC + 1] + 0xFF00
        self.A = self.memory[addr]

    # 16-bit load/store/move instructions
    def ld_n_nn(self, reg=None):
        """GBCPUman.pdf page 76

        Loads 16-bit immediate value into 16-bit register.

        n = register
        nn = 16-bit value"""
        val_h = self.memory[self.PC + 2]
        val_l = self.memory[self.PC + 1]

        if reg == LR35902.REGISTER_BC:
            self.B = val_h
            self.C = val_l
        elif reg == LR35902.REGISTER_DE:
            self.D = val_h
            self.E = val_l
        elif reg == LR35902.REGISTER_HL:
            self.H = val_h
            self.L = val_l
        elif reg == LR35902.REGISTER_SP:
            self.S = val_h
            self.P = val_l
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    def ld_sp_hl(self):
        """GBCPUman.pdf page 76

        Put HL into SP"""
        self.SP = (self.H << 8) | self.L

    def ld_hl_sp_n(self):
        """GBCPUman.pdf page 77

        Put SP + n into HL.

        n is a signed byte"""
        n = self.memory[self.PC + 1]
        if n & 0x80:
            # Negative, must convert with 2's complement
            n = -((~n & 0xFF) + 1)
        self.HL = self.SP + n

        # TODO: Set C and H flags correctly.
        # https://stackoverflow.com/a/7261149
        # For now, just clear all flags
        self.F = 0

    def ld_nn_sp(self):
        """GBCPUman.pdf page 78

        Put SP at address nn

        nn is two bytes."""
        nn = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
        self.memory[nn] = self.SP

    def push_nn(self, reg=None):
        """GBCPUman.pdf page 78

        Push register pair onto stack.
        Decrement SP twice.

        TODO: Keeping lower byte at lower address. Hopefully this is correct.
        """

        if reg == LR35902.REGISTER_BC:
            self.memory[self.SP] = self.B
            self.memory[self.SP - 1] = self.C
        elif reg == LR35902.REGISTER_DE:
            self.memory[self.SP] = self.D
            self.memory[self.SP - 1] = self.E
        elif reg == LR35902.REGISTER_HL:
            self.memory[self.SP] = self.H
            self.memory[self.SP - 1] = self.L
        elif reg == LR35902.REGISTER_AF:
            self.memory[self.SP] = self.A
            self.memory[self.SP - 1] = self.F
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        self.SP -= 2

    def pop_nn(self, reg=None):
        """GBCPUman.pdf page 79

        Pop two bytes off of stack into register pair
        Increment SP twice.

        TODO: Keeping lower byte at lower address. Hopefully this is correct.
        """

        if reg == LR35902.REGISTER_BC:
            self.B = self.memory[self.SP]
            self.C = self.memory[self.SP + 1]
        elif reg == LR35902.REGISTER_DE:
            self.D = self.memory[self.SP]
            self.E = self.memory[self.SP + 1]
        elif reg == LR35902.REGISTER_HL:
            self.H = self.memory[self.SP]
            self.L = self.memory[self.SP + 1]
        elif reg == LR35902.REGISTER_AF:
            self.A = self.memory[self.SP]
            self.F = self.memory[self.SP + 1]
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        self.SP += 2
