import unittest
from gbc_emulator.lr35902 import LR35902


class TestLR35902(unittest.TestCase):
    def test_initialize(self):
        LR35902([])
        self.assertEqual(1, 1)

    def test_clock(self):
        memory = [0] * 0x10000
        new_memory = [
            0xEA,
            0x00,
            0x00
        ]

        # Assign new memory
        for val, i in enumerate(new_memory):
            memory[val] = i

        cpu = LR35902(memory)

        cpu.clock()
        self.assertEqual(1, 1)

    def test_ld_nn_n(self):
        memory = [0] * 0x10000
        new_memory = [
            0x06,
            0x53
        ]

        # Assign new memory
        for val, i in enumerate(new_memory):
            memory[val] = i

        cpu = LR35902(memory)

        cpu.clock()

        self.assertEqual(cpu.B, 0x53)

    def test_cb_swap(self):
        memory = [0] * 0x10000
        new_memory = [
            0x06,
            0x53,
            0xCB,
            0x30
        ]

        # Assign new memory
        for val, i in enumerate(new_memory):
            memory[val] = i

        cpu = LR35902(memory)

        for _ in range(4):
            cpu.clock()

        self.assertEqual(cpu.B, 0x35)

    def test_interrupt_toggle(self):
        memory = [0] * 0x10000
        new_memory = [
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

        # Assign new memory
        for val, i in enumerate(new_memory):
            memory[val] = i

        cpu = LR35902(memory)

        for _ in range(4):
            cpu.clock()
        self.assertFalse(cpu.interrupts['enabled'])

        for _ in range(1):
            cpu.clock()
        self.assertFalse(cpu.interrupts['enabled'])

        for _ in range(2):
            cpu.clock()
        self.assertTrue(cpu.interrupts['enabled'])

        for _ in range(1):
            cpu.clock()
        self.assertTrue(cpu.interrupts['enabled'])

        for _ in range(2):
            cpu.clock()
        self.assertFalse(cpu.interrupts['enabled'])
