TEST_DATA = '''imoport a,b
import s ffe gr

import a f gr


@mark.sc.some_tag('smt','smt2','22')
@mark.sc.blank_region('asmt','asmt2','ass',


    'a22','feat_val')
@mark.sc.needed_line('blablahere
    some descriere here')
@starting_state(cevac)
def test1(some some fe
    fefe)
{
    code code
    code code
        code code    code code    code code
            code code
    code code    code code

    code code    code code

        code code
                code cod
    code code
        code code change
    code code
}


@mark.sc.blank_region('smth hre', 'and here')
@mark.sc.needed_line('here' 'bla' 'bla' 'too')
@starting_state(sss)
def test2(some some)
{
    code code
    code code
        code code    code code    code code
            code code
    code code    code code

    code code    code code

        code code
                code cod
    code code
        code code change2
    code code
}
'''

class FuncBlock:
    def __init__(self, headerLines, bodyLines):
        # self.headerLines = headerLines
        # self.bodyLines = bodyLines
        # self.headerLines = '\n'.join(headerLines)
        self.headerLines = headerLines
        self.bodyLines = '\n'.join(bodyLines)
        self.newLines = []
        ignoredLines = "needed_line"

        # Transformation needed in order to catch multiline key value pairs
        # for ln in self.headerLines.split(")"):
        #     if ignoredLines not in ln:
        #         self.newLines.append(ln.replace("\n","").replace(" ", "") + ")")
        #     else:
        #         self.newLines.append(ln.replace("\n","") + ")")
        
        print(self.headerLines)

        # KV = dict()
        # for ln in self.newLines:
        #     ln.split()
        # print([x.replace("\n","").replace(" ", "") for x in self.headerLines.split(")")])            


class PyFileTokenizer:
    def __init__(self, pyFileData, config):
        self.lines =  pyFileData.split("\n")
        self.config = config
        self.importPart = []
        self.functionBlocks = []
        self.sectionsIdxs = [0]

        self.sectionFile()

    def sectionFile(self):
        idx = 0
        dlimStart = self.config["header_start"]
        dlimEnd = self.config["header_end"]

        # Extract import part
        while dlimStart not in self.lines[idx]:
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

            if idx == len(self.lines):
                break

            while dlimStart not in self.lines[idx]:
                bodyLines.append(self.lines[idx])
                idx += 1
                if idx == len(self.lines):
                    break

            self.functionBlocks.append(FuncBlock(headerLines.copy(), bodyLines.copy()))
            headerLines = []
            bodyLines = []

        # for b in self.functionBlocks:
        #     print(b.headerLines)
            # print(b.bodyLines)


def main():
    config = {"header_start" : "@mark.", "header_end" : "@starting_state"}
    pf = PyFileTokenizer(TEST_DATA, config)

if __name__ == "__main__":
    main()