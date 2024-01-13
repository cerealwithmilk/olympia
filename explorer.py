from __future__ import annotations
import os
import uuid

import tkinter as tk
from tkinter import ttk, messagebox

from synapse import Synapse
from objects import Instance

from sigscan import Sigscan
from memview import Memview

WINDOW_WIDTH = 320
WINDOW_HEIGHT = 720
TITLE = "Olympia Explorer"

class Explorer:
    def __init__(self, synapse: Synapse, dataModel: Instance) -> Explorer:
        self.synapse = synapse
        self.root = tk.Tk()
        self.menuBar = tk.Menu(self.root)
        self.instanceTree = ttk.Treeview(self.root, show='tree')
        self.propertyTree = ttk.Treeview(self.root, show='tree')
        self.imageReferences = []
        self.rootInstance: Instance = dataModel
        self.rootItem = ""
        self.selectedInstance: Instance = None
        self.displayedProperties = []
        self.nodes = {}
        self.selectedItem = ""
        self.injected = False

        icon = tk.PhotoImage(file="./icons/Model.png")
        self.imageReferences.append(icon)

        screenWidth = self.root.winfo_screenwidth()
        screenHeight = self.root.winfo_screenheight()

        centerX = int(screenWidth / 2 - WINDOW_WIDTH / 2)
        centerY = int(screenHeight / 2 - WINDOW_HEIGHT / 2)

        self.root.title(TITLE)
        self.root.wm_iconphoto(False, icon)
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{centerX}+{centerY}')
        self.root.config(menu=self.menuBar)

        toolsMenu = tk.Menu(self.menuBar, tearoff=False)

        toolsMenu.add_command(
            label='Sigscan',
            command=self.openSigscanTool
        )
                
        toolsMenu.add_command(
            label='Find Xrefs',
            command=self.openXrefTool
        )
                
        toolsMenu.add_command(
            label='Memory Viewer',
            command=self.openMemoryViewer
        )

        toolsMenu.add_command(
            label='Dump Offsets',
            command=self.dumpOffsets
        )

        toolsMenu.add_command(
            label='Inject SynapseCE',
            command=self.inject,
            accelerator="I"
        )

        toolsMenu.add_command(
            label='Refresh',
            command=self.refresh,
            accelerator="Ctrl+R"
        )

        toolsMenu.add_command(
            label='Refresh All',
            command=self.refreshAll,
            accelerator="Ctrl+Alt+R"
        )

        self.menuBar.add_cascade(
            label="Tools",
            menu=toolsMenu
        )

        self.instanceTree.bind('<<TreeviewOpen>>', self.onTreeOpen)
        self.instanceTree.bind('<ButtonRelease-1>', self.onClick)

        self.propertyTree["columns"] = ("Name", "Value")

        self.propertyTree.column("#0", width=0, stretch=tk.NO)
        self.propertyTree.column("Name", anchor=tk.W, width=100)
        self.propertyTree.column("Value", anchor=tk.W, width=100)

        self.root.bind_all("<i>", self.inject)
        self.root.bind_all("<Control-r>", self.refresh)
        self.root.bind_all("<Control-Alt-r>", self.refreshAll)

    def openSigscanTool(self):
        window = tk.Toplevel()
        window.title("Sigscan")

        sigscan = Sigscan(window, self.synapse)
        sigscan.render()

    def openXrefTool(self):
        pass

    def openMemoryViewer(self):
        window = tk.Toplevel()
        window.title("Memory Viewer")

        sigscan = Memview(window, self.synapse)
        sigscan.render()

    def dumpOffsets(self):
        messagebox.showinfo("Olympia", f"ClientReplicator: 0x{self.synapse.d2h(self.synapse.addresses["clientReplicator"])}\nDataModel: 0x{self.synapse.d2h(self.synapse.addresses["dataModel"])}\nLocalPlayer: 0x{self.synapse.d2h(self.synapse.addresses["localPlayer"])}\n\nInstance->ClassDescriptor: 0x{self.synapse.d2h(self.synapse.offsets["classDescriptor"])}\nInstance->Name: 0x{self.synapse.d2h(self.synapse.offsets["name"])}\nInstance->Parent: 0x{self.synapse.d2h(self.synapse.offsets["parent"])}\nInstance->Children: 0x{self.synapse.d2h(self.synapse.offsets["children"])}")
        pass

    def inject(self, _ = None):
        if not self.injected:
            answer = messagebox.askokcancel(
            title='Synapse',
            message='Warning! Most public teleporter games are DETECTED and CAN GET YOU BANNED. It is recommended you make your own game; see https://youtu.be/p83aa9o78NI. Continue?',
            icon=messagebox.WARNING)

            if answer:
                localPlayer = Instance(self.synapse.addresses["localPlayer"], self.synapse)
                #targetScript = localPlayer.PlayerScripts.PlayerScriptsLoader or localPlayer.PlayerScripts.FindFirstChildOfClass("LocalScript")

                tool = localPlayer.Backpack.FindFirstChildOfClass("Tool")
                if not tool:
                    messagebox.showerror("Olympia", f"No tool found! Make sure the you have a tool in the game and try again.")
                    return
                
                targetScript = tool.FindFirstChildOfClass("LocalScript")

                injectScript = None
                results = self.synapse.aobScan("496E6A656374????????????????????06", True)
                valid = False

                if results == []:
                    messagebox.showerror("Olympia", f"No Inject script found! Please close Roblox and Synapse and join via the teleporter game again.")
                    return
                
                for rn in results:
                    result = rn
                    bres = self.synapse.d2h(result)
                    aobs = ""
                    for i in range(1, 16 + 1):
                        aobs = aobs + bres[i - 1 : i]
                    aobs = self.synapse.hex2le(aobs)
                    res = self.synapse.aobScan(aobs, True)
                    if res:
                        valid = False
                        for i in res:
                            result = i
                            if (
                                self.synapse.memory.read_longlong(result - 0x48 + 8)
                                == result - 0x48
                            ):
                                injectScript = result - 0x48
                                valid = True
                                break
                    if valid:
                        break

                if not injectScript:
                    messagebox.showerror("Olympia", f"No Inject script found! Please close Roblox and Synapse and join via the teleporter game again.")
                    return

                injectScript = Instance(injectScript, self.synapse)
                #b = self.synapse.memory.read_longlong(injectScript.self + 0x210)
                #self.synapse.memory.write_longlong(targetScript.self + 0x210, b)

                b = self.synapse.memory.read_bytes(injectScript.self + 0x100, 0x150)
                self.synapse.memory.write_bytes(targetScript.self + 0x100, b, len(b))

                self.injected = True

                answer = messagebox.askokcancel(
            title='Olympia',
            message='Equip the tool in your backpack and then press OK.', icon=messagebox.INFO)
                
                print("done")

                return targetScript
        else:
            messagebox.showinfo("Olympia", f"Already injected!")

    def refresh(self, _ = None):
        item = self.selectedItem
        nodeId = self.instanceTree.item(item, 'tags')[0]
        node = self.nodes[nodeId]

        if node["dummyChild"]:
            if node["childrenLoaded"]:
                for child in node["children"]:
                    self.instanceTree.delete(child)

            node["childrenLoaded"] = False
            node["children"] = []
            node["dummyChild"] = self.instanceTree.insert(item, 'end', text="???", open=False)

            self.initInstances(item)

    def refreshAll(self, _ = None):
        self.instanceTree.delete(self.rootItem)

        newItem = self.populateInstances(self.rootInstance, "", True, True)
        self.initInstances(newItem)

    def getClassIcon(self, className: str) -> str:
        if not os.path.exists(f"./assets/icons/{className}.png"):
            return f"./assets/icons/Unknown.png"
        
        return f"./assets/icons/{className}.png"
    
    def populateInstances(self, instance: Instance, parent: str = "", open: bool = False, root: bool = False) -> str:
        icon = tk.PhotoImage(file=self.getClassIcon(instance.ClassName))
        iconPadding = 8

        self.imageReferences.append(icon)

        newIcon = tk.PhotoImage(width=icon.width() + iconPadding, height=icon.height())
        newIcon.tk.call(newIcon, 'copy', icon, '-from', 0, 0, icon.width(), icon.height(), '-to', 0, 0)

        self.imageReferences.append(newIcon)

        nodeUuid = str(uuid.uuid4())
        itemId = self.instanceTree.insert(parent, 'end', text=instance.Name, tags=(nodeUuid,), image=newIcon, open=open)

        if root:
            self.rootItem = itemId

        dummyChildId = None
        parentUuid = None

        if instance.HasChildren:
            dummyChildId = self.instanceTree.insert(itemId, 'end', text="???", open=False)

        if len(parent) > 0:
            parentUuid = self.instanceTree.item(parent, 'tags')[0]

        self.nodes[nodeUuid] = {
            "item": itemId,
            "instance": instance,
            "parent": parentUuid,
            "childrenLoaded": False,
            "children": [],
            "dummyChild": dummyChildId
        }

        return itemId
    
    def initInstances(self, item: str):
        nodeUuid = self.instanceTree.item(item, 'tags')[0]
        node = self.nodes[nodeUuid]
        
        instance: Instance = node["instance"]

        if not node["childrenLoaded"]:
            if node["dummyChild"]:
                self.instanceTree.delete(node["dummyChild"])

            for child in instance.GetChildren():
                childId = self.populateInstances(child, item)
                node["children"].append(childId)
            
            node["childrenLoaded"] = True

    def initProperties(self, item: str):
        nodeUuid = self.instanceTree.item(item, 'tags')[0]
        node = self.nodes[nodeUuid]
        
        instance: Instance = node["instance"]

        for i in self.displayedProperties:
            self.propertyTree.delete(i)

        self.displayedProperties = []
        instanceProperties = [("Name", instance.Name), ("ClassName", instance.ClassName), ("Parent", instance.Parent), ("Address", f"0x{self.synapse.d2h(instance.self)}")]

        for i in instanceProperties:
            itemId = self.propertyTree.insert("", tk.END, values=(i[0], i[1]))
            self.displayedProperties.append(itemId)

    def onTreeOpen(self, event):
        self.selectedItem = self.instanceTree.focus()

        if self.instanceTree.item(self.selectedItem, 'tags'):
            self.initInstances(self.selectedItem)

    def onClick(self, event):
        self.selectedItem = self.instanceTree.focus()

        if self.instanceTree.item(self.selectedItem, 'tags'):
            self.initProperties(self.selectedItem)

    def render(self):
        self.populateInstances(self.rootInstance, "", True, True)
        self.initInstances(self.rootItem)
        self.instanceTree.pack(expand=True, fill=tk.BOTH)

        self.initProperties(self.rootItem)
        self.propertyTree.pack(expand=True, fill=tk.BOTH)

        self.root.mainloop()