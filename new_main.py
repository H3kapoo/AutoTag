

MAX_LEN = 70

def tokenize():
    MARKER_TO_SPLIT = "@pytest.mark."
    IGNORED_MARKERS = ["description", "dorondo"]
    markerSplitted = list(filter(None, DATA.split(MARKER_TO_SPLIT)))

    newKVs = {'use_case' : ['usc2', 'usc34', "CellMgmt_5gCellModification"]}

    # Put keys and values into a dict
    KVs = dict()
    for marker in markerSplitted:
        kvSplit = marker.split("(", 1)
        lastKv = None
        for i, kv in enumerate(kvSplit):
            if i%2 == 0:
                KVs[kv] = []
                lastKv = kv
            else:
                if lastKv in IGNORED_MARKERS:
                    KVs[lastKv].append(kv)
                else:
                    KVs[lastKv] =\
                        kv.replace(" ", "").replace("\n", "").replace('"', "")\
                            .replace("'", "").replace(")", "").split(",")
    
    # # add keys/values
    # for k,v in newKVs.items():
    #     if k in KVs:
    #         print(f"[INFO] Key {k} is already present. Checking value")
    #         for vi in v:
    #             if vi in KVs[k]:
    #                 print(f"[INFO] -- Value {vi} is already present. Skipping")
    #             else:
    #                 print(f"[INFO] -- Value {vi} is NOT present. Adding it")
    #                 KVs[k].append(vi)
    #     else:
    #         print(f"[INFO] Key {k} is NOT present. Adding key and value")
    #         KVs[k] = v

    # remove keys/values
    for k,v in newKVs.items():
        if k in KVs:
            print(f"[INFO] Key {k} is present. Checking value")
            for vi in v:
                if vi in KVs[k]:
                    print(f"[INFO] -- Value {vi} is present inside key. Deleting it")
                    KVs[k].remove(vi)
                    if not len(KVs[k]):
                        print(f"[INFO] -- Key {k} has no more elements. Deleting key.")
                        del KVs[k]
                else:
                    print(f"[INFO] -- Value {vi} is NOT present. Skipping it")
        else:
            print(f"[INFO] Key {k} is NOT present. Nothing to do")

    # Asseble key/value dict back into printable form
    for k,v in KVs.items():
        newVs = ''
        keyLen = len(f"{MARKER_TO_SPLIT}{k}(")
        curLen = keyLen
        if k in IGNORED_MARKERS:
            print(f"{MARKER_TO_SPLIT}{k}({''.join(v)}", end='')
        else:
            for i, vi in enumerate(v):
                possibleNewVal = vi + (", " if i < len(v)-1 else "")
                possibleNewValLen = len(possibleNewVal)
                nextLen = curLen + possibleNewValLen
                if nextLen > MAX_LEN:
                    newVs += "\n" + " "*keyLen
                    curLen = keyLen + possibleNewValLen
                else:
                    curLen = nextLen
                newVs += possibleNewVal
            print(f"{MARKER_TO_SPLIT}{k}({newVs})")

tokenize()


