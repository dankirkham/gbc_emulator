from collections import namedtuple
from enum import Enum
from gbc_emulator.memory import Memory
from gbc_emulator.lr35902.instructions import load_store_move_8bit as lsm8
from gbc_emulator.lr35902.instructions import load_16bit as l16
from gbc_emulator.lr35902.instructions import alu_8bit as alu8
from gbc_emulator.lr35902.instructions import nop
from gbc_emulator.lr35902 import flags

class LR35902:
    """Sharp LR35902 emulation. This is the CPU used in the Gameboy and Gameboy Color."""

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

    # Conditions
    CONDITION_C = 0
    CONDITION_NC = 1
    CONDITION_Z = 2
    CONDITION_NZ = 3

    # Interrupts
    INTERRUPT_VBLANK = 0
    INTERRUPT_LCD_STAT = 1
    INTERRUPT_TIMER = 2
    INTERRUPT_SERIAL = 3
    INTERRUPT_JOYPAD = 4

    INTERRUPT_VECTORS = [
        0x40, # INTERRUPT_VBLANK
        0x48, # INTERRUPT_LCD_STAT
        0x50, # INTERRUPT_TIMER
        0x58, # INTERRUPT_SERIAL
        0x60, # INTERRUPT_JOYPAD
    ]

    JUMPED = True
    BREAKPOINT_HIT = True

    class State(Enum):
        RUNNING = 0
        HALTED = 1
        STOPPED = 2

    Instruction = namedtuple('Instruction', [
        'function',
        'length_in_bytes',
        'duration_in_cycles',
        'mnemonic'
        ])

    def __init__(self, memory):
        self.memory = memory

        self.verbose = False
        self.debugger = None

        # 8-bit registers
        self.A = 0x01
        self.F = 0xB0
        self.B = 0x00
        self.C = 0x13
        self.D = 0x00
        self.E = 0xD8
        self.H = 0x01
        self.L = 0x4D

        # 16-bit registers
        self.SP = 0xFFFE
        self.PC = 0x0000

        # How long to wait for instruction to complete
        self.wait = 0

        self.state = LR35902.State.RUNNING

        self.interrupts = {
            "enabled": False,
            "change_in": 0
        }

        # Instruction map
        self.instructions = [
            LR35902.Instruction(lambda s: s.nop(), 1, 4, 'NOP'), # 0x00
            LR35902.Instruction(l16.ld_n_nn_bc, 3, 12, 'LD BC,d16'), # 0x01
            LR35902.Instruction(lsm8.ld_bc_a_pointer, 1, 8, 'LD (BC),A'), # 0x02
            LR35902.Instruction(lambda s: s.inc_nn(LR35902.REGISTER_BC), 1, 8, 'INC BC'), # 0x03
            LR35902.Instruction(alu8.inc_b_register, 1, 4, 'INC B'), # 0x04
            LR35902.Instruction(alu8.dec_b_register, 1, 4, 'DEC B'), # 0x05
            LR35902.Instruction(lsm8.ld_nn_n_b, 2, 8, 'LD B,d8'), # 0x06
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_A), 1, 4, 'RLCA'), # 0x07
            LR35902.Instruction(l16.ld_nn_sp, 3, 20, 'LD (a16),SP'), # 0x08
            LR35902.Instruction(lambda s: s.add_hl_n(LR35902.REGISTER_BC), 1, 8, 'ADD HL,BC'), # 0x09
            LR35902.Instruction(lsm8.ld_a_bc_from_memory, 1, 8, 'LD A,(BC)'), # 0x0A
            LR35902.Instruction(lambda s: s.dec_nn(LR35902.REGISTER_BC), 1, 8, 'DEC BC'), # 0x0B
            LR35902.Instruction(alu8.inc_c_register, 1, 4, 'INC C'), # 0x0C
            LR35902.Instruction(alu8.dec_c_register, 1, 4, 'DEC C'), # 0x0D
            LR35902.Instruction(lsm8.ld_nn_n_c, 2, 8, 'LD C,d8'), # 0x0E
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_A), 1, 4, 'RRCA'), # 0x0F
            LR35902.Instruction(lambda s: s.stop(), 2, 4, 'STOP 0'), # 0x10
            LR35902.Instruction(l16.ld_n_nn_de, 3, 12, 'LD DE,d16'), # 0x11
            LR35902.Instruction(lsm8.ld_de_a_pointer, 1, 8, 'LD (DE),A'), # 0x12
            LR35902.Instruction(lambda s: s.inc_nn(LR35902.REGISTER_DE), 1, 8, 'INC DE'), # 0x13
            LR35902.Instruction(alu8.inc_d_register, 1, 4, 'INC D'), # 0x14
            LR35902.Instruction(alu8.dec_d_register, 1, 4, 'DEC D'), # 0x15
            LR35902.Instruction(lsm8.ld_nn_n_d, 2, 8, 'LD D,d8'), # 0x16
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_A), 1, 4, 'RLA'), # 0x17
            LR35902.Instruction(lambda s: s.jr_n(), 2, 12, 'JR r8'), # 0x18
            LR35902.Instruction(lambda s: s.add_hl_n(LR35902.REGISTER_DE), 1, 8, 'ADD HL,DE'), # 0x19
            LR35902.Instruction(lsm8.ld_a_de_from_memory, 1, 8, 'LD A,(DE)'), # 0x1A
            LR35902.Instruction(lambda s: s.dec_nn(LR35902.REGISTER_DE), 1, 8, 'DEC DE'), # 0x1B
            LR35902.Instruction(alu8.inc_e_register, 1, 4, 'INC E'), # 0x1C
            LR35902.Instruction(alu8.dec_e_register, 1, 4, 'DEC E'), # 0x1D
            LR35902.Instruction(lsm8.ld_nn_n_e, 2, 8, 'LD E,d8'), # 0x1E
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_A), 1, 4, 'RRA'), # 0x1F
            LR35902.Instruction(lambda s: s.jr_cc_n(LR35902.CONDITION_NZ), 2, 8, 'JR NZ,r8'), # 0x20
            LR35902.Instruction(l16.ld_n_nn_hl, 3, 12, 'LD HL,d16'), # 0x21
            LR35902.Instruction(lsm8.ld_hl_a_increment, 1, 8, 'LD (HL+),A'), # 0x22
            LR35902.Instruction(lambda s: s.inc_nn(LR35902.REGISTER_HL), 1, 8, 'INC HL'), # 0x23
            LR35902.Instruction(alu8.inc_h_register, 1, 4, 'INC H'), # 0x24
            LR35902.Instruction(alu8.dec_h_register, 1, 4, 'DEC H'), # 0x25
            LR35902.Instruction(lsm8.ld_nn_n_h, 2, 8, 'LD H,d8'), # 0x26
            LR35902.Instruction(lambda s: s.daa(), 1, 4, 'DAA'), # 0x27
            LR35902.Instruction(lambda s: s.jr_cc_n(LR35902.CONDITION_Z), 2, 8, 'JR Z,r8'), # 0x28
            LR35902.Instruction(lambda s: s.add_hl_n(LR35902.REGISTER_HL), 1, 8, 'ADD HL,HL'), # 0x29
            LR35902.Instruction(lsm8.ld_a_hl_increment, 1, 8, 'LD A,(HL+)'), # 0x2A
            LR35902.Instruction(lambda s: s.dec_nn(LR35902.REGISTER_HL), 1, 8, 'DEC HL'), # 0x2B
            LR35902.Instruction(alu8.inc_l_register, 1, 4, 'INC L'), # 0x2C
            LR35902.Instruction(alu8.dec_l_register, 1, 4, 'DEC L'), # 0x2D
            LR35902.Instruction(lsm8.ld_nn_n_l, 2, 8, 'LD L,d8'), # 0x2E
            LR35902.Instruction(lambda s: s.cpl(), 1, 4, 'CPL'), # 0x2F
            LR35902.Instruction(lambda s: s.jr_cc_n(LR35902.CONDITION_NC), 2, 8, 'JR NC,r8'), # 0x30
            LR35902.Instruction(l16.ld_n_nn_sp, 3, 12, 'LD SP,d16'), # 0x31
            LR35902.Instruction(lsm8.ld_hl_a_decrement, 1, 8, 'LD (HL-),A'), # 0x32
            LR35902.Instruction(lambda s: s.inc_nn(LR35902.REGISTER_SP), 1, 8, 'INC SP'), # 0x33
            LR35902.Instruction(alu8.inc_n_memory, 1, 12, 'INC (HL)'), # 0x34
            LR35902.Instruction(alu8.dec_n_memory, 1, 12, 'DEC (HL)'), # 0x35
            LR35902.Instruction(lsm8.ld_r1_r2_immediate_to_memory, 2, 12, 'LD (HL),d8'), # 0x36
            LR35902.Instruction(lambda s: s.scf(), 1, 4, 'SCF'), # 0x37
            LR35902.Instruction(lambda s: s.jr_cc_n(LR35902.CONDITION_C), 2, 8, 'JR C,r8'), # 0x38
            LR35902.Instruction(lambda s: s.add_hl_n(LR35902.REGISTER_SP), 1, 8, 'ADD HL,SP'), # 0x39
            LR35902.Instruction(lsm8.ld_a_hl_decrement, 1, 8, 'LD A,(HL-)'), # 0x3A
            LR35902.Instruction(lambda s: s.dec_nn(LR35902.REGISTER_SP), 1, 8, 'DEC SP'), # 0x3B
            LR35902.Instruction(alu8.inc_a_register, 1, 4, 'INC A'), # 0x3C
            LR35902.Instruction(alu8.dec_a_register, 1, 4, 'DEC A'), # 0x3D
            LR35902.Instruction(lsm8.ld_nn_n_a, 2, 8, 'LD A,d8'), # 0x3E
            LR35902.Instruction(lambda s: s.ccf(), 1, 4, 'CCF'), # 0x3F
            LR35902.Instruction(nop, 1, 4, 'LD B,B'), # 0x40
            LR35902.Instruction(lsm8.ld_b_c_between_registers, 1, 4, 'LD B,C'), # 0x41
            LR35902.Instruction(lsm8.ld_b_d_between_registers, 1, 4, 'LD B,D'), # 0x42
            LR35902.Instruction(lsm8.ld_b_e_between_registers, 1, 4, 'LD B,E'), # 0x43
            LR35902.Instruction(lsm8.ld_b_h_between_registers, 1, 4, 'LD B,H'), # 0x44
            LR35902.Instruction(lsm8.ld_b_l_between_registers, 1, 4, 'LD B,L'), # 0x45
            LR35902.Instruction(lsm8.ld_hl_b_from_memory, 1, 8, 'LD B,(HL)'), # 0x46
            LR35902.Instruction(lsm8.ld_b_a, 1, 4, 'LD B,A'), # 0x47
            LR35902.Instruction(lsm8.ld_c_b_between_registers, 1, 4, 'LD C,B'), # 0x48
            LR35902.Instruction(nop, 1, 4, 'LD C,C'), # 0x49
            LR35902.Instruction(lsm8.ld_c_d_between_registers, 1, 4, 'LD C,D'), # 0x4A
            LR35902.Instruction(lsm8.ld_c_e_between_registers, 1, 4, 'LD C,E'), # 0x4B
            LR35902.Instruction(lsm8.ld_c_h_between_registers, 1, 4, 'LD C,H'), # 0x4C
            LR35902.Instruction(lsm8.ld_c_l_between_registers, 1, 4, 'LD C,L'), # 0x4D
            LR35902.Instruction(lsm8.ld_hl_c_from_memory, 1, 8, 'LD C,(HL)'), # 0x4E
            LR35902.Instruction(lsm8.ld_c_a, 1, 4, 'LD C,A'), # 0x4F
            LR35902.Instruction(lsm8.ld_d_b_between_registers, 1, 4, 'LD D,B'), # 0x50
            LR35902.Instruction(lsm8.ld_d_c_between_registers, 1, 4, 'LD D,C'), # 0x51
            LR35902.Instruction(nop, 1, 4, 'LD D,D'), # 0x52
            LR35902.Instruction(lsm8.ld_d_e_between_registers, 1, 4, 'LD D,E'), # 0x53
            LR35902.Instruction(lsm8.ld_d_h_between_registers, 1, 4, 'LD D,H'), # 0x54
            LR35902.Instruction(lsm8.ld_d_l_between_registers, 1, 4, 'LD D,L'), # 0x55
            LR35902.Instruction(lsm8.ld_hl_d_from_memory, 1, 8, 'LD D,(HL)'), # 0x56
            LR35902.Instruction(lsm8.ld_d_a, 1, 4, 'LD D,A'), # 0x57
            LR35902.Instruction(lsm8.ld_e_b_between_registers, 1, 4, 'LD E,B'), # 0x58
            LR35902.Instruction(lsm8.ld_e_c_between_registers, 1, 4, 'LD E,C'), # 0x59
            LR35902.Instruction(lsm8.ld_e_d_between_registers, 1, 4, 'LD E,D'), # 0x5A
            LR35902.Instruction(nop, 1, 4, 'LD E,E'), # 0x5B
            LR35902.Instruction(lsm8.ld_e_h_between_registers, 1, 4, 'LD E,H'), # 0x5C
            LR35902.Instruction(lsm8.ld_e_l_between_registers, 1, 4, 'LD E,L'), # 0x5D
            LR35902.Instruction(lsm8.ld_hl_e_from_memory, 1, 8, 'LD E,(HL)'), # 0x5E
            LR35902.Instruction(lsm8.ld_e_a, 1, 4, 'LD E,A'), # 0x5F
            LR35902.Instruction(lsm8.ld_h_b_between_registers, 1, 4, 'LD H,B'), # 0x60
            LR35902.Instruction(lsm8.ld_h_c_between_registers, 1, 4, 'LD H,C'), # 0x61
            LR35902.Instruction(lsm8.ld_h_d_between_registers, 1, 4, 'LD H,D'), # 0x62
            LR35902.Instruction(lsm8.ld_h_e_between_registers, 1, 4, 'LD H,E'), # 0x63
            LR35902.Instruction(nop, 1, 4, 'LD H,H'), # 0x64
            LR35902.Instruction(lsm8.ld_h_l_between_registers, 1, 4, 'LD H,L'), # 0x65
            LR35902.Instruction(lsm8.ld_hl_h_from_memory, 1, 8, 'LD H,(HL)'), # 0x66
            LR35902.Instruction(lsm8.ld_h_a, 1, 4, 'LD H,A'), # 0x67
            LR35902.Instruction(lsm8.ld_l_b_between_registers, 1, 4, 'LD L,B'), # 0x68
            LR35902.Instruction(lsm8.ld_l_c_between_registers, 1, 4, 'LD L,C'), # 0x69
            LR35902.Instruction(lsm8.ld_l_d_between_registers, 1, 4, 'LD L,D'), # 0x6A
            LR35902.Instruction(lsm8.ld_l_e_between_registers, 1, 4, 'LD L,E'), # 0x6B
            LR35902.Instruction(lsm8.ld_l_h_between_registers, 1, 4, 'LD L,H'), # 0x6C
            LR35902.Instruction(nop, 1, 4, 'LD L,L'), # 0x6D
            LR35902.Instruction(lsm8.ld_hl_l_from_memory, 1, 8, 'LD L,(HL)'), # 0x6E
            LR35902.Instruction(lsm8.ld_l_a, 1, 4, 'LD L,A'), # 0x6F
            LR35902.Instruction(lsm8.ld_hl_b_to_memory, 1, 8, 'LD (HL),B'), # 0x70
            LR35902.Instruction(lsm8.ld_hl_c_to_memory, 1, 8, 'LD (HL),C'), # 0x71
            LR35902.Instruction(lsm8.ld_hl_d_to_memory, 1, 8, 'LD (HL),D'), # 0x72
            LR35902.Instruction(lsm8.ld_hl_e_to_memory, 1, 8, 'LD (HL),E'), # 0x73
            LR35902.Instruction(lsm8.ld_hl_h_to_memory, 1, 8, 'LD (HL),H'), # 0x74
            LR35902.Instruction(lsm8.ld_hl_l_to_memory, 1, 8, 'LD (HL),L'), # 0x75
            LR35902.Instruction(lambda s: s.halt(), 1, 4, 'HALT'), # 0x76
            LR35902.Instruction(lsm8.ld_hl_a_pointer, 1, 8, 'LD (HL),A'), # 0x77
            LR35902.Instruction(lsm8.ld_a_b_between_registers, 1, 4, 'LD A,B'), # 0x78
            LR35902.Instruction(lsm8.ld_a_c_between_registers, 1, 4, 'LD A,C'), # 0x79
            LR35902.Instruction(lsm8.ld_a_d_between_registers, 1, 4, 'LD A,D'), # 0x7A
            LR35902.Instruction(lsm8.ld_a_e_between_registers, 1, 4, 'LD A,E'), # 0x7B
            LR35902.Instruction(lsm8.ld_a_h_between_registers, 1, 4, 'LD A,H'), # 0x7C
            LR35902.Instruction(lsm8.ld_a_l_between_registers, 1, 4, 'LD A,L'), # 0x7D
            LR35902.Instruction(lsm8.ld_a_hl_from_memory, 1, 8, 'LD A,(HL)'), # 0x7E
            LR35902.Instruction(nop, 1, 4, 'LD A,A'), # 0x7F
            LR35902.Instruction(alu8.add_a_b_register, 1, 4, 'ADD A,B'), # 0x80
            LR35902.Instruction(alu8.add_a_c_register, 1, 4, 'ADD A,C'), # 0x81
            LR35902.Instruction(alu8.add_a_d_register, 1, 4, 'ADD A,D'), # 0x82
            LR35902.Instruction(alu8.add_a_e_register, 1, 4, 'ADD A,E'), # 0x83
            LR35902.Instruction(alu8.add_a_h_register, 1, 4, 'ADD A,H'), # 0x84
            LR35902.Instruction(alu8.add_a_l_register, 1, 4, 'ADD A,L'), # 0x85
            LR35902.Instruction(alu8.add_a_n_memory, 1, 8, 'ADD A,(HL)'), # 0x86
            LR35902.Instruction(alu8.add_a_a_register, 1, 4, 'ADD A,A'), # 0x87
            LR35902.Instruction(alu8.adc_a_b_register, 1, 4, 'ADC A,B'), # 0x88
            LR35902.Instruction(alu8.adc_a_c_register, 1, 4, 'ADC A,C'), # 0x89
            LR35902.Instruction(alu8.adc_a_d_register, 1, 4, 'ADC A,D'), # 0x8A
            LR35902.Instruction(alu8.adc_a_e_register, 1, 4, 'ADC A,E'), # 0x8B
            LR35902.Instruction(alu8.adc_a_h_register, 1, 4, 'ADC A,H'), # 0x8C
            LR35902.Instruction(alu8.add_a_l_register, 1, 4, 'ADC A,L'), # 0x8D
            LR35902.Instruction(alu8.adc_a_n_memory, 1, 8, 'ADC A,(HL)'), # 0x8E
            LR35902.Instruction(alu8.adc_a_a_register, 1, 4, 'ADC A,A'), # 0x8F
            LR35902.Instruction(alu8.sub_a_b_register, 1, 4, 'SUB B'), # 0x90
            LR35902.Instruction(alu8.sub_a_c_register, 1, 4, 'SUB C'), # 0x91
            LR35902.Instruction(alu8.sub_a_d_register, 1, 4, 'SUB D'), # 0x92
            LR35902.Instruction(alu8.add_a_e_register, 1, 4, 'SUB E'), # 0x93
            LR35902.Instruction(alu8.sub_a_h_register, 1, 4, 'SUB H'), # 0x94
            LR35902.Instruction(alu8.sub_a_l_register, 1, 4, 'SUB L'), # 0x95
            LR35902.Instruction(alu8.sub_a_n_memory, 1, 8, 'SUB (HL)'), # 0x96
            LR35902.Instruction(alu8.sub_a_a_register, 1, 4, 'SUB A'), # 0x97
            LR35902.Instruction(alu8.subc_a_b_register, 1, 4, 'SBC A,B'), # 0x98
            LR35902.Instruction(alu8.subc_a_c_register, 1, 4, 'SBC A,C'), # 0x99
            LR35902.Instruction(alu8.subc_a_d_register, 1, 4, 'SBC A,D'), # 0x9A
            LR35902.Instruction(alu8.subc_a_e_register, 1, 4, 'SBC A,E'), # 0x9B
            LR35902.Instruction(alu8.subc_a_h_register, 1, 4, 'SBC A,H'), # 0x9C
            LR35902.Instruction(alu8.subc_a_l_register, 1, 4, 'SBC A,L'), # 0x9D
            LR35902.Instruction(alu8.subc_a_n_memory, 1, 8, 'SBC A,(HL)'), # 0x9E
            LR35902.Instruction(alu8.subc_a_a_register, 1, 4, 'SBC A,A'), # 0x9F
            LR35902.Instruction(alu8.and_a_b_register, 1, 4, 'AND B'), # 0xA0
            LR35902.Instruction(alu8.and_a_c_register, 1, 4, 'AND C'), # 0xA1
            LR35902.Instruction(alu8.and_a_d_register, 1, 4, 'AND D'), # 0xA2
            LR35902.Instruction(alu8.and_a_e_register, 1, 4, 'AND E'), # 0xA3
            LR35902.Instruction(alu8.and_a_h_register, 1, 4, 'AND H'), # 0xA4
            LR35902.Instruction(alu8.and_a_l_register, 1, 4, 'AND L'), # 0xA5
            LR35902.Instruction(alu8.and_a_n_memory, 1, 8, 'AND (HL)'), # 0xA6
            LR35902.Instruction(alu8.and_a_a_register, 1, 4, 'AND A'), # 0xA7
            LR35902.Instruction(alu8.xor_a_b_register, 1, 4, 'XOR B'), # 0xA8
            LR35902.Instruction(alu8.xor_a_c_register, 1, 4, 'XOR C'), # 0xA9
            LR35902.Instruction(alu8.xor_a_d_register, 1, 4, 'XOR D'), # 0xAA
            LR35902.Instruction(alu8.xor_a_e_register, 1, 4, 'XOR E'), # 0xAB
            LR35902.Instruction(alu8.xor_a_h_register, 1, 4, 'XOR H'), # 0xAC
            LR35902.Instruction(alu8.xor_a_l_register, 1, 4, 'XOR L'), # 0xAD
            LR35902.Instruction(alu8.xor_n_memory, 1, 8, 'XOR (HL)'), # 0xAE
            LR35902.Instruction(alu8.xor_a_a_register, 1, 4, 'XOR A'), # 0xAF
            LR35902.Instruction(alu8.or_a_b_register, 1, 4, 'OR B'), # 0xB0
            LR35902.Instruction(alu8.or_a_c_register, 1, 4, 'OR C'), # 0xB1
            LR35902.Instruction(alu8.or_a_d_register, 1, 4, 'OR D'), # 0xB2
            LR35902.Instruction(alu8.or_a_e_register, 1, 4, 'OR E'), # 0xB3
            LR35902.Instruction(alu8.or_a_h_register, 1, 4, 'OR H'), # 0xB4
            LR35902.Instruction(alu8.or_a_l_register, 1, 4, 'OR L'), # 0xB5
            LR35902.Instruction(alu8.or_n_memory, 1, 8, 'OR L)'), # 0xB6
            LR35902.Instruction(alu8.or_a_a_register, 1, 4, 'OR A'), # 0xB7
            LR35902.Instruction(alu8.cp_a_b_register, 1, 4, 'CP B'), # 0xB8
            LR35902.Instruction(alu8.cp_a_c_register, 1, 4, 'CP C'), # 0xB9
            LR35902.Instruction(alu8.cp_a_d_register, 1, 4, 'CP D'), # 0xBA
            LR35902.Instruction(alu8.cp_a_e_register, 1, 4, 'CP E'), # 0xBB
            LR35902.Instruction(alu8.cp_a_h_register, 1, 4, 'CP H'), # 0xBC
            LR35902.Instruction(alu8.cp_a_l_register, 1, 4, 'CP L'), # 0xBD
            LR35902.Instruction(alu8.cp_n_memory, 1, 8, 'OR (HL)'), # 0xBE
            LR35902.Instruction(alu8.cp_a_a_register, 1, 4, 'CP A'), # 0xBF
            LR35902.Instruction(lambda s: s.ret_cc(LR35902.CONDITION_NZ), 1, 8, 'RET NZ'), # 0xC0
            LR35902.Instruction(l16.pop_nn_bc, 1, 12, 'POP BC'), # 0xC1
            LR35902.Instruction(lambda s: s.jp_cc_nn(LR35902.CONDITION_NZ), 3, 12, 'JP NZ,a16'), # 0xC2
            LR35902.Instruction(lambda s: s.jp_nn(), 3, 16, 'JP a16'), # 0xC3
            LR35902.Instruction(lambda s: s.call_cc_nn(LR35902.CONDITION_NZ), 3, 12, 'CALL NZ,a16'), # 0xC4
            LR35902.Instruction(l16.push_nn_bc, 1, 16, 'PUSH BC'), # 0xC5
            LR35902.Instruction(alu8.add_a_n_immediate, 2, 8, 'ADD A,d8'), # 0xC6
            LR35902.Instruction(lambda s: s.rst(0x00), 1, 16, 'RST 00H'), # 0xC7
            LR35902.Instruction(lambda s: s.ret_cc(LR35902.CONDITION_Z), 1, 8, 'RET Z'), # 0xC8
            LR35902.Instruction(lambda s: s.ret(), 1, 16, 'RET'), # 0xC9
            LR35902.Instruction(lambda s: s.jp_cc_nn(LR35902.CONDITION_Z), 3, 12, 'JP Z,a16'), # 0xCA
            None, # 0xCB
            LR35902.Instruction(lambda s: s.call_cc_nn(LR35902.CONDITION_Z), 3, 12, 'CALL Z,a16'), # 0xCC
            LR35902.Instruction(lambda s: s.call_nn(), 3, 24, 'CALL a16'), # 0xCD
            LR35902.Instruction(alu8.adc_a_n_immediate, 2, 8, 'ADC A,d8'), # 0xCE
            LR35902.Instruction(lambda s: s.rst(0x08), 1, 16, 'RST 08H'), # 0xCF
            LR35902.Instruction(lambda s: s.ret_cc(LR35902.CONDITION_NC), 1, 8, 'RET NC'), # 0xD0
            LR35902.Instruction(l16.pop_nn_de, 1, 12, 'POP DE'), # 0xD1
            LR35902.Instruction(lambda s: s.jp_cc_nn(LR35902.CONDITION_NC), 3, 12, 'JP NC,a16'), # 0xD2
            None, # 0xD3
            LR35902.Instruction(lambda s: s.call_cc_nn(LR35902.CONDITION_NC), 3, 12, 'CALL NC,a16'), # 0xD4
            LR35902.Instruction(l16.push_nn_de, 1, 16, 'PUSH DE'), # 0xD5
            LR35902.Instruction(alu8.sub_n_immediate, 2, 8, 'SUB d8'), # 0xD6
            LR35902.Instruction(lambda s: s.rst(0x10), 1, 16, 'RST 10H'), # 0xD7
            LR35902.Instruction(lambda s: s.ret_cc(LR35902.CONDITION_C), 1, 8, 'RET C'), # 0xD8
            LR35902.Instruction(lambda s: s.reti(), 1, 16, 'RETI'), # 0xD9
            LR35902.Instruction(lambda s: s.jp_cc_nn(LR35902.CONDITION_C), 3, 12, 'JP C,a16'), # 0xDA
            None, # 0xDB
            LR35902.Instruction(lambda s: s.call_cc_nn(LR35902.CONDITION_C), 3, 12, 'CALL C,a16'), # 0xDC
            None, # 0xDD
            LR35902.Instruction(alu8.subc_a_immediate, 2, 8, 'SUB A,d8'), # 0xDE
            LR35902.Instruction(lambda s: s.rst(0x18), 1, 16, 'RST 18H'), # 0xDF
            LR35902.Instruction(lsm8.ldh_n_a, 2, 12, 'LDH (a8),A'), # 0xE0
            LR35902.Instruction(l16.pop_nn_hl, 1, 12, 'POP HL'), # 0xE1
            LR35902.Instruction(lsm8.ld_c_a_offset, 1, 8, 'LD (C),A'), # 0xE2  # This disagrees with pastraiser length of 2 bytes
            None, # 0xE3
            None, # 0xE4
            LR35902.Instruction(l16.push_nn_hl, 1, 16, 'PUSH HL'), # 0xE5
            LR35902.Instruction(alu8.and_n_immediate, 2, 8, 'AND d8'), # 0xE6
            LR35902.Instruction(lambda s: s.rst(0x20), 1, 16, 'RST 20H'), # 0xE7
            LR35902.Instruction(lambda s: s.add_sp_n(), 2, 16, 'ADD SP,r8'), # 0xE8
            LR35902.Instruction(lambda s: s.jp_memory(), 1, 4, 'JP (HL)'), # 0xE9
            LR35902.Instruction(lsm8.ld_n_a_immediate, 3, 16, 'LD (a16),A'), # 0xEA
            None, # 0xEB
            None, # 0xEC
            None, # 0xED
            LR35902.Instruction(alu8.xor_n_immediate, 2, 8, 'XOR d8'), # 0xEE
            LR35902.Instruction(lambda s: s.rst(0x28), 1, 16, 'RST 28H'), # 0xEF
            LR35902.Instruction(lsm8.ldh_a_n, 2, 12, 'LDH A,(a8)'), # 0xF0
            LR35902.Instruction(l16.pop_nn_af, 1, 12, 'POP AF'), # 0xF1
            LR35902.Instruction(lsm8.ld_a_c_offset, 1, 8, 'LD A,(C)'), # 0xF2 # This disagrees with pastraiser length of 2 bytes
            LR35902.Instruction(lambda s: s.di(), 1, 4, 'DI'), # 0xF3
            None, # 0xF4
            LR35902.Instruction(l16.push_nn_af, 1, 16, 'PUSH AF'), # 0xF5
            LR35902.Instruction(alu8.or_n_immediate, 2, 8, 'OR d8'), # 0xF6
            LR35902.Instruction(lambda s: s.rst(0x30), 1, 16, 'RST 30H'), # 0xF7
            LR35902.Instruction(l16.ld_hl_sp_n, 2, 12, 'LD HL,SP+r8'), # 0xF8
            LR35902.Instruction(l16.ld_sp_hl, 1, 8, 'LD SP,HL'), # 0xF9
            LR35902.Instruction(lsm8.ld_a_n_from_memory_immediate, 3, 16, 'LD A,(a16)'), # 0xFA
            LR35902.Instruction(lambda s: s.ei(), 1, 4, 'EI'), # 0xFB
            None, # 0xFC
            None, # 0xFD
            LR35902.Instruction(alu8.cp_n_immediate, 2, 8, 'CP d8'), # 0xFE
            LR35902.Instruction(lambda s: s.rst(0x38), 1, 16, 'RST 38H'), # 0xFF
        ]

        # Instruction map
        self.cb_instructions = [
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_B), 2, 8, 'RLC B'), # 0x00
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_C), 2, 8, 'RLC C'), # 0x01
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_D), 2, 8, 'RLC D'), # 0x02
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_E), 2, 8, 'RLC E'), # 0x03
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_H), 2, 8, 'RLC H'), # 0x04
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_L), 2, 8, 'RLC L'), # 0x05
            LR35902.Instruction(lambda s: s.rlc_memory(), 2, 16, 'RLC (HL)'), # 0x06
            LR35902.Instruction(lambda s: s.rlc(LR35902.REGISTER_A), 2, 8, 'RLC A'), # 0x07
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_B), 2, 8, 'RRC B'), # 0x08
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_C), 2, 8, 'RRC C'), # 0x09
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_D), 2, 8, 'RRC D'), # 0x0A
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_E), 2, 8, 'RRC E'), # 0x0B
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_H), 2, 8, 'RRC H'), # 0x0C
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_L), 2, 8, 'RRC L'), # 0x0D
            LR35902.Instruction(lambda s: s.rrc_memory(), 2, 16, 'RRC (HL)'), # 0x0E
            LR35902.Instruction(lambda s: s.rrc(LR35902.REGISTER_A), 2, 8, 'RRC A'), # 0x0F
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_B), 2, 8, 'RL B'), # 0x10
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_C), 2, 8, 'RL C'), # 0x11
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_D), 2, 8, 'RL D'), # 0x12
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_E), 2, 8, 'RL E'), # 0x13
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_H), 2, 8, 'RL H'), # 0x14
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_L), 2, 8, 'RL L'), # 0x15
            LR35902.Instruction(lambda s: s.rl_memory(), 2, 16, 'RL (HL)'), # 0x16
            LR35902.Instruction(lambda s: s.rl(LR35902.REGISTER_A), 2, 8, 'RL A'), # 0x17
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_B), 2, 8, 'RR B'), # 0x18
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_C), 2, 8, 'RR C'), # 0x19
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_D), 2, 8, 'RR D'), # 0x1A
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_E), 2, 8, 'RR E'), # 0x1B
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_H), 2, 8, 'RR H'), # 0x1C
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_L), 2, 8, 'RR L'), # 0x1D
            LR35902.Instruction(lambda s: s.rr_memory(), 2, 16, 'RR (HL)'), # 0x1E
            LR35902.Instruction(lambda s: s.rr(LR35902.REGISTER_A), 2, 8, 'RR A'), # 0x1F
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_B), 2, 8, 'SLA B'), # 0x20
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_C), 2, 8, 'SLA C'), # 0x21
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_D), 2, 8, 'SLA D'), # 0x22
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_E), 2, 8, 'SLA E'), # 0x23
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_H), 2, 8, 'SLA H'), # 0x24
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_L), 2, 8, 'SLA L'), # 0x25
            LR35902.Instruction(lambda s: s.sla_memory(), 2, 16, 'SLA (HL)'), # 0x26
            LR35902.Instruction(lambda s: s.sla(LR35902.REGISTER_A), 2, 8, 'SLA A'), # 0x27
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_B), 2, 8, 'SRA B'), # 0x28
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_C), 2, 8, 'SRA C'), # 0x29
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_D), 2, 8, 'SRA D'), # 0x2A
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_E), 2, 8, 'SRA E'), # 0x2B
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_H), 2, 8, 'SRA H'), # 0x2C
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_L), 2, 8, 'SRA L'), # 0x2D
            LR35902.Instruction(lambda s: s.sra_memory(), 2, 16, 'SRA (HL)'), # 0x2E
            LR35902.Instruction(lambda s: s.sra(LR35902.REGISTER_A), 2, 8, 'SRA A'), # 0x2F
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_B), 2, 8, 'SWAP B'), # 0x30
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_C), 2, 8, 'SWAP C'), # 0x31
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_D), 2, 8, 'SWAP D'), # 0x32
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_E), 2, 8, 'SWAP E'), # 0x33
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_H), 2, 8, 'SWAP H'), # 0x34
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_L), 2, 8, 'SWAP L'), # 0x35
            LR35902.Instruction(lambda s: s.swap_memory(), 2, 16, 'SWAP (HL)'), # 0x36
            LR35902.Instruction(lambda s: s.swap(LR35902.REGISTER_A), 2, 8, 'SWAP A'), # 0x37
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_B), 2, 8, 'SRL B'), # 0x38
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_C), 2, 8, 'SRL C'), # 0x39
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_D), 2, 8, 'SRL D'), # 0x3A
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_E), 2, 8, 'SRL E'), # 0x3B
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_H), 2, 8, 'SRL H'), # 0x3C
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_L), 2, 8, 'SRL L'), # 0x3D
            LR35902.Instruction(lambda s: s.srl_memory(), 2, 16, 'SRL (HL)'), # 0x3E
            LR35902.Instruction(lambda s: s.srl(LR35902.REGISTER_A), 2, 8, 'SRL A'), # 0x3F
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 0), 2, 8, 'BIT 0,B'), # 0x40
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 0), 2, 8, 'BIT 0,C'), # 0x41
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 0), 2, 8, 'BIT 0,D'), # 0x42
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 0), 2, 8, 'BIT 0,E'), # 0x43
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 0), 2, 8, 'BIT 0,H'), # 0x44
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 0), 2, 8, 'BIT 0,L'), # 0x45
            LR35902.Instruction(lambda s: s.bit_memory(0), 2, 16, 'BIT 0,(HL)'), # 0x46
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 0), 2, 8, 'BIT 0,A'), # 0x47
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 1), 2, 8, 'BIT 1,B'), # 0x48
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 1), 2, 8, 'BIT 1,C'), # 0x49
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 1), 2, 8, 'BIT 1,D'), # 0x4A
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 1), 2, 8, 'BIT 1,E'), # 0x4B
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 1), 2, 8, 'BIT 1,H'), # 0x4C
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 1), 2, 8, 'BIT 1,L'), # 0x4D
            LR35902.Instruction(lambda s: s.bit_memory(1), 2, 16, 'BIT 1,(HL)'), # 0x4E
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 1), 2, 8, 'BIT 1,A'), # 0x4F
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 2), 2, 8, 'BIT 2,B'), # 0x50
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 2), 2, 8, 'BIT 2,C'), # 0x51
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 2), 2, 8, 'BIT 2,D'), # 0x52
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 2), 2, 8, 'BIT 2,E'), # 0x53
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 2), 2, 8, 'BIT 2,H'), # 0x54
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 2), 2, 8, 'BIT 2,L'), # 0x55
            LR35902.Instruction(lambda s: s.bit_memory(2), 2, 16, 'BIT 2,(HL)'), # 0x56
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 2), 2, 8, 'BIT 2,A'), # 0x57
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 3), 2, 8, 'BIT 3,B'), # 0x58
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 3), 2, 8, 'BIT 3,C'), # 0x59
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 3), 2, 8, 'BIT 3,D'), # 0x5A
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 3), 2, 8, 'BIT 3,E'), # 0x5B
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 3), 2, 8, 'BIT 3,H'), # 0x5C
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 3), 2, 8, 'BIT 3,L'), # 0x5D
            LR35902.Instruction(lambda s: s.bit_memory(3), 2, 16, 'BIT 3,(HL)'), # 0x5E
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 3), 2, 8, 'BIT 3,A'), # 0x5F
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 4), 2, 8, 'BIT 4,B'), # 0x60
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 4), 2, 8, 'BIT 4,C'), # 0x61
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 4), 2, 8, 'BIT 4,D'), # 0x62
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 4), 2, 8, 'BIT 4,E'), # 0x63
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 4), 2, 8, 'BIT 4,H'), # 0x64
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 4), 2, 8, 'BIT 4,L'), # 0x65
            LR35902.Instruction(lambda s: s.bit_memory(4), 2, 16, 'BIT 4,(HL)'), # 0x66
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 4), 2, 8, 'BIT 4,A'), # 0x67
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 5), 2, 8, 'BIT 5,B'), # 0x68
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 5), 2, 8, 'BIT 5,C'), # 0x69
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 5), 2, 8, 'BIT 5,D'), # 0x6A
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 5), 2, 8, 'BIT 5,E'), # 0x6B
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 5), 2, 8, 'BIT 5,H'), # 0x6C
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 5), 2, 8, 'BIT 5,L'), # 0x6D
            LR35902.Instruction(lambda s: s.bit_memory(5), 2, 16, 'BIT 5,(HL)'), # 0x6E
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 5), 2, 8, 'BIT 5,A'), # 0x6F
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 6), 2, 8, 'BIT 6,B'), # 0x70
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 6), 2, 8, 'BIT 6,C'), # 0x71
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 6), 2, 8, 'BIT 6,D'), # 0x72
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 6), 2, 8, 'BIT 6,E'), # 0x73
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 6), 2, 8, 'BIT 6,H'), # 0x74
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 6), 2, 8, 'BIT 6,L'), # 0x75
            LR35902.Instruction(lambda s: s.bit_memory(6), 2, 16, 'BIT 6,(HL)'), # 0x76
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 6), 2, 8, 'BIT 6,B'), # 0x77
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_B, 7), 2, 8, 'BIT 7,B'), # 0x78
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_C, 7), 2, 8, 'BIT 7,C'), # 0x79
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_D, 7), 2, 8, 'BIT 7,D'), # 0x7A
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_E, 7), 2, 8, 'BIT 7,E'), # 0x7B
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_H, 7), 2, 8, 'BIT 7,H'), # 0x7C
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_L, 7), 2, 8, 'BIT 7,L'), # 0x7D
            LR35902.Instruction(lambda s: s.bit_memory(7), 2, 16, 'BIT 7,(HL)'), # 0x7E
            LR35902.Instruction(lambda s: s.bit(LR35902.REGISTER_A, 7), 2, 8, 'BIT 7,A'), # 0x7F
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 0), 2, 8, 'RES 0,B'), # 0x80
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 0), 2, 8, 'RES 0,C'), # 0x81
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 0), 2, 8, 'RES 0,D'), # 0x82
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 0), 2, 8, 'RES 0,E'), # 0x83
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 0), 2, 8, 'RES 0,H'), # 0x84
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 0), 2, 8, 'RES 0,L'), # 0x85
            LR35902.Instruction(lambda s: s.res_memory(0), 2, 16, 'RES 0,(HL)'), # 0x86
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 0), 2, 8, 'RES 0,A'), # 0x87
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 1), 2, 8, 'RES 1,B'), # 0x88
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 1), 2, 8, 'RES 1,C'), # 0x89
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 1), 2, 8, 'RES 1,D'), # 0x8A
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 1), 2, 8, 'RES 1,E'), # 0x8B
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 1), 2, 8, 'RES 1,H'), # 0x8C
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 1), 2, 8, 'RES 1,L'), # 0x8D
            LR35902.Instruction(lambda s: s.res_memory(1), 2, 16, 'RES 1,(HL)'), # 0x8E
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 1), 2, 8, 'RES 1,A'), # 0x8F
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 2), 2, 8, 'RES 2,B'), # 0x90
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 2), 2, 8, 'RES 2,C'), # 0x91
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 2), 2, 8, 'RES 2,D'), # 0x92
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 2), 2, 8, 'RES 2,E'), # 0x93
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 2), 2, 8, 'RES 2,H'), # 0x94
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 2), 2, 8, 'RES 2,L'), # 0x95
            LR35902.Instruction(lambda s: s.res_memory(2), 2, 16, 'RES 2,(HL)'), # 0x96
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 2), 2, 8, 'RES 2,A'), # 0x97
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 3), 2, 8, 'RES 3,B'), # 0x98
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 3), 2, 8, 'RES 3,C'), # 0x99
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 3), 2, 8, 'RES 3,D'), # 0x9A
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 3), 2, 8, 'RES 3,E'), # 0x9B
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 3), 2, 8, 'RES 3,H'), # 0x9C
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 3), 2, 8, 'RES 3,L'), # 0x9D
            LR35902.Instruction(lambda s: s.res_memory(3), 2, 16, 'RES 3,(HL)'), # 0x9E
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 3), 2, 8, 'RES 3,A'), # 0x9F
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 4), 2, 8, 'RES 4,B'), # 0xA0
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 4), 2, 8, 'RES 4,C'), # 0xA1
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 4), 2, 8, 'RES 4,D'), # 0xA2
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 4), 2, 8, 'RES 4,E'), # 0xA3
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 4), 2, 8, 'RES 4,H'), # 0xA4
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 4), 2, 8, 'RES 4,L'), # 0xA5
            LR35902.Instruction(lambda s: s.res_memory(4), 2, 16, 'RES 4,(HL)'), # 0xA6
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 4), 2, 8, 'RES 4,A'), # 0xA7
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 5), 2, 8, 'RES 5,B'), # 0xA8
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 5), 2, 8, 'RES 5,C'), # 0xA9
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 5), 2, 8, 'RES 5,D'), # 0xAA
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 5), 2, 8, 'RES 5,E'), # 0xAB
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 5), 2, 8, 'RES 5,H'), # 0xAC
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 5), 2, 8, 'RES 5,L'), # 0xAD
            LR35902.Instruction(lambda s: s.res_memory(5), 2, 16, 'RES 5,(HL)'), # 0xAE
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 5), 2, 8, 'RES 5,A'), # 0xAF
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 6), 2, 8, 'RES 6,B'), # 0xB0
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 6), 2, 8, 'RES 6,C'), # 0xB1
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 6), 2, 8, 'RES 6,D'), # 0xB2
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 6), 2, 8, 'RES 6,E'), # 0xB3
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 6), 2, 8, 'RES 6,H'), # 0xB4
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 6), 2, 8, 'RES 6,L'), # 0xB5
            LR35902.Instruction(lambda s: s.res_memory(6), 2, 16, 'RES 6,(HL)'), # 0xB6
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 6), 2, 8, 'RES 6,A'), # 0xB7
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_B, 7), 2, 8, 'RES 7,B'), # 0xB8
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_C, 7), 2, 8, 'RES 7,C'), # 0xB9
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_D, 7), 2, 8, 'RES 7,D'), # 0xBA
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_E, 7), 2, 8, 'RES 7,E'), # 0xBB
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_H, 7), 2, 8, 'RES 7,H'), # 0xBC
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_L, 7), 2, 8, 'RES 7,L'), # 0xBD
            LR35902.Instruction(lambda s: s.res_memory(7), 2, 16, 'RES 7,(HL)'), # 0xBE
            LR35902.Instruction(lambda s: s.res(LR35902.REGISTER_A, 7), 2, 8, 'RES 7,A'), # 0xBF
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 0), 2, 8, 'SET 0,B'), # 0xC0
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 0), 2, 8, 'SET 0,C'), # 0xC1
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 0), 2, 8, 'SET 0,D'), # 0xC2
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 0), 2, 8, 'SET 0,E'), # 0xC3
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 0), 2, 8, 'SET 0,H'), # 0xC4
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 0), 2, 8, 'SET 0,L'), # 0xC5
            LR35902.Instruction(lambda s: s.set_memory(0), 2, 16, 'SET 0,(HL)'), # 0xC6
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 0), 2, 8, 'SET 0,A'), # 0xC7
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 1), 2, 8, 'SET 1,B'), # 0xC8
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 1), 2, 8, 'SET 1,C'), # 0xC9
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 1), 2, 8, 'SET 1,D'), # 0xCA
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 1), 2, 8, 'SET 1,E'), # 0xCB
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 1), 2, 8, 'SET 1,H'), # 0xCC
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 1), 2, 8, 'SET 1,L'), # 0xCD
            LR35902.Instruction(lambda s: s.set_memory(1), 2, 16, 'SET 1,(HL)'), # 0xCE
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 1), 2, 8, 'SET 1,A'), # 0xCF
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 2), 2, 8, 'SET 2,B'), # 0xD0
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 2), 2, 8, 'SET 2,C'), # 0xD1
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 2), 2, 8, 'SET 2,D'), # 0xD2
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 2), 2, 8, 'SET 2,E'), # 0xD3
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 2), 2, 8, 'SET 2,H'), # 0xD4
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 2), 2, 8, 'SET 2,L'), # 0xD5
            LR35902.Instruction(lambda s: s.set_memory(2), 2, 16, 'SET 2,(HL)'), # 0xD6
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 2), 2, 8, 'SET 2,A'), # 0xD7
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 3), 2, 8, 'SET 3,B'), # 0xD8
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 3), 2, 8, 'SET 3,C'), # 0xD9
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 3), 2, 8, 'SET 3,D'), # 0xDA
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 3), 2, 8, 'SET 3,E'), # 0xDB
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 3), 2, 8, 'SET 3,H'), # 0xDC
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 3), 2, 8, 'SET 3,L'), # 0xDD
            LR35902.Instruction(lambda s: s.set_memory(3), 2, 16, 'SET 3,(HL)'), # 0xDE
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 3), 2, 8, 'SET 3,A'), # 0xDF
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 4), 2, 8, 'SET 4,B'), # 0xE0
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 4), 2, 8, 'SET 4,C'), # 0xE1
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 4), 2, 8, 'SET 4,D'), # 0xE2
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 4), 2, 8, 'SET 4,E'), # 0xE3
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 4), 2, 8, 'SET 4,H'), # 0xE4
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 4), 2, 8, 'SET 4,L'), # 0xE5
            LR35902.Instruction(lambda s: s.set_memory(4), 2, 16, 'SET 4,(HL)'), # 0xE6
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 4), 2, 8, 'SET 4,A'), # 0xE7
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 5), 2, 8, 'SET 5,B'), # 0xE8
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 5), 2, 8, 'SET 5,C'), # 0xE9
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 5), 2, 8, 'SET 5,D'), # 0xEA
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 5), 2, 8, 'SET 5,E'), # 0xEB
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 5), 2, 8, 'SET 5,H'), # 0xEC
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 5), 2, 8, 'SET 5,L'), # 0xED
            LR35902.Instruction(lambda s: s.set_memory(5), 2, 16, 'SET 5,(HL)'), # 0xEE
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 5), 2, 8, 'SET 5,A'), # 0xEF
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 6), 2, 8, 'SET 6,B'), # 0xF0
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 6), 2, 8, 'SET 6,C'), # 0xF1
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 6), 2, 8, 'SET 6,D'), # 0xF2
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 6), 2, 8, 'SET 6,E'), # 0xF3
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 6), 2, 8, 'SET 6,H'), # 0xF4
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 6), 2, 8, 'SET 6,L'), # 0xF5
            LR35902.Instruction(lambda s: s.set_memory(6), 2, 16, 'SET 6,(HL)'), # 0xF6
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 6), 2, 8, 'SET 6,A'), # 0xF7
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_B, 7), 2, 8, 'SET 7,B'), # 0xF8
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_C, 7), 2, 8, 'SET 7,C'), # 0xF9
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_D, 7), 2, 8, 'SET 7,D'), # 0xFA
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_E, 7), 2, 8, 'SET 7,E'), # 0xFB
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_H, 7), 2, 8, 'SET 7,H'), # 0xFC
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_L, 7), 2, 8, 'SET 7,L'), # 0xFD
            LR35902.Instruction(lambda s: s.set_memory(7), 2, 16, 'SET 7,(HL)'), # 0xFE
            LR35902.Instruction(lambda s: s.set(LR35902.REGISTER_A, 7), 2, 8, 'SET 7,A'), # 0xFF
        ]

    def set_zero(self, value):
        if value == 0:
            self.F |= (1 << flags.FLAG_Z)
        else:
            self.F &= ~(1 << flags.FLAG_Z)

    def set_flag(self, flag, value):
        if value:
            self.F |= (1 << flag)
        else:
            self.F &= ~(1 << flag)

    def fetch_and_decode(self):
        # Fetch
        opcode = self.memory[self.PC]

        # Decode
        if opcode != 0xCB:
            instruction = self.instructions[opcode]
        else:
            cb_opcode = self.memory[self.PC + 1]
            instruction = self.cb_instructions[cb_opcode]

        return instruction, opcode

    def clock(self):
        # Idle if necessary
        if self.wait > 0:
            self.wait -= 1
            return

        # If the CPU is not stopped and interrupts are enabled, process
        # interrupts.
        # http://gbdev.gg8.se/wiki/articles/Interrupts
        if not self.state == LR35902.State.STOPPED:
            # Check if interrupts are enabled and requested
            enabled_and_requested = (
                self.memory[Memory.REGISTER_IE] & # Enabled
                self.memory[Memory.REGISTER_IF] # Requested
            )
            for interrupt in range(5):
                if enabled_and_requested & (1 << interrupt):
                    self.state = LR35902.State.RUNNING # CPU running again

                    if self.interrupts["enabled"]:
                        # Reset Request Flag
                        self.memory[Memory.REGISTER_IF] &= ~(1 << interrupt)

                        # Disable global interrupts
                        self.interrupts["enabled"] = False

                        # Save program counter to stack
                        self.SP -= 2
                        self.memory[self.SP + 1] = ((self.PC) >> 8) & 0xFF
                        self.memory[self.SP] = (self.PC) & 0xFF

                        # Jump to Interrupt Vector
                        self.PC = LR35902.INTERRUPT_VECTORS[interrupt]

                        self.wait = 4 # Wait four more cycles

                        return # Only one interrupt at a time



        # Do nothing if CPU is not running
        if not self.state == LR35902.State.RUNNING:
            return

        # Fetch and Decode
        instruction, opcode = self.fetch_and_decode()

        # Report
        if self.verbose:
            report = "Instruction: {}; Opcode: {}".format(instruction.mnemonic, hex(opcode))
            if instruction.length_in_bytes == 2:
                report += "; Operand: {}".format(hex(self.memory[self.PC + 1]))
            elif instruction.length_in_bytes == 3:
                val = self.memory[self.PC + 1] | (self.memory[self.PC + 2] << 8)
                report += "; Operand: {}".format(hex(val))
            print(report)

            print("PC: {}".format(hex(self.PC)))
            print("SP: {}".format(hex(self.SP)))
            print("A: {}".format(hex(self.A)))
            print("B: {}".format(hex(self.B)))
            print("C: {}".format(hex(self.C)))
            print("D: {}".format(hex(self.D)))
            print("E: {}".format(hex(self.E)))
            print("F: {}".format(hex(self.F)))
            print("H: {}".format(hex(self.H)))
            print("L: {}".format(hex(self.L)))

        # Execute
        action = instruction.function(self)
        self.wait = (instruction.duration_in_cycles / 4) - 1
        if action != LR35902.JUMPED:
            self.PC += instruction.length_in_bytes

        if self.debugger and (self.PC in self.debugger.breakpoints):
            return LR35902.BREAKPOINT_HIT

        # Interrupt change
        if self.interrupts["change_in"] > 0:
            self.interrupts["change_in"] -= 1

            if self.interrupts["change_in"] == 0:
                self.interrupts["enabled"] = not self.interrupts["enabled"]

    # 16-bit Arithmetic
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

        hl_val += val

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

    def swap(self, reg=None):
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

    def swap_memory(self):
        """GBCPUman.pdf page 94
        0xCB Opcodes 0x36
        Swap upper and lower nibbles of byte stored at n
        """

        self.F = 0 # Clear flags

        addr = (self.H << 8) | self.L
        self.memory[addr] = (((self.memory[addr] & 0x0F) << 4) | ((self.memory[addr] & 0xF0) >> 4)) & 0xFF

        self.set_zero(self.memory[addr])

    def daa(self):
        """GBCPUman.pdf page 95
        Opcode 0x27
        Decimal adjust A register

        Source: https://forums.nesdev.com/viewtopic.php?f=20&t=15944
        """

        if (self.F >> flags.FLAG_N) & 1 == 0:
            # Last operation was an additon
            if ((self.F >> flags.FLAG_C) & 1) or self.A > 0x99:
                self.A += 0x60
                self.set_flag(flags.FLAG_C, True)

            if ((self.F >> flags.FLAG_H) & 1) or (self.A & 0xF) > 0x9:
                self.A += 0x6
        else:
            # Last operation was a subtraction
            if (self.F >> flags.FLAG_C) & 1:
                self.A -= 0x60
            if (self.F >> flags.FLAG_H) & 1:
                self.A -= 0x06

        self.set_zero(self.A)
        self.set_flag(flags.FLAG_H, False)

    def cpl(self):
        """GBCPUman.pdf page 95
        Opcode 0x2F
        Complement (flip all bits) in A register
        """

        self.A = (~self.A) & 0xFF

        self.set_flag(flags.FLAG_N, True)
        self.set_flag(flags.FLAG_H, True)

    def ccf(self):
        """GBCPUman.pdf page 96
        Opcode 0x3F
        Complement carry flag
        """

        self.set_flag(flags.FLAG_N, False)
        self.set_flag(flags.FLAG_H, False)
        self.set_flag(flags.FLAG_C, ((self.F >> flags.FLAG_C) & 1) == 0)

    def scf(self):
        """GBCPUman.pdf page 96
        Opcode 0x37
        Set carry flag
        """

        self.set_flag(flags.FLAG_N, False)
        self.set_flag(flags.FLAG_H, False)
        self.set_flag(flags.FLAG_C, True)

    def nop(self):
        """GBCPUman.pdf page 97
        Opcode 0x00
        Do nothing
        """

    def halt(self):
        """GBCPUman.pdf page 97
        Opcode 0x76
        Power down the CPU until an interrupt occurs
        """
        self.state = LR35902.State.HALTED

    def stop(self):
        """GBCPUman.pdf page 97
        Opcode 0x10
        Halt CPU and LCD until button is pressed.
        """
        self.state = LR35902.State.STOPPED

    def di(self):
        """GBCPUman.pdf page 98
        Opcode 0xF3
        Interrupts are disabled after the instruction after DI is executed
        """
        if self.interrupts["enabled"]:
            self.interrupts["change_in"] = 2

    def ei(self):
        """GBCPUman.pdf page 98
        Opcode 0xFB
        Interrupts are enabled after the instruction after EI is executed
        """
        if not self.interrupts["enabled"]:
            self.interrupts["change_in"] = 2

    # Rotates and Shifts
    def rlc(self, reg=None):
        """GBCPUman.pdf page 99 & 101
        Opcode 0x07
        0xCB Opcodes 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x07
        Rotate reg left. Old bit 7 to carry flag.
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

        # Reset flags
        self.F = 0

        # Old bit 7 to carry flag
        if getattr(self, reg_attr) & 0x80:
            self.F |= (1 << flags.FLAG_C)

        # Rotate
        setattr(
            self,
            reg_attr,
            (
                ((getattr(self, reg_attr) << 1) & 0xFE) |
                ((getattr(self, reg_attr) & 0x80) >> 7)
            )
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            self.F |= (1 << flags.FLAG_Z)

    def rlc_memory(self):
        """GBCPUman.pdf page 101
        0xCB Opcodes 0x06
        Rotate value stored at address pointed to by HL left. Old bit 7 to carry flag.
        """
        addr = (self.H << 8) | self.L

        # Reset flags
        self.F = 0

        # Old bit 7 to carry flag
        if self.memory[addr] & 0x80:
            self.F |= (1 << flags.FLAG_C)

        # Rotate
        self.memory[addr] = ((self.memory[addr] << 1) & 0xFE) | ((self.memory[addr] & 0x80) >> 7)

        # Set Z flag if 0
        if self.memory[addr] == 0:
            self.F |= (1 << flags.FLAG_Z)

    def rl(self, reg=None):
        """GBCPUman.pdf page 99 & 102
        Opcode 0x17
        0xCB Opcodes 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x17
        Rotate register left through carry flag. Old bit 7 to carry flag.
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

        new_flags = 0

        # Old bit 7 to carry flag
        if getattr(self, reg_attr) & 0x80:
            new_flags |= (1 << flags.FLAG_C)

        # Rotate
        setattr(
            self,
            reg_attr,
            ((getattr(self, reg_attr) << 1) & 0xFE)
        )

        # Old carry flag to bit 0
        if self.F & (1 << flags.FLAG_C):
            setattr(
                self,
                reg_attr,
                getattr(self, reg_attr) | 1
            )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def rl_memory(self):
        """GBCPUman.pdf page 102
        0xCB Opcodes 0x16
        Rotate value stored at address pointed to by HL left through carry flag. Old bit 7 to carry flag.
        """
        addr = (self.H << 8) | self.L

        new_flags = 0

        # Old bit 7 to carry flag
        if self.memory[addr] & 0x80:
            new_flags |= (1 << flags.FLAG_C)

        # Rotate
        self.memory[addr] = (self.memory[addr] << 1) & 0xFE

        # Old carry flag to bit 0
        if self.F & (1 << flags.FLAG_C):
            self.memory[addr] |= 1

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def rrc(self, reg=None):
        """GBCPUman.pdf page 100 & 103
        Opcode 0x0F
        0xCB Opcodes 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0F
        Rotate register right. Old bit 0 to carry flag.
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

        # Reset flags
        self.F = 0

        # Old bit 0 to carry flag
        if getattr(self, reg_attr) & 0x1:
            self.F |= (1 << flags.FLAG_C)

        # Rotate
        setattr(
            self,
            reg_attr,
            (
                ((getattr(self, reg_attr) >> 1) & 0x7F) |
                ((getattr(self, reg_attr) & 0x01) << 7)
            )
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            self.F |= (1 << flags.FLAG_Z)

    def rrc_memory(self):
        """GBCPUman.pdf 103
        0xCB Opcodes 0x0E
        Rotate value pointed to by HL right. Old bit 0 to carry flag.
        """
        addr = (self.H << 8) | self.L

        # Reset flags
        self.F = 0

        # Old bit 0 to carry flag
        if self.memory[addr] & 0x1:
            self.F |= (1 << flags.FLAG_C)

        # Rotate
        self.memory[addr] = ((self.memory[addr] >> 1) & 0x7F) | ((self.memory[addr] & 0x01) << 7)

        # Set Z flag if 0
        if self.memory[addr] == 0:
            self.F |= (1 << flags.FLAG_Z)

    def rr(self, reg=None):
        """GBCPUman.pdf page 100 & 104
        Opcode 0x1F
        0xCB Opcodes 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1F
        Rotate register right through carry flag. Old bit 0 to carry flag.
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

        new_flags = 0

        # Old bit 0 to carry flag
        if getattr(self, reg_attr) & 0x1:
            new_flags |= (1 << flags.FLAG_C)

        # Rotate
        setattr(
            self,
            reg_attr,
            ((getattr(self, reg_attr) >> 1) & 0x7F)
        )

        # Old carry flag to bit 7
        if self.F & (1 << flags.FLAG_C):
            setattr(
                self,
                reg_attr,
                getattr(self, reg_attr) | 0x80
            )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def rr_memory(self):
        """GBCPUman.pdf page 104
        0xCB Opcodes 0x1E
        Rotate register pointed to by HL to the right through carry flag. Old bit 0 to carry flag.
        """
        addr = (self.H << 8) | self.L

        new_flags = 0

        # Old bit 0 to carry flag
        if self.memory[addr] & 0x1:
            new_flags |= (1 << flags.FLAG_C)

        # Rotate
        self.memory[addr] = (self.memory[addr] >> 1) & 0x7F

        # Old carry flag to bit 7
        if self.F & (1 << flags.FLAG_C):
            self.memory[addr] |= 0x80

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def sla(self, reg=None):
        """GBCPUman.pdf page 105
        0xCB Opcodes 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x27
        Shift register left into carry. LSB of register set to 0.
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

        new_flags = 0

        # Set carry flag
        if getattr(self, reg_attr) & 0x80:
            self.F |= (1 << flags.FLAG_C)

        # Shift left
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) << 1) & 0xFE
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def sla_memory(self):
        """GBCPUman.pdf page 105
        0xCB Opcode 0x26
        Shift value stored a memory address HL left into carry. LSB of register set to 0.
        """
        addr = (self.H << 8) | self.L

        new_flags = 0

        # Set carry flag
        if self.memory[addr] & 0x80:
            self.F |= (1 << flags.FLAG_C)

        # Shift left
        self.memory[addr] = (self.memory[addr] << 1) & 0xFE

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def sra(self, reg=None):
        """GBCPUman.pdf page 106
        0xCB Opcodes 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2F
        Shift register right into carry. MSB doesn't change.
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

        new_flags = 0

        # Set carry flag
        if getattr(self, reg_attr) & 0x01:
            self.F |= (1 << flags.FLAG_C)

        # Shift Right
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) & 0x80) |
            (getattr(self, reg_attr) >> 1) & 0x7F
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def sra_memory(self):
        """GBCPUman.pdf page 106
        0xCB Opcode 0x2E
        Shift value stored at address HL right into carry. MSB doesn't change.
        """
        addr = (self.H << 8) | self.L

        new_flags = 0

        # Set carry flag
        if self.memory[addr] & 0x01:
            self.F |= (1 << flags.FLAG_C)

        # Shift Right
        self.memory[addr] = (self.memory[addr] & 0x80) | (self.memory[addr] >> 1) & 0x7F

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def srl(self, reg=None):
        """GBCPUman.pdf page 107
        0xCB Opcodes 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3F
        Shift register right into carry. MSB set to 0.
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

        new_flags = 0

        # Set carry flag
        if getattr(self, reg_attr) & 0x01:
            self.F |= (1 << flags.FLAG_C)

        # Shift Right
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) >> 1) & 0x7F
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def srl_memory(self):
        """GBCPUman.pdf page 107
        0xCB Opcode 0x3E
        Shift value stored at address HL right into carry. MSB doesn't change.
        """
        addr = (self.H << 8) | self.L

        new_flags = 0

        # Set carry flag
        if self.memory[addr] & 0x01:
            self.F |= (1 << flags.FLAG_C)

        # Shift Right
        self.memory[addr] = (self.memory[addr] >> 1) & 0x7F

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << flags.FLAG_Z)

        # Update flags
        self.F = new_flags

    def bit(self, reg=None, bit=None):
        """GBCPUman.pdf page 108
        0xCB Opcodes 0x40-0x7F, except 0x*6 and 0x*E
        Test bit in register
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

        self.set_flag(flags.FLAG_N, False)
        self.set_flag(flags.FLAG_H, True)
        self.set_flag(flags.FLAG_Z, not getattr(self, reg_attr) & (1 << bit))

    def bit_memory(self, bit=None):
        """GBCPUman.pdf page 108
        0xCB Opcodes 0x46, 0x4E, 0x56, 0x5E, 0x66, 0x6E, 0x76, 0x7E
        Test bit in value stored at HL
        """
        addr = (self.H << 8) | self.L

        self.set_flag(flags.FLAG_N, False)
        self.set_flag(flags.FLAG_H, True)
        self.set_flag(flags.FLAG_Z, not self.memory[addr] & (1 << bit))

    def set(self, reg=None, bit=None):
        """GBCPUman.pdf page 109
        0xCB Opcodes 0xC0-0xFF, except 0x*6 and 0x*E
        Set bit in register
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

        setattr(
            self,
            reg_attr,
            getattr(self, reg_attr) | (1 << bit)
        )

    def set_memory(self, bit=None):
        """GBCPUman.pdf page 109
        0xCB Opcodes 0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE
        Set bit in memory at HL
        """
        addr = (self.H << 8) | self.L

        self.memory[addr] |= (1 << bit)

    def res(self, reg=None, bit=None):
        """GBCPUman.pdf page 110
        0xCB Opcodes 0x80-0xBF, except 0x*6 and 0x*E
        Clear bit in register
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

        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) & ~(1 << bit)) & 0xFF
        )

    def res_memory(self, bit=None):
        """GBCPUman.pdf page 110
        0xCB Opcodes 0x86, 0x8E, 0x96, 0x9E, 0xA6, 0xAE, 0xB6, 0xBE
        Clear bit in memory at HL
        """
        addr = (self.H << 8) | self.L

        self.memory[addr] = (self.memory[addr] & ~(1 << bit)) & 0xFF

    def jp_nn(self):
        """GBCPUman.pdf page 111
        Opcode 0xC3
        Jump to address NN
        """
        addr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]

        self.PC = addr
        return LR35902.JUMPED

    def jp_cc_nn(self, condition=None):
        """GBCPUman.pdf page 111
        Opcode 0xC2, 0xCA, 0xD2, 0xDA
        Jump to two byte immediate value if condition is met.
        """
        if condition == LR35902.CONDITION_NZ:
            test = not self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not self.F & (1 << flags.FLAG_C)
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << flags.FLAG_C)
        else:
            raise RuntimeError('Invalid condition "{}" specified!'.format(condition))

        if test:
            addr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
            self.PC = addr
            self.wait += 1
            return LR35902.JUMPED

    def jp_memory(self):
        """GBCPUman.pdf page 112
        Opcode 0xE9
        Jump to address contained in HL
        """
        addr = (self.H << 8) | self.L
        self.PC = addr
        return LR35902.JUMPED

    def jr_n(self):
        """GBCPUman.pdf page 112
        Opcode 0x18
        Add 8-bit immediate value to PC and jump to it.
        """
        value = self.memory[self.PC + 1]

        if value & 0x80:
            value = (0x100 - value) & 0xFFFF
            self.PC = (self.PC - value + 2) & 0xFFFF
        else:
            value = (value + 2) & 0xFFFF
            self.PC += value

        return LR35902.JUMPED

    def jr_cc_n(self, condition=None):
        """GBCPUman.pdf page 113
        Opcode 0x20, 0x28, 0x30, 0x38
        Add 8-bit immediate value to PC and jump to it if condition is met.
        """
        if condition == LR35902.CONDITION_NZ:
            test = not self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not self.F & (1 << flags.FLAG_C)
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << flags.FLAG_C)
        else:
            raise RuntimeError('Invalid condition "{}" specified!'.format(condition))

        if test:
            value = self.memory[self.PC + 1]

            if value & 0x80:
                value = (0x100 - value) & 0xFFFF
                self.PC = (self.PC - value + 2) & 0xFFFF
            else:
                value = (value + 2) & 0xFFFF
                self.PC += value

            self.wait += 1 # TODO: Hacky
            return LR35902.JUMPED

    def call_nn(self):
        """GBCPUman.pdf page 114
        Opcode 0xCD
        Push next instruction address on to stack and jump to two-byte immediate
        address.
        """
        # Save program counter to stack
        self.SP -= 2
        self.memory[self.SP + 1] = ((self.PC + 3) >> 8) & 0xFF
        self.memory[self.SP] = (self.PC + 3) & 0xFF

        # Jump to 16-bit immediate value
        addr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
        self.PC = addr
        return LR35902.JUMPED

    def call_cc_nn(self, condition):
        """GBCPUman.pdf page 114
        Opcode 0xC4, 0xCC, 0xD4, 0xDC
        Push next instruction address on to stack and jump to two-byte immediate
        address, if condition is met
        """
        if condition == LR35902.CONDITION_NZ:
            test = not self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not self.F & (1 << flags.FLAG_C)
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << flags.FLAG_C)
        else:
            raise RuntimeError('Invalid condition "{}" specified!'.format(condition))

        if test:
            # Save program counter to stack
            self.SP -= 2
            self.memory[self.SP + 1] = ((self.PC + 3) >> 8) & 0xFF
            self.memory[self.SP] = (self.PC + 3) & 0xFF

            # Jump to 16-bit immediate value
            addr = (self.memory[self.PC + 2] << 8) | self.memory[self.PC + 1]
            self.PC = addr

            self.wait += 3 # TODO: Hacky
            return LR35902.JUMPED

    def rst(self, offset=None):
        """GBCPUman.pdf page 116
        Opcode 0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF
        Push present instruction address on to stack and jump to relative offset
        address from 0x0000.
        """
        # Save program counter to stack
        self.SP -= 2
        self.memory[self.SP + 1] = (self.PC >> 8) & 0xFF
        self.memory[self.SP] = self.PC & 0xFF

        # Jump to address
        self.PC += offset
        return LR35902.JUMPED

    def ret(self):
        """GBCPUman.pdf page 117
        Opcode 0xC9
        Pop two bytes off the stack and jump to the address.
        """
        self.PC = (
            ((self.memory[self.SP + 1] << 8) & 0xFF00) |
            (self.memory[self.SP] & 0xFF)
        )
        self.SP += 2
        return LR35902.JUMPED

    def ret_cc(self, condition=None):
        """GBCPUman.pdf page 117
        Opcode 0xC0, 0xC8, 0xD0, 0xD8
        Pop two bytes off the stack and jump to the address, if condition is
        met.
        """
        if condition == LR35902.CONDITION_NZ:
            test = not self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << flags.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not self.F & (1 << flags.FLAG_C)
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << flags.FLAG_C)
        else:
            raise RuntimeError('Invalid condition "{}" specified!'.format(condition))

        if test:
            self.PC = (
                ((self.memory[self.SP + 1] << 8) & 0xFF00) |
                (self.memory[self.SP] & 0xFF)
            )
            self.SP += 2

            self.wait += 3
            return LR35902.JUMPED

    def reti(self):
        """GBCPUman.pdf page 117
        Opcode 0xD9
        Pop two bytes off the stack and jump to the address and then enable
        interrupts.
        """
        self.PC = (
            ((self.memory[self.SP + 1] << 8) & 0xFF00) |
            (self.memory[self.SP] & 0xFF)
        )
        self.SP += 2

        self.interrupts = {
            "enabled": True,
            "change_in": 0
        }

        return LR35902.JUMPED
