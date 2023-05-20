# Notes:
#   - Need to read from a file and parse into a similar array (input instruction array)
#   - Reservation station and functional units have a 1-to-1 relationship
#   - Registers and Memory should be taken into account and implemented
#   - Validation of instructions provided should be handled. Ex: Register names and bounds should be valid & their format
#   - Simulating Clock Cycles are not yet implemented
#   - Number of execution cycles for each instruction should be input from the user
#   - Need to implement the load-store queue (probably)
#   - Need to consider flushing when using jal or ret
#   - Need to update the qj/k to none after writing an instruction

class ReservationStation:
    def __init__(self, index, name, op, busy=False, vj=None, vk=None, qj=None, qk=None, rd=None, offset=None, A=None):
        self.index = index
        self.name = name
        self.busy = busy
        self.op = op
        self.vj = vj
        self.vk = vk
        self.qj = qj
        self.qk = qk
        self.rd = rd
        self.offset = offset
        self.A = A
        self.result = None
        self.executed = False
        self.cycles_of_ex = None

    def __iter__(self):
        return self


class Tomasulo:
    def __init__(self, instructions, num_rs, instruction_cycles):
        self.inst_types = ["LOAD", "STORE", "BNE", "JAL",
                           "RET", "ADD", "ADDI", "NEG", "NAND", "SLL"]
        self.instructions = instructions
        self.instuction_cycles = instruction_cycles
        self.cdb = True
        self.num_rs = num_rs
        self.clock_cycles = 0
        # self.executed_cycles = 0
        self.RegFile = {
            "R0": 0,
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5,
            "R6": 6,
            "R7": 7
        }

        word_size = 4  # size in bytes
        address_size = 16  # address in bits
        memory_capacity = 128 * 1024  # Memory capacity in bytes
        num_words = memory_capacity // word_size  # Number of words in the memory

        # Create a list of words in the memory, initialized with zeros
        self.memory = [0] * num_words

        self.rs = {
            "LOAD": [None] * num_rs["LOAD"],
            "STORE": [None] * num_rs["STORE"],
            "BNE": [None] * num_rs["BNE"],
            "JAL": [None] * num_rs["JAL"],
            "RET": [None] * num_rs["RET"],
            "ADD": [None] * num_rs["ADD"],
            "ADDI": [None] * num_rs["ADDI"],
            "NEG": [None] * num_rs["NEG"],
            "NAND": [None] * num_rs["NAND"],
            "SLL": [None] * num_rs["SLL"]
        }
        # Set up the array of reservation stations for each instruction type
        for i in range(self.num_rs["LOAD"]):
            self.rs["LOAD"][i] = ReservationStation(i, f"LOAD{i+1}", "LOAD")

        for i in range(self.num_rs["STORE"]):
            self.rs["STORE"][i] = ReservationStation(i, f"STORE{i+1}", "STORE")

        for i in range(self.num_rs["BNE"]):
            self.rs["BNE"][i] = ReservationStation(i, f"BNE{i+1}", "BNE")

        for i in range(self.num_rs["JAL"]):
            self.rs["JAL"][i] = ReservationStation(i, f"JAL{i+1}", "JAL")

        for i in range(self.num_rs["RET"]):
            self.rs["RET"][i] = ReservationStation(i, f"RET{i+1}", "RET")

        for i in range(self.num_rs["ADD"]):
            self.rs["ADD"][i] = ReservationStation(i, f"ADD{i+1}", "ADD")

        for i in range(self.num_rs["ADDI"]):
            self.rs["ADDI"][i] = ReservationStation(i, f"ADDI{i+1}", "ADDI")

        for i in range(self.num_rs["NEG"]):
            self.rs["NEG"][i] = ReservationStation(i, f"NEG{i+1}", "NEG")

        for i in range(self.num_rs["NAND"]):
            self.rs["NAND"][i] = ReservationStation(i, f"NAND{i+1}", "NAND")

        for i in range(self.num_rs["SLL"]):
            self.rs["SLL"][i] = ReservationStation(i, f"SLL{i+1}", "SLL")

        # Status has the register name as key and its corresponding Qi --> set initially as none
        self.register_stat = {
            "R0": None,
            "R1": None,
            "R2": None,
            "R3": None,
            "R4": None,
            "R5": None,
            "R6": None,
            "R7": None
        }

    def fill_qj(self, operation, r, rs1):
        if (self.register_stat[rs1] != None):
            self.rs[operation][r].qj = self.register_stat.get(rs1)
        else:
            self.rs[operation][r].vj = self.RegFile[rs1]
            self.rs[operation][r].qj = None
        return

    def fill_qk(self, operation, r, rs2):
        if (self.register_stat[rs2] != None):
            self.rs[operation][r].qk = self.register_stat.get(rs2)
        else:
            self.rs[operation][r].vk = self.RegFile[rs2]
            self.rs[operation][r].qk = None
        return

    def fetch(self, pc):
        if pc < len(self.instructions):
            return self.instructions[pc]
        return None

    def issue(self, instruction):
        # For Tracing Purposes
        print("\nInstruction: ", instruction.get("op"), instruction.get(
            "rd"), instruction.get("rs1"), instruction.get("rs2"), "\n")

        # issued = False
        operation = instruction.get("op")

        if operation == "LOAD":
            rs1 = instruction.get("rs1")
            rd = instruction.get("rd")
            for r in range(self.num_rs[operation]):
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.rs[operation][r].rd = rd
                    self.register_stat[rd] = self.rs[operation][r].name
                    self.rs[operation][r].A = instruction.get("imm")
                    self.rs[operation][r].busy = True
                    self.rs[operation][r].cycles_of_ex = self.instuction_cycles[operation]
                    return True

        elif operation == "STORE":
            rs1 = instruction.get("rs1")
            rs2 = instruction.get("rs2")
            for r in range(self.num_rs[operation]):
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.fill_qk(operation, r, rs2)
                    self.rs[operation][r].A = instruction.get("imm")
                    self.rs[operation][r].busy = True
                    self.rs[operation][r].cycles_of_ex = self.instuction_cycles[operation]
                    return True

        else:
            for r in range(self.num_rs[operation]):
                rs1 = instruction.get("rs1")
                rs2 = instruction.get("rs2")
                rd = instruction.get("rd")
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.fill_qk(operation, r, rs2)
                    self.rs[operation][r].rd = rd
                    self.register_stat[rd] = self.rs[operation][r].name
                    self.rs[operation][r].busy = True
                    self.rs[operation][r].cycles_of_ex = self.instuction_cycles[operation]
                    print("I was issued in clock cycle: ", self.clock_cycles)
                    return True
        return False

    def execute_all(self):
        for inst in self.inst_types:
            for i in range(self.num_rs[inst]):
                # and self.rs[inst][i].cycles_of_ex > 1):
                if (self.rs[inst][i].busy == True):
                    # print("Execution Cycle: ", self.rs[inst][i].cycles_of_ex)
                    self.check_to_execute(self.rs[inst][i].op, i)
                    # print("Execution Cycle: ", self.rs[inst][i].cycles_of_ex)

                # elif (self.rs[inst][i].cycles_of_ex == 1):
                #     self.execute(self.rs[inst][i].op, i)

                # operation = self.rs[inst][i].op
        return

    def check_to_execute(self, operation, i):
        if operation == "LOAD":
            for inst in self.inst_types:
                for i in range(self.num_rs[inst]):
                    if self.rs[inst][i].qj == 0:  # && r is at the head of the load-store queue
                        self.rs[inst][i].A = self.rs[inst][i].vj + \
                            self.rs[inst][i].A
                        self.regFile[self.rs[inst]
                                     [i].rd] = self.memory[self.rs[inst][i].A]
                        self.rs[inst][i].cycles_of_ex -= 1
                        # read from memory at address A
                        # Lec 18 Slide 6

        elif operation == "STORE":
            for inst in self.inst_types:
                for i in range(self.num_rs[inst]):
                    if self.rs[inst][i].qj == 0:  # && r is at the head of the load-store queue
                        self.rs[inst][i].A = self.rs[inst][i].vj + \
                            self.rs[inst][i].A
                        self.rs[inst][i].cycles_of_ex -= 1
                        # Lec 18 Slide 7.

        else:
            if self.rs[operation][i].qj == None and self.rs[operation][i].qk == None:
                print("I am executing in cycle: ", self.clock_cycles)
                self.compute_result(self.rs[operation][i].op, i)
                # self.compute_result(operation, i)
                self.rs[operation][i].cycles_of_ex -= 1
        return

    def compute_result(self, operation, r):
        # Set the executed bool of the rs to "True" here or before returning from the execute function
        self.rs[operation][r].executed = True
        # cycles = self.instruction_cycles[operation]

        if (operation == "ADD"):
            self.rs[operation][r].result = self.rs[operation][r].vj + \
                self.rs[operation][r].vk

        elif (operation == "ADDI"):
            self.rs[operation][r].result = self.rs[operation][r].vj + \
                self.rs[operation][r].A

        elif (operation == "NEG"):
            self.rs[operation][r].result = ~self.rs[operation][r].vj

        elif (operation == "NAND"):
            self.rs[operation][r].result = ~(
                self.rs[operation][r].vj & self.rs[operation][r].vk)

        elif (operation == "SLL"):
            self.rs[operation][r].result = self.rs[operation][r].vj << self.rs[operation][r].A

    def write_all(self):
        for inst in self.inst_types:
            for i in range(self.num_rs[inst]):
                if (self.rs[inst][i] != None and self.rs[inst][i].executed == True):
                    self.write(self.rs[inst][i].op, i)
        return

    def write(self, operation, i):

        if operation == "STORE":
            if (self.rs[operation][i].qk == 0 and self.cdb == True):
                self.memory[self.rs[operation][i].A] = self.rs[operation][i].vk
                self.empty_entry(self.rs[operation])
                self.cdb == False
        else:
            if (self.cdb == True):
                rd = self.rs[operation][i].rd
                r_name = self.rs[operation][i].name

                for reg, value in self.register_stat.items():
                    if (self.register_stat[reg] == r_name):
                        self.register_stat[reg] = None
                        self.RegFile[reg] = self.rs[operation][i].result

                for inst in self.inst_types:
                    for sub_entry in range(self.num_rs[inst]):
                        if (self.rs[inst][sub_entry].qj == r_name):
                            self.rs[inst][sub_entry].vj = self.rs[operation][i].result
                            self.rs[inst][sub_entry].qj = None

                        if (self.rs[inst][sub_entry].qk == r_name):
                            self.rs[inst][sub_entry].vk = self.rs[operation][i].result
                            self.rs[inst][sub_entry].qk = None

                self.empty_entry(self.rs[operation][i])
                self.cdb == False
                print("I am writing in clock cycle: ", self.clock_cycles)

    def empty_entry(self, station):
        station.busy = False
        station.op = None
        station.vj = None
        station.vk = None
        station.qj = None
        station.qk = None
        station.rd = None
        station.offset = None
        station.A = None
        station.result = None
        station.executed = False

    def print_reservation_stations(self):
        print("Reservation Stations:")
        for inst in self.inst_types:
            # print("\n", inst, " Instructions:")
            for i in range(self.num_rs[inst]):
                rs = self.rs[inst][i]
                if rs.busy == True:
                    print(
                        f"{rs.name}: op = {rs.op}, busy = {rs.busy}, vj = {rs.vj}, vk = {rs.vk}, qj = {rs.qj}, qk = {rs.qk}, result = {rs.result}")

    def print_register_status(self):
        print("\nRegister Status:\n")
        for reg, value in self.register_stat.items():
            print(f"{reg}: {value}")

    def register_file(self):
        print("\nRegister File:\n")
        for reg, value in self.RegFile.items():
            print(f"{reg}: {value}")

    def memory_state(self):
        print("\nMemory State:\n")
        for i in range(len(self.memory)):
            print(f"{i}: {self.memory[i]}")

    def run(self):
        pc = 0
        ctr = 0
        # Each iteration represents a clock cycle
        while True:
            print("I am standing in the begining of the while loop")
            # for i in range(70):
            #     print('*', end='')
            # print("\nNEW INSTRUCTION: ")
            instruction = self.fetch(pc)
            if (pc < len(self.instructions)):
                print("PC is ", pc, " which is less than ",
                      len(self.instructions))
                if (self.issue(instruction)):
                    pc += 1
            self.execute_all()
            self.write_all()
            self.clock_cycles += 1
            print("Just Incremented the clock cycles by 1")
            for inst in self.inst_types:
                for i in range(self.num_rs[inst]):
                    if (self.rs[inst][i].busy == False):
                        ctr += 1
            # and pc == len(self.instructions)):
            if (ctr == sum(self.num_rs.values())):
                print("We will break here!")
                break
        print("Execution completed.")
        self.print_reservation_stations()
        self.print_register_status()
        self.register_file()
        # self.memory_state()

        print("Clock Cycles: ", self.clock_cycles)


# Need to read from a file and parse into a similar array
# instructions = [
#     {"op": "ADD", "rd": "R1", "rs1": "R2", "rs2": "R3"},
#     {"op": "NAND", "rd": "R4", "rs1": "R5", "rs2": "R6"},
#     {"op": "ADD", "rd": "R7", "rs1": "R2", "rs2": "R5"},
#     {"op": "NAND", "rd": "R5", "rs1": "R3", "rs2": "R6"},
# ]
instructions = [
    {"op": "ADD", "rd": "R1", "rs1": "R2", "rs2": "R3"},

]
var_rs = {
    "LOAD": 1,
    "STORE": 1,
    "BNE": 1,
    "JAL": 1,
    "RET": 1,
    "ADD": 2,
    "ADDI": 1,
    "NEG": 1,
    "NAND": 1,
    "SLL": 1
}
execution_cycles = {
    "LOAD": 1,
    "STORE": 1,
    "BNE": 1,
    "JAL": 1,
    "RET": 1,
    "ADD": 1,
    "ADDI": 1,
    "NEG": 1,
    "NAND": 1,
    "SLL": 1
}

tomasulo = Tomasulo(instructions, num_rs=var_rs,
                    instruction_cycles=execution_cycles)
tomasulo.run()


# find the sum of the values in num_rs
# self.total_rs = sum(num_rs.values())
# for inst in inst_type:
#     if inst not in self.inst_types:
#         print("Error: Instruction type not recognized.")
#         return
