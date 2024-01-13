from __future__ import annotations

import time
import threading
import uuid

import tkinter as tk
from tkinter import ttk, messagebox

from synapse import Synapse
from objects import Instance

class Memview:
    def __init__(self, root: tk.Toplevel, synapse: Synapse) -> Memview:
        self.root = root
        self.synapse = synapse
        self.dataTypeNames = ["pointer", "int", "bool", "string"]
        self.leftFrame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        self.inputLabel = ttk.Label(self.leftFrame, text="Jump to:")
        self.inputEntry = ttk.Entry(self.leftFrame)
        self.confirmButton = ttk.Button(self.leftFrame, text="Confirm", command=self.onJump)
        self.readLabel = ttk.Label(self.leftFrame, text="Read:")
        self.dataTypeEntry = ttk.Combobox(self.leftFrame, values=self.dataTypeNames)
        self.pointerEntry = ttk.Entry(self.leftFrame)
        self.readConfirmButton = ttk.Button(self.leftFrame, text="Read", command=self.onRead)
        self.rightFrame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        self.hexViewer = tk.Text(self.rightFrame, wrap=tk.WORD, height=20, width=30, state=tk.DISABLED)
        self.currentAddress = 0
        self.readingActive = False

        # layout

        self.leftFrame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.inputLabel.grid(column=0, row=0, pady=0, sticky=tk.W)
        self.inputEntry.grid(column=0, row=1, pady=5, sticky=tk.W)
        self.confirmButton.grid(column=1, row=1, padx=5, pady=5, sticky=tk.W)

        self.dataTypeEntry.current(0)

        self.readLabel.grid(column=0, row=2, pady=0, sticky=tk.W)
        self.dataTypeEntry.grid(column=0, row=3, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.pointerEntry.grid(column=0, row=4, pady=0, sticky=tk.W)
        self.readConfirmButton.grid(column=1, row=4, padx=5, pady=0, sticky=tk.W)

        self.rightFrame.grid(column=1, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.hexViewer.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S))

    def watchAddress(self):
        lastData = ""
        while self.readingActive:
            data = self.synapse.memory.read_bytes(self.currentAddress, 512).hex()
            self.updateHexViewer(" ".join([data.upper()[i:i+2] for i in range(0, len(data), 2)]))

            if not lastData == data:
                print(" ".join([data.upper()[i:i+2] for i in range(0, len(data), 2)]))
                print()

            lastData = data
            time.sleep(0.5)

        print("ZIZZY BALLS ACK")

    def onJump(self):
        self.readingActive = False

        self.currentAddress = self.synapse.h2d(self.inputEntry.get().replace(" ", ""))
        self.readingActive = True
        
        thread = threading.Thread(target=self.watchAddress, name=f"Memview_{str(uuid.uuid4())}")
        thread.start()

    def onRead(self):
        self.readingActive = False

        dataType = self.dataTypeEntry.get()
        pointer = self.synapse.h2d(self.pointerEntry.get().replace(" ", ""))

        data = ""

        # " ".join([data.upper()[i:i+2] for i in range(0, len(data), 2)])

        if dataType == "pointer":
            data = self.synapse.d2h(self.synapse.memory.read_longlong(pointer))
            data = data.upper()
        elif dataType == "int":
            data = self.synapse.d2h(self.synapse.memory.read_int(pointer))
            data = data.upper()
        elif dataType == "bool":
            data = self.synapse.d2h(self.synapse.memory.read_bool(pointer))
            data = data.upper()
        elif dataType == "string":            
            data = self.synapse.readRobloxString(pointer)
        
        self.updateHexViewer(data)

        print(dataType, pointer, data)

    def updateHexViewer(self, data):
        self.hexViewer.config(state=tk.NORMAL)
        self.hexViewer.delete(1.0, tk.END)

        self.hexViewer.insert(tk.END, data)

        self.hexViewer.config(state=tk.DISABLED)

    def render(self):
        self.root.mainloop()