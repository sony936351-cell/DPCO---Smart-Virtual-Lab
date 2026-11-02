import unittest

from logic_engine import (
    logic_gate,
    truth_table,
    binary_convert,
    adder,
    alu_operation,
    Memory,
    CacheSimulator,
    CPU
)


class TestDigitalLogic(unittest.TestCase):

    def test_and_gate(self):
        self.assertEqual(logic_gate("AND", 1, 1), 1)
        self.assertEqual(logic_gate("AND", 1, 0), 0)

    def test_or_gate(self):
        self.assertEqual(logic_gate("OR", 0, 0), 0)
        self.assertEqual(logic_gate("OR", 1, 0), 1)

    def test_not_gate(self):
        self.assertEqual(logic_gate("NOT", 0), 1)
        self.assertEqual(logic_gate("NOT", 1), 0)

    def test_xor_gate(self):
        self.assertEqual(logic_gate("XOR", 0, 1), 1)
        self.assertEqual(logic_gate("XOR", 1, 1), 0)

    def test_truth_table(self):
        table = truth_table("AND")
        self.assertEqual(len(table), 4)
        self.assertEqual(table[0]["output"], 0)
        self.assertEqual(table[3]["output"], 1)

    def test_invalid_logic_input(self):
        with self.assertRaises(ValueError):
            logic_gate("AND", 2, 1)


class TestAdder(unittest.TestCase):

    def test_half_adder(self):
        result = adder(1, 1, "half")

        self.assertEqual(result["sum"], 0)
        self.assertEqual(result["carry"], 1)

    def test_full_adder(self):
        result = adder(1, 0, "full")

        self.assertEqual(result["sum"], 1)
        self.assertEqual(result["carry"], 0)


class TestBinaryConverter(unittest.TestCase):

    def test_binary_conversion(self):
        result = binary_convert(10, 8)

        self.assertEqual(result["binary"], "00001010")
        self.assertEqual(result["hexadecimal"], "A")
        self.assertEqual(result["octal"], "12")

    def test_invalid_bit_width(self):
        with self.assertRaises(ValueError):
            binary_convert(10, 40)


class TestALU(unittest.TestCase):

    def test_addition(self):
        result = alu_operation("ADD", 10, 5, 8)

        self.assertEqual(result["result"], 15)
        self.assertEqual(result["zero"], 0)

    def test_subtraction(self):
        result = alu_operation("SUB", 10, 5, 8)

        self.assertEqual(result["result"], 5)

    def test_and_operation(self):
        result = alu_operation("AND", 12, 10, 8)

        self.assertEqual(result["result"], 8)

    def test_xor_operation(self):
        result = alu_operation("XOR", 12, 10, 8)

        self.assertEqual(result["result"], 6)


class TestMemory(unittest.TestCase):

    def test_memory_write_and_read(self):
        memory = Memory(16)

        memory.write(3, 100)

        result = memory.read(3)

        self.assertEqual(result["value"], 100)

    def test_memory_initial_value(self):
        memory = Memory(16)

        result = memory.read(0)

        self.assertEqual(result["value"], 0)

    def test_invalid_memory_address(self):
        memory = Memory(16)

        with self.assertRaises(ValueError):
            memory.read(20)


class TestCacheSimulator(unittest.TestCase):

    def test_cache_miss(self):
        cache = CacheSimulator(4, 1)

        result = cache.access(5, "READ")

        self.assertFalse(result["hit"])

    def test_cache_hit(self):
        cache = CacheSimulator(4, 1)

        cache.access(5, "READ")

        result = cache.access(5, "READ")

        self.assertTrue(result["hit"])

    def test_cache_statistics(self):
        cache = CacheSimulator(4, 1)

        cache.access(5, "READ")
        cache.access(5, "READ")

        stats = cache.stats()

        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 50.0)


class TestCPU(unittest.TestCase):

    def test_cpu_program(self):

        cpu = CPU()

        program = """
        LOAD R0 10
        LOAD R1 5
        ADD R0
        ADD R1
        STORE R2
        HALT
        """

        result = cpu.run_text(program)

        self.assertEqual(result["registers"]["R0"], 10)
        self.assertEqual(result["registers"]["R1"], 5)
        self.assertEqual(result["registers"]["R2"], 15)
        self.assertEqual(result["acc"], 15)

    def test_cpu_increment(self):

        cpu = CPU()

        program = """
        LOAD R0 5
        INC R0
        HALT
        """

        result = cpu.run_text(program)

        self.assertEqual(result["registers"]["R0"], 6)


if __name__ == "__main__":
    unittest.main()