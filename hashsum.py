"""hashsum：文件校验和工具。用法：hashsum <文件> [--md5|--sha1|--sha512|--blake2b]"""
import argparse
import hashlib
import json
import os
import sys

ALGOS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
    "blake2b": hashlib.blake2b,
}

VERSION = "0.1.0"


def hash_file(path, algo="sha256"):
    h = ALGOS[algo]()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_algo_from_line(digest):
    n = len(digest)
    for algo in ("sha512", "blake2b", "sha256", "sha1", "md5"):
        if len(ALGOS[algo]().hexdigest()) == n:
            return algo
    return None


def parse_sums_file(path):
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                print(f"警告：第 {lineno} 行格式不对，已跳过：{line}", file=sys.stderr)
                continue
            digest, fname = parts
            if fname.startswith("*"):
                fname = fname[1:]
            algo = detect_algo_from_line(digest)
            if algo is None:
                print(f"警告：第 {lineno} 行校验和长度未知，已跳过", file=sys.stderr)
                continue
            entries.append((algo, digest.lower(), fname, lineno))
    return entries


def cmd_hash(args):
    if args.algo is None:
        algo = "sha256"
    else:
        algo = args.algo
    results = []
    failed = False
    for path in args.files:
        if not os.path.isfile(path):
            print(f"error: 文件不存在：{path}", file=sys.stderr)
            failed = True
            continue
        digest = hash_file(path, algo)
        results.append({"file": path, "algo": algo, "digest": digest})
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"{r['digest']}  {r['file']}")
    return 1 if failed else 0


def cmd_check(args):
    try:
        entries = parse_sums_file(args.check)
    except OSError as e:
        print(f"error: 无法读取校验文件：{e}", file=sys.stderr)
        return 2
    base = os.path.dirname(os.path.abspath(args.check))
    ok_count = 0
    fail_count = 0
    results = []
    for algo, digest, fname, lineno in entries:
        fpath = fname if os.path.isabs(fname) else os.path.join(base, fname)
        if not os.path.isfile(fpath):
            msg = "文件不存在"
            fail_count += 1
            results.append({"file": fname, "status": "missing", "message": msg})
            if not args.json:
                print(f"{fname}: {msg}")
            continue
        actual = hash_file(fpath, algo)
        if actual == digest:
            ok_count += 1
            results.append({"file": fname, "status": "ok"})
            if not args.json:
                print(f"{fname}: OK")
        else:
            fail_count += 1
            results.append({"file": fname, "status": "failed",
                            "expected": digest, "actual": actual})
            if not args.json:
                print(f"{fname}: FAILED")
    if args.json:
        print(json.dumps({"ok": ok_count, "failed": fail_count,
                          "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"\n共 {ok_count + fail_count} 个：{ok_count} 通过，{fail_count} 失败。")
    return 1 if fail_count else 0


def cmd_write(args):
    target = args.write
    if not os.path.isdir(target):
        print(f"error: 不是目录：{target}", file=sys.stderr)
        return 1
    lines = []
    for root, dirs, files in os.walk(target):
        dirs.sort()
        for name in sorted(files):
            if name == "CHECKSUMS.sha256":
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, target)
            lines.append(f"{hash_file(full, 'sha256')}  {rel}")
    out = os.path.join(target, "CHECKSUMS.sha256")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"已写入：{out}（{len(lines)} 个文件）")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="hashsum", description="文件校验和工具（默认 sha256）")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    p.add_argument("--check", metavar="SUMS", help="按校验文件逐项验证")
    p.add_argument("--write", metavar="DIR", help="为目录生成 CHECKSUMS.sha256")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--md5", dest="algo", action="store_const", const="md5")
    g.add_argument("--sha1", dest="algo", action="store_const", const="sha1")
    g.add_argument("--sha256", dest="algo", action="store_const", const="sha256")
    g.add_argument("--sha512", dest="algo", action="store_const", const="sha512")
    g.add_argument("--blake2b", dest="algo", action="store_const", const="blake2b")
    p.set_defaults(algo=None)
    p.add_argument("files", nargs="*", help="要计算校验和的文件")
    args = p.parse_args(argv)
    if args.write:
        return cmd_write(args)
    if args.check:
        return cmd_check(args)
    if not args.files:
        print("error: 请指定文件，或使用 --check/--write。", file=sys.stderr)
        return 2
    return cmd_hash(args)


if __name__ == "__main__":
    sys.exit(main())
