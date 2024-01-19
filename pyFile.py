class DefBlock:
    def __init__(self, header, body):
        self.header = header
        self.body = body
        self.defName = body[0].rstrip()

    def addHeaderKv(self, KV):
        excludedMarks = ["@mark.needed_line"]
        finalHeaders = {}
        sHeaders = ''.join(self.header).split('@')
        sHeaders = list(filter(bool, sHeaders))

        # some magic to parse tags: [vals] . I hate text parsing
        for h in sHeaders:
            hr = h.replace("\n", "").replace(" ", "")
            tag = hr.split("(")[0].split(".")[-1]
            vals = hr.split("(")[1][:-1].split(",")
            vals = [v.replace("'", "").replace('"', "") for v in vals]
            finalHeaders[tag] = vals

        print(finalHeaders)

        # Check tokens and add keys, values accordingly
        for kv in KV:
            print(f"[INFO] Verifying: {kv}")
            if kv[0] in finalHeaders:
                print(f"[INFO] -> key '{kv[0]}' already present! Checking value..")
                if kv[1] in finalHeaders[kv[0]]:
                    print(f"[INFO] ->> value '{kv[1]}' already within key!")
                    # skip
                else:
                    print(f"[INFO] -x> value '{kv[1]}' NOT within key! Will add.")
                    # handle value add
                    finalHeaders[kv[0]].append(kv[1])

            else:
                print(f"[INFO] -x> key '{kv[0]}' NOT present! Will add.") # Shall add value too
                # handle key+value add
                finalHeaders[kv[0]] = [kv[1]]

        # assemble back
        self.header = []
        for k,v in finalHeaders.items():
            self.header.append(f"@mark.sc.{k}({','.join(v)})\n")
            # print(f"@mark.sc.{k}({','.join(v)})")

    def getText(self):
        # return self.header.getText() + ''.join(self.body)
        return ''.join(self.header) + ''.join(self.body)

    def __repr__(self):
        return f"Name: {self.defName}\nHeader: {self.header}\nBody: {self.body}"


class PyFile:
    def __init__(self, fileName, changedDefs):
        self.fileName = fileName
        self.changedDefs = changedDefs
        self.importBlock = []
        self.defBlocks = []
        self.headerMarker = "@mark.sc"
        self.bodyStartMarker = "starting_state"
        self.fileLines = []

        with open(self.fileName, 'r') as f:
            self.fileLines = f.readlines()

    def extractImportBlock(self):
        for ln in self.fileLines:
            if self.headerMarker not in ln:
                self.importBlock.append(ln)
            else:
                break

        self.extractDefBlocks()
    
    def extractDefBlocks(self):
        headerEnd = len(self.importBlock)

        # extract header start/end body start/end indexes
        markerDone = False
        indexes = []
        for i, ln in enumerate(self.fileLines[headerEnd:]):
            if self.headerMarker in ln and not markerDone:
                markerDone = True
                indexes.append(i+headerEnd)
            if self.bodyStartMarker in ln and markerDone:
                markerDone = False
                indexes.append(i+headerEnd)


        indexes.append(len(self.fileLines))


        # sliding window over of 2 over the indexes
        x = 0
        y = 1
        l = len(indexes)
        addToHeader = True
        headerLines = []
        bodyLines = []
        while y < l:
            for ln in range(indexes[x], indexes[y]):
                if addToHeader:
                    headerLines.append(self.fileLines[ln])
                else:
                    bodyLines.append(self.fileLines[ln])
            x += 1
            y += 1

            if not addToHeader:
                self.defBlocks.append(DefBlock(headerLines.copy(), bodyLines.copy()))
                headerLines = []
                bodyLines = []

            addToHeader = not addToHeader

        # self.getText()

    def getText(self):
        # return
        for ln in self.importBlock:
            print(ln, end='')
        for db in self.defBlocks:
            print(db.getText(), end='')
        
        # with open('test.py', 'w') as f:
        #     for ln in self.importBlock:
        #         f.writelines(ln)
        #     for db in self.defBlocks:
        #         f.writelines(db.getText())
    
