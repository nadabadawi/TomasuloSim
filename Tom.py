# Notes:
#   - Need to read from a file and parse into a similar array (input instruction array)
#   - Validation of instructions provided should be handled. Ex: Register names and bounds should be valid & their format
#   - Simulating Clock Cycles are not yet implemented
#   - Number of execution cycles for each instruction should be input from the user
#   - Need to implement the load-store queue (probably) (NOT NEEDED)
#   - Need to give priority to older instruction to write
#   - Ensure that R0 does not get overwritten

# Done
#   - Registers and Memory should be taken into account and implemented
#   - Reservation station and functional units have a 1-to-1 relationship
#   - Need to update the qj/k to none after writing an instruction


##############################
#What's Left:
# Clock cycles stalling
# Flushing for BNE
# JAL and RET Stalling
# Storing/Loading addresses are not equal --> if they are, do not issue second instruction
# Return is R1

class ReservationStation:
    def __init__(self, index, name, op, busy=False, vj=None, vk=None, qj=None, qk=None, rd=None, offset=None, A=None, pc = None):
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
        self.pc = pc
        self.result = None
        self.executed = False
        self.total_ex_cycles = None
        self.issue_cycle = 100
        self.execute_cycle = 100
        # self.write_cycle = None

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
        self.clock_cycles = 1
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
        self.flush = False
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
        if (self.flush == True):
            self.flush = False
            return None
        
        if pc < len(self.instructions):
            return self.instructions[pc]
        
    def issue(self, instruction, pc):
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
                    self.rs[operation][r].total_ex_cycles = self.instuction_cycles[operation]
                    self.rs[operation][r].issue_cycle = self.clock_cycles
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
                    self.rs[operation][r].total_ex_cycles = self.instuction_cycles[operation]
                    self.rs[operation][r].issue_cycle = self.clock_cycles
                    return True
        
        elif operation == "BNE":
            rs1 = instruction.get("rs1")
            rs2 = instruction.get("rs2")
            # Fill in A, rs1, rs2, pc
            for r in range(self.num_rs[operation]):
                if self.rs[operation][r].busy is False:
                    self.fill_qj(operation, r, rs1)
                    self.fill_qk(operation, r, rs2)
                    self.rs[operation][r].A = instruction.get("imm") #NOT PRESENT YET #LABEL imm
                    self.rs[operation][r].pc = pc
                    self.rs[operation][r].busy = True
                    self.rs[operation][r].total_ex_cycles = self.instuction_cycles[operation]
                    self.rs[operation][r].issue_cycle = self.clock_cycles
                    return True
                   
        elif operation == "JAL":
            #stall until execution is finished  
            return 
                      
        elif operation == "RET":
            #stall until execution is finished
            return
            
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
                    self.rs[operation][r].total_ex_cycles = self.instuction_cycles[operation]
                    if (operation == "ADD"):
                        print("I was issued in clock cycle: ", self.clock_cycles)
                    self.rs[operation][r].issue_cycle = self.clock_cycles
                    return True
        return False

    def execute_all(self):
        for inst in self.inst_types:
            for i in range(self.num_rs[inst]):
                # and self.rs[inst][i].total_ex_cycles > 1):
                if (self.rs[inst][i].busy == True and self.rs[inst][i].executed == False):
                    # print("Execution Cycle: ", self.rs[inst][i].total_ex_cycles)
                    self.check_to_execute(self.rs[inst][i].op, i)
                    # print("Execution Cycle: ", self.rs[inst][i].total_ex_cycles)

                # elif (self.rs[inst][i].total_ex_cycles == 1):
                #     self.execute(self.rs[inst][i].op, i)

                # operation = self.rs[inst][i].op 
        return

    def check_to_execute(self, operation, i): ############# REMAINING JAL AND RET
        if (operation == "ADD"):
            print("************************************************************************************************")
            print("Issue Cycle: ", self.rs[operation][i].issue_cycle, " and clock cycles: ", self.clock_cycles)
        if self.rs[operation][i].total_ex_cycles <= 0:
            if (operation == "ADD"):
                print("Breaking out of the execute function")
            return
        if self.rs[operation][i].issue_cycle >= self.clock_cycles:
            if (operation == "ADD"):
                print("Cannot issue and execute at the same time!!")
            return 
        
        if operation == "LOAD":
            if (self.rs[operation][i].qj == None):  # && r is at the head of the load-store queue
                self.rs[operation][i].A = self.rs[operation][i].vj + self.rs[operation][i].A
                self.regFile[self.rs[operation][i].rd] = self.memory[self.rs[operation][i].A]
                self.compute_result(self.rs[operation][i].op, i)
                self.rs[operation][i].execute_cycle = self.clock_cycles
                self.rs[operation][i].total_ex_cycles -= 1
                # read from memory at address A
                # Lec 18 Slide 6

        elif (operation == "STORE"):
            if (self.rs[operation][i].qj == None):  ##REMOVED --> NOT SAME CONDITION AS SLIDES QK IS EXTRAA # && r is at the head of the load-store queue
                self.rs[operation][i].A = self.rs[operation][i].vj + self.rs[operation][i].A
                self.compute_result(self.rs[operation][i].op, i)
                self.rs[operation][i].execute_cycle = self.clock_cycles
                self.rs[operation][i].total_ex_cycles -= 1
                # Lec 18 Slide 7.

        elif (operation == "BNE"):
            if (self.rs[operation][i].qj == None and self.rs[operation][i].qk == None):
                self.compute_result(self.rs[operation][i].op, i)
                self.rs[operation][i].execute_cycle = self.clock_cycles
                self.rs[operation][i].total_ex_cycles -= 1
                
        elif (operation == "JAL" and operation == "RET"):
            return
            

        else:
            if (self.rs[operation][i].qj == None and self.rs[operation][i].qk == None):
                print("I am executing in cycle: ", self.clock_cycles)
                self.compute_result(self.rs[operation][i].op, i)
                self.rs[operation][i].execute_cycle = self.clock_cycles
                self.rs[operation][i].total_ex_cycles -= 1
        return

    def compute_result(self, operation, r):
        # Set the executed bool of the rs to "True" here or before returning from the execute function
        self.rs[operation][r].executed = True

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
        
        elif (operation == "JAL"):
            self.rs[operation][r].result = self.rs[operation][r].A + self.rs[operation][r].pc
            # self.flush = True
            # self.flush_all()
        
        elif (operation == "BNE"):
            #  TO BE CONTINUED... FLUSHING NEEDED!
            if (self.rs[operation][r].vj != self.rs[operation][r].vk): # branch taken
                self.rs[operation][r].result = self.rs[operation][r].A + self.rs[operation][r].pc
                self.flush = True
            
        # elif (operation == "RET"):
        #     self.rs[operation][r].result = self.rs[operation][r].vj + self.rs[operation][r].A
            
    def write_all(self):
        for inst in self.inst_types:
            for i in range(self.num_rs[inst]):
                if (self.rs[inst][i].executed == True): #self.rs[inst][i] != None and 
                    self.write(self.rs[inst][i].op, i)
        return

    def write(self, operation, i):
        if self.rs[operation][i].execute_cycle >= self.clock_cycles:
            print("Execute Cyle: ", self.rs[operation][i].execute_cycle, " Clock cycle: ", self.clock_cycles)
            return 
        if (self.cdb == False):
            return
        if operation == "STORE":
            if (self.rs[operation][i].qk == None):
                self.memory[self.rs[operation][i].A] = self.rs[operation][i].vk
                self.empty_entry(self.rs[operation])
                self.cdb == False

        elif (operation == "BNE" or operation == "RET" or operation == "JAL"):
            # Update Global PC
            return
        

        else: # For load and arithmeti operations
            rd = self.rs[operation][i].rd
            r_name = self.rs[operation][i].name

            for reg, value in self.register_stat.items(): # gets qi
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
 ## c = 4
 ## 
 
 ##############################
 #cycles to exe BNE = 4
 #i1
 #i2
 #i3
 #i4
 ##############################
 #Target address i8 > PC  erase---> target address
 #Taregt address < PC  
 
 ### If down, flush from branch pc to target address
 ### If up, flush all
 ### Pseudo-code:
 ###  
 
    #need to place flush  
    def flush_all(self, operation, r):
        #reset all reservation stations by calling empty_entry
        for res_st in self.rs[operation]:
            self.empty_entry(res_st)
        
        #reset register status
        for reg in self.register_stat:
            self.register_stat[reg] = None

        # Reset program counter (PC) to target address
        self.pc = self.rs[operation][r].result

            
            
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
        # Each iteration represents a clock cycle
        while True:
            ctr = 0
            print("I am standing in the begining of the while loop")
            # for i in range(70):
            #     print('*', end='')
            # print("\nNEW INSTRUCTION: ")
            instruction = self.fetch(pc)
            if (pc < len(self.instructions)): #check if last instruction
                print("PC is ", pc, " which is less than ",
                      len(self.instructions))
                if (self.issue(instruction, pc)): # issue or not issue --> stall
                    pc += 1
            self.execute_all()
            self.write_all()
            self.clock_cycles += 1
            # print("Just Incremented the clock cycles by 1")
            for inst in self.inst_types: #check if rs are empty
                for i in range(self.num_rs[inst]):
                    if (self.rs[inst][i].busy == False):
                        ctr += 1
            # and pc == len(self.instructions)):
            # print("Counter: ", ctr, " Sum: ", sum(self.num_rs.values()))
            if (ctr == sum(self.num_rs.values())): #check if pc is last instruction
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
    {"op": "NAND", "rd": "R4", "rs1": "R5", "rs2": "R6"},
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
