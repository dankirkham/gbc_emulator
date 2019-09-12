import cmd
from gbc_emulator.lr35902 import LR35902

class Debugger(cmd.Cmd):
    prompt = '(dgbdb) '

    def __init__(self, cpu):
        super(Debugger, self).__init__()

        self.breakpoints = []
        self.cpu = cpu

        self.cpu.debugger = self

    def do_bp(self, arg):
        'Add breakpoint.'
        bp = int(arg, 0)
        if bp not in self.breakpoints:
            self.breakpoints.append(bp)
            print('Added breakpoint {}.'.format(hex(bp)))
        else:
            print('Breakpoint {} already exists.'.format(hex(bp)))

    def do_bpd(self, arg):
        'Delete breakpoint.'

        bp = int(arg, 0)
        if bp in self.breakpoints:
            self.breakpoints.remove(bp)
            print('Removed breakpoint {}.'.format(hex(bp)))
        else:
            print('Breakpoint {} does not exist.'.format(hex(bp)))

    def do_bpl(self, arg):
        'List breakpoints.'
        for bp in self.breakpoints:
            print(hex(bp))

    def do_n(self, arg):
        'Run next instruction.'
        if self.cpu.wait == 0:
            info = self.cpu.clock()
        else:
            while self.cpu.wait != 0:
                self.cpu.clock()
            info = self.cpu.clock()

        if info == LR35902.BREAKPOINT_HIT:
            print("Breakpoint hit")

        self.do_p(None)

    def do_c(self, arg):
        'Continue to breakpoint.'
        while self.cpu.clock() != LR35902.BREAKPOINT_HIT:
            pass

        print("Breakpoint hit")
        self.do_p(None)

    def do_p(self, arg):
        'Print CPU state'
        instruction, opcode = self.cpu.fetch_and_decode()

        report = "Instruction: {}\nOpcode: {}".format(instruction.mnemonic, hex(opcode))
        if instruction.length_in_bytes == 2:
            report += "\nOperand: {}".format(hex(self.cpu.memory[self.cpu.PC + 1]))
        elif instruction.length_in_bytes == 3:
            val = self.cpu.memory[self.cpu.PC + 1] | (self.cpu.memory[self.cpu.PC + 2] << 8)
            report += "\nOperand: {}".format(hex(val))
        print(report)

        print("\nRegisters: ")
        print("AF: {}".format(hex((self.cpu.A << 8) | self.cpu.F)))
        print("BC: {}".format(hex((self.cpu.B << 8) | self.cpu.C)))
        print("DE: {}".format(hex((self.cpu.D << 8) | self.cpu.E)))
        print("HL: {}".format(hex((self.cpu.H << 8) | self.cpu.L)))
        print("SP: {}".format(hex(self.cpu.SP)))
        print("PC: {}".format(hex(self.cpu.PC)))

    def do_m(self, arg):
        'Print memory at address.'
        addr = int(arg, 0)
        print(hex(self.cpu.memory[addr]))

    def do_EOF(self, arg):
        return True
