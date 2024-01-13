import re
from itertools import chain

DIFF_PATH = "file_bc.diff"
UTMT_FILE_RULE = "^\+\+\+.*/(ut|mt)/.*"
PY_FILE_RULE = "^\+\+\+.*/py/.*"
PY_REGEX_RULE = ".* def .*"
KV = [("usecase", "SBTS_ceva_case"), ("usecase", "SBTS_ceva_case2"), ("usecase", "SBTS_ceva_case3")]
FOOTER = "Some Copyright 2024"
MAX_LINE = 30

from pyFile import PyFile

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
    for k, v in interestingPyTokens.items():
        pyFiles.append(PyFile(k, v))
    # print(interestingPyTokens)
    # print()

    pyFiles[0].extractImportBlock()

if __name__ == "__main__":
    main()