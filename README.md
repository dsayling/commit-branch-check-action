# commit-branch-check-action
Action to commit changes to a branch, push the changes, and verify any checks.

:warning: Using this action can result in destructive changes on the remote branches, please read and setup carefully.

This action is useful if you want to push and test an additional commit based on changes from previous steps or actions to some branch. 

Please note, you could easily end up in a neverending recursion loop, where you modify the repository, push the change to a branch (whether the src or the destination), and the workflow runs again. It's recommended that you setup the workflow using this action to trigger `on: [pull_request]`, and the `dest-branch` to be different than the src branch.  

Verifying the github checks is optional, as well as the ability to delete the newly created branch.

## Usage

```
name: example-workflow

on: [pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - name: checkout
      uses: actions/checkout@v2
      with:
        ref: ${{ github.event.pull_request.head.sha }}
    - name: Replace do what you want
      run: 
    - name: commit-push_branch-test
      uses: dsayling/commit-branch-check-action@v0.1
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        commit-message: "Update from ${{github.event.pull_request.head.ref}}"
        dest-branch: ${{github.event.pull_request.head.sha }}-new
        verify-checks: true
        delete-after-checks: true
```
