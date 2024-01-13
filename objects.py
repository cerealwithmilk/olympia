from __future__ import annotations
from synapse import Synapse

class ReturnValue:
    def __init__(self, address: int, synapse: Synapse) -> ReturnValue:
        self.self = address
        self.synapse = synapse
        self.offsets = {
            "vftable": 0x0,
            "value": 0x8,
        }

    @property
    def Value(self) -> str:
        try:
            ptr = self.synapse.memory.read_longlong(self.self + self.offsets["value"])
            fl = self.synapse.memory.read_longlong(ptr + 0x18)
            if fl == 0x1F:
                ptr = self.synapse.memory.read_longlong(ptr)
            return self.synapse.readRobloxString(ptr)
        except:
            return "???"

class PropertyDescriptor:
    def __init__(self, address: int, synapse: Synapse) -> PropertyDescriptor:
        self.self = address
        self.synapse = synapse
        self.offsets = {
            "vftable": 0x0,
            "name": 0x8,
            "return_value": 0x30,
            "get_set_impl": 0x48
        }

    @property
    def Name(self) -> str:
        try:
            ptr = self.synapse.memory.read_longlong(self.self + self.offsets["name"])
            fl = self.synapse.memory.read_longlong(ptr + 0x18)
            if fl == 0x1F:
                ptr = self.synapse.memory.read_longlong(ptr)
            return self.synapse.readRobloxString(ptr)
        except:
            return "???"
        
    @property
    def Value(self) -> str:
        try:
            returnValue = ReturnValue(self.synapse.memory.read_longlong(self.self + self.offsets["return_value"]), self.synapse)
            return returnValue.Value
        except:
            return "???"

class ClassDescriptor:
    def __init__(self, address: int, synapse: Synapse) -> ClassDescriptor:
        self.self = address
        self.synapse = synapse
        self.offsets = {
            "vftable": 0x0,
            "class_name": 0x8,
            "properties": 0x40, # 0x20
        }

    @property
    def ClassName(self) -> str:
        try:
            ptr = self.synapse.memory.read_longlong(self.self + self.offsets["class_name"])
            fl = self.synapse.memory.read_longlong(ptr + 0x18)
            if fl == 0x1F:
                ptr = self.synapse.memory.read_longlong(ptr)
            return self.synapse.readRobloxString(ptr)
        except:
            return "???"
        
    def GetProperties(self) -> list[PropertyDescriptor]:
        prop_begin = self.synapse.memory.read_longlong(self.self + self.offsets["properties"])
        prop_end = self.synapse.memory.read_longlong(self.self + self.offsets["properties"] + 0x8)
        children = []
        if prop_begin == 0 or prop_end == 0:
            return []
        while prop_begin != prop_end:
            current_prop = self.synapse.memory.read_longlong(prop_begin)
            if (current_prop != 0):
                prop = PropertyDescriptor(current_prop, self.synapse)
                
                if not prop.Name == "???":
                    children.append(prop)
            prop_begin += 0x8
        return children

class Instance:
    def __init__(self, address: int, synapse: Synapse) -> Instance:
        self.self = address
        self.synapse = synapse
        self.offsets = {
            "vftable": 0x0,
            "self": 0x8,
            "class_descriptor": 0x18,
            "name": 0x48,
            "children": 0x50,
            "parent": 0x60
        }

    @property
    def ClassDescriptor(self) -> ClassDescriptor:
        try:
            ptr = self.synapse.memory.read_longlong(self.self + self.offsets["class_descriptor"])
            classDescriptor = ClassDescriptor(ptr, self.synapse)

            return classDescriptor
        except:
            return None

    @property
    def ClassName(self) -> str:
        try:
            return self.ClassDescriptor.ClassName
        except:
            return "???"

    @property
    def Name(self) -> str:
        try:
            ptr = self.synapse.memory.read_longlong(self.self + self.offsets["name"])
            fl = self.synapse.memory.read_longlong(ptr + 0x18)
            if fl == 0x1F:
                ptr = self.synapse.memory.read_longlong(ptr)

            name = self.synapse.readRobloxString(ptr)

            if len(name.strip()) > 1:
                return name
            else:
                return self.ClassName
        except:
            return self.ClassName
        
    @property
    def Parent(self) -> Instance:
        try:
            if self.synapse.memory.read_longlong(self.self + self.offsets["parent"]) != 0:
                return Instance(self.synapse.memory.read_longlong(self.self + self.offsets["parent"]), self.synapse)
            
            return None
        except:
            return None
        
    @property
    def HasChildren(self) -> bool:
        if self.self != 0:
            child_list = self.synapse.memory.read_longlong(self.self + self.offsets["children"])
            if child_list != 0:
                child_begin = self.synapse.memory.read_longlong(child_list)
                end_child = self.synapse.memory.read_longlong(child_list + 0x8)
                
                child_offset = 0x10

                return int((end_child - child_begin) / child_offset) > 0
        
        return False
        
    def GetChildren(self) -> list[Instance]:
        children = []
        if self.self != 0:
            child_list = self.synapse.memory.read_longlong(self.self + self.offsets["children"])
            if child_list != 0:
                child_begin = self.synapse.memory.read_longlong(child_list)
                end_child = self.synapse.memory.read_longlong(child_list + 0x8)
                
                child_offset = 0x10
                
                while child_begin != end_child:
                    current_instance = self.synapse.memory.read_longlong(child_begin)
                    if current_instance !=0:
                        child = Instance(current_instance, self.synapse)

                        if not child.Name == "???" and not child.ClassName == "???":
                            children.append(child)

                        child_begin = child_begin + child_offset
        return children
    
    def GetProperties(self) -> list[PropertyDescriptor]:
        return self.ClassDescriptor.GetProperties()
    
    def FindFirstChild(self, name: str) -> Instance:
        for child in self.GetChildren():
            if child.Name == name:
                return child
            
        return None
    
    def FindFirstChildOfClass(self, className: str) -> Instance:
        for child in self.GetChildren():
            if child.ClassName == className:
                return child
            
        return None
    
    def IsA(self, className: str) -> bool:
        return self.ClassName == className
    
    def __getattr__(self, name: str) -> Instance:
        return self.FindFirstChild(name)