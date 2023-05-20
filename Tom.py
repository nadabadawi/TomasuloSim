# Notes:
#   - Need to read from a file and parse into a similar array (input instruction array)
#   - Reservation station and functional units have a 1-to-1 relationship
#   - Registers and Memory should be taken into account and implemented
#   - Validation of instructions provided should be handled. Ex: Register names and bounds should be valid & their format
#   - Simulating Clock Cycles are not yet implemented
#   - Number of execution cycles for each instruction should be input from the user
#   - Need to implement the load-store queue (probably)

class ReservationStation:
    def __init__(self, index, name, op, busy = False, vj=None, vk=None, qj=None, qk=None, A=None):
        self.index = index
        self.name = name
        self.busy = busy
        self.op = op
        self.vj = vj
        self.vk = vk
        self.qj = qj
        self.qk = qk
        self.A = A
        self.result = None
        self.executed = False
    
    def __iter__(self):
        return self

class Tomasulo:
    def __init__(self, instructions, num_rs):
        self.inst_types = ["LOAD", "STORE", "BNE", "JAL", "RET", "ADD", "ADDI", "NEG", "NAND", "SLL"]
        self.instructions = instructions
        self.cdb = False
        self.num_rs = num_rs
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

        word_size = 4  #size in bytes
        address_size = 16  #address in bits
        memory_capacity = 128 * 1024  #Memory capacity in bytes
        num_words = memory_capacity // word_size  # Number of words in the memory

        # Create a list of words in the memory, initialized with zeros
        self.memory = [0] * num_words
        
        # find the sum of the values in num_rs
        # self.total_rs = sum(num_rs.values())
        # for inst in inst_type:
        #     if inst not in self.inst_types:
        #         print("Error: Instruction type not recognized.")
        #         return
        
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
            "R3": "LOAD1",
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
        print("\nInstruction: ", instruction.get("op"), instruction.get("rd"), instruction.get("rs1"), instruction.get("rs2"), "\n")
        
        issued = False
        operation = instruction.get("op")
   
        if operation == "LOAD":
            rs1 = instruction.get("rs1")
            rd = instruction.get("rd")
            for r in range(self.num_rs[operation]):
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.register_stat[rd] = self.rs[operation][r].name
                    self.rs[operation][r].A = instruction.get("imm")
                    self.rs[operation][r].busy = True
                    issued = True
                    return
                
        elif operation == "STORE":
            rs1 = instruction.get("rs1")
            rs2 = instruction.get("rs2")
            for r in range(self.num_rs[operation]):
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.fill_qk(operation, r, rs2)
                    self.rs[operation][r].A = instruction.get("imm")
                    self.rs[operation][r].busy = True
                    issued = True
                    return
        
        else:
            for r in range(self.num_rs[operation]):
                rs1 = instruction.get("rs1")
                rs2 = instruction.get("rs2")
                rd = instruction.get("rd")
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.fill_qk(operation, r, rs2)
                    self.register_stat[rd] = self.rs[operation][r].name
                    self.rs[operation][r].busy = True
                    issued = True
                    return
            
        if issued == False:
            print("NOT ISSUED\n")
            return
        #Need to stall cycles here if not issued


    def execute(self, operation):
        # All Reservation Stations:
        if operation == "LOAD":
            for inst in self.inst_types:
                for i in range(self.num_rs[inst]):
                    if self.rs[inst][i].qj == 0: # && r is at the head of the load-store queue
                        self.rs[inst][i].A = self.rs[inst][i].vj + self.rs[inst][i].A
                        #read from memory at address A
                        # Add rd to REGFILE From rs
                        # self.regFile[] = self.memory[self.rs[inst][i].A]
                        # Lec 18 Slide 6

        elif operation == "STORE":
            for inst in self.inst_types:
                for i in range(self.num_rs[inst]):
                    if self.rs[inst][i].qj == 0: # && r is at the head of the load-store queue
                        self.rs[inst][i].A = self.rs[inst][i].vj + self.rs[inst][i].A
                        # Lec 18 Slide 7.

        else: 
            for inst in self.inst_types:
                for i in range(self.num_rs[inst]):
                    if self.rs[inst][i].qj == 0 and self.rs[inst][i].qk == 0:
                        self.compute_result(operation, i)
        return
    
    def compute_result(self, operation, r):
        # Set the executed bool of the rs to "True" here or before returning from the execute function
        self.rs[operation][r].executed = True

        # Consider the number of cycles required for execution.
        cycles = self.instruction_cycles[operation]

        # Wait for the specified number of cycles before returning the result.
        for _ in range(cycles):
            pass
        # To be continued...
        
        if(operation == "ADD"):
            self.rs[operation][r].result = self.rs[operation][r].vj + self.rs[operation][r].vk
        
        elif (operation == "ADDI"):
            self.rs[operation][r].result = self.rs[operation][r].vj + self.rs[operation][r].A
        
        elif (operation == "NEG"):
            self.rs[operation][r].result = -self.rs[operation][r].vj

        elif (operation == "NAND"):
            self.rs[operation][r].result = ~(self.rs[operation][r].vj & self.rs[operation][r].vk)
        
        elif (operation == "SLL"):
            self.rs[operation][r].result = self.rs[operation][r].vj << self.rs[operation][r].A   
        
        
    def write(self, operation):
        if operation == "STORE":
            for r in range(self.num_rs[operation]):
                if (self.rs[operation][r].executed == True and  self.rs[operation][r].qk == 0):
                    self.rs[operation][r].busy = False
                    self.rs[operation][r].executed = False
                    self.rs[operation][r].vj = None
                    self.rs[operation][r].vk = None
                    self.rs[operation][r].qj = None
                    self.rs[operation][r].qk = None
                    self.rs[operation][r].result = None
                    self.rs[operation][r].A = None
                    self.memory[self.rs[operation][r].A] = self.rs[operation][r].vk
        else: # To be continued...
            for x in range(self.num_rs[operation]):
                if (self.rs[operation][x].executed == True): #CDB is free
                    
                    # if (self.register_stat[x].qi == r):
                    #     self.RegFile[x] = self.rs[operation][r].result
                    #     self.register_stat[x].qi = 0
                    
                    if (self.rs[operation][x].qj == r):
                        self.rs[operation][x].vj = self.rs[operation][r].result
                        self.rs[operation][x].qj = 0
                        
                    if(self.rs[operation][x].qk == r):
                        self.rs[operation][x].vk = self.rs[operation][r].result
                        self.rs[operation][x].qk = 0
                    
                    self.rs[operation][r].busy = False
                    # self.rs[operation][r].executed = False
                    # self.rs[operation][r].vj = None
                    # self.rs[operation][r].vk = None
                    # self.rs[operation][r].qj = None
                    # self.rs[operation][r].qk = None
                    # self.rs[operation][r].result = None
                    # self.rs[operation][r].A = None

    def print_reservation_stations(self):
        print("Reservation Stations:")
        for inst in self.inst_types:
            print("\n", inst, " Instructions:")
            for i in range(self.num_rs[inst]):
                rs = self.rs[inst][i]
                # if rs.busy == True:
                print(f"{rs.name}: op = {rs.op}, busy = {rs.busy}, vj = {rs.vj}, vk = {rs.vk}, qj = {rs.qj}, qk = {rs.qk}, result = {rs.result}")
                
    def print_register_status(self):
        print("\nRegister Status:\n")
        for reg, value in self.register_stat.items():
            print(f"{reg}: {value}")

    def run(self):
        pc = 0
        while True:
            for i in range(70):
                print('*', end='')
            print("\nNEW INSTRUCTION: ")
            instruction = self.fetch(pc)
            self.issue(instruction)
            pc += 1
            self.print_reservation_stations()
            self.print_register_status()
            if (pc == 4):
                break
        print("Execution completed.")

#Need to read from a file and parse into a similar array   
instructions = [
    {"op": "ADD", "rd": "R1", "rs1": "R2", "rs2": "R3"},
    {"op": "NAND", "rd": "R4", "rs1": "R5", "rs2": "R6"},
    {"op": "ADD", "rd": "R7", "rs1": "R2", "rs2": "R5"},
    {"op": "NAND", "rd": "R5", "rs1": "R3", "rs2": "R6"},
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

tomasulo = Tomasulo(instructions, num_rs=var_rs)
tomasulo.run()