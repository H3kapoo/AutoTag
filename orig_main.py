import re
from itertools import chain

DIFF_PATH = "file_bc.diff"
UTMT_FILE_RULE = "^\+\+\+.*/(ut|mt)/.*"
PY_FILE_RULE = "^\+\+\+.*/py/.*"
PY_REGEX_RULE = ".* def .*"
KV = [("usecase", "SBTS_ceva_case"), ("usecase", "SBTS_ceva_case2"), ("usecase", "SBTS_ceva_case3")]
FOOTER = "Some Copyright 2024"
MAX_LINE = 30

def handleUTMTDiff(candidateFile):
    print(f'[INFO] File "{candidateFile}" is UT/MT one.')

    # Check if file starts with /** and save all contents in buffer between it and **/
    fullFile = []
    editBuffer = []
    shallAppend = False
    needToCreateBuffer = False # Create buffer from scratch if none is present in file
    lastLineNo = 0
    with open(candidateFile, 'r') as file:
        fullFile = file.readlines()
        for lineNo, line in enumerate(fullFile):

            if re.search("^/\*\*", line):
                print(f"[INFO] {lineNo} Line starts with /**")
                shallAppend = True

            if shallAppend:
                editBuffer.append(line)

            if re.search("^\*\*/", line):
                print(f"[INFO] {lineNo} Line ends with **/")
                shallAppend = False
                lastLineNo = lineNo+1 # Needed so we know where the non-edit buffer starts
                break

    # parse header into manageable tokens
    tokensDict = {}
    for line in editBuffer[1:-1]:
        sLine = line.split(":")
        if len(sLine) == 2:
            key = sLine[0].lstrip().rstrip().split(" ")[-1][1:]
            # values could also be space separated, but in the end they all need to be comma separated
            # This code ensures that norm
            values = [v.lstrip().rstrip() for v in sLine[1].rstrip().split(",")]
            vSplitted = [v.split(' ') for v in values]
            flattened = list(chain.from_iterable(vSplitted))
            tokensDict[key] = list(filter(str.strip, flattened)) 

    #TODO: Good place to do a swithc between k:v addition or removal

    # Check tokens and add keys, values accordingly
    for kv in KV:
        print(f"[INFO] Verifying: {kv}")
        if kv[0] in tokensDict:
            print(f"[INFO] -> key '{kv[0]}' already present! Checking value..")
            if kv[1] in tokensDict[kv[0]]:
                print(f"[INFO] ->> value '{kv[1]}' already within key!")
                # skip
            else:
                print(f"[INFO] -x> value '{kv[1]}' NOT within key! Will add.")
                # handle value add
                tokensDict[kv[0]].append(kv[1])

        else:
            print(f"[INFO] -x> key '{kv[0]}' NOT present! Will add.") # Shall add value too
            # handle key+value add
            tokensDict[kv[0]] = [kv[1]]

    print()
    print()


    # Construct new buffer according to KV supplied by user
    # Sort dict by alpha keys to keep consistency
    sortedTokensDict = dict(sorted(tokensDict.items(), key=lambda x: x[0].lower()))
    print("/**")
    for kv in sortedTokensDict.items():
        key = f"  * @{kv[0]}:"
        keyLen = len(key)
        print(key, end='')

        currLineLen = keyLen
        setValues = list(set(kv[1]))
        for i, v in enumerate(setValues):
            val = f" {v}," if i < len(setValues)-1 else f" {v}"
            currLineLen = currLineLen + len(val)
            if currLineLen > MAX_LINE:
                print(f"\n  *  {' ' * (keyLen-5)}", end='')
                currLineLen = keyLen
            print(val, end='')
        print()
    print(f"  *\n  * {FOOTER}")
    print("**/")

    # Write new buffer and rest of the file back
    with open('test.txt', 'w') as file:
        file.writelines("/**\n")
        for kv in sortedTokensDict.items():
            key = f"  * @{kv[0]}:"
            keyLen = len(key)
            file.writelines(key)

            currLineLen = keyLen
            setValues = list(set(kv[1]))
            for i, v in enumerate(setValues):
                val = f" {v}," if i < len(setValues)-1 else f" {v}"
                currLineLen = currLineLen + len(val)
                if currLineLen > MAX_LINE:
                    file.writelines(f"\n  *  {' ' * (keyLen-5)}")
                    currLineLen = keyLen
                file.writelines(val)
            file.writelines("\n")
        file.writelines(f"  *\n  * {FOOTER}\n")
        file.writelines("**/\n")


def handlePYDiff(candidateFile):
    print(f'[INFO] File "{candidateFile}" is PY one.')

    # # we shall find the "def" of the test given the edited zones
    # with open(candidateFile, 'r') as file:
    #     for line in file.readlines():
    #         if " def " in line:
    #             print("Contains")


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


    print(interestingPyTokens)
    for k,v in interestingPyTokens.items():
        lineNumbers = []
        with open(k, 'r') as pyf:
            fileLines = pyf.readlines()
            for i, line in enumerate(fileLines):
                for func in v:
                    if func in line:
                        print(f"Found {func} at line {i}")
                        lineNumbers.append(i)

        headerLines = []
        with open(k, 'r') as pyf:
            fileLines = pyf.readlines()

            for ln in lineNumbers:
                headerStartLnNo = ln
                headerLines.append(fileLines[headerStartLnNo].rstrip())
                while len(fileLines[headerStartLnNo].rstrip()):
                    headerStartLnNo -= 1
                    headerLines.append(fileLines[headerStartLnNo].rstrip())

                print(headerStartLnNo, ' ', ln)

        print(list(reversed(headerLines)))
    # for l in fileLines:
    #     print(l, end='')
    # for k,v in pyDefToLine:
    #     x = v
    #     line = fileLines[x].rstrip()
    #     while x != 0 and len(line):
    #         print(x+1)
    #         x -= 1
    #         line = fileLines[x].rstrip()

    # for k,v in interestingPyTokens.items():
    #     with open(k, 'r') as pyf:
    #         fileLines = pyf.readlines()
    #         for i, line in enumerate(fileLines):
    #             for func in v:
    #                 if func in line:
    #                     print(f"Found {func} at line {i}")
    #                     pyDefToLine.append((func, i))
    #                     # x = i
    #                     # upLine = fileLines[x]
    #                     # while x != 0 or len(upLine):
    #                     #     print(fileLines[x][:-1])
    #                     #     upLine = fileLines[x]
    #                     #     x = x-1

    # for k,v in pyDefToLine:
    #     x = v
    #     line = fileLines[x].rstrip()
    #     while x != 0 and len(line):
    #         print(x+1)
    #         x -= 1
    #         line = fileLines[x].rstrip()

# def main():
#     import fileinput

#     file_path = '/home/hekapoo/auto_tagger/test_bed/ut/file_c.txt'  # Replace with the actual path to your file
#     line_number_to_edit = 3  # Replace with the line number you want to edit

#     # Open the file in-place for editing
#     with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
#         for line_number, line in enumerate(file, start=1):
#             # Edit the line if it's the desired line
#             if line_number == line_number_to_edit:
#                 # Modify the line as needed
#                 # edited_line = line.replace('code', 'new_text')
#                 edited_line = "something new"
#                 print(edited_line, end='')
#             else:
#                 print(line, end='')

if __name__ == "__main__":
    main()