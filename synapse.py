from pymem import *
import re
import time
import ctypes
import time

class Synapse:
    def __init__(self):
        self.programName = None
        self.memory = pymem.Pymem()
        self.addresses = {
            "clientReplicator": 0x0,
            "dataModel": 0x0,
            "localPlayer": 0x0
        }
        self.offsets = {
            "classDescriptor": 0x18,
            "name": 0x48,
            "parent": 0x60,
            "children": 0x50,
            "localPlayer": 0x240
        }
        self.is64Bit = False
        self.pid = None

    def h2d(self, hz: str, bit: int = 16) -> int:
        if type(hz) == int:
            return hz
        return int(hz, bit)

    def d2h(self, dc: int, UseAuto=None) -> str:
        if type(dc) == str:
            return dc
        if UseAuto:
            if UseAuto == 32:
                dc = hex(dc & (2**32 - 1)).replace("0x", "")
            else:
                dc = hex(dc & (2**64 - 1)).replace("0x", "")
        else:
            if abs(dc) > 4294967295:
                dc = hex(dc & (2**64 - 1)).replace("0x", "")
            else:
                dc = hex(dc & (2**32 - 1)).replace("0x", "")
        if len(dc) > 8:
            while len(dc) < 16:
                dc = "0" + dc
        if len(dc) < 8:
            while len(dc) < 8:
                dc = "0" + dc
        return dc
    
    def aob2re(self, aob: str):
        if type(aob) == bytes:
            return aob
        trueB = bytearray(b"")
        aob = aob.replace(" ", "")
        PLATlist = []
        for i in range(0, len(aob), 2):
            PLATlist.append(aob[i : i + 2])
        for i in PLATlist:
            if "?" in i:
                trueB.extend(b".")
            if "?" not in i:
                trueB.extend(re.escape(bytes.fromhex(i)))
        return bytes(trueB)
    
    def aobScan(self, AOB_HexArray: str, xreturn_multiple=False):
        return pymem.pattern.pattern_scan_all(
            self.memory.process_handle,
            self.aob2re(AOB_HexArray),
            return_multiple=xreturn_multiple,
        )
    
    def gethexc(self, hex: str):
        hex = hex.replace(" ", "")
        hxlist = []
        for i in range(0, len(hex), 2):
            hxlist.append(hex[i : i + 2])
        return len(hxlist)

    def hex2le(self, hex: str):
        lehex = hex.replace(" ", "")
        lelist = []
        if len(lehex) > 8:
            while len(lehex) < 16:
                lehex = "0" + lehex
            for i in range(0, len(lehex), 2):
                lelist.append(lehex[i : i + 2])
            lelist.reverse()
            return "".join(lelist)
        if len(lehex) < 9:
            while len(lehex) < 8:
                lehex = "0" + lehex
            for i in range(0, len(lehex), 2):
                lelist.append(lehex[i : i + 2])
            lelist.reverse()
            return "".join(lelist)

    def calcjmpop(self, des, cur):
        jmpopc = (self.h2d(des) - self.h2d(cur)) - 5
        jmpopc = hex(jmpopc & (2**32 - 1)).replace("0x", "")
        if len(jmpopc) % 2 != 0:
            jmpopc = "0" + str(jmpopc)
        return jmpopc

    def isProgramGameActive(self):
        try:
            self.memory.read_char(self.memory.base_address)
            return True
        except:
            return False

    def DRP(self, Address: int, is64Bit: bool = None) -> int:
        Address = Address
        if type(Address) == str:
            Address = self.h2d(Address)
        if is64Bit:
            return int.from_bytes(self.memory.read_bytes(Address, 8), "little")
        if self.is64bit:
            return int.from_bytes(self.memory.read_bytes(Address, 8), "little")
        return int.from_bytes(self.memory.read_bytes(Address, 4), "little")
    
    def isValidPointer(self, Address: int, is64Bit: bool = None) -> bool:
        try:
            if type(Address) == str:
                Address = self.h2d(Address)
            self.memory.read_bytes(self.memory.read_longlong(Address, is64Bit), 1)
            return True
        except:
            return False
        
    def getAddressFromName(self, Address: str) -> int:
        if type(Address) == int:
            return Address
        AddressBase = 0
        AddressOffset = 0
        for i in self.GetModules():
            if i.name in Address:
                AddressBase = i.lpBaseOfDll
                AddressOffset = self.h2d(Address.replace(i.name + "+", ""))
                AddressNamed = AddressBase + AddressOffset
                return AddressNamed
        print("Unable to find Address: " + Address)
        return Address

    def getNameFromAddress(self, Address: int) -> str:
        memoryInfo = pymem.memory.virtual_query(self.memory.process_handle, Address)
        BaseAddress = memoryInfo.BaseAddress
        NameOfDLL = ""
        AddressOffset = 0
        for i in self.GetModules():
            if i.lpBaseOfDll == BaseAddress:
                NameOfDLL = i.name
                AddressOffset = Address - BaseAddress
                break
        if NameOfDLL == "":
            return Address
        NameOfAddress = NameOfDLL + "+" + self.d2h(AddressOffset)
        return NameOfAddress

    def getRawProcesses(self):
        toreturn = []
        for i in pymem.process.list_processes():
            toreturn.append(
                [
                    i.cntThreads,
                    i.cntUsage,
                    i.dwFlags,
                    i.dwSize,
                    i.pcPriClassBase,
                    i.szExeFile,
                    i.th32DefaultHeapID,
                    i.th32ModuleID,
                    i.th32ParentProcessID,
                    i.th32ProcessID,
                ]
            )
        return toreturn

    def simpleGetProcesses(self):
        toreturn = []
        for i in self.getRawProcesses():
            toreturn.append({"Name": i[5].decode(), "Threads": i[0], "ProcessId": i[9]})
        return toreturn

    def yieldForProgram(self, programName, AutoOpen: bool = False, Limit=15):
        Count = 0
        while True:
            if Count > Limit:
                print("Yielded too long, failed!")
                return False
            ProcessesList = self.simpleGetProcesses()
            for i in ProcessesList:
                if i["Name"] == programName:
                    print(
                        "Found "
                        + programName
                        + " with Process ID: "
                        + str(i["ProcessId"])
                    )
                    if AutoOpen:
                        self.memory.open_process_from_id(i["ProcessId"])
                        self.programName = programName
                        self.handle = self.memory.process_handle
                        self.is64bit = not pymem.process.is_64_bit(self.handle)
                        self.pid = self.memory.process_id
                        print("Successfully attached to Process.")
                    return True
            time.sleep(1)
            Count += 1

    def readPointer(
        self, BaseAddress: int, Offsets_L2R: list, is64Bit: bool = None
    ) -> int:
        x = self.memory.read_longlong(BaseAddress, is64Bit)
        y = Offsets_L2R
        z = x
        if y == None or len(y) == 0:
            return z
        count = 0
        for i in y:
            try:
                print(self.d2h(x + i))
                print(self.d2h(i))
                z = self.memory.read_longlong(z + i, is64Bit)
                count += 1
                print(self.d2h(z))
            except:
                print("Failed to read Offset at Index: " + str(count))
                return z
        return z

    def getMemoryInfo(self, Address: int, Handle: int = None):
        if Handle:
            return pymem.memory.virtual_query(Handle, Address)
        else:
            return pymem.memory.virtual_query(self.handle, Address)

    def memoryInfoToDictionary(self, MemoryInfo):
        return {
            "BaseAddress": MemoryInfo.BaseAddress,
            "AllocationBase": MemoryInfo.AllocationBase,
            "AllocationProtect": MemoryInfo.AllocationProtect,
            "RegionSize": MemoryInfo.RegionSize,
            "State": MemoryInfo.State,
            "Protect": MemoryInfo.Protect,
            "Type": MemoryInfo.Type,
        }

    def setProtection(
        self,
        Address: int,
        ProtectionType=0x40,
        Size: int = 4,
        OldProtect=ctypes.c_ulong(0),
    ):
        pymem.resources.kernel32.VirtualProtectEx(
            self.memory.process_handle,
            Address,
            Size,
            ProtectionType,
            ctypes.byref(OldProtect),
        )
        return OldProtect

    def changeProtection(
        self,
        Address: int,
        ProtectionType=0x40,
        Size: int = 4,
        OldProtect=ctypes.c_ulong(0),
    ):
        return self.setProtection(Address, ProtectionType, Size, OldProtect)

    def getProtection(self, Address: int):
        return self.getMemoryInfo(Address).Protect

    def knowProtection(self, Protection):
        if Protection == 0x10:
            return "PAGE_EXECUTE"
        if Protection == 0x20:
            return "PAGE_EXECUTE_READ"
        if Protection == 0x40:
            return "PAGE_EXECUTE_READWRITE"
        if Protection == 0x80:
            return "PAGE_EXECUTE_WRITECOPY"
        if Protection == 0x01:
            return "PAGE_NOACCESS"
        if Protection == 0x02:
            return "PAGE_READONLY"
        if Protection == 0x04:
            return "PAGE_READWRITE"
        if Protection == 0x08:
            return "PAGE_WRITECOPY"
        if Protection == 0x100:
            return "PAGE_GUARD"
        if Protection == 0x200:
            return "PAGE_NOCACHE"
        if Protection == 0x400:
            return "PAGE_WRITECOMBINE"
        if Protection in ["PAGE_EXECUTE", "execute", "e"]:
            return 0x10
        if Protection in [
            "PAGE_EXECUTE_READ",
            "execute read",
            "read execute",
            "execute_read",
            "read_execute",
            "er",
            "re",
        ]:
            return 0x20
        if Protection in [
            "PAGE_EXECUTE_READWRITE",
            "execute read write",
            "execute write read",
            "write execute read",
            "write read execute",
            "read write execute",
            "read execute write",
            "erw",
            "ewr",
            "wre",
            "wer",
            "rew",
            "rwe",
        ]:
            return 0x40
        if Protection in [
            "PAGE_EXECUTE_WRITECOPY",
            "execute copy write",
            "execute write copy",
            "write execute copy",
            "write copy execute",
            "copy write execute",
            "copy execute write",
            "ecw",
            "ewc",
            "wce",
            "wec",
            "cew",
            "cwe",
        ]:
            return 0x80
        if Protection in ["PAGE_NOACCESS", "noaccess", "na", "n"]:
            return 0x01
        if Protection in ["PAGE_READONLY", "readonly", "ro", "r"]:
            return 0x02
        if Protection in ["PAGE_READWRITE", "read write", "write read", "wr", "rw"]:
            return 0x04
        if Protection in ["PAGE_WRITECOPY", "write copy", "copy write", "wc", "cw"]:
            return 0x08
        if Protection in ["PAGE_GUARD", "pg", "guard", "g"]:
            return 0x100
        if Protection in ["PAGE_NOCACHE", "nc", "nocache"]:
            return 0x200
        if Protection in ["PAGE_WRITECOMBINE", "write combine", "combine write"]:
            return 0x400
        return Protection

    def suspend(self, pid: int = None):
        kernel32 = ctypes.WinDLL("kernel32.dll")
        if pid:
            kernel32.DebugActiveProcess(pid)
        if self.PID:
            kernel32.DebugActiveProcess(self.PID)

    def resume(self, pid: int = None):
        kernel32 = ctypes.WinDLL("kernel32.dll")
        if pid:
            kernel32.DebugActiveProcessStop(pid)
        if self.PID:
            kernel32.DebugActiveProcessStop(self.PID)
          
    def readRobloxString(self, ExpectedAddress: int, ExpectedLength: int = 1024) -> str:
        StringCount = self.memory.read_int(ExpectedAddress + 0x10)
        length = (StringCount > 0 and StringCount < 16384) and StringCount or ExpectedLength
        #if StringCount > 15:
        #    return self.memory.read_string(self.synapse.memory.read_longlong(ExpectedAddress), StringCount)
        return self.memory.read_string(ExpectedAddress, length)

    def readByte(self, addr: int) -> int:
        return self.h2d(self.memory.read_bytes(addr, 0x1).hex())