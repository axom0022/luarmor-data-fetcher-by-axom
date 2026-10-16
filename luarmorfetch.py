import hashlib
import os
import re
import sys
import time
import urllib.request

mkreq = getattr(urllib.request, "Request")

uas = ["Roblox/WinInet", "lua/5.1", "SynapseX/1.0"]
loaderre = re.compile(r"/files/(v\d+)/loaders/([0-9a-fA-F]{32})\.lua")
bareidre = re.compile(r"^[0-9a-fA-F]{32}$")
apibase = "https://api.luarmor.net"
usage = ("usage: python3 luarmor_snap.py <loaderurl|32hexid> [more...]"
         " [-i idsfile] [-o outdir] [--timeout 20] [--tries 3]")
banner = ("-- [[ fetched by AXOM - luarmor fetcher \n"
          " script url : {url}\n"
          " our discord server : https://discord.gg/Sps39CydcZ \n"
          " our youtube channel : https://youtube.com/@axos0022\n"
          "]]\n")


def httpget(url, ua, timeout, tries):
    for n in range(tries):
        try:
            req = mkreq(url, headers={"User-Agent": ua,
                                      "Accept": "*/*",
                                      "Connection": "close"})
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read(), None
        except:
            time.sleep(1.5 * (n + 1))
    return None, "http failed after " + str(tries) + " tries: " + url


def normtarget(raw):
    t = raw.strip()
    m = loaderre.search(t)
    if m:
        return t.split("#")[0], m.group(2).lower()
    if bareidre.match(t):
        return apibase + "/files/v4/loaders/" + t.lower() + ".lua", t.lower()
    return None, None


def tablespan(text, name):
    m = re.search(re.escape(name) + r"\s*=\s*\{", text)
    if not m:
        return None
    start = m.end() - 1
    depth = 0
    instr = False
    esc = False
    i = start
    while i < len(text):
        c = text[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    return None


def countitems(lit):
    n = 0
    depth = 0
    instr = False
    esc = False
    pending = False
    for c in lit:
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
            pending = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 1:
            if c == ",":
                if pending:
                    n += 1
                pending = False
            elif not c.isspace():
                pending = True
    if pending:
        n += 1
    return n


def countstrings(lit):
    lens = []
    instr = False
    esc = False
    cur = 0
    for c in lit:
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
                lens.append(cur)
                cur = 0
            else:
                cur += 1
        elif c == '"':
            instr = True
    return lens


def stubmeta(text):
    d = {}
    m = re.search(r'local\s+f,b,a\s*=\s*"([^"]*)"\s*,\s*"([^"]*)"', text)
    if m:
        d["folder"] = m.group(1)
        d["key"] = m.group(2)
    m = re.search(r'game:HttpGet\(\s*"([^"]+)"', text)
    if m:
        d["init"] = m.group(1)
    return d


def fetchsnap(target, outdir, timeout, tries):
    url, uid = normtarget(target)
    if not url:
        return None, "cannot parse loader url/id: " + target
    try:
        os.makedirs(outdir)
    except:
        pass
    stub = None
    for ua in uas:
        data, err = httpget(url, ua, timeout, tries)
        if data and not data.lstrip()[:15].lower().startswith(b"<!doctype"):
            stub = data.decode("utf-8", "replace")
            break
    if stub is None:
        return None, uid + ": no raw lua stub from any ua"
    bslit = tablespan(stub, "_bsdata0")
    if bslit is None:
        return None, uid + ": no _bsdata0 in stub"
    sm = stubmeta(stub)
    sflit = None
    fallback = False
    initurl = sm.get("init")
    if initurl:
        for ua in uas:
            data, err = httpget(initurl, ua, timeout, tries)
            if not data:
                continue
            text = data.decode("utf-8", "replace")
            lit = tablespan(text, "superflow_bytecode")
            if lit:
                sflit = lit
                break
            if "not supported by Luarmor" in text:
                fallback = True
    nb = countitems(bslit)
    ns = countstrings(sflit) if sflit else []
    body = banner.format(url=url) + "\n_bsdata0=" + bslit + ";\n"
    if sflit:
        body += "\nsuperflow_bytecode=" + sflit + ";\n"
    path = os.path.join(outdir, uid + ".snap.txt")
    fh = open(path, "w", encoding="utf-8")
    fh.write(body)
    fh.close()
    info = {}
    info["id"] = uid
    info["path"] = path
    info["bytes"] = len(body.encode("utf-8"))
    info["nb"] = nb
    info["ns"] = len(ns)
    info["sfbytes"] = sum(ns)
    info["fallback"] = fallback or sflit is None
    info["stubsha"] = hashlib.sha256(stub.encode("utf-8")).hexdigest()
    return info, None


def main(argv):
    targets = []
    infile = None
    outdir = "snap"
    timeout = 20
    tries = 3
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-i" and i + 1 < len(argv):
            i += 1
            infile = argv[i]
        elif a == "-o" and i + 1 < len(argv):
            i += 1
            outdir = argv[i]
        elif a == "--timeout" and i + 1 < len(argv):
            i += 1
            timeout = int(argv[i])
        elif a == "--tries" and i + 1 < len(argv):
            i += 1
            tries = int(argv[i])
        elif a == "-h" or a == "--help":
            print(usage)
            return 0
        else:
            targets.append(a)
        i += 1
    if infile:
        fh = open(infile, encoding="utf-8")
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                targets.append(ln)
        fh.close()
    if not targets:
        print(usage)
        return 2
    rc = 0
    for t in targets:
        info, err = fetchsnap(t, outdir, timeout, tries)
        if err:
            print("ERR " + err)
            rc = 1
        else:
            line = ("OK  " + info["id"] + "  -> " + info["path"] +
                    "  (" + str(info["bytes"]) + " B lua: _bsdata0 " +
                    str(info["nb"]) + " items + superflow_bytecode " +
                    str(info["ns"]) + " strings / " + str(info["sfbytes"]) +
                    " literal bytes")
            if info["fallback"]:
                line += ", INIT FALLBACK!"
            print(line + ")")
    return rc


sys.exit(main(sys.argv[1:]))
