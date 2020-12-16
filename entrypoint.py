import subprocess

def run_cmd(cmd, cwd=None):
    """Run a shell command."""

    proc = subprocess.Popen(cmd,
                            cwd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    std_out, std_err = proc.communicate()
    return std_out.decode("utf-8"), std_err.decode('utf-8')

def run():
    run_cmd("git config --get user.email")

if __name__ == "__main__":
    run()