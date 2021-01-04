#!/usr/bin/env python3
import time
from os import PathLike
import os
import shlex
import subprocess
import requests


def get_env(envvar: str):
    """Boolean envvars as strings suck, fix that"""
    var = os.getenv(envvar)
    if var in ("False", "false"):
        var = False
    elif var in ("True", "true"):
        var = True
    return var


PBANNER = "*" * 5 + " {} " + "*" * 5


def run_cmd(
    cmd: str, cwd: PathLike = None, raise_on_fail: bool = True, debug: bool = True
):
    """Run a shell command."""

    print(f"Running {cmd} ...")
    proc = subprocess.Popen(
        shlex.split(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        result = proc.communicate(timeout=60)  # should configure this timeout
        std_out, std_err = result[0].decode("utf-8"), result[1].decode("utf-8")
    except subprocess.TimeoutExpired:
        print(f"{cmd} timeod out, killing process and getting error.")
        proc.kill()
        std_out, std_err = proc.communicate()
    if debug:
        if std_out:
            print(PBANNER.format("stdout"))
            print(std_out)
        if std_err:
            print(PBANNER.format("stderr"))
            print(std_err)
    if raise_on_fail and proc.returncode != 0:
        raise RuntimeError(std_err)
    return std_out, std_err


# these are from the 'action.yml'
github_token = get_env("INPUT_GITHUB-TOKEN")
dest_branch = get_env("INPUT_DEST-BRANCH")
verify_checks = get_env("INPUT_VERIFY-CHECKS")
commit_message = get_env("INPUT_COMMIT-MESSAGE")
delete_branch = get_env("INPUT_DELETE-AFTER-CHECKS")
files = get_env("INPUT_FILES")
# See https://docs.github.com/en/free-pro-team@latest/actions/reference/environment-variables
repo_ref = get_env("GITHUB_REPOSITORY")
src_ref = get_env("GITHUB_HEAD_REF")
actor = get_env("GITHUB_ACTOR")


def write_net_rc():
    with open(os.path.join(os.getenv("HOME"), ".netrc"), "w") as f:
        f.write(f"machine github.com\n" f"login {actor}\n" f"password {github_token}\n")


def add_files():
    cmd = "git add "
    if files:
        cmd += files
    else:
        cmd += "-A"
    run_cmd(cmd)


def pull_dest():
    # maybe I should fetch first, and then we can determine this.
    # if dest_branch is not set, rebase makes sense. If dest branch is set,
    #   then I dunno if a rebase makes sense unless I commit the changes to the dest branch...?
    cmd = "git fetch --all "
    # cmd += f"{dest_branch} " if dest_branch else ''
    # cmd += "--rebase --progress" if rebase else ''
    run_cmd(cmd)  # need to manually check std_err


def delete_dest_branch():
    run_cmd(f"git checkout -b throw-away")
    run_cmd(f"git branch -d {dest_branch}")
    run_cmd(f"git push origin --delete {dest_branch}")


def wait_on_branch_checks():
    # determine the hash of the head we just pushed to dest_branch
    out, _ = run_cmd(f"git ls-remote -q")
    ref_hash = None
    for i in out.splitlines():
        if dest_branch in i:
            ref_hash = i.split()[0]
            break

    # now use the checks API to verify completed and success
    status = "unknown"
    # TODO: determine the latest check based on the datetime, for now assumes 0 index is latest
    while status != "completed":
        print(f"Verifying github checks against {ref_hash}, current status: {status}")
        # the checks API takes a second or two to register the queued checks...
        time.sleep(10)
        resp = requests.get(
            f"https://api.github.com/repos/{repo_ref}/commits/{ref_hash}/check-runs"
        )
        status = resp.json().get("check_runs", [{}])[0].get("status")
    conclusion = resp.json().get("check_runs", [{}])[0].get("conclusion")
    if "success" != conclusion:
        print(
            f"{repo_ref} commit {ref_hash} github checks failed with conclusion {conclusion}\n\
            raising exception now, visit {dest_branch} branch checks for more information"
        )
        raise RuntimeError(f"{repo_ref} commit {ref_hash} github checks failed")


def run():
    # Setup git config - we need to be able to commit and push
    # Add the files, force if necessary and commit and changes
    # Push, with force
    # Verify github checks against the branch

    run_cmd(f"git config --global user.email {actor}@noreply")
    run_cmd(f"git config --global user.name {actor}")
    write_net_rc()
    add_files()
    run_cmd("git status")
    # Originally I figured we'd try and update the remote branch with the local change.
    # I think the better choice here is to simple force push on the branch, TBH.
    # I really only care about the one change between the src_branch, and making sure that it gets tested via a branch workflow.
    run_cmd(f"git commit -m '{commit_message}'") if commit_message else None
    run_cmd(f"git switch -c {dest_branch}")
    run_cmd(f"git push origin {dest_branch} -f -v")
    wait_on_branch_checks() if verify_checks else exit(0)
    # if there's success, delete the branch, failure will leave the branch up
    delete_dest_branch() if delete_branch else exit(0)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        time.sleep(1)
        raise
