from synapse import Synapse
from capstone import *

class OffsetFinder:
    def __init__(self, synapse: Synapse):
        self.synapse = synapse

    def getXrefs(self, signature: str):
        xrefs = []
        signatureBytes = int(len(signature) / 2)

        results = self.synapse.aobScan(signature, True)
        if results == []:
            return []
        for rn in results:
            try:
                result = rn

                print(f"signature match: 0x{self.synapse.d2h(rn)}, {self.synapse.memory.read_bytes(rn, signatureBytes)}")

                bres = self.synapse.d2h(result)
                aobs = ""
                for i in range(1, 16 + 1):
                    aobs = aobs + bres[i - 1 : i]
                aobs = self.synapse.hex2le(aobs)

                print(f"xref search: {aobs}")

                res = self.synapse.aobScan(aobs, True)

                for i in res:
                    print(f"found xref: 0x{self.synapse.d2h(rn)}, {self.synapse.memory.read_bytes(i, 0x128).hex()}")
                    xrefs.append(i)
            except:
                pass
        
        return xrefs

    def nextCall(self, addr: int):
        start = addr
        currentAddr = start

        md = Cs(CS_ARCH_X86, CS_MODE_64)

        for i in md.disasm(self.synapse.memory.read_bytes(addr, 0x420), 0x0):
            print("0x%x:\t%s\t%s\t0x%x" %(i.address, i.mnemonic, i.op_str, self.synapse.readByte(addr + i.address)))

        for i in range(0x420):
            if self.synapse.readByte(currentAddr) == 0xE8:
                return currentAddr

            currentAddr += 0x1

        print()
        return 0

    def getCalling(self, call_add: int):
        if not call_add or not self.synapse.readByte(call_add) == 0xE8:
            return 0
        
        rel_addr = self.synapse.memory.read_longlong(call_add + 0x1)
        return call_add + rel_addr + 5