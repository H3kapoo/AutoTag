import re

CONFIG = {
    # general
    "max_row_len" : 50,
    "enable_logs" : True,
    # "enable_logs" : False
    # py specific
    "ignored_markers" : ["description", "dorondo"],
    "marker_to_split" : "@mark.sc.",
    "markers_end" : "@starting_state",
    # um spcific
    "comm_start" : "/**",
    "comm_end" : "**/",
    "footer_msg" : "Some copyright here"
}

DIFF_PATH = "file_bc.diff"
UTMT_FILE_RULE = "^\+\+\+.*/(ut|mt)/.*"
PY_FILE_RULE = "^\+\+\+.*/py/.*"
PY_REGEX_RULE = ".*@@ def .*"

class PyHeaderMarks():
    def __init__(self, data):
        self.data = data
        self.KVs = {}

        self.tokenize()

    def __log(self, msg, end='\n'):
        if CONFIG['enable_logs']:
            print(msg, end=end)

    def __str__(self):

        self.data = ''
        for k,v in self.KVs.items():
            newVs = ''
            keyLen = len(f"{CONFIG['marker_to_split']}{k}(")
            curLen = keyLen
            if k in CONFIG['ignored_markers']:
                self.data += f"{CONFIG['marker_to_split']}{k}({''.join(v)}\n"
            else:
                vLen = len(v)
                for i, vi in enumerate(v):
                    possibleNewVal = vi + (", " if i < vLen-1 else "")
                    possibleNewValLen = len(possibleNewVal)
                    nextLen = curLen + possibleNewValLen
                    if nextLen > CONFIG['max_row_len']:
                        newVs += "\n" + " "*keyLen
                        curLen = keyLen + possibleNewValLen
                    else:
                        curLen = nextLen
                    newVs += possibleNewVal
                self.data += f"{CONFIG['marker_to_split']}{k}({newVs})\n"
        return self.data

    def addKVs(self, newKVs):
        for k,v in newKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key {k} is already present. Checking value")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value {vi} is already present. Skipping")
                    else:
                        self.__log(f"[INFO] -- Value {vi} is NOT present. Adding it")
                        self.KVs[k].append(vi)
            else:
                self.__log(f"[INFO] Key {k} is NOT present. Adding key and value")
                self.KVs[k] = v

    def removeKVs(self, oldKVs):
        for k,v in oldKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key {k} is present. Checking value")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value {vi} is present inside key. Deleting it")
                        self.KVs[k].remove(vi)
                        if not len(self.KVs[k]):
                            self.__log(f"[INFO] -- Key {k} has no more elements. Deleting key.")
                            del self.KVs[k]
                    else:
                        self.__log(f"[INFO] -- Value {vi} is NOT present. Skipping it")
            else:
                self.__log(f"[INFO] Key {k} is NOT present. Nothing to do")

    def tokenize(self):
        markerSplitted = list(filter(None, self.data.split(CONFIG['marker_to_split'])))

        # Put keys and values into a dict
        for marker in markerSplitted:
            kvSplit = marker.split("(", 1)
            lastKv = None
            for i, kv in enumerate(kvSplit):
                if i%2 == 0:
                    self.KVs[kv] = []
                    lastKv = kv
                else:
                    if lastKv in CONFIG['ignored_markers']:
                        self.KVs[lastKv].append(kv)
                    else:
                        self.KVs[lastKv] =\
                            kv.replace(" ", "").replace("\n", "").replace('"', "")\
                                .replace("'", "").replace(")", "").split(",")
        

class PyBody():
    def __init__(self, lines):
        self.lines = lines

    def __str__(self):
        return self.lines


class PyFile():
    def __init__(self, fileChangeData):
        self.filePath = fileChangeData[0]
        self.changedDefs = fileChangeData[1]
        self.lines = []
        self.includeHeaders = ''
        self.tests = []

        self.__log(f"[INFO] Separating file {self.filePath} into blocks..");
        with open(self.filePath, 'r') as f:
            self.lines = f.readlines()
        self.separate()
        self.__log(f"[INFO] Separation done.");
        self.__log(f"[INFO] Functions needing modification: {self.changedDefs}");


    def separate(self):
        idx = 0
        dlimStart = CONFIG["marker_to_split"]
        dlimEnd = CONFIG["markers_end"]

        # Extract import part
        while dlimStart not in self.lines[idx]:
            self.includeHeaders += self.lines[idx]
            idx += 1
            if idx == len(self.lines):
                self.__log("[WRN] Looks like end of the file and no headers could be found :(")
                break

        # Extract marks and func body
        headerLines = []
        bodyLines = []
        while idx < len(self.lines):
            while dlimStart in self.lines[idx] or dlimEnd not in self.lines[idx]:
                headerLines.append(self.lines[idx])
                
                idx += 1
                if idx == len(self.lines):
                    break
            
            # While will exit when hitting dlimEnd but will not add the line, so
            # add it here
            headerLines.append(self.lines[idx-1])

            if idx == len(self.lines):
                break

            while dlimStart not in self.lines[idx]:
                bodyLines.append(self.lines[idx])
                idx += 1
                if idx == len(self.lines):
                    break
            
            # For the body part it's currently no need to join, but in the future we
            # might need it like so, so leave it like it is now
            self.tests.append((
                PyHeaderMarks(''.join(headerLines.copy())),
                PyBody(bodyLines.copy())
                ))

            headerLines = []
            bodyLines = []

    def addKVsToModifiedDefs(self, newKVs):
        for test in self.tests:
            for bLine in test[1].lines:
                if bLine[:-1] in self.changedDefs:
                    print(f"[INFO] Found function '{bLine[:-1]}' inside body that needs to be modified..")
                    test[0].addKVs(newKVs)

    def removeKVsToModifiedDefs(self, oldKVs):
        for test in self.tests:
            for bLine in test[1].lines:
                if bLine[:-1] in self.changedDefs:
                    print(f"[INFO] Found function '{bLine[:-1]}' inside body that needs to be modified..")
            test[0].removeKVs(oldKVs)

    def __str__(self):
        allNewLines = self.includeHeaders

        for v in self.tests:
            allNewLines += v[0].__str__() + ''.join(v[1].lines)

        return allNewLines

    def __log(self, msg, end='\n'):
        if CONFIG['enable_logs']:
            print(msg, end=end)


class UMFile():
    def __init__(self, filePath):
        self.filePath = filePath
        self.lines = []
        self.bodyStartIndex = 0
        self.footer = ''
        self.KVs = {}

        self.__log(f"[INFO] Separating file {self.filePath} into header & block..");
        with open(self.filePath, 'r') as f:
            self.lines = f.readlines()
        self.separate()
        self.__log(f"[INFO] Separation done.");

    def separate(self):
        headerData = ''
        bodyData = ''
        startMarkerFound = False

        # This assumes /** **/ correctly exist
        for i, ln in enumerate(self.lines):
            if CONFIG['comm_start'] in ln:
                startMarkerFound = True

            if startMarkerFound:
                headerData += ln

            if startMarkerFound and CONFIG['comm_end'] in ln:
                self.bodyStartIndex = i+1
                break
        
        # In case they dont exist, means file has no header data yet, create one
        if not startMarkerFound:
            headerData = f"{CONFIG['comm_start']}\n  * {CONFIG['footer_msg']}\n{CONFIG['comm_end']}\n"

        splittedHeader = headerData.split('\n')  
        tagsUnfiltered = splittedHeader[1:-4]
        tagsAlmostThere = ''.join([v.replace(" ", "").replace("*","") for v in tagsUnfiltered])
        
        # This is done in order to account for multiline tags
        tags = tagsAlmostThere.split("@")[1:]

        for tag in tags:
            k,v = tag.split(":")
            self.KVs[k] = v.split(",") 

        self.footer = splittedHeader[-3]

    def addKVsToModifiedDefs(self, newKVs):
        for k,v in newKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key {k} is already present. Checking value")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value {vi} is already present. Skipping")
                    else:
                        self.__log(f"[INFO] -- Value {vi} is NOT present. Adding it")
                        self.KVs[k].append(vi)
            else:
                self.__log(f"[INFO] Key {k} is NOT present. Adding key and value")
                self.KVs[k] = v

    def removeKVsToModifiedDefs(self, oldKVs):
        for k,v in oldKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key {k} is present. Checking value")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value {vi} is present inside key. Deleting it")
                        self.KVs[k].remove(vi)
                        if not len(self.KVs[k]):
                            self.__log(f"[INFO] -- Key {k} has no more elements. Deleting key.")
                            del self.KVs[k]
                    else:
                        self.__log(f"[INFO] -- Value {vi} is NOT present. Skipping it")
            else:
                self.__log(f"[INFO] Key {k} is NOT present. Nothing to do")

    def __str__(self):
        newHeader = ''

        # Assemble back
        newHeader += f"{CONFIG['comm_start']}\n"    
        for k,v in self.KVs.items():
            newVs = ''
            keyLen = len(f"  * @{k}: ")
            curLen = keyLen
            vLen = len(v)
            for i, vi in enumerate(v):
                possibleNewVal = vi + (", " if i < vLen-1 else "")
                possibleNewValLen = len(possibleNewVal)
                nextLen = curLen + possibleNewValLen
                if nextLen > CONFIG['max_row_len']:
                    newVs += "\n" + " "*keyLen
                    curLen = keyLen + possibleNewValLen
                else:
                    curLen = nextLen
                newVs += possibleNewVal

            newHeader += f"  * @{k}: {newVs}\n"
        newHeader += f"  *\n{self.footer}\n"
        newHeader += f"{CONFIG['comm_end']}\n\n"

        return newHeader + ''.join(self.lines[self.bodyStartIndex:])

    def __log(self, msg, end='\n'):
        if CONFIG['enable_logs']:
            print(msg, end=end)

def main():
    # File paths that need to have top headers updated
    interestingUtMtTokens = []

    # File paths + functions that need to have headers updated
    interestingPyTokens = {}

    with open(DIFF_PATH) as diffFile:
        pyLine = ""
        for line in diffFile.readlines():
            if re.search(UTMT_FILE_RULE, line):
                interestingUtMtTokens.append(line[6:-1])
            elif re.search(PY_FILE_RULE, line):
                lineNoEnd = line[:-1].split(" ")[1][2:]
                interestingPyTokens[lineNoEnd] = []
                pyLine = lineNoEnd
            elif re.search(PY_REGEX_RULE, line):
                lineStrip = line[:-1].split("@@")[2].lstrip()
                interestingPyTokens[pyLine].append(lineStrip)

    # umFiles = []
    # for v in interestingUtMtTokens:
    #     umFiles.append(UMFile(v))
    
    # umFiles[0].addKVsToModifiedDefs({"thats" : ["ceva_val"]})
    # # umFiles[0].removeKVsToModifiedDefs({"thats" : ["ceva_val"]})
    # with open('output.txt', 'w') as f:
    #     f.writelines(umFiles[0].__str__())
    # print(umFiles[0])

    for v in interestingUtMtTokens:
        p = UMFile(v)
        with open(p.filePath, 'w') as f:
            f.writelines(p.__str__())

    for v in interestingPyTokens.items():
        p = PyFile(v)
        with open(p.filePath, 'w') as f:
            f.writelines(p.__str__())

    # pyFiles[0].addKVsToModifiedDefs({"some_key": ["some_val"]})
    # print(pyFiles[0])


if __name__ == "__main__":
    main()

# h = PyHeader(DATA)
# h.tokenize()
# h.addKVs({'new_key': ['new_va']})
# h.removeKVs({'new_key': ['new_va']})
# print()
# h.getStr()
