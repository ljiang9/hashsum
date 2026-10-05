# hashsum

文件校验和工具：算、验、批量生成，一次搞定。纯标准库，零依赖。

## 安装

```bash
cd hashsum
python3 -m hashsum --help
```

## 用法

```bash
# 默认 sha256
python3 -m hashsum photo.zip

# 指定算法
python3 -m hashsum photo.zip --md5
python3 -m hashsum photo.zip --sha512

# 为目录生成校验文件
python3 -m hashsum --write ./dist
# → dist/CHECKSUMS.sha256

# 验证（兼容 sha256sum 输出格式）
python3 -m hashsum --check dist/CHECKSUMS.sha256
# a.zip: OK
# b.zip: FAILED

# JSON 输出（给脚本用）
python3 -m hashsum --check sums.txt --json
```

## 退出码

| 场景 | 退出码 |
|---|---|
| 全部成功 | 0 |
| `--check` 有失败/缺失 | 1 |
| 用法错误、文件不可读 | 2 |

## 设计说明

- `--check` 按校验和**长度**推断算法（64 位 hex → sha256），兼容 `sha256sum`/`md5sum` 生成的文件。
- 大文件分块读取（64KB），不一次性吃内存。
- `--write` 会跳过已存在的 `CHECKSUMS.sha256` 本身，避免自指。

## 已知局限

- 算法靠长度推断：sha256 和 blake2b-256 都是 64 位 hex，会被判为 sha256（两者都是 256 位，实践中无影响）。
- `--write` 只认当前目录树，不跟随符号链接之外的特殊文件。
- md5/sha1 已不抗碰撞，只保留用于和老文件对账；新校验请用 sha256。
