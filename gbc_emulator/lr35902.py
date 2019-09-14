from collections import namedtuple
from enum import Enum
from gbc_emulator.memory import Memory

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
        RUNNING = 0,
        HALTED = 1,
        STOPPED = 2

    Instruction = namedtuple('Instruction', ['function', 'length_in_bytes', 'duration_in_cycles', 'mnemonic'])

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
            LR35902.Instruction(function=lambda s: s.nop(), length_in_bytes=1, duration_in_cycles=4, mnemonic='NOP'), # 0x00
            LR35902.Instruction(function=lambda s: s.ld_n_nn(LR35902.REGISTER_BC), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD BC,d16'), # 0x01
            LR35902.Instruction(function=lambda s: s.ld_n_a_pointer(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (BC),A'), # 0x02
            LR35902.Instruction(function=lambda s: s.inc_nn(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC BC'), # 0x03
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC B'), # 0x04
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC B'), # 0x05
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD B,d8'), # 0x06
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='RLCA'), # 0x07
            LR35902.Instruction(function=lambda s: s.ld_nn_sp(), length_in_bytes=3, duration_in_cycles=20, mnemonic='LD (a16),SP'), # 0x08
            LR35902.Instruction(function=lambda s: s.add_hl_n(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,BC'), # 0x09
            LR35902.Instruction(function=lambda s: s.ld_a_n_from_memory(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(BC)'), # 0x0A
            LR35902.Instruction(function=lambda s: s.dec_nn(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC BC'), # 0x0B
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC C'), # 0x0C
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC C'), # 0x0D
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD C,d8'), # 0x0E
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='RRCA'), # 0x0F
            LR35902.Instruction(function=lambda s: s.stop(), length_in_bytes=2, duration_in_cycles=4, mnemonic='STOP 0'), # 0x10
            LR35902.Instruction(function=lambda s: s.ld_n_nn(LR35902.REGISTER_DE), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD DE,d16'), # 0x11
            LR35902.Instruction(function=lambda s: s.ld_n_a_pointer(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (DE),A'), # 0x12
            LR35902.Instruction(function=lambda s: s.inc_nn(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC DE'), # 0x13
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC D'), # 0x14
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC D'), # 0x15
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD D,d8'), # 0x16
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='RLA'), # 0x17
            LR35902.Instruction(function=lambda s: s.jr_n(), length_in_bytes=2, duration_in_cycles=12, mnemonic='JR r8'), # 0x18
            LR35902.Instruction(function=lambda s: s.add_hl_n(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,DE'), # 0x19
            LR35902.Instruction(function=lambda s: s.ld_a_n_from_memory(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(DE)'), # 0x1A
            LR35902.Instruction(function=lambda s: s.dec_nn(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC DE'), # 0x1B
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC E'), # 0x1C
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC E'), # 0x1D
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD E,d8'), # 0x1E
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='RRA'), # 0x1F
            LR35902.Instruction(function=lambda s: s.jr_cc_n(LR35902.CONDITION_NZ), length_in_bytes=2, duration_in_cycles=8, mnemonic='JR NZ,r8'), # 0x20
            LR35902.Instruction(function=lambda s: s.ld_n_nn(LR35902.REGISTER_HL), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD HL,d16'), # 0x21
            LR35902.Instruction(function=lambda s: s.ld_hl_a_increment(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL+),A'), # 0x22
            LR35902.Instruction(function=lambda s: s.inc_nn(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC HL'), # 0x23
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC H'), # 0x24
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC H'), # 0x25
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD H,d8'), # 0x26
            LR35902.Instruction(function=lambda s: s.daa(), length_in_bytes=1, duration_in_cycles=4, mnemonic='DAA'), # 0x27
            LR35902.Instruction(function=lambda s: s.jr_cc_n(LR35902.CONDITION_Z), length_in_bytes=2, duration_in_cycles=8, mnemonic='JR Z,r8'), # 0x28
            LR35902.Instruction(function=lambda s: s.add_hl_n(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,HL'), # 0x29
            LR35902.Instruction(function=lambda s: s.ld_a_hl_increment(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(HL+)'), # 0x2A
            LR35902.Instruction(function=lambda s: s.dec_nn(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC HL'), # 0x2B
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC L'), # 0x2C
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC L'), # 0x2D
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD L,d8'), # 0x2E
            LR35902.Instruction(function=lambda s: s.cpl(), length_in_bytes=1, duration_in_cycles=4, mnemonic='CPL'), # 0x2F
            LR35902.Instruction(function=lambda s: s.jr_cc_n(LR35902.CONDITION_NC), length_in_bytes=2, duration_in_cycles=8, mnemonic='JR NC,r8'), # 0x30
            LR35902.Instruction(function=lambda s: s.ld_n_nn(LR35902.REGISTER_SP), length_in_bytes=3, duration_in_cycles=12, mnemonic='LD SP,d16'), # 0x31
            LR35902.Instruction(function=lambda s: s.ld_hl_a_decrement(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL-),A'), # 0x32
            LR35902.Instruction(function=lambda s: s.inc_nn(LR35902.REGISTER_SP), length_in_bytes=1, duration_in_cycles=8, mnemonic='INC SP'), # 0x33
            LR35902.Instruction(function=lambda s: s.inc_n_memory(), length_in_bytes=1, duration_in_cycles=12, mnemonic='INC (HL)'), # 0x34
            LR35902.Instruction(function=lambda s: s.dec_n_memory(), length_in_bytes=1, duration_in_cycles=12, mnemonic='DEC (HL)'), # 0x35
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_immediate_to_memory(LR35902.REGISTER_HL), length_in_bytes=2, duration_in_cycles=12, mnemonic='LD (HL),d8'), # 0x36
            LR35902.Instruction(function=lambda s: s.scf(), length_in_bytes=1, duration_in_cycles=4, mnemonic='SCF'), # 0x37
            LR35902.Instruction(function=lambda s: s.jr_cc_n(LR35902.CONDITION_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='JR C,r8'), # 0x38
            LR35902.Instruction(function=lambda s: s.add_hl_n(LR35902.REGISTER_SP), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD HL,SP'), # 0x39
            LR35902.Instruction(function=lambda s: s.ld_a_hl_decrement(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(HL-)'), # 0x3A
            LR35902.Instruction(function=lambda s: s.dec_nn(LR35902.REGISTER_SP), length_in_bytes=1, duration_in_cycles=8, mnemonic='DEC SP'), # 0x3B
            LR35902.Instruction(function=lambda s: s.inc_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='INC A'), # 0x3C
            LR35902.Instruction(function=lambda s: s.dec_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='DEC A'), # 0x3D
            LR35902.Instruction(function=lambda s: s.ld_nn_n(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='LD A,d8'), # 0x3E
            LR35902.Instruction(function=lambda s: s.ccf(), length_in_bytes=1, duration_in_cycles=4, mnemonic='CCF'), # 0x3F
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,B'), # 0x40
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,C'), # 0x41
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,D'), # 0x42
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,E'), # 0x43
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,H'), # 0x44
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,L'), # 0x45
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_from_memory(src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD B,(HL)'), # 0x46
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD B,A'), # 0x47
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,B'), # 0x48
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,C'), # 0x49
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,D'), # 0x4A
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,E'), # 0x4B
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,H'), # 0x4C
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,L'), # 0x4D
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_from_memory(src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD C,(HL)'), # 0x4E
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD C,A'), # 0x4F
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,B'), # 0x50
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,C'), # 0x51
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,D'), # 0x52
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,E'), # 0x53
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,H'), # 0x54
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,L'), # 0x55
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_from_memory(src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD D,(HL)'), # 0x56
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD D,A'), # 0x57
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,B'), # 0x58
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,C'), # 0x59
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,D'), # 0x5A
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,E'), # 0x5B
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,H'), # 0x5C
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,L'), # 0x5D
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_from_memory(src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD E,(HL)'), # 0x5E
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD E,A'), # 0x5F
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,B'), # 0x60
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,C'), # 0x61
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,D'), # 0x62
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,E'), # 0x63
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,H'), # 0x64
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,L'), # 0x65
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_from_memory(src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD H,(HL)'), # 0x66
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD H,A'), # 0x67
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,B'), # 0x68
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,C'), # 0x69
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,D'), # 0x6A
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,E'), # 0x6B
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,H'), # 0x6C
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,L'), # 0x6D
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_from_memory(src=LR35902.REGISTER_HL, dst=LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD L,(HL)'), # 0x6E
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD L,A'), # 0x6F
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_to_memory(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),B'), # 0x70
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_to_memory(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),C'), # 0x71
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_to_memory(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),D'), # 0x72
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_to_memory(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),E'), # 0x73
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_to_memory(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),H'), # 0x74
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_to_memory(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),L'), # 0x75
            LR35902.Instruction(function=lambda s: s.halt(), length_in_bytes=1, duration_in_cycles=4, mnemonic='HALT'), # 0x76
            LR35902.Instruction(function=lambda s: s.ld_n_a_pointer(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (HL),A'), # 0x77
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_B, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,B'), # 0x78
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_C, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,C'), # 0x79
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_D, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,D'), # 0x7A
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_E, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,E'), # 0x7B
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_H, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,H'), # 0x7C
            LR35902.Instruction(function=lambda s: s.ld_r1_r2_between_registers(src=LR35902.REGISTER_L, dst=LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,L'), # 0x7D
            LR35902.Instruction(function=lambda s: s.ld_a_n_from_memory(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(HL)'), # 0x7E
            LR35902.Instruction(function=lambda s: s.ld_n_a(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='LD A,A'), # 0x7F
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,B'), # 0x80
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,C'), # 0x81
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,D'), # 0x82
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,E'), # 0x83
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,H'), # 0x84
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,L'), # 0x85
            LR35902.Instruction(function=lambda s: s.add_a_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADD A,(HL)'), # 0x86
            LR35902.Instruction(function=lambda s: s.add_a_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADD A,A'), # 0x87
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,B'), # 0x88
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,C'), # 0x89
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,D'), # 0x8A
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,E'), # 0x8B
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,H'), # 0x8C
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,L'), # 0x8D
            LR35902.Instruction(function=lambda s: s.adc_a_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='ADC A,(HL)'), # 0x8E
            LR35902.Instruction(function=lambda s: s.adc_a_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='ADC A,A'), # 0x8F
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB B'), # 0x90
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB C'), # 0x91
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB D'), # 0x92
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB E'), # 0x93
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB H'), # 0x94
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB L'), # 0x95
            LR35902.Instruction(function=lambda s: s.sub_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='SUB (HL)'), # 0x96
            LR35902.Instruction(function=lambda s: s.sub_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='SUB A'), # 0x97
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,B'), # 0x98
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,C'), # 0x99
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,D'), # 0x9A
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,E'), # 0x9B
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,H'), # 0x9C
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,L'), # 0x9D
            LR35902.Instruction(function=lambda s: s.subc_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='SBC A,(HL)'), # 0x9E
            LR35902.Instruction(function=lambda s: s.subc_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='SBC A,A'), # 0x9F
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND B'), # 0xA0
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND C'), # 0xA1
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND D'), # 0xA2
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND E'), # 0xA3
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND H'), # 0xA4
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND L'), # 0xA5
            LR35902.Instruction(function=lambda s: s.and_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='AND (HL)'), # 0xA6
            LR35902.Instruction(function=lambda s: s.and_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='AND A'), # 0xA7
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR B'), # 0xA8
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR C'), # 0xA9
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR D'), # 0xAA
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR E'), # 0xAB
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR H'), # 0xAC
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR L'), # 0xAD
            LR35902.Instruction(function=lambda s: s.xor_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='XOR (HL)'), # 0xAE
            LR35902.Instruction(function=lambda s: s.xor_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='XOR A'), # 0xAF
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR B'), # 0xB0
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR C'), # 0xB1
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR D'), # 0xB2
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR E'), # 0xB3
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR H'), # 0xB4
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR L'), # 0xB5
            LR35902.Instruction(function=lambda s: s.or_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='OR (HL)'), # 0xB6
            LR35902.Instruction(function=lambda s: s.or_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='OR A'), # 0xB7
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_B), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP B'), # 0xB8
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_C), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP C'), # 0xB9
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_D), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP D'), # 0xBA
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_E), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP E'), # 0xBB
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_H), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP H'), # 0xBC
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_L), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP L'), # 0xBD
            LR35902.Instruction(function=lambda s: s.cp_n_memory(), length_in_bytes=1, duration_in_cycles=8, mnemonic='OR (HL)'), # 0xBE
            LR35902.Instruction(function=lambda s: s.cp_n_register(LR35902.REGISTER_A), length_in_bytes=1, duration_in_cycles=4, mnemonic='CP A'), # 0xBF
            LR35902.Instruction(function=lambda s: s.ret_cc(LR35902.CONDITION_NZ), length_in_bytes=1, duration_in_cycles=8, mnemonic='RET NZ'), # 0xC0
            LR35902.Instruction(function=lambda s: s.pop_nn(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP BC'), # 0xC1
            LR35902.Instruction(function=lambda s: s.jp_cc_nn(LR35902.CONDITION_NZ), length_in_bytes=3, duration_in_cycles=12, mnemonic='JP NZ,a16'), # 0xC2
            LR35902.Instruction(function=lambda s: s.jp_nn(), length_in_bytes=3, duration_in_cycles=16, mnemonic='JP a16'), # 0xC3
            LR35902.Instruction(function=lambda s: s.call_cc_nn(LR35902.CONDITION_NZ), length_in_bytes=3, duration_in_cycles=12, mnemonic='CALL NZ,a16'), # 0xC4
            LR35902.Instruction(function=lambda s: s.push_nn(LR35902.REGISTER_BC), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH BC'), # 0xC5
            LR35902.Instruction(function=lambda s: s.add_a_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='ADD A,d8'), # 0xC6
            LR35902.Instruction(function=lambda s: s.rst(0x00), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 00H'), # 0xC7
            LR35902.Instruction(function=lambda s: s.ret_cc(LR35902.CONDITION_Z), length_in_bytes=1, duration_in_cycles=8, mnemonic='RET Z'), # 0xC8
            LR35902.Instruction(function=lambda s: s.ret(), length_in_bytes=1, duration_in_cycles=16, mnemonic='RET'), # 0xC9
            LR35902.Instruction(function=lambda s: s.jp_cc_nn(LR35902.CONDITION_Z), length_in_bytes=3, duration_in_cycles=12, mnemonic='JP Z,a16'), # 0xCA
            None, # 0xCB
            LR35902.Instruction(function=lambda s: s.call_cc_nn(LR35902.CONDITION_Z), length_in_bytes=3, duration_in_cycles=12, mnemonic='CALL Z,a16'), # 0xCC
            LR35902.Instruction(function=lambda s: s.call_nn(), length_in_bytes=3, duration_in_cycles=24, mnemonic='CALL a16'), # 0xCD
            LR35902.Instruction(function=lambda s: s.adc_a_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='ADC A,d8'), # 0xCE
            LR35902.Instruction(function=lambda s: s.rst(0x08), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 08H'), # 0xCF
            LR35902.Instruction(function=lambda s: s.ret_cc(LR35902.CONDITION_NC), length_in_bytes=1, duration_in_cycles=8, mnemonic='RET NC'), # 0xD0
            LR35902.Instruction(function=lambda s: s.pop_nn(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP DE'), # 0xD1
            LR35902.Instruction(function=lambda s: s.jp_cc_nn(LR35902.CONDITION_NC), length_in_bytes=3, duration_in_cycles=12, mnemonic='JP NC,a16'), # 0xD2
            None, # 0xD3
            LR35902.Instruction(function=lambda s: s.call_cc_nn(LR35902.CONDITION_NC), length_in_bytes=3, duration_in_cycles=12, mnemonic='CALL NC,a16'), # 0xD4
            LR35902.Instruction(function=lambda s: s.push_nn(LR35902.REGISTER_DE), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH DE'), # 0xD5
            LR35902.Instruction(function=lambda s: s.sub_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='SUB d8'), # 0xD6
            LR35902.Instruction(function=lambda s: s.rst(0x10), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 10H'), # 0xD7
            LR35902.Instruction(function=lambda s: s.ret_cc(LR35902.CONDITION_C), length_in_bytes=1, duration_in_cycles=8, mnemonic='RET C'), # 0xD8
            LR35902.Instruction(function=lambda s: s.reti(), length_in_bytes=1, duration_in_cycles=16, mnemonic='RETI'), # 0xD9
            LR35902.Instruction(function=lambda s: s.jp_cc_nn(LR35902.CONDITION_C), length_in_bytes=3, duration_in_cycles=12, mnemonic='JP C,a16'), # 0xDA
            None, # 0xDB
            LR35902.Instruction(function=lambda s: s.call_cc_nn(LR35902.CONDITION_C), length_in_bytes=3, duration_in_cycles=12, mnemonic='CALL C,a16'), # 0xDC
            None, # 0xDD
            LR35902.Instruction(function=lambda s: s.subc_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='SUB A,d8'), # 0xDE
            LR35902.Instruction(function=lambda s: s.rst(0x18), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 18H'), # 0xDF
            LR35902.Instruction(function=lambda s: s.ldh_n_a(), length_in_bytes=2, duration_in_cycles=12, mnemonic='LDH (a8),A'), # 0xE0
            LR35902.Instruction(function=lambda s: s.pop_nn(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP HL'), # 0xE1
            LR35902.Instruction(function=lambda s: s.ld_c_a(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD (C),A'), # 0xE2  # This disagrees with pastraiser length of 2 bytes
            None, # 0xE3
            None, # 0xE4
            LR35902.Instruction(function=lambda s: s.push_nn(LR35902.REGISTER_HL), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH HL'), # 0xE5
            LR35902.Instruction(function=lambda s: s.and_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='AND d8'), # 0xE6
            LR35902.Instruction(function=lambda s: s.rst(0x20), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 20H'), # 0xE7
            LR35902.Instruction(function=lambda s: s.add_sp_n(), length_in_bytes=2, duration_in_cycles=16, mnemonic='ADD SP,r8'), # 0xE8
            LR35902.Instruction(function=lambda s: s.jp_memory(), length_in_bytes=1, duration_in_cycles=4, mnemonic='JP (HL)'), # 0xE9
            LR35902.Instruction(function=lambda s: s.ld_n_a_immediate(), length_in_bytes=3, duration_in_cycles=16, mnemonic='LD (a16),A'), # 0xEA
            None, # 0xEB
            None, # 0xEC
            None, # 0xED
            LR35902.Instruction(function=lambda s: s.xor_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='XOR d8'), # 0xEE
            LR35902.Instruction(function=lambda s: s.rst(0x28), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 28H'), # 0xEF
            LR35902.Instruction(function=lambda s: s.ldh_a_n(), length_in_bytes=2, duration_in_cycles=12, mnemonic='LDH A,(a8)'), # 0xF0
            LR35902.Instruction(function=lambda s: s.pop_nn(LR35902.REGISTER_AF), length_in_bytes=1, duration_in_cycles=12, mnemonic='POP AF'), # 0xF1
            LR35902.Instruction(function=lambda s: s.ld_a_c(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD A,(C)'), # 0xF2 # This disagrees with pastraiser length of 2 bytes
            LR35902.Instruction(function=lambda s: s.di(), length_in_bytes=1, duration_in_cycles=4, mnemonic='DI'), # 0xF3
            None, # 0xF4
            LR35902.Instruction(function=lambda s: s.push_nn(LR35902.REGISTER_AF), length_in_bytes=1, duration_in_cycles=16, mnemonic='PUSH AF'), # 0xF5
            LR35902.Instruction(function=lambda s: s.or_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='OR d8'), # 0xF6
            LR35902.Instruction(function=lambda s: s.rst(0x30), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 30H'), # 0xF7
            LR35902.Instruction(function=lambda s: s.ld_hl_sp_n(), length_in_bytes=2, duration_in_cycles=12, mnemonic='LD HL,SP+r8'), # 0xF8
            LR35902.Instruction(function=lambda s: s.ld_sp_hl(), length_in_bytes=1, duration_in_cycles=8, mnemonic='LD SP,HL'), # 0xF9
            LR35902.Instruction(function=lambda s: s.ld_a_n_from_memory_immediate(), length_in_bytes=3, duration_in_cycles=16, mnemonic='LD A,(a16)'), # 0xFA
            LR35902.Instruction(function=lambda s: s.ei(), length_in_bytes=1, duration_in_cycles=4, mnemonic='EI'), # 0xFB
            None, # 0xFC
            None, # 0xFD
            LR35902.Instruction(function=lambda s: s.cp_n_immediate(), length_in_bytes=2, duration_in_cycles=8, mnemonic='CP d8'), # 0xFE
            LR35902.Instruction(function=lambda s: s.rst(0x38), length_in_bytes=1, duration_in_cycles=16, mnemonic='RST 38H'), # 0xFF
        ]

        # Instruction map
        self.cb_instructions = [
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC B'), # 0x00
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC C'), # 0x01
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC D'), # 0x02
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC E'), # 0x03
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC H'), # 0x04
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC L'), # 0x05
            LR35902.Instruction(function=lambda s: s.rlc_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='RLC (HL)'), # 0x06
            LR35902.Instruction(function=lambda s: s.rlc(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='RLC A'), # 0x07
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC B'), # 0x08
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC C'), # 0x09
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC D'), # 0x0A
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC E'), # 0x0B
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC H'), # 0x0C
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC L'), # 0x0D
            LR35902.Instruction(function=lambda s: s.rrc_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='RRC (HL)'), # 0x0E
            LR35902.Instruction(function=lambda s: s.rrc(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='RRC A'), # 0x0F
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL B'), # 0x10
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL C'), # 0x11
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL D'), # 0x12
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL E'), # 0x13
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL H'), # 0x14
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL L'), # 0x15
            LR35902.Instruction(function=lambda s: s.rl_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='RL (HL)'), # 0x16
            LR35902.Instruction(function=lambda s: s.rl(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='RL A'), # 0x17
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR B'), # 0x18
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR C'), # 0x19
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR D'), # 0x1A
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR E'), # 0x1B
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR H'), # 0x1C
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR L'), # 0x1D
            LR35902.Instruction(function=lambda s: s.rr_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='RR (HL)'), # 0x1E
            LR35902.Instruction(function=lambda s: s.rr(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='RR A'), # 0x1F
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA B'), # 0x20
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA C'), # 0x21
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA D'), # 0x22
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA E'), # 0x23
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA H'), # 0x24
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA L'), # 0x25
            LR35902.Instruction(function=lambda s: s.sla_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='SLA (HL)'), # 0x26
            LR35902.Instruction(function=lambda s: s.sla(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='SLA A'), # 0x27
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA B'), # 0x28
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA C'), # 0x29
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA D'), # 0x2A
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA E'), # 0x2B
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA H'), # 0x2C
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA L'), # 0x2D
            LR35902.Instruction(function=lambda s: s.sra_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='SRA (HL)'), # 0x2E
            LR35902.Instruction(function=lambda s: s.sra(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRA A'), # 0x2F
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP B'), # 0x30
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP C'), # 0x31
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP D'), # 0x32
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP E'), # 0x33
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP H'), # 0x34
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP L'), # 0x35
            LR35902.Instruction(function=lambda s: s.swap_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='SWAP (HL)'), # 0x36
            LR35902.Instruction(function=lambda s: s.swap(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='SWAP A'), # 0x37
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_B), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL B'), # 0x38
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_C), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL C'), # 0x39
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_D), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL D'), # 0x3A
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_E), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL E'), # 0x3B
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_H), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL H'), # 0x3C
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_L), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL L'), # 0x3D
            LR35902.Instruction(function=lambda s: s.srl_memory(), length_in_bytes=2, duration_in_cycles=16, mnemonic='SRL (HL)'), # 0x3E
            LR35902.Instruction(function=lambda s: s.srl(LR35902.REGISTER_A), length_in_bytes=2, duration_in_cycles=8, mnemonic='SRL A'), # 0x3F
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,B'), # 0x40
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,C'), # 0x41
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,D'), # 0x42
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,E'), # 0x43
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,H'), # 0x44
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,L'), # 0x45
            LR35902.Instruction(function=lambda s: s.bit_memory(0), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 0,(HL)'), # 0x46
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 0,A'), # 0x47
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,B'), # 0x48
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,C'), # 0x49
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,D'), # 0x4A
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,E'), # 0x4B
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,H'), # 0x4C
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,L'), # 0x4D
            LR35902.Instruction(function=lambda s: s.bit_memory(1), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 1,(HL)'), # 0x4E
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 1,A'), # 0x4F
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,B'), # 0x50
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,C'), # 0x51
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,D'), # 0x52
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,E'), # 0x53
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,H'), # 0x54
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,L'), # 0x55
            LR35902.Instruction(function=lambda s: s.bit_memory(2), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 2,(HL)'), # 0x56
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 2,A'), # 0x57
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,B'), # 0x58
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,C'), # 0x59
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,D'), # 0x5A
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,E'), # 0x5B
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,H'), # 0x5C
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,L'), # 0x5D
            LR35902.Instruction(function=lambda s: s.bit_memory(3), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 3,(HL)'), # 0x5E
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 3,A'), # 0x5F
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,B'), # 0x60
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,C'), # 0x61
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,D'), # 0x62
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,E'), # 0x63
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,H'), # 0x64
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,L'), # 0x65
            LR35902.Instruction(function=lambda s: s.bit_memory(4), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 4,(HL)'), # 0x66
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 4,A'), # 0x67
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,B'), # 0x68
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,C'), # 0x69
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,D'), # 0x6A
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,E'), # 0x6B
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,H'), # 0x6C
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,L'), # 0x6D
            LR35902.Instruction(function=lambda s: s.bit_memory(5), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 5,(HL)'), # 0x6E
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 5,A'), # 0x6F
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,B'), # 0x70
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,C'), # 0x71
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,D'), # 0x72
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,E'), # 0x73
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,H'), # 0x74
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,L'), # 0x75
            LR35902.Instruction(function=lambda s: s.bit_memory(6), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 6,(HL)'), # 0x76
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 6,B'), # 0x77
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_B, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,B'), # 0x78
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_C, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,C'), # 0x79
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_D, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,D'), # 0x7A
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_E, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,E'), # 0x7B
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_H, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,H'), # 0x7C
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_L, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,L'), # 0x7D
            LR35902.Instruction(function=lambda s: s.bit_memory(7), length_in_bytes=2, duration_in_cycles=16, mnemonic='BIT 7,(HL)'), # 0x7E
            LR35902.Instruction(function=lambda s: s.bit(LR35902.REGISTER_A, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='BIT 7,A'), # 0x7F
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,B'), # 0x80
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,C'), # 0x81
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,D'), # 0x82
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,E'), # 0x83
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,H'), # 0x84
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,L'), # 0x85
            LR35902.Instruction(function=lambda s: s.res_memory(0), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 0,(HL)'), # 0x86
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 0,A'), # 0x87
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,B'), # 0x88
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,C'), # 0x89
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,D'), # 0x8A
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,E'), # 0x8B
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,H'), # 0x8C
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,L'), # 0x8D
            LR35902.Instruction(function=lambda s: s.res_memory(1), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 1,(HL)'), # 0x8E
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 1,A'), # 0x8F
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,B'), # 0x90
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,C'), # 0x91
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,D'), # 0x92
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,E'), # 0x93
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,H'), # 0x94
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,L'), # 0x95
            LR35902.Instruction(function=lambda s: s.res_memory(2), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 2,(HL)'), # 0x96
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 2,A'), # 0x97
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,B'), # 0x98
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,C'), # 0x99
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,D'), # 0x9A
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,E'), # 0x9B
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,H'), # 0x9C
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,L'), # 0x9D
            LR35902.Instruction(function=lambda s: s.res_memory(3), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 3,(HL)'), # 0x9E
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 3,A'), # 0x9F
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,B'), # 0xA0
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,C'), # 0xA1
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,D'), # 0xA2
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,E'), # 0xA3
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,H'), # 0xA4
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,L'), # 0xA5
            LR35902.Instruction(function=lambda s: s.res_memory(4), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 4,(HL)'), # 0xA6
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 4,A'), # 0xA7
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,B'), # 0xA8
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,C'), # 0xA9
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,D'), # 0xAA
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,E'), # 0xAB
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,H'), # 0xAC
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,L'), # 0xAD
            LR35902.Instruction(function=lambda s: s.res_memory(5), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 5,(HL)'), # 0xAE
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 5,A'), # 0xAF
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,B'), # 0xB0
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,C'), # 0xB1
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,D'), # 0xB2
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,E'), # 0xB3
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,H'), # 0xB4
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,L'), # 0xB5
            LR35902.Instruction(function=lambda s: s.res_memory(6), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 6,(HL)'), # 0xB6
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 6,A'), # 0xB7
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_B, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,B'), # 0xB8
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_C, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,C'), # 0xB9
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_D, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,D'), # 0xBA
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_E, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,E'), # 0xBB
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_H, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,H'), # 0xBC
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_L, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,L'), # 0xBD
            LR35902.Instruction(function=lambda s: s.res_memory(7), length_in_bytes=2, duration_in_cycles=16, mnemonic='RES 7,(HL)'), # 0xBE
            LR35902.Instruction(function=lambda s: s.res(LR35902.REGISTER_A, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='RES 7,A'), # 0xBF
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,B'), # 0xC0
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,C'), # 0xC1
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,D'), # 0xC2
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,E'), # 0xC3
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,H'), # 0xC4
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,L'), # 0xC5
            LR35902.Instruction(function=lambda s: s.set_memory(0), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 0,(HL)'), # 0xC6
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 0), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 0,A'), # 0xC7
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,B'), # 0xC8
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,C'), # 0xC9
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,D'), # 0xCA
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,E'), # 0xCB
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,H'), # 0xCC
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,L'), # 0xCD
            LR35902.Instruction(function=lambda s: s.set_memory(1), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 1,(HL)'), # 0xCE
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 1), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 1,A'), # 0xCF
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,B'), # 0xD0
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,C'), # 0xD1
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,D'), # 0xD2
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,E'), # 0xD3
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,H'), # 0xD4
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,L'), # 0xD5
            LR35902.Instruction(function=lambda s: s.set_memory(2), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 2,(HL)'), # 0xD6
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 2), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 2,A'), # 0xD7
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,B'), # 0xD8
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,C'), # 0xD9
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,D'), # 0xDA
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,E'), # 0xDB
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,H'), # 0xDC
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,L'), # 0xDD
            LR35902.Instruction(function=lambda s: s.set_memory(3), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 3,(HL)'), # 0xDE
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 3), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 3,A'), # 0xDF
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,B'), # 0xE0
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,C'), # 0xE1
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,D'), # 0xE2
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,E'), # 0xE3
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,H'), # 0xE4
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,L'), # 0xE5
            LR35902.Instruction(function=lambda s: s.set_memory(4), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 4,(HL)'), # 0xE6
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 4), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 4,A'), # 0xE7
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,B'), # 0xE8
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,C'), # 0xE9
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,D'), # 0xEA
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,E'), # 0xEB
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,H'), # 0xEC
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,L'), # 0xED
            LR35902.Instruction(function=lambda s: s.set_memory(5), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 5,(HL)'), # 0xEE
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 5), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 5,A'), # 0xEF
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,B'), # 0xF0
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,C'), # 0xF1
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,D'), # 0xF2
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,E'), # 0xF3
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,H'), # 0xF4
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,L'), # 0xF5
            LR35902.Instruction(function=lambda s: s.set_memory(6), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 6,(HL)'), # 0xF6
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 6), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 6,A'), # 0xF7
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_B, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,B'), # 0xF8
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_C, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,C'), # 0xF9
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_D, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,D'), # 0xFA
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_E, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,E'), # 0xFB
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_H, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,H'), # 0xFC
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_L, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,L'), # 0xFD
            LR35902.Instruction(function=lambda s: s.set_memory(7), length_in_bytes=2, duration_in_cycles=16, mnemonic='SET 7,(HL)'), # 0xFE
            LR35902.Instruction(function=lambda s: s.set(LR35902.REGISTER_A, 7), length_in_bytes=2, duration_in_cycles=8, mnemonic='SET 7,A'), # 0xFF
        ]

    def set_zero(self, value):
        if value == 0:
            self.F |= (1 << LR35902.FLAG_Z)
        else:
            self.F &= ~(1 << LR35902.FLAG_Z)

    def set_flag(self, flag, value):
        if value == True:
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
        if (not self.state == LR35902.State.STOPPED) and self.interrupts["enabled"]:
            # Check if interrupts are enabled and requested
            enabled_and_requested = (
                self.memory[Memory.REGISTER_IE] & # Enabled
                self.memory[Memory.REGISTER_IF] # Requested
            )
            for interrupt in range(5):
                if enabled_and_requested & (1 << interrupt):
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

                    self.state = LR35902.State.RUNNING # CPU running again

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
            self.SP = (val_h << 8) | val_l
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

    def push_nn(self, reg=None):
        """GBCPUman.pdf page 78
        Opcodes 0xC5, 0xD5, 0xE5, 0xF5
        Push register pair onto stack.
        Decrement SP twice.
        TODO: Keeping lower byte at lower address. Verify this is correct.
        """
        self.SP -= 2

        if reg == LR35902.REGISTER_BC:
            self.memory[self.SP + 1] = self.B
            self.memory[self.SP] = self.C
        elif reg == LR35902.REGISTER_DE:
            self.memory[self.SP + 1] = self.D
            self.memory[self.SP] = self.E
        elif reg == LR35902.REGISTER_HL:
            self.memory[self.SP + 1] = self.H
            self.memory[self.SP] = self.L
        elif reg == LR35902.REGISTER_AF:
            self.memory[self.SP + 1] = self.A
            self.memory[self.SP] = self.F
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

    def pop_nn(self, reg=None):
        """GBCPUman.pdf page 79
        Opcodes 0xC1, 0xD1, 0xE1, 0xF1
        Pop two bytes off of stack into register pair
        Increment SP twice.
        """
        if reg == LR35902.REGISTER_BC:
            self.B = self.memory[self.SP + 1]
            self.C = self.memory[self.SP]
        elif reg == LR35902.REGISTER_DE:
            self.D = self.memory[self.SP + 1]
            self.E = self.memory[self.SP]
        elif reg == LR35902.REGISTER_HL:
            self.H = self.memory[self.SP + 1]
            self.L = self.memory[self.SP]
        elif reg == LR35902.REGISTER_AF:
            self.A = self.memory[self.SP + 1]
            self.F = self.memory[self.SP] & 0xF0 # Lower 4 bytes of can never be 1
        else:
            raise RuntimeError('Invalid register "{}" specified!'.format(reg))

        self.SP += 2

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
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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

        carry_bit = (self.F & (1 << LR35902.FLAG_C)) >> LR35902.FLAG_C

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def adc_a_n_memory(self):
        """GBCPUman.pdf page 81
        Opcodes 0x8E
        Add value from memory at location HL and carry bit to register A and store it in register A.
        """

        addr = (self.H << 8) | self.L
        addend = self.memory[addr]

        carry_bit = (self.F & (1 << LR35902.FLAG_C)) >> LR35902.FLAG_C

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def adc_a_n_immediate(self):
        """GBCPUman.pdf page 81
        Opcodes 0xCE
        Add immediate byte and carry bit to register A and store it in register A.
        """

        addend = self.memory[self.PC + 1]

        carry_bit = (self.F & (1 << LR35902.FLAG_C)) >> LR35902.FLAG_C

        new_flags = 0

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = (1 << LR35902.FLAG_N)

        # Process half borrow
        if (self.A & 0xF) < (subtrahend & 0xF):
            new_flags |= (1 << LR35902.FLAG_H)

        # Process borrow
        if (self.A & 0xFF) < (subtrahend & 0xFF):
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = (1 << LR35902.FLAG_N)

        # Process half borrow
        if (self.A & 0xF) < (subtrahend & 0xF):
            new_flags |= (1 << LR35902.FLAG_H)

        # Process borrow
        if (self.A & 0xFF) < (subtrahend & 0xFF):
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def sub_n_immediate(self):
        """GBCPUman.pdf page 82
        Opcodes 0xD6
        Subtract immediate byte from register A.
        """

        subtrahend = self.memory[self.PC + 1]

        # N is always set
        new_flags = (1 << LR35902.FLAG_N)

        # Process half borrow
        if (self.A & 0xF) < (subtrahend & 0xF):
            new_flags |= (1 << LR35902.FLAG_H)

        # Process borrow
        if (self.A & 0xFF) < (subtrahend & 0xFF):
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform subtraction
        self.A = (self.A - subtrahend) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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

        carry_bit = (self.F & (1 << LR35902.FLAG_C)) >> LR35902.FLAG_C

        # N is always set
        new_flags = (1 << LR35902.FLAG_N)

        # Twos complement operands
        addend = (~subtrahend + 1) & 0xFF
        carry_bit = (~carry_bit + 1) & 0xFF

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def subc_n_memory(self):
        """GBCPUman.pdf page 83
        Opcodes 0x9E
        Subtract value pointed to by register HL and carry bit from register A.
        """

        addr = (self.H << 8) | self.L
        subtrahend = self.memory[addr]

        carry_bit = (self.F & (1 << LR35902.FLAG_C)) >> LR35902.FLAG_C

        # N is always set
        new_flags = (1 << LR35902.FLAG_N)

        # Twos complement operands
        addend = (~subtrahend + 1) & 0xFF
        carry_bit = (~carry_bit + 1) & 0xFF

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def subc_n_immediate(self):
        """GBCPUman.pdf page 83
        Opcodes 0xDE
        Subtract immediate byte and carry bit from register A.
        Note: GBCPUman.pdf does not list an opcode for this, but pastraiser does.
        """

        subtrahend = self.memory[self.PC + 1]

        carry_bit = (self.F & (1 << LR35902.FLAG_C)) >> LR35902.FLAG_C

        # N is always set
        new_flags = (1 << LR35902.FLAG_N)

        # Twos complement operands
        addend = (~subtrahend + 1) & 0xFF
        carry_bit = (~carry_bit + 1) & 0xFF

        # Process half carry
        if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Process carry
        if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
            new_flags |= (1 << LR35902.FLAG_C)

        # Perform addition
        self.A = (self.A + addend + carry_bit) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = (1 << LR35902.FLAG_H)

        # Perform arithmetic
        self.A = (self.A & operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = (1 << LR35902.FLAG_H)

        # Perform arithmetic
        self.A = (self.A & operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def and_n_immediate(self):
        """GBCPUman.pdf page 84
        Opcodes 0xE6
        And immediate byte with A and store it in A
        """

        operand = self.memory[self.PC + 1]

        # H is always set
        new_flags = (1 << LR35902.FLAG_H)

        # Perform arithmetic
        self.A = (self.A & operand) & 0xFF

        # Process zero
        if self.A == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def cp_n_register(self, reg=None):
        """GBCPUman.pdf page 87
        Opcodes 0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBF
        Compare register reg with register A.
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
        new_flags = (1 << LR35902.FLAG_N)

        # Process half borrow
        if (self.A & 0xF) < (operand & 0xF):
            new_flags |= (1 << LR35902.FLAG_H)

        # Process borrow
        if (self.A & 0xFF) < (operand & 0xFF):
            new_flags |= (1 << LR35902.FLAG_C)

        # Process equals
        if self.A == operand:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = (1 << LR35902.FLAG_N)

        # Process half borrow
        if (self.A & 0xF) < (operand & 0xF):
            new_flags |= (1 << LR35902.FLAG_H)

        # Process borrow
        if (self.A & 0xFF) < (operand & 0xFF):
            new_flags |= (1 << LR35902.FLAG_C)

        # Process equals
        if self.A == operand:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def cp_n_immediate(self):
        """GBCPUman.pdf page 87
        Opcodes 0xFE
        Compare immediate byte with register A.
        """

        operand = self.memory[self.PC + 1]

        # N is always set
        new_flags = (1 << LR35902.FLAG_N)

        # Process half borrow
        if (self.A & 0xF) < (operand & 0xF):
            new_flags |= (1 << LR35902.FLAG_H)

        # Process borrow
        if (self.A & 0xFF) < (operand & 0xFF):
            new_flags |= (1 << LR35902.FLAG_C)

        # Process equals
        if self.A == operand:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = 0 | (self.F & (1 << LR35902.FLAG_C))

        # Process half carry
        if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Perform increment
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) + 1) & 0xFF
        )

        # Process zero
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def inc_n_memory(self):
        """GBCPUman.pdf page 88
        Opcodes 0x34
        Increment value at memory location HL
        """

        addr = (self.H << 8) | self.L

        # Keep C flag
        new_flags = 0 | (self.F & (1 << LR35902.FLAG_C))

        # Process half carry
        if ((self.memory[addr] & 0xF) + 1) & 0x10:
            new_flags |= (1 << LR35902.FLAG_H)

        # Perform addition
        self.memory[addr] = (self.memory[addr] + 1) & 0xFF

        # Process zero
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
        new_flags = 0 | (self.F & (1 << LR35902.FLAG_C))

        # Set N Flag
        new_flags |= (1 << LR35902.FLAG_N)

        # Process half carry
        if getattr(self, reg_attr) & 0xF == 0:
            new_flags |= (1 << LR35902.FLAG_H)

        # Perform decrement
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) - 1) & 0xFF
        )

        # Process zero
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

    def dec_n_memory(self):
        """GBCPUman.pdf page 89
        Opcodes 0x35
        Decrement value at memory location HL
        """

        addr = (self.H << 8) | self.L

        # Keep C flag
        new_flags = 0 | (self.F & (1 << LR35902.FLAG_C))

        # Set N Flag
        new_flags |= (1 << LR35902.FLAG_N)

        # Process half carry
        if self.memory[addr] & 0xF == 0:
            new_flags |= (1 << LR35902.FLAG_H)

        # Perform decrement
        self.memory[addr] = (self.memory[addr] - 1) & 0xFF

        # Process zero
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

        # Set Flags
        self.F = new_flags

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

        if (self.F >> LR35902.FLAG_N) & 1 == 0:
            # Last operation was an additon
            if ((self.F >> LR35902.FLAG_C) & 1) or self.A > 0x99:
                self.A += 0x60
                self.set_flag(LR35902.FLAG_C, True)

            if ((self.F >> LR35902.FLAG_H) & 1) or (self.A & 0xF) > 0x9:
                self.A += 0x6
        else:
            # Last operation was a subtraction
            if ((self.F >> LR35902.FLAG_C) & 1):
                self.A -= 0x60
            if ((self.F >> LR35902.FLAG_H) & 1):
                self.A -= 0x06

        self.set_zero(self.A)
        self.set_flag(LR35902.FLAG_H, False)

    def cpl(self):
        """GBCPUman.pdf page 95
        Opcode 0x2F
        Complement (flip all bits) in A register
        """

        self.A = (~self.A) & 0xFF

        self.set_flag(LR35902.FLAG_N, True)
        self.set_flag(LR35902.FLAG_H, True)

    def ccf(self):
        """GBCPUman.pdf page 96
        Opcode 0x3F
        Complement carry flag
        """

        self.set_flag(LR35902.FLAG_N, False)
        self.set_flag(LR35902.FLAG_H, False)
        self.set_flag(LR35902.FLAG_C, ((self.F >> LR35902.FLAG_C) & 1) == 0)

    def scf(self):
        """GBCPUman.pdf page 96
        Opcode 0x37
        Set carry flag
        """

        self.set_flag(LR35902.FLAG_N, False)
        self.set_flag(LR35902.FLAG_H, False)
        self.set_flag(LR35902.FLAG_C, True)

    def nop(self):
        """GBCPUman.pdf page 97
        Opcode 0x00
        Do nothing
        """
        pass

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
            self.F |= (1 << LR35902.FLAG_C)

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
            self.F |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Rotate
        self.memory[addr] = ((self.memory[addr] << 1) & 0xFE) | ((self.memory[addr] & 0x80) >> 7)

        # Set Z flag if 0
        if self.memory[addr] == 0:
            self.F |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_C)

        # Rotate
        setattr(
            self,
            reg_attr,
            ((getattr(self, reg_attr) << 1) & 0xFE)
        )

        # Old carry flag to bit 0
        if self.F & (1 << LR35902.FLAG_C):
            setattr(
                self,
                reg_attr,
                getattr(self, reg_attr) | 1
            )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_C)

        # Rotate
        self.memory[addr] = (self.memory[addr] << 1) & 0xFE

        # Old carry flag to bit 0
        if self.F & (1 << LR35902.FLAG_C):
            self.memory[addr] |= 1

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

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
            self.F |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Rotate
        self.memory[addr] = ((self.memory[addr] >> 1) & 0x7F) | ((self.memory[addr] & 0x01) << 7)

        # Set Z flag if 0
        if self.memory[addr] == 0:
            self.F |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_C)

        # Rotate
        setattr(
            self,
            reg_attr,
            ((getattr(self, reg_attr) >> 1) & 0x7F)
        )

        # Old carry flag to bit 7
        if self.F & (1 << LR35902.FLAG_C):
            setattr(
                self,
                reg_attr,
                getattr(self, reg_attr) | 0x80
            )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            new_flags |= (1 << LR35902.FLAG_C)

        # Rotate
        self.memory[addr] = (self.memory[addr] >> 1) & 0x7F

        # Old carry flag to bit 7
        if self.F & (1 << LR35902.FLAG_C):
            self.memory[addr] |= 0x80

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Shift left
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) << 1) & 0xFE
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Shift left
        self.memory[addr] = (self.memory[addr] << 1) & 0xFE

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Shift Right
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) & 0x80) |
            (getattr(self, reg_attr) >> 1) & 0x7F
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Shift Right
        self.memory[addr] = (self.memory[addr] & 0x80) | (self.memory[addr] >> 1) & 0x7F

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Shift Right
        setattr(
            self,
            reg_attr,
            (getattr(self, reg_attr) >> 1) & 0x7F
        )

        # Set Z flag if 0
        if getattr(self, reg_attr) == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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
            self.F |= (1 << LR35902.FLAG_C)

        # Shift Right
        self.memory[addr] = (self.memory[addr] >> 1) & 0x7F

        # Set Z flag if 0
        if self.memory[addr] == 0:
            new_flags |= (1 << LR35902.FLAG_Z)

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

        self.set_flag(LR35902.FLAG_N, False)
        self.set_flag(LR35902.FLAG_H, True)
        self.set_flag(LR35902.FLAG_Z, not (getattr(self, reg_attr) & (1 << bit)))

    def bit_memory(self, bit=None):
        """GBCPUman.pdf page 108
        0xCB Opcodes 0x46, 0x4E, 0x56, 0x5E, 0x66, 0x6E, 0x76, 0x7E
        Test bit in value stored at HL
        """
        addr = (self.H << 8) | self.L

        self.set_flag(LR35902.FLAG_N, False)
        self.set_flag(LR35902.FLAG_H, True)
        self.set_flag(LR35902.FLAG_Z, not (self.memory[addr] & (1 << bit)))

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
            test = not (self.F & (1 << LR35902.FLAG_Z))
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << LR35902.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not (self.F & (1 << LR35902.FLAG_C))
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << LR35902.FLAG_C)
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
            test = not (self.F & (1 << LR35902.FLAG_Z))
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << LR35902.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not (self.F & (1 << LR35902.FLAG_C))
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << LR35902.FLAG_C)
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
            test = not (self.F & (1 << LR35902.FLAG_Z))
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << LR35902.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not (self.F & (1 << LR35902.FLAG_C))
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << LR35902.FLAG_C)
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
            test = not (self.F & (1 << LR35902.FLAG_Z))
        elif condition == LR35902.CONDITION_Z:
            test = self.F & (1 << LR35902.FLAG_Z)
        elif condition == LR35902.CONDITION_NC:
            test = not (self.F & (1 << LR35902.FLAG_C))
        elif condition == LR35902.CONDITION_C:
            test = self.F & (1 << LR35902.FLAG_C)
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
