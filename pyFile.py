class Header:
    def __init__(self, lines):
        self.kvPairs = {}
        self.lines = lines

    def addKVs(self, kvs):
        pass

    def getText(self):
        return ''.join(self.lines)

    def __repr__(self):
        return f"{self.lines}"


class DefBlock:
    def __init__(self, defName, header, body):
        self.header = header
        self.body = body
        self.defName = '?'#body[0].rstrip()

    def getText(self):
        return self.header.getText() + ''.join(self.body)

    def __repr__(self):
        return f"Name: {self.defName}\nHeader: {self.header}\nBody: {self.body}"


class PyFile:
    def __init__(self, fileName, changedDefs):
        self.fileName = fileName
        self.changedDefs = changedDefs
        self.importBlock = []
        self.defBlocks = []
        self.headerMarker = "@mark."
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

        headerLines = []
        bodyLines = []
        insideBody = False
        for ln in self.fileLines[headerEnd:]:
            if self.headerMarker in ln:
                if insideBody:
                    self.defBlocks.append(
                        DefBlock("name", Header(headerLines.copy()), bodyLines.copy()))
                    bodyLines = []
                    headerLines = []
                    insideBody = False
                headerLines.append(ln)
            else:
                insideBody = True
                bodyLines.append(ln)

        self.defBlocks.append(
            DefBlock("name", Header(headerLines.copy()), bodyLines.copy()))

        self.getText()

    def getText(self):
        # for ln in self.importBlock:
        #     print(ln, end='')
        # for db in self.defBlocks:
        #     print(db.getText(), end='')
        
        with open('test.py', 'w') as f:
            for ln in self.importBlock:
                f.writelines(ln)
            for db in self.defBlocks:
                f.writelines(db.getText())
    
