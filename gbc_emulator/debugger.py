import cmd
from gbc_emulator.lr35902 import LR35902

class Debugger(cmd.Cmd):
    prompt = '(dgbdb) '

    def __init__(self, gameboy):
        """Create a debugger and attach to a gameboy."""
        super(Debugger, self).__init__()

        self.breakpoints = []
        self.gameboy = gameboy

        self.gameboy.cpu.debugger = self

        self.memory = self.gameboy.memory.audit_port # Use audit port

        self.stop = False

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
        cpu_result = self.gameboy.step()

        if cpu_result == LR35902.BREAKPOINT_HIT:
            print("Breakpoint hit")

        self.do_p(None)

    def do_c(self, arg):
        'Continue to breakpoint.'
        self.gameboy.run()

        print("Breakpoint hit")
        self.do_p(None)

    def do_p(self, arg):
        'Print CPU state'
        instruction, opcode = self.gameboy.cpu.fetch_and_decode()

        report = "Instruction: {}\nOpcode: {}".format(instruction.mnemonic, hex(opcode))
        if instruction.length_in_bytes == 2:
            report += "\nOperand: {}".format(hex(self.memory[self.gameboy.cpu.PC + 1]))
        elif instruction.length_in_bytes == 3:
            val = self.memory[self.gameboy.cpu.PC + 1] | (self.memory[self.gameboy.cpu.PC + 2] << 8)
            report += "\nOperand: {}".format(hex(val))
        print(report)

        print("\nRegisters: ")
        print("AF: {}".format(hex((self.gameboy.cpu.A << 8) | self.gameboy.cpu.F)))
        print("BC: {}".format(hex((self.gameboy.cpu.B << 8) | self.gameboy.cpu.C)))
        print("DE: {}".format(hex((self.gameboy.cpu.D << 8) | self.gameboy.cpu.E)))
        print("HL: {}".format(hex((self.gameboy.cpu.H << 8) | self.gameboy.cpu.L)))
        print("SP: {}".format(hex(self.gameboy.cpu.SP)))
        print("PC: {}".format(hex(self.gameboy.cpu.PC)))

    def do_m(self, arg):
        'Print memory at address.'
        addr = int(arg, 0)
        print(hex(self.memory[addr]))

    def do_EOF(self, arg):
        self.stop = True

        return True
