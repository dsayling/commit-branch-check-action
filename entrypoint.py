#!/usr/bin/env python
from os import PathLike
import subprocess

def run_cmd(cmd: list, cwd: PathLike=None):
    """Run a shell command."""

    proc = subprocess.Popen(cmd,
                            cwd=cwd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    std_out, std_err = proc.communicate()
    return std_out.decode("utf-8"), std_err.decode('utf-8')

def run():
    print(run_cmd("git config --get user.email".split()))
    print(run_cmd("ls -al".split()))

if __name__ == "__main__":
    run()