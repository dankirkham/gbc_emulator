from time import time, sleep
from collections import deque
from statistics import mean
from math import floor, ceil

STACK_DEPTH = 9

def hexp(s, length=4):
    s = hex(s)
    return s[2:].zfill(length)

def do_reporter(gameboy, mqtt):
    cpu = gameboy.cpu
    memory = gameboy.memory.audit_port

    last_time = time()
    # FRAME_PERIOD = 1 / 59.73
    FRAME_PERIOD = 1 / 5
    frame_times = deque()
    while 1:
        now = time()
        if not now >= (last_time + FRAME_PERIOD):
            sleep(0) # Release the GIL
        else:
            # Save frame time
            frame_times.append(now - last_time)
            if len(frame_times) > 5:
                frame_times.popleft()
            last_time = now

            fps = str(floor(1 / mean(frame_times)))

            registers = {
                "AF": hexp((cpu.A << 8) | cpu.F),
                "BC": hexp((cpu.B << 8) | cpu.C),
                "DE": hexp((cpu.D << 8) | cpu.E),
                "HL": hexp((cpu.H << 8) | cpu.L),
                "SP": hexp(cpu.SP),
                "PC": hexp(cpu.PC),
            }

            lower_bound = floor(STACK_DEPTH / 2)
            upper_bound = ceil(STACK_DEPTH / 2)

            if (cpu.SP + upper_bound) > 0x10000:
                center = 0xFFFF - upper_bound + 1
            elif (cpu.SP - lower_bound) < 0:
                center = lower_bound
            else:
                center = cpu.SP

            stack = []
            for address in range(center - lower_bound, center + upper_bound):
                stack.append((hexp(address), hexp(memory[address], 2)))

            lower_bound = floor(STACK_DEPTH / 2)
            upper_bound = ceil(STACK_DEPTH / 2)

            if (cpu.PC + upper_bound) > 0x10000:
                center = 0xFFFF - upper_bound + 1
            elif (cpu.PC - lower_bound) < 0:
                center = lower_bound
            else:
                center = cpu.PC

            program = []
            for address in range(center - lower_bound, center + upper_bound):
                program.append((hexp(address), hexp(memory[address], 2)))

            payload = {
                "fps": fps,
                "rate": gameboy.rate,
                "registers": registers,
                "stack": stack,
                "program": program
            }

            mqtt.publish("monitor", payload)
