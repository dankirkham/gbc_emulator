from gbc_emulator.lr35902 import LR35902
import unittest


class TestLR35902(unittest.TestCase):
    def test_initialize(self):
        cpu = LR35902([])

    def test_clock(self):
        memory = [
            0xEA,
            0x00,
            0x00
        ]

        cpu = LR35902(memory)

        cpu.clock()

    def test_ld_a_n_from_memory_immediate(self):
        memory = [
            0xFA,
            0x53,
            0xCA
        ]

        cpu = LR35902(memory)

        cpu.clock()

        self.assertEquals(cpu.A, 0xCA53)
