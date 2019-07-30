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
            LR35902.Instruction(function=lambda s: ld_n_a_pointer(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (BC),A'), # 0x02
            LR35902.Instruction(function=lambda s: inc_nn(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC BC'), # 0x03
            None, # 0x04
            None, # 0x05
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD B,d8'), # 0x06
            None, # 0x07
            LR35902.Instruction(function=ld_nn_sp, length_in_bytes=3, duration_in_cycles=20, mnemonic='LD (a16),SP'), # 0x08
            LR35902.Instruction(function=lambda s: add_hl_n(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,BC'), # 0x09
            LR35902.Instruction(function=lambda s: ld_a_n_from_memory(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(BC)'), # 0x0A
            LR35902.Instruction(function=lambda s: dec_nn(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC BC'), # 0x0B
            None, # 0x0C
            None, # 0x0D
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD C,d8'), # 0x0E
            None, # 0x0F
            LR35902.Instruction(function=None, length_in_bytes=1, duration_in_cycles=4, mnemonic='NOP'), # 0x20
            LR35902.Instruction(function=lambda s: ld_n_nn(s, LR35902.REGISTER_BC), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD BC,d16'), # 0x21
            LR35902.Instruction(function=lambda s: ld_n_a_pointer(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (BC),A'), # 0x22
            LR35902.Instruction(function=lambda s: inc_nn(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC BC'), # 0x23
            None, # 0x24
            None, # 0x25
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD B,d8'), # 0x26
            None, # 0x27
            LR35902.Instruction(function=ld_nn_sp, length_in_bytes=3, duration_in_cycles=20, mnemonic='LD (a16),SP'), # 0x28
            LR35902.Instruction(function=lambda s: add_hl_n(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,BC'), # 0x29
            LR35902.Instruction(function=lambda s: ld_a_n_from_memory(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(BC)'), # 0x2A
            LR35902.Instruction(function=lambda s: dec_nn(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC BC'), # 0x2B
            None, # 0x2C
            None, # 0x2D
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD C,d8'), # 0x2E
            None, # 0x2F
            None, # 0x10
            LR35902.Instruction(function=lambda s: ld_n_nn(s, LR35902.REGISTER_DE), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD DE,d16'), # 0x11
            LR35902.Instruction(function=lambda s: ld_n_a_pointer(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (DE),A'), # 0x12
            LR35902.Instruction(function=lambda s: inc_nn(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC DE'), # 0x13
            None, # 0x14
            None, # 0x15
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD D,d8'), # 0x16
            None, # 0x17
            None, # 0x18
            LR35902.Instruction(function=lambda s: add_hl_n(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,DE'), # 0x19
            LR35902.Instruction(function=lambda s: ld_a_n_from_memory(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(DE)'), # 0x1A
            LR35902.Instruction(function=lambda s: dec_nn(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC DE'), # 0x1B
            None, # 0x1C
            None, # 0x1D
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD E,d8'), # 0x1E
            None, # 0x1F
            None, # 0x20
            LR35902.Instruction(function=lambda s: ld_n_nn(s, LR35902.REGISTER_HL), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD HL,d16'), # 0x21
            LR35902.Instruction(function=ld_hl_a_increment, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL+),A'), # 0x22
            LR35902.Instruction(function=lambda s: inc_nn(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC HL'), # 0x23
            None, # 0x24
            None, # 0x25
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD H,d8'), # 0x26
            None, # 0x27
            None, # 0x28
            LR35902.Instruction(function=lambda s: add_hl_n(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,HL'), # 0x29
            LR35902.Instruction(function=ld_a_hl_increment, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(HL+)'), # 0x2A
            LR35902.Instruction(function=lambda s: dec_nn(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC HL'), # 0x2B
            None, # 0x2C
            None, # 0x2D
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD L,d8'), # 0x2E
            None, # 0x2F
            None, # 0x30
            LR35902.Instruction(function=lambda s: ld_n_nn(s, LR35902.REGISTER_SP), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD SP,d16'), # 0x31
            LR35902.Instruction(function=ld_hl_a_decrement, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL-),A'), # 0x32
            LR35902.Instruction(function=lambda s: inc_nn(s, LR35902.REGISTER_SP), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC SP'), # 0x33
            None, # 0x34
            None, # 0x35
            LR35902.Instruction(function=lambda s: ld_r1_r2_immediate_to_memory(s, LR35902.REGISTER_HL), length_in_bytes=2, duration_in_cycles=12, mnemonic='LD (HL),d8'), # 0x36
            None, # 0x37
            None, # 0x38
            LR35902.Instruction(function=lambda s: add_hl_n(s, LR35902.REGISTER_SP), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,SP'), # 0x39
            LR35902.Instruction(function=ld_a_hl_decrement, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(HL-)'), # 0x3A
            LR35902.Instruction(function=lambda s: dec_nn(s, LR35902.REGISTER_SP), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC SP'), # 0x3B
            None, # 0x3C
            None, # 0x3D
            LR35902.Instruction(function=lambda s: ld_nn_n(s, LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD A,d8'), # 0x3E
            None, # 0x3F
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,B'), # 0x40
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,C'), # 0x41
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,D'), # 0x42
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,E'), # 0x43
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,H'), # 0x44
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,L'), # 0x45
            LR35902.Instruction(function=lambda s: ld_r1_r2_from_memory(s, src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD B,(HL)'), # 0x46
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,A'), # 0x47
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,B'), # 0x48
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,C'), # 0x49
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,D'), # 0x4A
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,E'), # 0x4B
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,H'), # 0x4C
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,L'), # 0x4D
            LR35902.Instruction(function=lambda s: ld_r1_r2_from_memory(s, src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD C,(HL)'), # 0x4E
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,A'), # 0x4F
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,B'), # 0x50
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,C'), # 0x51
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,D'), # 0x52
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,E'), # 0x53
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,H'), # 0x54
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,L'), # 0x55
            LR35902.Instruction(function=lambda s: ld_r1_r2_from_memory(s, src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD D,(HL)'), # 0x56
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,A'), # 0x57
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,B'), # 0x58
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,C'), # 0x59
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,D'), # 0x5A
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,E'), # 0x5B
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,H'), # 0x5C
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,L'), # 0x5D
            LR35902.Instruction(function=lambda s: ld_r1_r2_from_memory(s, src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD E,(HL)'), # 0x5E
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,A'), # 0x5F
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,B'), # 0x60
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,C'), # 0x61
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,D'), # 0x62
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,E'), # 0x63
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,H'), # 0x64
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,L'), # 0x65
            LR35902.Instruction(function=lambda s: ld_r1_r2_from_memory(s, src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD H,(HL)'), # 0x66
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,A'), # 0x67
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,B'), # 0x68
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,C'), # 0x69
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,D'), # 0x6A
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,E'), # 0x6B
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,H'), # 0x6C
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,L'), # 0x6D
            LR35902.Instruction(function=lambda s: ld_r1_r2_from_memory(s, src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD L,(HL)'), # 0x6E
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,A'), # 0x6F
            LR35902.Instruction(function=lambda s: ld_r1_r2_to_memory(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),B'), # 0x70
            LR35902.Instruction(function=lambda s: ld_r1_r2_to_memory(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),C'), # 0x71
            LR35902.Instruction(function=lambda s: ld_r1_r2_to_memory(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),D'), # 0x72
            LR35902.Instruction(function=lambda s: ld_r1_r2_to_memory(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),E'), # 0x73
            LR35902.Instruction(function=lambda s: ld_r1_r2_to_memory(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),H'), # 0x74
            LR35902.Instruction(function=lambda s: ld_r1_r2_to_memory(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),L'), # 0x75
            None, # 0x76
            LR35902.Instruction(function=lambda s: ld_n_a_pointer(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),A'), # 0x77
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_B, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,B'), # 0x78
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_C, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,C'), # 0x79
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_D, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,D'), # 0x7A
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_E, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,E'), # 0x7B
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_H, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,H'), # 0x7C
            LR35902.Instruction(function=lambda s: ld_r1_r2_between_registers(s, src=LR35902.REGISTER_L, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,L'), # 0x7D
            LR35902.Instruction(function=lambda s: ld_a_n_from_memory(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(HL)'), # 0x7E
            LR35902.Instruction(function=lambda s: ld_n_a(s, LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,A'), # 0x7F
            None, # 0x80
            None, # 0x81
            None, # 0x82
            None, # 0x83
            None, # 0x84
            None, # 0x85
            None, # 0x86
            None, # 0x87
            None, # 0x88
            None, # 0x89
            None, # 0x8A
            None, # 0x8B
            None, # 0x8C
            None, # 0x8D
            None, # 0x8E
            None, # 0x8F
            None, # 0x90
            None, # 0x91
            None, # 0x92
            None, # 0x93
            None, # 0x94
            None, # 0x95
            None, # 0x96
            None, # 0x97
            None, # 0x98
            None, # 0x99
            None, # 0x9A
            None, # 0x9B
            None, # 0x9C
            None, # 0x9D
            None, # 0x9E
            None, # 0x9F
            None, # 0xA0
            None, # 0xA1
            None, # 0xA2
            None, # 0xA3
            None, # 0xA4
            None, # 0xA5
            None, # 0xA6
            None, # 0xA7
            None, # 0xA8
            None, # 0xA9
            None, # 0xAA
            None, # 0xAB
            None, # 0xAC
            None, # 0xAD
            None, # 0xAE
            None, # 0xAF
            None, # 0xB0
            None, # 0xB1
            None, # 0xB2
            None, # 0xB3
            None, # 0xB4
            None, # 0xB5
            None, # 0xB6
            None, # 0xB7
            None, # 0xB8
            None, # 0xB9
            None, # 0xBA
            None, # 0xBB
            None, # 0xBC
            None, # 0xBD
            None, # 0xBE
            None, # 0xBF
            None, # 0xC0
            LR35902.Instruction(function=lambda s: pop_nn(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP BC'), # 0xC1
            None, # 0xC2
            None, # 0xC3
            None, # 0xC4
            LR35902.Instruction(function=lambda s: push_nn(s, LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH BC'), # 0xC5
            None, # 0xC6
            None, # 0xC7
            None, # 0xC8
            None, # 0xC9
            None, # 0xCA
            None, # 0xCB
            None, # 0xCC
            None, # 0xCD
            None, # 0xCE
            None, # 0xCF
            None, # 0xD0
            LR35902.Instruction(function=lambda s: pop_nn(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP DE'), # 0xD1
            None, # 0xD2
            None, # 0xD3
            None, # 0xD4
            LR35902.Instruction(function=lambda s: push_nn(s, LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH DE'), # 0xD5
            None, # 0xD6
            None, # 0xD7
            None, # 0xD8
            None, # 0xD9
            None, # 0xDA
            None, # 0xDB
            None, # 0xDC
            None, # 0xDD
            None, # 0xDE
            None, # 0xDF
            LR35902.Instruction(function=ldh_n_a, length_in_bytes=2, duration_in_cycles=12, mnemonic='LDH (a8),A'), # 0xE0
            LR35902.Instruction(function=lambda s: pop_nn(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP HL'), # 0xE1
            LR35902.Instruction(function=ld_c_a, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (C),A'), # 0xE2  # This disagrees with pastraiser length of 2 bytes
            None, # 0xE3
            None, # 0xE4
            LR35902.Instruction(function=lambda s: push_nn(s, LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH HL'), # 0xE5
            None, # 0xE6
            None, # 0xE7
            LR35902.Instruction(function=add_sp_n, length_in_bytes=2, duration_in_cycles=16, mnemonic='ADD SP,r8'), # 0xE8
            None, # 0xE9
            LR35902.Instruction(function=ld_n_a_immediate, length_in_bytes=3, duration_in_cycles=16, mnemonic='LD (a16),A'), # 0xEA
            None, # 0xEB
            None, # 0xEC
            None, # 0xED
            None, # 0xEE
            None, # 0xEF
            LR35902.Instruction(function=ldh_a_n, length_in_bytes=2, duration_in_cycles=12, mnemonic='LDH A,(a8)'), # 0xF0
            LR35902.Instruction(function=lambda s: pop_nn(s, LR35902.REGISTER_AF), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP AF'), # 0xF1
            LR35902.Instruction(function=ld_a_c, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(C)'), # 0xF2 # This disagrees with pastraiser length of 2 bytes
            None, # 0xF3
            None, # 0xF4
            LR35902.Instruction(function=lambda s: push_nn(s, LR35902.REGISTER_AF), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH AF'), # 0xF5
            None, # 0xF6
            None, # 0xF7
            LR35902.Instruction(function=ld_hl_sp_n, length_in_bytes=2, duration_in_cycles=12, mnemonic='LD HL,SP+r8'), # 0xF8
            LR35902.Instruction(function=ld_sp_hl, length_in_bytes=1, duration_in_cycles=8, mnemonic='LD SP,HL'), # 0xF9
            LR35902.Instruction(function=ld_a_n_from_memory_immediate, length_in_bytes=3, duration_in_cycles=16, mnemonic='LD A,(a16)'), # 0xFA
            None, # 0xFB
            None, # 0xFC
            None, # 0xFD
            None, # 0xFE
            None, # 0xFF
        ]

        # Instruction map
        self.cb_instructions = [
            None, # 0x00
            None, # 0x01
            None, # 0x02
            None, # 0x03
            None, # 0x04
            None, # 0x05
            None, # 0x06
            None, # 0x07
            None, # 0x08
            None, # 0x09
            None, # 0x0A
            None, # 0x0B
            None, # 0x0C
            None, # 0x0D
            None, # 0x0E
            None, # 0x0F
            None, # 0x10
            None, # 0x11
            None, # 0x12
            None, # 0x13
            None, # 0x14
            None, # 0x15
            None, # 0x16
            None, # 0x17
            None, # 0x18
            None, # 0x19
            None, # 0x1A
            None, # 0x1B
            None, # 0x1C
            None, # 0x1D
            None, # 0x1E
            None, # 0x1F
            None, # 0x20
            None, # 0x21
            None, # 0x22
            None, # 0x23
            None, # 0x24
            None, # 0x25
            None, # 0x26
            None, # 0x27
            None, # 0x28
            None, # 0x29
            None, # 0x2A
            None, # 0x2B
            None, # 0x2C
            None, # 0x2D
            None, # 0x2E
            None, # 0x2F
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP B'), # 0x30
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP C'), # 0x31
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP D'), # 0x32
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP E'), # 0x33
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP H'), # 0x34
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP L'), # 0x35
            LR35902.Instruction(function=lambda s: swap_memory(s), length_in_bytes=2, duration_in_cycles=16, mnemonic='SWAP (HL)'), # 0x36
            LR35902.Instruction(function=lambda s: swap(s, LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP A'), # 0x37
            None, # 0x38
            None, # 0x39
            None, # 0x3A
            None, # 0x3B
            None, # 0x3C
            None, # 0x3D
            None, # 0x3E
            None, # 0x3F
            None, # 0x40
            None, # 0x41
            None, # 0x42
            None, # 0x43
            None, # 0x44
            None, # 0x45
            None, # 0x46
            None, # 0x47
            None, # 0x48
            None, # 0x49
            None, # 0x4A
            None, # 0x4B
            None, # 0x4C
            None, # 0x4D
            None, # 0x4E
            None, # 0x4F
            None, # 0x50
            None, # 0x51
            None, # 0x52
            None, # 0x53
            None, # 0x54
            None, # 0x55
            None, # 0x56
            None, # 0x57
            None, # 0x58
            None, # 0x59
            None, # 0x5A
            None, # 0x5B
            None, # 0x5C
            None, # 0x5D
            None, # 0x5E
            None, # 0x5F
            None, # 0x60
            None, # 0x61
            None, # 0x62
            None, # 0x63
            None, # 0x64
            None, # 0x65
            None, # 0x66
            None, # 0x67
            None, # 0x68
            None, # 0x69
            None, # 0x6A
            None, # 0x6B
            None, # 0x6C
            None, # 0x6D
            None, # 0x6E
            None, # 0x6F
            None, # 0x70
            None, # 0x71
            None, # 0x72
            None, # 0x73
            None, # 0x74
            None, # 0x75
            None, # 0x76
            None, # 0x77
            None, # 0x78
            None, # 0x79
            None, # 0x7A
            None, # 0x7B
            None, # 0x7C
            None, # 0x7D
            None, # 0x7E
            None, # 0x7F
            None, # 0x80
            None, # 0x81
            None, # 0x82
            None, # 0x83
            None, # 0x84
            None, # 0x85
            None, # 0x86
            None, # 0x87
            None, # 0x88
            None, # 0x89
            None, # 0x8A
            None, # 0x8B
            None, # 0x8C
            None, # 0x8D
            None, # 0x8E
            None, # 0x8F
            None, # 0x90
            None, # 0x91
            None, # 0x92
            None, # 0x93
            None, # 0x94
            None, # 0x95
            None, # 0x96
            None, # 0x97
            None, # 0x98
            None, # 0x99
            None, # 0x9A
            None, # 0x9B
            None, # 0x9C
            None, # 0x9D
            None, # 0x9E
            None, # 0x9F
            None, # 0xA0
            None, # 0xA1
            None, # 0xA2
            None, # 0xA3
            None, # 0xA4
            None, # 0xA5
            None, # 0xA6
            None, # 0xA7
            None, # 0xA8
            None, # 0xA9
            None, # 0xAA
            None, # 0xAB
            None, # 0xAC
            None, # 0xAD
            None, # 0xAE
            None, # 0xAF
            None, # 0xB0
            None, # 0xB1
            None, # 0xB2
            None, # 0xB3
            None, # 0xB4
            None, # 0xB5
            None, # 0xB6
            None, # 0xB7
            None, # 0xB8
            None, # 0xB9
            None, # 0xBA
            None, # 0xBB
            None, # 0xBC
            None, # 0xBD
            None, # 0xBE
            None, # 0xBF
            None, # 0xC0
            None, # 0xC1
            None, # 0xC2
            None, # 0xC3
            None, # 0xC4
            None, # 0xC5
            None, # 0xC6
            None, # 0xC7
            None, # 0xC8
            None, # 0xC9
            None, # 0xCA
            None, # 0xCB
            None, # 0xCC
            None, # 0xCD
            None, # 0xCE
            None, # 0xCF
            None, # 0xD0
            None, # 0xD1
            None, # 0xD2
            None, # 0xD3
            None, # 0xD4
            None, # 0xD5
            None, # 0xD6
            None, # 0xD7
            None, # 0xD8
            None, # 0xD9
            None, # 0xDA
            None, # 0xDB
            None, # 0xDC
            None, # 0xDD
            None, # 0xDE
            None, # 0xDF
            None, # 0xE0
            None, # 0xE1
            None, # 0xE2
            None, # 0xE3
            None, # 0xE4
            None, # 0xE5
            None, # 0xE6
            None, # 0xE7
            None, # 0xE8
            None, # 0xE9
            None, # 0xEA
            None, # 0xEB
            None, # 0xEC
            None, # 0xED
            None, # 0xEE
            None, # 0xEF
            None, # 0xF0
            None, # 0xF1
            None, # 0xF2
            None, # 0xF3
            None, # 0xF4
            None, # 0xF5
            None, # 0xF6
            None, # 0xF7
            None, # 0xF8
            None, # 0xF9
            None, # 0xFA
            None, # 0xFB
            None, # 0xFC
            None, # 0xFD
            None, # 0xFE
            None, # 0xFF
        ]

    def set_zero(self, value):
        if value == 0:
            self.F |= (1 << LR35902.FLAG_Z)
        else:
            self.F &= ~(1 << LR35902.FLAG_Z)

    def clock(self):
        if self.wait > 0:
            self.wait -= 1
        else:
            pass

        # Fetch

        # Decode

        # Execute

    def bit_extension(self):
        # Handle bit manipulation instruction on 0xCB prefix'd instructions
        pass

    # 8-bit load/store/move instructions
    def ld_nn_n(self, reg=None):
        """GBCPUman.pdf page 65
        Opcodes 0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E
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
        Opcodes
        A - 0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D
        B - 0x40, 0x41, 0x42, 0x43, 0x44, 0x45
        C - 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D
        D - 0x50, 0x51, 0x52, 0x53, 0x54, 0x55
        E - 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D
        H - 0x60, 0x61, 0x62, 0x63, 0x64, 0x65
        L - 0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D
        Put value of r2 into r1
        r2 = src register
        r1 = dst register
        Note: A is not a valid source for this function. It is documented in
        ld_n_a page 69.
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

        if dst == LR35902.REGISTER_A:
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
        Opcodes 0x46, 0x4E, 0x56, 0x5E, 0x66, 0x6E, 0x7E
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
        Opcodes 0x70, 0x71, 0x72, 0x73, 0x74, 0x75
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
        Opcode 0x36
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
        Opcodes 0x0A, 0x1A, 0x7E
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
        Opcode 0xFA
        Put value memory at nn into A
        nn - two byte immediate value
        """
        ptr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
        self.A = self.memory[ptr]

    def ld_n_a(self, dst):
        """"GBCPUman.pdf page 69
        Opcodes 0x47, 0x4F, 0x57, 0x5F, 0x67, 0x6F, 0x7F
        Put value of A into register
        dst - source register
        """
        if dst == LR35902.REGISTER_A:
            # self.A = self.A
            pass
        elif dst == LR35902.REGISTER_B:
            self.B = self.A
        elif dst == LR35902.REGISTER_C:
            self.C = self.A
        elif dst == LR35902.REGISTER_D:
            self.D = self.A
        elif dst == LR35902.REGISTER_E:
            self.E = self.A
        elif dst == LR35902.REGISTER_H:
            self.H = self.A
        elif dst == LR35902.REGISTER_L:
            self.L = self.A
        else:
            raise RuntimeError('Invalid destination register "{}" specified!'.format(dst))

    def ld_n_a_pointer(self, dst):
        """"GBCPUman.pdf page 69
        Opcodes 0x02, 0x12, 0x77
        Put value of A into memory at register pointer
        dst - source register
        """
        if dst == LR35902.REGISTER_BC:
            addr = (self.B << 8) | self.C
        elif dst == LR35902.REGISTER_DE:
            addr = (self.D << 8) | self.E
        elif dst == LR35902.REGISTER_HL:
            addr = (self.H << 8) | self.L
        else:
            raise RuntimeError('Invalid destination register "{}" specified!'.format(dst))

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

    # 16-bit load/store/move instructions
    def ld_n_nn(self, reg=None):
        """GBCPUman.pdf page 76
        Opcodes 0x01, 0x11, 0x21, 0x31
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
        Self.L = result & 0xFF

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
        self.memory[nn] = (self.SP >> 8) & 0xFF

    def push_nn(self, reg=None):
        """GBCPUman.pdf page 78
        Opcodes 0xC5, 0xD5, 0xE5, 0xF5
        Push register pair onto stack.
        Decrement SP twice.
        TODO: Keeping lower byte at lower address. Verify this is correct.
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
        Opcodes 0xC1, 0xD1, 0xE1, 0xF1
        Pop two bytes off of stack into register pair
        Increment SP twice.
        TODO: Keeping lower byte at lower address. Verify this is correct.
        """

        self.SP += 2

        if reg == LR35902.REGISTER_BC:
            self.B = self.memory[self.SP]
            self.C = self.memory[self.SP - 1]
        elif reg == LR35902.REGISTER_DE:
            self.D = self.memory[self.SP]
            self.E = self.memory[self.SP - 1]
        elif reg == LR35902.REGISTER_HL:
            self.H = self.memory[self.SP]
            self.L = self.memory[self.SP - 1]
        elif reg == LR35902.REGISTER_AF:
            self.A = self.memory[self.SP]
            self.F = self.memory[self.SP - 1]
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    # 8-bit arithmetic
    def add_a_n_register(self, reg=None):
        """GBCPUman.pdf page 80
        Opcodes 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x87
        Add register to A and store it in A.
        """

        if reg == LR35902.REGISTER_A:
            addend = self.A
        elif reg == LR35902.REGISTER_B:
            addend = self.B
        elif reg == LR35902.REGISTER_C:
            addend = self.C
        elif reg == LR35902.REGISTER_D:
            addend = self.D
        elif reg == LR35902.REGISTER_E:
            addend = self.E
        elif reg == LR35902.REGISTER_H:
            addend = self.H
        elif reg == LR35902.REGISTER_L:
            addend = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform addition
        self.A = (self.A + addend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def add_a_n_memory(self):
        """GBCPUman.pdf page 80
        Opcodes 0x86
        Add value from memory at location HL to register A and store it in register A.
        """

        addr = (self.H << 8) | self.L
        addend = self.memory[addr]

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform addition
        self.A = (self.A + addend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def add_a_n_immediate(self):
        """GBCPUman.pdf page 80
        Opcodes 0xC6
        Add immediate byte to register A and store it in register A.
        """

        addend = self.memory[self.PC + 1]

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform addition
        self.A = (self.A + addend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def adc_a_n_register(self, reg=None):
        """GBCPUman.pdf page 81
        Opcodes 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8F
        Add register and carry bit to A and store it in A.
        """

        if reg == LR35902.REGISTER_A:
            addend = self.A
        elif reg == LR35902.REGISTER_B:
            addend = self.B
        elif reg == LR35902.REGISTER_C:
            addend = self.C
        elif reg == LR35902.REGISTER_D:
            addend = self.D
        elif reg == LR35902.REGISTER_E:
            addend = self.E
        elif reg == LR35902.REGISTER_H:
            addend = self.H
        elif reg == LR35902.REGISTER_L:
            addend = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        carry_bit = (self.F & (1 << LR3590s.FLAG_C)) >> LR3590s.FLAG_C

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def adc_a_n_memory(self):
        """GBCPUman.pdf page 81
        Opcodes 0x8E
        Add value from memory at location HL and carry bit to register A and store it in register A.
        """

        addr = (self.H << 8) | self.L
        addend = self.memory[addr]

        carry_bit = (self.F & (1 << LR3590s.FLAG_C)) >> LR3590s.FLAG_C

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def adc_a_n_immediate(self):
        """GBCPUman.pdf page 81
        Opcodes 0xCE
        Add immediate byte and carry bit to register A and store it in register A.
        """

        addend = self.memory[self.PC + 1]

        carry_bit = (self.F & (1 << LR3590s.FLAG_C)) >> LR3590s.FLAG_C

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def sub_n_register(self, reg=None):
        """GBCPUman.pdf page 82
        Opcodes 0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x97
        Subtract register reg from register A.
        """

        if reg == LR35902.REGISTER_A:
            subtrahend = self.A
        elif reg == LR35902.REGISTER_B:
            subtrahend = self.B
        elif reg == LR35902.REGISTER_C:
            subtrahend = self.C
        elif reg == LR35902.REGISTER_D:
            subtrahend = self.D
        elif reg == LR35902.REGISTER_E:
            subtrahend = self.E
        elif reg == LR35902.REGISTER_H:
            subtrahend = self.H
        elif reg == LR35902.REGISTER_L:
            subtrahend = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (subtrahend & 0xF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (subtrahend & 0xFF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def sub_n_memory(self):
        """GBCPUman.pdf page 82
        Opcodes 0x96
        Subtract value pointed to by register HL from register A.
        """

        addr = (self.H << 8) | self.L
        subtrahend = self.memory[addr]

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (subtrahend & 0xF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (subtrahend & 0xFF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def sub_n_immediate(self):
        """GBCPUman.pdf page 82
        Opcodes 0xD6
        Subtract immediate byte from register A.
        """

        subtrahend = self.memory[self.PC + 1]

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (subtrahend & 0xF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (subtrahend & 0xFF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def subc_n_register(self, reg=None):
        """GBCPUman.pdf page 83
        Opcodes 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9F
        Subtract register reg and carry bit from register A.
        """

        if reg == LR35902.REGISTER_A:
            subtrahend = self.A
        elif reg == LR35902.REGISTER_B:
            subtrahend = self.B
        elif reg == LR35902.REGISTER_C:
            subtrahend = self.C
        elif reg == LR35902.REGISTER_D:
            subtrahend = self.D
        elif reg == LR35902.REGISTER_E:
            subtrahend = self.E
        elif reg == LR35902.REGISTER_H:
            subtrahend = self.H
        elif reg == LR35902.REGISTER_L:
            subtrahend = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        carry_bit = (self.F & (1 << LR3590s.FLAG_C)) >> LR3590s.FLAG_C

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (subtrahend & 0xF) - carry_bit) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (subtrahend & 0xFF) - carry_bit) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend - carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def subc_n_memory(self):
        """GBCPUman.pdf page 83
        Opcodes 0x9E
        Subtract value pointed to by register HL and carry bit from register A.
        """

        addr = (self.H << 8) | self.L
        subtrahend = self.memory[addr]

        carry_bit = (self.F & (1 << LR3590s.FLAG_C)) >> LR3590s.FLAG_C

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (subtrahend & 0xF) - carry_bit) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (subtrahend & 0xFF) - carry_bit) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend - carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def subc_n_immediate(self):
        """GBCPUman.pdf page 83
        Opcodes 0xDE
        Subtract immediate byte and carry bit from register A.
        Note: GBCPUman.pdf does not list an opcode for this, but pastraiser does.
        """

        subtrahend = self.memory[self.PC + 1]

        carry_bit = (self.F & (1 << LR3590s.FLAG_C)) >> LR3590s.FLAG_C

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (subtrahend & 0xF) - carry_bit) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (subtrahend & 0xFF) - carry_bit) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend - carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def and_n_register(self, reg=None):
        """GBCPUman.pdf page 84
        Opcodes 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA7
        And register reg with A and store it in A.
        """

        if reg == LR35902.REGISTER_A:
            operand = self.A
        elif reg == LR35902.REGISTER_B:
            operand = self.B
        elif reg == LR35902.REGISTER_C:
            operand = self.C
        elif reg == LR35902.REGISTER_D:
            operand = self.D
        elif reg == LR35902.REGISTER_E:
            operand = self.E
        elif reg == LR35902.REGISTER_H:
            operand = self.H
        elif reg == LR35902.REGISTER_L:
            operand = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # H is always set
        new_flags = (1 << LR3590s.FLAG_H)

        # Perform arithmetic
        self.A = (self.A & operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def and_n_memory(self):
        """GBCPUman.pdf page 84
        Opcodes 0xA6
        And value pointed to by register HL with A and store it in A
        """

        addr = (self.H << 8) | self.L
        operand = self.memory[addr]

        # H is always set
        new_flags = (1 << LR3590s.FLAG_H)

        # Perform arithmetic
        self.A = (self.A & operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def and_n_immediate(self):
        """GBCPUman.pdf page 84
        Opcodes 0xE6
        And immediate byte with A and store it in A
        """

        operand = self.memory[self.PC + 1]

        # H is always set
        new_flags = (1 << LR3590s.FLAG_H)

        # Perform arithmetic
        self.A = (self.A & operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def or_n_register(self, reg=None):
        """GBCPUman.pdf page 85
        Opcodes 0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB7
        OR register reg with A and store it in A.
        """

        if reg == LR35902.REGISTER_A:
            operand = self.A
        elif reg == LR35902.REGISTER_B:
            operand = self.B
        elif reg == LR35902.REGISTER_C:
            operand = self.C
        elif reg == LR35902.REGISTER_D:
            operand = self.D
        elif reg == LR35902.REGISTER_E:
            operand = self.E
        elif reg == LR35902.REGISTER_H:
            operand = self.H
        elif reg == LR35902.REGISTER_L:
            operand = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # Clear all flags
        new_flags = 0

        # Perform arithmetic
        self.A = (self.A | operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def or_n_memory(self):
        """GBCPUman.pdf page 85
        Opcodes 0xB6
        OR value pointed to by register HL with A and store it in A
        """

        addr = (self.H << 8) | self.L
        operand = self.memory[addr]

        # Clear all flags
        new_flags = 0

        # Perform arithmetic
        self.A = (self.A | operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def or_n_immediate(self):
        """GBCPUman.pdf page 85
        Opcodes 0xF6
        OR immediate byte with A and store it in A
        """

        operand = self.memory[self.PC + 1]

        # Clear all flags
        new_flags = 0

        # Perform arithmetic
        self.A = (self.A | operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def xor_n_register(self, reg=None):
        """GBCPUman.pdf page 86
        Opcodes 0xA8, 0xA9, 0xAA, 0xAB, 0xAC, 0xAD, 0xAF
        XOR register reg with A and store it in A.
        """

        if reg == LR35902.REGISTER_A:
            operand = self.A
        elif reg == LR35902.REGISTER_B:
            operand = self.B
        elif reg == LR35902.REGISTER_C:
            operand = self.C
        elif reg == LR35902.REGISTER_D:
            operand = self.D
        elif reg == LR35902.REGISTER_E:
            operand = self.E
        elif reg == LR35902.REGISTER_H:
            operand = self.H
        elif reg == LR35902.REGISTER_L:
            operand = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # Clear all flags
        new_flags = 0

        # Perform arithmetic
        self.A = (self.A ^ operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def xor_n_memory(self):
        """GBCPUman.pdf page 86
        Opcodes 0xAE
        XOR value pointed to by register HL with A and store it in A
        """

        addr = (self.H << 8) | self.L
        operand = self.memory[addr]

        # Clear all flags
        new_flags = 0

        # Perform arithmetic
        self.A = (self.A ^ operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def xor_n_immediate(self):
        """GBCPUman.pdf page 85
        Opcodes 0xEE
        XOR immediate byte with A and store it in A
        """

        operand = self.memory[self.PC + 1]

        # Clear all flags
        new_flags = 0

        # Perform arithmetic
        self.A = (self.A ^ operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def cp_n_register(self, reg=None):
        """GBCPUman.pdf page 87
        Opcodes 0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBF
        Comparee register reg with register A.
        """

        if reg == LR35902.REGISTER_A:
            operand = self.A
        elif reg == LR35902.REGISTER_B:
            operand = self.B
        elif reg == LR35902.REGISTER_C:
            operand = self.C
        elif reg == LR35902.REGISTER_D:
            operand = self.D
        elif reg == LR35902.REGISTER_E:
            operand = self.E
        elif reg == LR35902.REGISTER_H:
            operand = self.H
        elif reg == LR35902.REGISTER_L:
            operand = self.L
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (operand & 0xF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (operand & 0xFF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        result = (self.A - operand) & 0xFF

        # Process zero
        if result == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def cp_n_memory(self):
        """GBCPUman.pdf page 87
        Opcodes 0xBE
        Compare value pointed to by register HL with register A.
        """

        addr = (self.H << 8) | self.L
        operand = self.memory[addr]

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (operand & 0xF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (operand & 0xFF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        result = (self.A - operand) & 0xFF

        # Process zero
        if result == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def cp_n_immediate(self):
        """GBCPUman.pdf page 87
        Opcodes 0xFE
        Compare immediate byte with register A.
        """

        operand = self.memory[self.PC + 1]

        # N is always set
        new_flags = (1 << LR3590s.FLAG_N)

        # Process half borrow
        if ((self.A & 0xF) - (operand & 0xF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Process borrow
        if ((self.A & 0xFF) - (operand & 0xFF)) >= 0:
            new_flags |= (1 << LR3590s.FLAG_C)

        # Perform subtraction
        result = (self.A - operand) & 0xFF

        # Process zero
        if result == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def inc_n_register(self, reg=None):
        """GBCPUman.pdf page 88
        Opcodes 0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x3C
        Increment register reg
        """

        if reg == LR35902.REGISTER_A:
            reg_attr = 'A'
        elif reg == LR35902.REGISTER_B:
            reg_attr = 'B'
        elif reg == LR35902.REGISTER_C:
            reg_attr = 'C'
        elif reg == LR35902.REGISTER_D:
            reg_attr = 'D'
        elif reg == LR35902.REGISTER_E:
            reg_attr = 'E'
        elif reg == LR35902.REGISTER_H:
            reg_attr = 'H'
        elif reg == LR35902.REGISTER_L:
            reg_attr = 'L'
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # Keep C flag
        new_flags = 0 | (self.F & (1 << LR3590s.FLAG_C))

        # Process half carry
        if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Perform increment
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) + 1) & 0xFF
        )

        # Process zero
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def inc_n_memory(self):
        """GBCPUman.pdf page 88
        Opcodes 0x34
        Increment value at memory location HL
        """

        addr = (self.H << 8) | self.L

        # Keep C flag
        new_flags = 0 | (self.F & (1 << LR3590s.FLAG_C))

        # Process half carry
        if ((self.memory[addr] & 0xF) + 1) & 0x10:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Perform addition
        self.memory[addr] = (self.memory[addr] + 1) & 0xFF

        # Process zero
        if self.memory[addr] == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def dec_n_register(self, reg=None):
        """GBCPUman.pdf page 89
        Opcodes 0x05, 0x0D, 0x15, 0x1D, 0x25, 0x2D, 0x3D
        Decrement register reg
        """

        if reg == LR35902.REGISTER_A:
            reg_attr = 'A'
        elif reg == LR35902.REGISTER_B:
            reg_attr = 'B'
        elif reg == LR35902.REGISTER_C:
            reg_attr = 'C'
        elif reg == LR35902.REGISTER_D:
            reg_attr = 'D'
        elif reg == LR35902.REGISTER_E:
            reg_attr = 'E'
        elif reg == LR35902.REGISTER_H:
            reg_attr = 'H'
        elif reg == LR35902.REGISTER_L:
            reg_attr = 'L'
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        # Keep C flag
        new_flags = 0 | (self.F & (1 << LR3590s.FLAG_C))

        # Process half carry
        if getattr(self, reg_attr) & 0xF == 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Perform decrement
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) - 1) & 0xFF
        )

        # Process zero
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def dec_n_memory(self):
        """GBCPUman.pdf page 89
        Opcodes 0x35
        Decrement value at memory location HL
        """

        addr = (self.H << 8) | self.L

        # Keep C flag
        new_flags = 0 | (self.F & (1 << LR3590s.FLAG_C))

        # Process half carry
        if self.memory[addr] & 0xF == 0:
            new_flags |= (1 << LR3590s.FLAG_H)

        # Perform decrement
        self.memory[addr] = (self.memory[addr] - 1) & 0xFF

        # Process zero
        if self.memory[addr] == 0:
            new_flags |= (1 << LR3590s.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def add_hl_n(self, reg=None):
        """GBCPUman.pdf page 90
        Opcodes 0x09, 0x19, 0x29, 0x39
        Add 16-bit register to register HL
        """

        hl_val = (self.H << 8) | self.L

        if reg == LR35902.REGISTER_BC:
            val = (self.B << 8) | self.C
        elif reg == LR35902.REGISTER_DE:
            val = (self.D << 8) | self.E
        elif reg == LR35902.REGISTER_HL:
            val = hl_val
        elif reg == LR35902.REGISTER_SP:
            val = self.SP
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        hv_val += val

        self.H = ((hl_val & 0xFF00) >> 8) & 0xFF
        self.L = hl_val & 0xFF

    def add_sp_n(self):
        """GBCPUman.pdf page 91
        Opcode 0xE8
        Add immediate byte to SP.
        """

        operand = self.memory[self.PC + 1]

        self.SP = (self.SP + operand) & 0xFFFF

    def inc_nn(self, reg=None):
        """GBCPUman.pdf page 92
        Opcodes 0x03, 0x13, 0x23, 0x33
        Increment 16-bit register
        """

        if reg == LR35902.REGISTER_BC:
            val = (self.B << 8) | self.C
        elif reg == LR35902.REGISTER_DE:
            val = (self.D << 8) | self.E
        elif reg == LR35902.REGISTER_HL:
            val = (self.H << 8) | self.L
        elif reg == LR35902.REGISTER_SP:
            val = self.SP
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        val = (val + 1) & 0xFFFF

        if reg == LR35902.REGISTER_BC:
            self.B = ((val & 0xFF00) >> 8) & 0xFF
            self.C = val & 0xFF
        elif reg == LR35902.REGISTER_DE:
            self.D = ((val & 0xFF00) >> 8) & 0xFF
            self.E = val & 0xFF
        elif reg == LR35902.REGISTER_HL:
            self.H = ((val & 0xFF00) >> 8) & 0xFF
            self.L = val & 0xFF
        elif reg == LR35902.REGISTER_SP:
            self.SP = val
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    def dec_nn(self, reg=None):
        """GBCPUman.pdf page 93
        Opcodes 0x0B, 0x1B, 0x2B, 0x3B
        Increment 16-bit register
        """

        if reg == LR35902.REGISTER_BC:
            val = (self.B << 8) | self.C
        elif reg == LR35902.REGISTER_DE:
            val = (self.D << 8) | self.E
        elif reg == LR35902.REGISTER_HL:
            val = (self.H << 8) | self.L
        elif reg == LR35902.REGISTER_SP:
            val = self.SP
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        val = (val - 1) & 0xFFFF

        if reg == LR35902.REGISTER_BC:
            self.B = ((val & 0xFF00) >> 8) & 0xFF
            self.C = val & 0xFF
        elif reg == LR35902.REGISTER_DE:
            self.D = ((val & 0xFF00) >> 8) & 0xFF
            self.E = val & 0xFF
        elif reg == LR35902.REGISTER_HL:
            self.H = ((val & 0xFF00) >> 8) & 0xFF
            self.L = val & 0xFF
        elif reg == LR35902.REGISTER_SP:
            self.SP = val
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    def swap(self, reg=None)::
        """GBCPUman.pdf page 94
        0xCB Opcodes 0x30, 0x31, 0x32, 0x33, 0x34, 0x35 0x37
        Swap upper and lower nibbles of n
        """

        self.F = 0 # Clear flags

        if reg == LR35902.REGISTER_A:
            self.A = (((self.A & 0x0F) << 4) | ((self.A & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.A)
        elif reg == LR35902.REGISTER_B:
            self.B = (((self.B & 0x0F) << 4) | ((self.B & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.B)
        elif reg == LR35902.REGISTER_C:
            self.C = (((self.C & 0x0F) << 4) | ((self.A & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.C)
        elif reg == LR35902.REGISTER_D:
            self.D = (((self.D & 0x0F) << 4) | ((self.A & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.D)
        elif reg == LR35902.REGISTER_E:
            self.E = (((self.E & 0x0F) << 4) | ((self.A & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.E)
        elif reg == LR35902.REGISTER_H:
            self.H = (((self.H & 0x0F) << 4) | ((self.A & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.H)
        elif reg == LR35902.REGISTER_L:
            self.L = (((self.L & 0x0F) << 4) | ((self.A & 0xF0) >> 4)) & 0xFF
            self.set_zero(self.L)
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    def swap_memory(self)::
        """GBCPUman.pdf page 94
        0xCB Opcodes 0x36
        Swap upper and lower nibbles of byte stored at n
        """

        self.F = 0 # Clear flags

        addr = (self.H << 8) | self.L
        self.memory[addr] = (((self.memory[addr] & 0x0F) << 4) | ((self.memory[addr] & 0xF0) >> 4)) & 0xFF

        self.set_zero(self.memory[addr])
