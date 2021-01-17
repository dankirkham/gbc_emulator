from gbc_emulator.lr35902 import flags

# GBCPUman.pdf page 80
# Opcodes 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x87
# Add register to A and store it in A.

def add_a_a_register(self):
    addend = self.A

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def add_a_b_register(self):
    addend = self.B

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def add_a_c_register(self):
    addend = self.C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def add_a_d_register(self):
    addend = self.D

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def add_a_e_register(self):
    addend = self.E

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def add_a_h_register(self):
    addend = self.H

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def add_a_l_register(self):
    addend = self.L

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF)) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

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
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

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
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF)) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 81
# Opcodes 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8F
# Add register and carry bit to A and store it in A.

def adc_a_a_register(self):
    addend = self.A

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_b_register(self):
    addend = self.B

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_c_register(self):
    addend = self.C

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_d_register(self):
    addend = self.D

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_e_register(self):
    addend = self.E

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_h_register(self):
    addend = self.H

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_l_register(self):
    addend = self.L

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) > 0xF:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if (self.A + addend + carry_bit) > 0xFF:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_n_memory(self):
    """GBCPUman.pdf page 81
    Opcodes 0x8E
    Add value from memory at location HL and carry bit to register A and store it in register A.
    """

    addr = (self.H << 8) | self.L
    addend = self.memory[addr]

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def adc_a_n_immediate(self):
    """GBCPUman.pdf page 81
    Opcodes 0xCE
    Add immediate byte and carry bit to register A and store it in register A.
    """

    addend = self.memory[self.PC + 1]

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    new_flags = 0

    # Process half carry
    if ((self.A & 0xF) + (addend & 0xF) + carry_bit) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if ((self.A & 0xFF) + (addend & 0xFF) + carry_bit) & 0x100:
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 82
# Opcodes 0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x97
# Subtract register reg from register A.
def sub_a_a_register(self):
    subtrahend = self.A

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_b_register(self):
    subtrahend = self.B

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_c_register(self):
    subtrahend = self.C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_d_register(self):
    subtrahend = self.D

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_e_register(self):
    subtrahend = self.E

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_h_register(self):
    subtrahend = self.H

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_l_register(self):
    subtrahend = self.L

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_a_n_memory(self):
    """GBCPUman.pdf page 82
    Opcodes 0x96
    Subtract value pointed to by register HL from register A.
    """

    addr = (self.H << 8) | self.L
    subtrahend = self.memory[addr]

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def sub_n_immediate(self):
    """GBCPUman.pdf page 82
    Opcodes 0xD6
    Subtract immediate byte from register A.
    """

    subtrahend = self.memory[self.PC + 1]

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (subtrahend & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (subtrahend & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Perform subtraction
    self.A = (self.A - subtrahend) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 83
# Opcodes 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9F
# Subtract register reg and carry bit from register A.

def subc_a_a_register(self):
    subtrahend = self.A

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_b_register(self):
    subtrahend = self.B

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_c_register(self):
    subtrahend = self.C

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_d_register(self):
    subtrahend = self.D

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_e_register(self):
    subtrahend = self.E

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_h_register(self):
    subtrahend = self.H

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_l_register(self):
    subtrahend = self.L

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_n_memory(self):
    """GBCPUman.pdf page 83
    Opcodes 0x9E
    Subtract value pointed to by register HL and carry bit from register A.
    """

    addr = (self.H << 8) | self.L
    subtrahend = self.memory[addr]

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def subc_a_immediate(self):
    """GBCPUman.pdf page 83
    Opcodes 0xDE
    Subtract immediate byte and carry bit from register A.
    Note: GBCPUman.pdf does not list an opcode for this, but pastraiser does.
    """

    subtrahend = self.memory[self.PC + 1]

    carry_bit = (self.F & (1 << flags.FLAG_C)) >> flags.FLAG_C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Twos complement operands
    addend = (~subtrahend + 1) & 0xFF
    neg_carry_bit = (~carry_bit + 1) & 0xFF

    # Process half carry
    if (self.A & 0xF) < ((subtrahend & 0xF) + (carry_bit & 0xF)):
        new_flags |= (1 << flags.FLAG_H)

    # Process carry
    if self.A < (subtrahend + carry_bit):
        new_flags |= (1 << flags.FLAG_C)

    # Perform addition
    self.A = (self.A + addend + neg_carry_bit) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 84
# Opcodes 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA7
# And register reg with A and store it in A.

def and_a_a_register(self):
    operand = self.A

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_b_register(self):
    operand = self.B

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_c_register(self):
    operand = self.C

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_d_register(self):
    operand = self.D

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_e_register(self):
    operand = self.E

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_h_register(self):
    operand = self.H

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_l_register(self):
    operand = self.L

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_a_n_memory(self):
    """GBCPUman.pdf page 84
    Opcodes 0xA6
    And value pointed to by register HL with A and store it in A
    """

    addr = (self.H << 8) | self.L
    operand = self.memory[addr]

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def and_n_immediate(self):
    """GBCPUman.pdf page 84
    Opcodes 0xE6
    And immediate byte with A and store it in A
    """

    operand = self.memory[self.PC + 1]

    # H is always set
    new_flags = (1 << flags.FLAG_H)

    # Perform arithmetic
    self.A = (self.A & operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 85
# Opcodes 0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB7
# OR register reg with A and store it in A.

def or_a_a_register(self):
    operand = self.A

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def or_a_b_register(self):
    operand = self.B

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def or_a_c_register(self):
    operand = self.C

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def or_a_d_register(self):
    operand = self.D

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def or_a_e_register(self):
    operand = self.E

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def or_a_h_register(self):
    operand = self.H

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def or_a_l_register(self):
    operand = self.L

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A | operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

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
        new_flags |= (1 << flags.FLAG_Z)

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
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 86
# Opcodes 0xA8, 0xA9, 0xAA, 0xAB, 0xAC, 0xAD, 0xAF
# XOR register reg with A and store it in A.

def xor_a_a_register(self):
    operand = self.A

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def xor_a_b_register(self):
    operand = self.B

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def xor_a_c_register(self):
    operand = self.C

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def xor_a_d_register(self):
    operand = self.D

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def xor_a_e_register(self):
    operand = self.E

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def xor_a_h_register(self):
    operand = self.H

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def xor_a_l_register(self):
    operand = self.L

    # Clear all flags
    new_flags = 0

    # Perform arithmetic
    self.A = (self.A ^ operand) & 0xFF

    # Process zero
    if self.A == 0:
        new_flags |= (1 << flags.FLAG_Z)

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
        new_flags |= (1 << flags.FLAG_Z)

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
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 87
# Opcodes 0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBF
# Compare register reg with register A.

def cp_a_a_register(self):
    operand = self.A

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_a_b_register(self):
    operand = self.B

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_a_c_register(self):
    operand = self.C

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_a_d_register(self):
    operand = self.D

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_a_e_register(self):
    operand = self.E

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_a_h_register(self):
    operand = self.H

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_a_l_register(self):
    operand = self.L

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

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
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def cp_n_immediate(self):
    """GBCPUman.pdf page 87
    Opcodes 0xFE
    Compare immediate byte with register A.
    """

    operand = self.memory[self.PC + 1]

    # N is always set
    new_flags = (1 << flags.FLAG_N)

    # Process half borrow
    if (self.A & 0xF) < (operand & 0xF):
        new_flags |= (1 << flags.FLAG_H)

    # Process borrow
    if (self.A & 0xFF) < (operand & 0xFF):
        new_flags |= (1 << flags.FLAG_C)

    # Process equals
    if self.A == operand:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 88
# Opcodes 0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x3C
# Increment register reg

def inc_a_register(self):
    reg_attr = 'A'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_b_register(self):
    reg_attr = 'B'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_c_register(self):
    reg_attr = 'C'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_d_register(self):
    reg_attr = 'D'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_e_register(self):
    reg_attr = 'E'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_h_register(self):
    reg_attr = 'H'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_l_register(self):
    reg_attr = 'L'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((getattr(self, reg_attr) & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform increment
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) + 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def inc_n_memory(self):
    """GBCPUman.pdf page 88
    Opcodes 0x34
    Increment value at memory location HL
    """

    addr = (self.H << 8) | self.L

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Process half carry
    if ((self.memory[addr] & 0xF) + 1) & 0x10:
        new_flags |= (1 << flags.FLAG_H)

    # Perform addition
    self.memory[addr] = (self.memory[addr] + 1) & 0xFF

    # Process zero
    if self.memory[addr] == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

# GBCPUman.pdf page 89
# Opcodes 0x05, 0x0D, 0x15, 0x1D, 0x25, 0x2D, 0x3D
# Decrement register reg

def dec_a_register(self):
    reg_attr = 'A'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_b_register(self):
    reg_attr = 'B'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_c_register(self):
    reg_attr = 'C'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_d_register(self):
    reg_attr = 'D'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_e_register(self):
    reg_attr = 'E'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_h_register(self):
    reg_attr = 'H'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_l_register(self):
    reg_attr = 'L'

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if getattr(self, reg_attr) & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    setattr(
        self,
        reg_attr,
        (getattr(self, reg_attr) - 1) & 0xFF
    )

    # Process zero
    if getattr(self, reg_attr) == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags

def dec_n_memory(self):
    """GBCPUman.pdf page 89
    Opcodes 0x35
    Decrement value at memory location HL
    """

    addr = (self.H << 8) | self.L

    # Keep C flag
    new_flags = 0 | (self.F & (1 << flags.FLAG_C))

    # Set N Flag
    new_flags |= (1 << flags.FLAG_N)

    # Process half carry
    if self.memory[addr] & 0xF == 0:
        new_flags |= (1 << flags.FLAG_H)

    # Perform decrement
    self.memory[addr] = (self.memory[addr] - 1) & 0xFF

    # Process zero
    if self.memory[addr] == 0:
        new_flags |= (1 << flags.FLAG_Z)

    # Set Flags
    self.F = new_flags
