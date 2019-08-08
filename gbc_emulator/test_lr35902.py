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

    def test_ld_nn_n(self):
        memory = [
            0x06,
            0x53
        ]

        cpu = LR35902(memory)

        cpu.clock()

        self.assertEqual(cpu.B, 0x53)

    def test_cb_swap(self):
        memory = [
            0x06,
            0x53,
            0xCB,
            0x30
        ]

        cpu = LR35902(memory)

        for _ in range(16):
            cpu.clock()

        self.assertEqual(cpu.B, 0x35)

    def test_interrupt_toggle(self):
        memory = [
            0x06, # 8
            0x53,
            0x06, # 8
            0x53,
            0xFB, # 4
            0x06, # 8
            0x53,
            0xF3, # 4
            0x06, # 8
            0x53
        ]

        cpu = LR35902(memory)

        for _ in range(16):
            cpu.clock()
        self.assertFalse(cpu.interrupts['enabled'])

        for _ in range(4):
            cpu.clock()
        self.assertFalse(cpu.interrupts['enabled'])

        for _ in range(8):
            cpu.clock()
        self.assertTrue(cpu.interrupts['enabled'])

        for _ in range(4):
            cpu.clock()
        self.assertTrue(cpu.interrupts['enabled'])

        for _ in range(8):
            cpu.clock()
        self.assertFalse(cpu.interrupts['enabled'])
