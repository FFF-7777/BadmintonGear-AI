#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份 Chroma 向量库到项目内独立副本（backups/chroma_db_<时间戳>/）。

用途：HNSW 索引损坏（进程被强杀时易发）会让整个向量库不可用，
重向量化要花时间+钱。有了这份备份，损坏时直接复制回去即可秒恢复。

重要：请在「后端已停止或空闲、且最近一次向量化已完成并落盘」时运行，
以保证 Chroma 已正确 flush，备份是一致的。

零 API 费用，纯本地文件操作。
"""
import os
import sys
import shutil
import sqlite3
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根
SRC = os.path.join(ROOT, "server", "chroma_db")
DEST_PARENT = os.path.join(ROOT, "backups")


def count_embeddings(meta_path):
    """返回 chroma 中已索引的向量数；表不存在/异常返回 -1。"""
    try:
        con = sqlite3.connect(meta_path)
        n = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        con.close()
        return n
    except Exception:
        return -1


def main():
    force = "--force" in sys.argv

    if not os.path.isdir(SRC):
        print(f"[错误] 源目录不存在: {SRC}")
        sys.exit(1)

    meta = os.path.join(SRC, "chroma.sqlite3")
    # 护栏：向量库为空时备份无意义
    if os.path.isfile(meta):
        n = count_embeddings(meta)
        if n == 0 and not force:
            print("[警告] 当前向量库为空（0 embeddings），备份无意义。")
            print("        请先完成知识库向量化，再运行本脚本。")
            print("        （若确需备份空库，加 --force 参数。）")
            sys.exit(1)
        elif n > 0:
            print(f"[信息] 向量库含 {n} 条向量，开始备份。")
    else:
        print("[警告] 未找到 chroma.sqlite3，可能不是有效向量库。")

    # 复制前做完整性检查，避免备份一个已损坏的库
    if os.path.isfile(meta):
        try:
            con = sqlite3.connect(meta)
            res = con.execute("PRAGMA integrity_check").fetchone()[0]
            con.close()
            if res != "ok":
                print(f"[警告] chroma.sqlite3 完整性检查未通过: {res}")
                print("        当前库可能已损坏，备份价值有限。")
        except Exception as e:
            print(f"[警告] 无法校验 chroma.sqlite3: {e}")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(DEST_PARENT, f"chroma_db_{ts}")

    os.makedirs(DEST_PARENT, exist_ok=True)
    shutil.copytree(SRC, dest)

    total = 0
    fcount = 0
    for root, _, files in os.walk(dest):
        for f in files:
            fp = os.path.join(root, f)
            total += os.path.getsize(fp)
            fcount += 1

    print(f"[完成] 已备份到: {dest}")
    print(f"        大小: {total / 1024 / 1024:.1f} MB，文件数: {fcount}")
    print(f"        恢复方法: 停后端 -> 删 server/chroma_db/ -> 把本目录复制回去 -> 重启后端")


if __name__ == "__main__":
    main()
