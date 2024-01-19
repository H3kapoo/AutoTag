import re


CONFIG = {
    "max_row_len" : 120,
    "ignored_markers" : ["description", "dorondo"],
    "marker_to_split" : "@mark.sc.",
    "markers_end" : "@starting_state",
    # "enable_logs" : True
    "enable_logs" : False
}

DIFF_PATH = "file_bc.diff"
UTMT_FILE_RULE = "^\+\+\+.*/(ut|mt)/.*"
PY_FILE_RULE = "^\+\+\+.*/py/.*"
PY_REGEX_RULE = ".* def .*"

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

        with open(self.filePath) as f:
            self.lines = f.readlines()
        self.separate()

    def separate(self):
        idx = 0
        dlimStart = CONFIG["marker_to_split"]
        dlimEnd = CONFIG["markers_end"]

        # Extract import part
        while dlimStart not in self.lines[idx]:
            self.includeHeaders += self.lines[idx]
            idx += 1

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
                ''.join(bodyLines.copy())
                ))
            headerLines = []
            bodyLines = []


    def __str__(self):
        allNewLines = self.includeHeaders

        for v in self.tests:
            allNewLines += v[0].__str__() + v[1]

        return allNewLines

def main():
    interestingUtMtTokens = []
    interestingPyTokens = {}

    with open(DIFF_PATH) as diffFile:
        pyLine = ""
        for i, line in enumerate(diffFile.readlines()):
            if re.search(UTMT_FILE_RULE, line):
                interestingUtMtTokens.append(line[:-1])
            elif re.search(PY_FILE_RULE, line):
                lineNoEnd = line[:-1].split(" ")[1][2:]
                interestingPyTokens[lineNoEnd] = []
                pyLine = lineNoEnd
            elif re.search(PY_REGEX_RULE, line):
                lineStrip = line[:-1].split("@@")[2].lstrip()
                interestingPyTokens[pyLine].append(lineStrip)

    pyFiles = []
    for v in interestingPyTokens.items():
        print(v)
        pyFiles.append(PyFile(v))

    print(pyFiles[0])
    # print(interestingPyTokens)
    # print()

    # pyFiles[0].extractImportBlock()
    # pyFiles[0].defBlocks[0].addHeaderKv(
    #     [("some_tag", "smt"), ("blank_region", "feat_val")])

    # pyFiles[0].getText()
    # pyFiles[0].defBlocks[1].addHeaderKv(("key", "value"))

if __name__ == "__main__":
    main()

# h = PyHeader(DATA)
# h.tokenize()
# h.addKVs({'new_key': ['new_va']})
# h.removeKVs({'new_key': ['new_va']})
# print()
# h.getStr()
