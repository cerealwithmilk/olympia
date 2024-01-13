from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from synapse import Synapse
from objects import Instance
from offsets import OffsetFinder

class Sigscan:
    def __init__(self, root: tk.Toplevel, synapse: Synapse) -> Sigscan:
        self.root = root
        self.synapse = synapse
        self.leftFrame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        self.inputLabel = ttk.Label(self.leftFrame, text="Signature:")
        self.inputEntry = ttk.Entry(self.leftFrame)
        self.confirmButton = ttk.Button(self.leftFrame, text="Confirm", command=self.onConfirm)
        self.listbox = tk.Listbox(self.leftFrame, selectmode=tk.SINGLE, height=16)
        self.rightFrame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        self.hexViewer = tk.Text(self.rightFrame, wrap=tk.WORD, height=20, width=30, state=tk.DISABLED)
        self.selectedItem = ""
        self.signature = ""
        self.signatureLength = 0

        self.leftFrame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.inputLabel.grid(column=0, row=0, sticky=tk.W)
        self.inputEntry.grid(column=0, row=1, pady=5, sticky=tk.W)
        self.confirmButton.grid(column=1, row=1, padx=5, pady=5, sticky=tk.W)

        self.listbox.grid(column=0, row=2, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.listbox.bind("<<ListboxSelect>>", self.onListboxSelect)

        self.rightFrame.grid(column=1, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.hexViewer.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.hexViewer.tag_config('match', background="yellow", foreground="red")

    def onConfirm(self):
        self.signature = self.inputEntry.get()
        self.signatureLength = int(len(self.signature) / 2)
        
        results = self.synapse.aobScan(self.signature, True)

        if results == []:
            messagebox.showerror("Sigscan", "No results found.")
            return
        
        for rn in results:
            try:
                bytes = self.synapse.memory.read_bytes(rn, self.signatureLength)
                print(f"signature match: 0x{self.synapse.d2h(rn)}, {bytes.hex()}")

                self.listbox.insert(tk.END, f"0x{self.synapse.d2h(rn)}")
            except:
                pass

    def onListboxSelect(self, event):
        self.selectedItem = self.listbox.get(self.listbox.curselection())
        self.updateHexViewer()

    def updateHexViewer(self):
        address = self.synapse.h2d(self.selectedItem)

        signBytes = self.synapse.memory.read_bytes(address, self.signatureLength)
        signHex = signBytes.hex()

        tailBytes = self.synapse.memory.read_bytes(address + self.signatureLength, 0x20)
        tailHex = tailBytes.hex()

        signHexData = " ".join([signHex.upper()[i:i+2] for i in range(0, len(signHex), 2)])
        tailHexData = " ".join([tailHex.upper()[i:i+2] for i in range(0, len(tailHex), 2)])

        self.hexViewer.config(state=tk.NORMAL)
        self.hexViewer.delete(1.0, tk.END)

        self.hexViewer.insert(tk.END, signHexData, 'match')
        self.hexViewer.insert(tk.END, " " + tailHexData)

        self.hexViewer.config(state=tk.DISABLED)

    def render(self):
        self.root.mainloop()