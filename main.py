import re

CONFIG = {
    # general
    "max_row_len" : 120,
    "enable_logs" : True,
    # "enable_logs" : False
    # py specific
    "ignored_markers" : ["description", "parametrize"],
    "marker_to_split" : "@pytest.mark.",
    "markers_end" : "@starting_state",
    # "markers_end" : "def ",
    # um spcific
    "comm_start" : "/**",
    "comm_end" : "**/",
    "footer_hint" : "Copyright",
    "footer_msg" : "Copyright Me 2024"
}

DIFF_PATH = "file_bc.diff"
UTMT_FILE_RULE = "^\+\+\+.*/(ut|mt)/.*"
PY_FILE_RULE = "^\+\+\+.*/py/.*"
PY_REGEX_RULE = ".*@@ def .*"
PY_REGEX_RULE_SECONDARY = ".*\+def .*"


class PyHeaderMarks():
    def __init__(self, data, shouldTokenize):
        self.data = data
        self.KVs = {}
        self.shouldTokenize = shouldTokenize

        # Not all headers in a file will change, so tokenize only those who will
        if shouldTokenize:
            self.tokenize()

    def __log(self, msg, end='\n'):
        if CONFIG['enable_logs']:
            print(msg, end=end)

    def addKVs(self, newKVs):
        for k,v in newKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key ''{k}'' is already present. Checking value..")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value ''{vi}'' is already present. Skipping it.")
                    else:
                        self.__log(f"[INFO] -- Value ''{vi}'' is NOT present. Adding it.")
                        self.KVs[k].append(vi)
            else:
                self.__log(f"[INFO] Key ''{k}'' is NOT present. Adding key and value(s) ''{','.join(v)}''")
                self.KVs[k] = v

    def removeKVs(self, oldKVs):
        for k,v in oldKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key ''{k}'' is present. Checking value..")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value ''{vi}'' is present inside key. Deleting it.")
                        self.KVs[k].remove(vi)
                        if not len(self.KVs[k]):
                            self.__log(f"[INFO] -- Key ''{k}'' has no more elements. Deleting key.")
                            del self.KVs[k]
                    else:
                        self.__log(f"[INFO] -- Value ''{vi}'' is NOT present. Skipping it.")
            else:
                self.__log(f"[INFO] Key ''{k}'' is NOT present. Nothing to do.")

    def tokenize(self):
        markerSplitted = list(filter(None, self.data.split(CONFIG['marker_to_split'])))

        # start state doesn't obey 'marker_to_split' syntax

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

    def __str__(self):
        if not self.shouldTokenize:
            return self.data

        self.data = ''
        for k,v in self.KVs.items():
            newVs = ''
            keyLen = len(f"{CONFIG['marker_to_split']}{k}(")
            curLen = keyLen
            if k in CONFIG['ignored_markers']:
                self.data += f"{CONFIG['marker_to_split']}{k}({''.join(v)}"
            else:
                vLen = len(v)
                for i, vi in enumerate(v):
                    possibleNewVal = "'" + vi +  "'" + (", " if i < vLen-1 else "")
                    possibleNewValLen = len(possibleNewVal)
                    nextLen = curLen + possibleNewValLen
                    if nextLen >= CONFIG['max_row_len']:
                        newVs += "\n" + " "*keyLen
                        curLen = keyLen + possibleNewValLen
                    else:
                        curLen = nextLen
                    newVs += possibleNewVal
                self.data += f"{CONFIG['marker_to_split']}{k}({newVs})\n"

            # Quick fix for space remaining after last item on line
            self.data = self.data.replace(" \n", "\n")
        return self.data


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

        # Extract import part
        while CONFIG["marker_to_split"] not in self.lines[idx]:
            self.includeHeaders += self.lines[idx]
            idx += 1
            if idx == len(self.lines):
                self.__log("[WARN] Looks like end of the file and no headers could be found :(")
                return
        
        for x in ''.join(self.lines[idx:]).split("\n\n\n"):
            headerLines = ''
            bodyLines = ''
            idx = 0
            lines = x.split("\n")
            while CONFIG["markers_end"] not in lines[idx] and "def " not in lines[idx]:
                headerLines += lines[idx] + "\n"
                idx +=1
                
                if idx == len(lines):
                    break

            bodyLines = '\n'.join(lines[idx:])
            shouldTokenize = False
            for bLine in lines[idx:]:
                if bLine in self.changedDefs:
                    self.__log(f"[INFO] Function '{bLine}' changed and needs to be tokenized..")
                    shouldTokenize = True
                    break
            
            # For the body part it's currently no need to join, but in the future we
            # might need it like so, so leave it like it is now
            self.tests.append((
                PyHeaderMarks(headerLines, shouldTokenize),
                PyBody(bodyLines)
                ))
            
    def addKVsToModifiedDefs(self, newKVs):
        self.__log(f"[INFO] {'-'*10} Addition Step ({self.filePath}) {'-'*10}")
        for test in self.tests:
            for bLine in test[1].lines.split("\n"):
                if bLine in self.changedDefs:
                    self.__log(f"[INFO] Found function '{bLine}' inside body that needs to be modified..")
                    test[0].addKVs(newKVs)
        self.__log(f"[INFO] {'-'*10} Done ({self.filePath}) {'-'*10}")


    def removeKVsToModifiedDefs(self, oldKVs):
        self.__log(f"[INFO] {'-'*10} Removal Step ({self.filePath}) {'-'*10}")
        for test in self.tests:
            for bLine in test[1].lines:
                if bLine[:-1] in self.changedDefs:
                    self.__log(f"[INFO] Found function '{bLine[:-1]}' inside body that needs to be modified..")
            test[0].removeKVs(oldKVs)
        self.__log(f"[INFO] {'-'*10} Done ({self.filePath}) {'-'*10}")

    def __str__(self):
        allNewLines = self.includeHeaders

        for i, v in enumerate(self.tests):
            allNewLines += v[0].__str__() + v[1].__str__() + ("\n\n\n" if i < len(self.tests)-1 else "")
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
        # If headers are of the type /* ... */, this is incorrect input and will lead to errors.
        if not startMarkerFound:
            headerData = f"{CONFIG['comm_start']}\n * {CONFIG['footer_msg']}\n{CONFIG['comm_end']}\n"

        splittedHeader = headerData.split('\n')
        
        # Find "footer". Because not all files are standardized, sometimes the copyright footer is at the top of the
        # tags..
        tagsUnfiltered = []
        for ln in splittedHeader:
            if CONFIG['footer_hint'] in ln:
                self.footer = ln
            else:
                tagsUnfiltered.append(ln)

        # Note: we would need to replace " "s also, but some files dont have the ":" delimiter between
        #       the tag and the values
        tagsAlmostThere = ''.join([v.replace("*", "").replace("/", "") for v in tagsUnfiltered])

        # This is done in order to account for multiline tags
        tags = tagsAlmostThere.split("@")[1:]

        for tag in tags:
            # This if/else if needed because not all files have : separator
            vals = tag.split(":")
            if len(vals) == 2:
                vals[1] = vals[1].replace(" ", "")
                self.KVs[vals[0]] = vals[1].split(",")
            else:
                self.__log(f"[WARN] >>> One of the tags is not properly formatted (no : delimiter). Resolving..")
                newFilteredTags = list(filter(None, vals[0].split(" ")))
                newKey = newFilteredTags[0]
                newVals = [x.replace(",", "") for x in newFilteredTags[1:]]
                self.KVs[newKey] = newVals

    def addKVsToModifiedDefs(self, newKVs):
        self.__log(f"[INFO] >>> Addition Step For ({self.filePath}) <<< ")
        for k,v in newKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key {k} is already present. Checking value..")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value ''{vi}'' is already present. Skipping it.")
                    else:
                        self.__log(f"[INFO] -- Value ''{vi}'' is NOT present. Adding it.")
                        self.KVs[k].append(vi)
            else:
                self.__log(f"[INFO] Key ''{k}'' is NOT present. Adding key and value(s) ''{','.join(v)}''")
                self.KVs[k] = v
        self.__log(f"[INFO] {'-'*10} Done {'-'*10}\n")

    def removeKVsToModifiedDefs(self, oldKVs):
        self.__log(f"[INFO] {'-'*10} Removal Step ({self.filePath}) {'-'*10}")
        for k,v in oldKVs.items():
            if k in self.KVs:
                self.__log(f"[INFO] Key ''{k}'' is present. Checking value..")
                for vi in v:
                    if vi in self.KVs[k]:
                        self.__log(f"[INFO] -- Value ''{vi}'' is present inside key. Deleting it")
                        self.KVs[k].remove(vi)
                        if not len(self.KVs[k]):
                            self.__log(f"[INFO] -- Key ''{k}'' has no more elements. Deleting key.")
                            del self.KVs[k]
                    else:
                        self.__log(f"[INFO] -- Value ''{vi}'' is NOT present. Skipping it.")
            else:
                self.__log(f"[INFO] Key ''{k}'' is NOT present. Nothing to do.")
        self.__log(f"[INFO] {'-'*10} Done {'-'*10}\n")

    def __str__(self):
        newHeader = ''

        # Assemble back
        newHeader += f"{CONFIG['comm_start']}\n"
        for k,v in self.KVs.items():
            newVs = ''
            keyLen = len(f" * @{k}: ")
            curLen = keyLen
            vLen = len(v)
            for i, vi in enumerate(v):
                possibleNewVal = vi + (", " if i < vLen-1 else "")
                possibleNewValLen = len(possibleNewVal)
                nextLen = curLen + possibleNewValLen
                if nextLen >= CONFIG['max_row_len']:
                    newVs += "\n *" + " "*(keyLen-2)
                    curLen = keyLen + possibleNewValLen
                else:
                    curLen = nextLen
                newVs += possibleNewVal

            newHeader += f" * @{k}: {newVs}\n"
        newHeader += f" *\n{self.footer}\n"
        newHeader += f"{CONFIG['comm_end']}\n\n"

        # Quick fix for space remaining after last item on line
        newHeader = newHeader.replace(" \n", "\n")

        return newHeader + ''.join(self.lines[self.bodyStartIndex:])

    def __log(self, msg, end='\n'):
        if CONFIG['enable_logs']:
            print(msg, end=end)


def main():
    # Note: If new tests are introduced, secondary py regex rule will be used

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
            elif re.search(PY_REGEX_RULE_SECONDARY, line):
                lineStrip = line[:-1].split("+")[1].lstrip()
                interestingPyTokens[pyLine].append(lineStrip)

    for v in interestingUtMtTokens:
        p = UMFile(v)
        p.addKVsToModifiedDefs({"new_tag" : ["newFeat", "next"]})

    #     # print(p.__str__())
        with open(p.filePath, 'w') as f:
            f.writelines(p.__str__())

    for v in interestingPyTokens.items():
        p = PyFile(v)
        p.addKVsToModifiedDefs({"new_tag" : ["newFeat"]})
        with open(p.filePath, 'w') as f:
            f.writelines(p.__str__())
        # print(p.__str__())

if __name__ == "__main__":
    main()
