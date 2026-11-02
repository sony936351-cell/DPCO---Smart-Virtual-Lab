def validate_bit(value):
    value = int(value)

    if value not in (0, 1):
        raise ValueError("Input must be 0 or 1.")

    return value


def logic_gate(gate, a, b=None):

    a = validate_bit(a)

    if gate == "NOT":
        return 1 - a

    b = validate_bit(b)

    gates = {

        "AND": a & b,

        "OR": a | b,

        "XOR": a ^ b,

        "NAND": 1 - (a & b),

        "NOR": 1 - (a | b),

        "XNOR": 1 - (a ^ b)

    }

    if gate not in gates:
        raise ValueError("Unsupported logic gate.")

    return gates[gate]


def truth_table(gate):

    gate = gate.upper()

    if gate == "NOT":

        return [
            {"a": 0, "output": 1},
            {"a": 1, "output": 0}
        ]

    rows = []

    for a in (0, 1):

        for b in (0, 1):

            rows.append({

                "a": a,

                "b": b,

                "output": logic_gate(gate, a, b)

            })

    return rows


def adder(a, b, adder_type="half"):

    a = validate_bit(a)
    b = validate_bit(b)

    if adder_type == "half":

        total = a + b

        return {

            "sum": total % 2,

            "carry": total // 2

        }

    if adder_type == "full":

        carry_in = 0

        total = a + b + carry_in

        return {

            "sum": total % 2,

            "carry": total // 2

        }

    raise ValueError("Adder type must be half or full.")


def binary_convert(number, bits=8):

    bits = int(bits)

    if bits < 1 or bits > 32:
        raise ValueError("Bits must be between 1 and 32.")

    minimum = -(2 ** (bits - 1))
    maximum = (2 ** bits) - 1

    if number < minimum or number > maximum:
        raise ValueError("Number is outside the selected bit range.")

    binary = format(number & ((1 << bits) - 1), f"0{bits}b")

    return {

        "decimal": number,

        "binary": binary,

        "hexadecimal": format(
            number & ((1 << bits) - 1),
            "X"
        ),

        "octal": format(
            number & ((1 << bits) - 1),
            "o"
        ),

        "bits": bits

    }


def alu_operation(operation, a, b, bits=8):

    operation = operation.upper()

    bits = int(bits)

    if bits < 1 or bits > 32:
        raise ValueError("Bits must be between 1 and 32.")

    mask = (1 << bits) - 1

    operations = {

        "ADD": lambda: a + b,

        "SUB": lambda: a - b,

        "AND": lambda: a & b,

        "OR": lambda: a | b,

        "XOR": lambda: a ^ b,

        "NOT": lambda: ~a,

        "SHL": lambda: a << 1,

        "SHR": lambda: a >> 1

    }

    if operation not in operations:
        raise ValueError("Unsupported ALU operation.")

    raw_result = operations[operation]()

    result = raw_result & mask

    return {

        "operation": operation,

        "a": a,

        "b": b,

        "result": result,

        "binary": format(result, f"0{bits}b"),

        "carry": int(raw_result > mask),

        "zero": int(result == 0),

        "negative": int(bool(result & (1 << (bits - 1)))),

        "bits": bits

    }


class Memory:

    def __init__(self, size=16):

        self.size = size

        self.cells = [0] * size

    def check_address(self, address):

        if address < 0 or address >= self.size:
            raise ValueError("Invalid memory address.")

    def read(self, address):

        self.check_address(address)

        return {

            "address": address,

            "value": self.cells[address]

        }

    def write(self, address, value):

        self.check_address(address)

        if value < 0:
            raise ValueError("Memory value cannot be negative.")

        self.cells[address] = value

    def dump(self):

        return [

            {

                "address": index,

                "value": value

            }

            for index, value in enumerate(self.cells)

        ]


class CacheSimulator:

    def __init__(self, lines=4, block_size=1):

        self.lines = lines

        self.block_size = block_size

        self.cache = {}

        self.hits = 0

        self.misses = 0

    def access(self, address, operation="READ", value=0):

        if address < 0:
            raise ValueError("Address cannot be negative.")

        operation = operation.upper()

        if operation not in ("READ", "WRITE"):
            raise ValueError("Operation must be READ or WRITE.")

        block = address // self.block_size

        slot = block % self.lines

        hit = slot in self.cache and self.cache[slot]["block"] == block

        if hit:
            self.hits += 1
        else:
            self.misses += 1

        if not hit:

            self.cache[slot] = {

                "block": block,

                "value": 0

            }

        if operation == "WRITE":

            self.cache[slot]["value"] = value

        return {

            "address": address,

            "operation": operation,

            "hit": hit,

            "slot": slot,

            "value": self.cache[slot]["value"]

        }

    def stats(self):

        total = self.hits + self.misses

        return {

            "hits": self.hits,

            "misses": self.misses,

            "total": total,

            "hit_rate": round(
                self.hits / total * 100,
                2
            ) if total else 0

        }

    def dump(self):

        return [

            {

                "slot": slot,

                "block": self.cache.get(slot, {}).get("block"),

                "value": self.cache.get(slot, {}).get("value")

            }

            for slot in range(self.lines)

        ]


class CPU:

    def __init__(self):

        self.registers = {

            "R0": 0,

            "R1": 0,

            "R2": 0,

            "R3": 0

        }

        self.pc = 0

        self.acc = 0

        self.log = []

    def execute(self, instruction):

        parts = instruction.strip().upper().split()

        if not parts:
            return

        opcode = parts[0]

        if opcode == "LOAD":

            register = parts[1]

            value = int(parts[2])

            self.registers[register] = value

        elif opcode == "ADD":

            register = parts[1]

            self.acc += self.registers[register]

        elif opcode == "SUB":

            register = parts[1]

            self.acc -= self.registers[register]

        elif opcode == "STORE":

            register = parts[1]

            self.registers[register] = self.acc

        elif opcode == "MOV":

            destination = parts[1]

            source = parts[2]

            self.registers[destination] = self.registers[source]

        elif opcode == "INC":

            register = parts[1]

            self.registers[register] += 1

        elif opcode == "HALT":

            return "HALT"

        else:

            raise ValueError(
                f"Unknown instruction: {opcode}"
            )

        self.log.append({

            "pc": self.pc,

            "instruction": instruction,

            "registers": self.registers.copy(),

            "acc": self.acc

        })

        self.pc += 1

    def run_text(self, program):

        self.__init__()

        instructions = [

            line.strip()

            for line in program.splitlines()

            if line.strip()

        ]

        for instruction in instructions:

            result = self.execute(instruction)

            if result == "HALT":
                break

        return {

            "registers": self.registers,

            "acc": self.acc,

            "pc": self.pc,

            "log": self.log

        }