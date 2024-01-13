import ctypes
import random
import string
import time
import sys
import os
import shutil
import json
import httpx
import threading
import pyautogui
import webview
import pyperclip
from plyer import notification

from synapse import Synapse
from objects import Instance

synapse = Synapse()
cwd = os.path.dirname(os.path.abspath(sys.argv[0]))

def newest(path, target_string):
    files = os.listdir(path)
    matching_files = [os.path.join(path, basename) for basename in files if target_string in basename]

    if not matching_files:
        return None  # No matching files found

    return max(matching_files, key=os.path.getctime)

def getClientReplicatorFromFlog():
    latestLogFile = newest(f"{os.getenv('LOCALAPPDATA')}\\Roblox\\logs", "Player")
    log = open(latestLogFile, 'r', encoding="utf8")
    lines = log.readlines()

    lines.reverse()

    for line in lines:
        if "Replicator created:" in line:
            line = line.strip()
            synapse.addresses["clientReplicator"] = synapse.h2d(line[len(line) - 16:])

            break

print()

def HttpGet(payload):
    url = payload["request"]["url"]
    return httpx.get(url).text

def readfile(payload):
    path = os.path.join(cwd, payload["request"]["path"])

    if os.path.exists(path):
        file = open(path, "r", encoding="utf8")
        result = file.read()
        
        return result
    else:
        return None

def writefile(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    data = payload["request"]["data"]

    file = open(path, "w", encoding="utf8")
    file.write(data)
    file.close()

def listfiles(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    print(path, os.listdir(path))
    return os.listdir(path)

def makefolder(payload):
    path = os.path.join(cwd, payload["request"]["path"])

    if not os.path.exists(path):
        os.makedirs(path)

def appendfile(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    data = payload["request"]["data"]

    file = open(path, "a", encoding="utf8")
    file.write(data)
    file.close()

def isfile(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    return os.path.isfile(path)

def isfolder(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    return os.path.isdir(path)

def delfile(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    os.remove(path)

def delfolder(payload):
    path = os.path.join(cwd, payload["request"]["path"])
    shutil.rmtree(path)

def identifyexecutor():
    return { "name": "Olympia", "version": "Beta" }

def setclipboard(payload):
    data = payload["request"]["data"]
    pyperclip.copy(data)

def focus_window():
    hwnd = ctypes.windll.user32.FindWindowW(None, "Roblox")
    ctypes.windll.user32.ShowWindow(hwnd, 5)
    ctypes.windll.user32.SetForegroundWindow(hwnd)

VK_TAB = 0x09
VK_ENTER = 0x0D
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02

def keypress(keycode):
    pyautogui.press(chr(keycode))

def mouse1click():
    if is_window_active():
        pyautogui.click(button='left')

def mouse1press():
    if is_window_active():
        pyautogui.mouseDown(button='left')

def mouse1release():
    if is_window_active():
        pyautogui.mouseUp(button='left')

def mouse2click():
    if is_window_active():
        pyautogui.click(button='right')

def mouse2press():
    if is_window_active():
        pyautogui.mouseDown(button='right')

def mouse2release():
    if is_window_active():
        pyautogui.mouseUp(button='right')

def is_window_active():
    return ctypes.windll.user32.GetForegroundWindow() == pyautogui.getWindowsWithTitle("ROBLOX")[0]._hWnd

def randomstring(payload):
    length = payload["request"]["length"]
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

lastRaw = ""
lastBuffer = 0x0
robloxToPython = None
pythonToRoblox = None
injected = False

def inject():
    global lastRaw, lastBuffer, robloxToPython, pythonToRoblox, injected

    while True:
        if synapse.yieldForProgram("RobloxPlayerBeta.exe", True, 60):
            break
        if synapse.yieldForProgram("Windows10Universal.exe", True, 60):
            break

    getClientReplicatorFromFlog()

    clientReplicator = Instance(synapse.addresses["clientReplicator"], synapse)
    game = clientReplicator.Parent.Parent
    players = game.Players
    localPlayer = Instance(synapse.memory.read_longlong(players.self + synapse.offsets["localPlayer"]), synapse)
    
    if localPlayer.Backpack.GetChildren() == []:
        notification.notify(
            title = "Olympia",
            message = "You have no tools in your backpack!",
            timeout = 10
        )
        return
    
    targetTool = None
    
    for tool in localPlayer.Backpack.GetChildren():
        if tool.FindFirstChildOfClass("LocalScript"):
            targetTool = tool
            break
    
    targetScript = targetTool.FindFirstChildOfClass("LocalScript")
    
    if not targetScript:
        notification.notify(
            title = "Olympia",
            message = "No tools in your backpack contain any scripts - we can't inject. Sorry!",
            timeout = 10
        )
        return

    injectScript = None
    results = synapse.aobScan("496E6A656374????????????????????06", True)
    valid = False

    if results == []:
        notification.notify(
            title = "Olympia",
            message = "Couldn't find the required scripts for injection. Try closing Roblox and rejoining the teleporter game.",
            timeout = 10
        )
        return
    
    for rn in results:
        result = rn
        bres = synapse.d2h(result)
        aobs = ""
        for i in range(1, 16 + 1):
            aobs = aobs + bres[i - 1 : i]
        aobs = synapse.hex2le(aobs)
        res = synapse.aobScan(aobs, True)
        if res:
            valid = False
            for i in res:
                result = i
                if (
                    synapse.memory.read_longlong(result - 0x48 + 8)
                    == result - 0x48
                ):
                    injectScript = result - 0x48
                    valid = True
                    break
        if valid:
            break

    injectScript = Instance(injectScript, synapse)
    #b = self.synapse.memory.read_longlong(injectScript.self + 0x210)
    #self.synapse.memory.write_longlong(targetScript.self + 0x210, b)

    b = synapse.memory.read_bytes(injectScript.self + 0x100, 0x150)
    synapse.memory.write_bytes(targetScript.self + 0x100, b, len(b))

    injected = True

    notification.notify(
        title = "Olympia",
        message = f"Injected into Roblox successfully! Equip the tool \"{targetTool.Name}\" in your backpack to load the internal UI.",
        timeout = 10
    )

    bridgeScript = targetScript
    bridge = bridgeScript

    while True:
        if bridge.RobloxToPython and bridge.PythonToRoblox:
            break

    robloxToPython = bridge.RobloxToPython
    pythonToRoblox = bridge.PythonToRoblox

    print(f"Bridge: 0x{synapse.d2h(bridge.self)}")
    print(f"Interface: 0x{synapse.d2h(robloxToPython.self)}")

    print()

    def watch():
        global lastRaw, lastBuffer, robloxToPython, pythonToRoblox, injected

        while True:
            if not localPlayer.PlayerGui.Executor:
                print("[*] player *most likely* died so we'll bring back the gui for them in the tool if possible")

                if localPlayer.Backpack.GetChildren() == []:
                    notification.notify(
                        title = "Olympia",
                        message = "You have no tools in your backpack!",
                        timeout = 10
                    )
                    return
                
                targetTool = None
                
                for tool in localPlayer.Backpack.GetChildren():
                    if tool.FindFirstChildOfClass("LocalScript"):
                        targetTool = tool
                        break
                
                targetScript = targetTool.FindFirstChildOfClass("LocalScript")
                
                if not targetScript:
                    notification.notify(
                        title = "Olympia",
                        message = "No tools in your backpack contain any scripts - we can't reinject. Sorry!",
                        timeout = 10
                    )
                    return

                b = synapse.memory.read_bytes(injectScript.self + 0x100, 0x150)
                synapse.memory.write_bytes(targetScript.self + 0x100, b, len(b))

                bridgeScript = targetScript
                bridge = bridgeScript

                while True:
                    if bridge.RobloxToPython and bridge.PythonToRoblox:
                        break

                robloxToPython = bridge.RobloxToPython
                pythonToRoblox = bridge.PythonToRoblox

                print("[+] reinjected... sigh\n")

                print(f"[+] got Bridge: 0x{synapse.d2h(bridge.self)}")
                print(f"[+] got Interface: 0x{synapse.d2h(robloxToPython.self)}")

            stringAddress = synapse.memory.read_longlong(robloxToPython.self + 0xC0)
            raw = ""

            if stringAddress > 0:
                length = synapse.memory.read_longlong(robloxToPython.self + 0xD0)
                raw = synapse.readRobloxString(stringAddress, length)
                
                if len(raw) > 0 and not raw == lastRaw:
                    print(raw)
                    payload = json.loads(raw)

                    if not payload["fulfilled"] and not payload["type"] == "execute":
                        match payload["type"]:
                            case "HttpGet":
                                payload["result"] = HttpGet(payload)
                                payload["fulfilled"] = True

                            case "readfile":
                                payload["result"] = readfile(payload)
                                payload["fulfilled"] = True

                            case "writefile":
                                writefile(payload)
                                payload["fulfilled"] = True

                            case "listfiles":
                                payload["result"] = listfiles(payload)
                                payload["fulfilled"] = True

                            case "makefolder":
                                makefolder(payload)
                                payload["fulfilled"] = True

                            case "appendfile":
                                appendfile(payload)
                                payload["fulfilled"] = True

                            case "isfile":
                                payload["result"] = isfile(payload)
                                payload["fulfilled"] = True

                            case "isfolder":
                                payload["result"] = isfolder(payload)
                                payload["fulfilled"] = True

                            case "delfile":
                                delfile(payload)
                                payload["fulfilled"] = True

                            case "delfolder":
                                delfolder(payload)
                                payload["fulfilled"] = True

                            case "identifyexecutor":
                                payload["result"] = identifyexecutor()
                                payload["fulfilled"] = True

                            case "setclipboard":
                                setclipboard(payload)
                                payload["fulfilled"] = True

                            case "focusroblox":
                                focus_window()
                                payload["fulfilled"] = True

                            case "iswindowactive":
                                payload["result"] = is_window_active()
                                payload["fulfilled"] = True
                            
                            case "mouse1click":
                                if not is_window_active(): focus_window()
                                mouse1click()

                                payload["fulfilled"] = True
                            
                            case "mouse1press":
                                if not is_window_active(): focus_window()
                                mouse1press()

                                payload["fulfilled"] = True
                            
                            case "mouse1release":
                                if not is_window_active(): focus_window()
                                mouse1release()

                                payload["fulfilled"] = True
                            
                            case "mouse2click":
                                if not is_window_active(): focus_window()
                                mouse2click()

                                payload["fulfilled"] = True
                            
                            case "mouse2press":
                                if not is_window_active(): focus_window()
                                mouse2press()

                                payload["fulfilled"] = True
                            
                            case "mouse2release":
                                if not is_window_active(): focus_window()
                                mouse2release()

                                payload["fulfilled"] = True
                            
                            case "randomstring":
                                payload["result"] = randomstring(payload)
                                payload["fulfilled"] = True

                            case _:
                                pass

                        newString = json.dumps(payload)
                        newStringPtr = synapse.memory.allocate(len(newString))
                        synapse.memory.write_string(newStringPtr, newString)

                        synapse.memory.write_bytes(pythonToRoblox.self + 0xD0, bytes.fromhex(synapse.hex2le(synapse.d2h(len(newString)))), 8)
                        synapse.memory.write_longlong(pythonToRoblox.self + 0xC0, newStringPtr)

                        print(f"wrote new string to ptr: 0x{synapse.d2h(newStringPtr)}, length {hex(len(newString))}")

            lastRaw = raw
            time.sleep(1)

    thread = threading.Thread(target=watch)
    thread.start()

def execute(code):
    if not injected:
        thread = threading.Thread(target=inject)
        thread.start()

        while True:
            if injected:
                break

    newString = json.dumps({
        "type": "execute",
        "request": {
            "string": "task.spawn(function() "+ code + " end)"
        },
        "fulfilled": False,
        "result": ""
    })
    
    newStringPtr = synapse.memory.allocate(len(newString))
    synapse.memory.write_string(newStringPtr, newString)

    synapse.memory.write_bytes(pythonToRoblox.self + 0xD0, bytes.fromhex(synapse.hex2le(synapse.d2h(len(newString)))), 8)
    synapse.memory.write_longlong(pythonToRoblox.self + 0xC0, newStringPtr)

    print(f"wrote new string to ptr: 0x{synapse.d2h(newStringPtr)}, length {hex(len(newString))}")

window = webview.create_window(
    'Olympia', 'index.html', width=500, height=300, frameless=True, on_top=True
)

window.expose(execute, inject)
webview.start()