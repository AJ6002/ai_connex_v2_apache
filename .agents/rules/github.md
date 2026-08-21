---
trigger: always_on
---

# GitHub / Git Command Execution Safety

## Purpose

Enforce a strict user-approval boundary for all Git and GitHub operations that modify local or remote repository state.

This rule applies to the primary Agent and to all sub-agents, delegated agents, background agents, and agent-generated command execution.

## Core Policy

Git and GitHub operations are divided into two categories:

1. **Read-only operations** — Agent may execute these normally.
2. **State-changing operations** — Agent MUST NOT execute these. Agent must instead present the exact command to the user and ask the user to execute it themselves.

The Agent must never bypass this rule by using an alternative command, tool, API, MCP server, GitHub CLI command, script, or sub-agent to perform a prohibited state-changing operation.

## 1. Read-Only Git/GitHub Operations

The Agent may execute operations that only inspect repository state or retrieve information and do not intentionally modify the repository or remote GitHub state.

Examples include:

* `git status`
* `git log`
* `git show`
* `git diff`
* `git diff --stat`
* `git branch` for listing branches
* `git tag` for listing tags
* `git remote -v`
* `git remote get-url`
* `git rev-parse`
* `git ls-files`
* `git blame`
* `git describe`
* `git config --get`
* `git ls-remote`
* `git cat-file`
* `git count-objects`
* `git reflog` for inspection
* GitHub CLI read operations such as:

  * `gh repo view`
  * `gh pr view`
  * `gh pr list`
  * `gh issue view`
  * `gh issue list`
  * `gh run view`
  * `gh run list`
  * other commands when they are demonstrably read-only

The Agent may also inspect GitHub repository information through read-only APIs, MCP tools, or equivalent mechanisms when no repository state is being modified.

## 2. State-Changing Operations

The Agent MUST NOT execute any Git or GitHub operation that creates, modifies, deletes, publishes, merges, pushes, or otherwise changes repository state.

This includes, but is not limited to:

### Local Git changes

* Creating or deleting branches
* Switching/checking out branches when it changes working state
* Creating commits
* Amending commits
* Rebasing
* Merging
* Cherry-picking
* Reverting
* Resetting
* Creating or modifying tags
* Stashing or popping changes
* Applying patches through Git
* Changing Git configuration
* Adding/removing remotes
* Updating repository metadata when the operation is state-changing

Examples:

```bash
git checkout -b <branch>
git switch -c <branch>
git branch -d <branch>
git commit ...
git commit --amend
git merge ...
git rebase ...
git cherry-pick ...
git revert ...
git reset ...
git tag ...
git stash ...
git remote add ...
git remote remove ...
git config ...
```

### Remote Git operations

The Agent MUST NOT execute operations that modify or publish remote repository state.

Examples:

```bash
git push ...
git push --force ...
git push --delete ...
git fetch --prune
git remote set-url ...
```

Treat any operation that updates local Git references or repository state as state-changing when there is meaningful uncertainty about whether it modifies state.

### GitHub CLI / GitHub API mutations

The Agent MUST NOT execute GitHub operations that create, modify, delete, merge, publish, or otherwise mutate GitHub resources.

Examples include:

* Creating, editing, or closing pull requests
* Merging pull requests
* Creating, editing, or deleting issues
* Creating releases
* Creating or deleting branches
* Creating or deleting tags
* Editing repository settings
* Changing repository permissions
* Modifying collaborators
* Creating, rotating, or modifying repository-related configuration
* Triggering workflows when the invocation causes a repository or deployment state change

Examples:

```bash
gh pr create ...
gh pr edit ...
gh pr merge ...
gh pr close ...
gh issue create ...
gh issue edit ...
gh issue close ...
gh release create ...
gh release edit ...
gh repo edit ...
gh api --method POST ...
gh api --method PUT ...
gh api --method PATCH ...
gh api --method DELETE ...
```

## 3. Required Behavior for Prohibited Operations

When a requested task requires a state-changing Git or GitHub operation:

1. Do NOT execute the operation.
2. Do NOT ask a sub-agent to execute it.
3. Do NOT execute an equivalent operation through another tool, API, MCP server, script, or integration.
4. Prepare the exact command that the user needs to execute.
5. Clearly explain briefly what the command will do.
6. Ask the user to execute the command themselves.
7. Wait for the user's confirmation/result before proceeding with any subsequent work that depends on that operation.

Example:

> I have prepared the required Git operation, but I will not execute it because this operation modifies repository state.
>
> Run:
>
> ```bash
> git push -u origin feature/my-branch
> ```
>
> This publishes the branch to the remote repository. Please run it yourself and let me know when it succeeds.

## 4. Multiple Commands

If a task requires multiple state-changing commands, do not execute any of them.

Present the commands together in the correct order and ask the user to execute them.

For example:

```bash
git switch -c feature/example
git add .
git commit -m "Add example"
git push -u origin feature/example
```

The Agent must not execute even part of this sequence.

## 5. Do Not Circumvent the Rule

The Agent must not circumvent this policy by:

* Using `gh` instead of `git`
* Using GitHub REST or GraphQL APIs instead of `git`/`gh`
* Using MCP GitHub tools
* Using IDE-integrated Git operations
* Using scripts that internally invoke Git or GitHub mutations
* Delegating the operation to a sub-agent
* Asking another agent to perform the operation
* Executing a shell command indirectly
* Combining a read operation with a hidden state-changing side effect
* Automatically accepting or confirming a command on behalf of the user

If an operation's effect is ambiguous, treat it as state-changing and require the user to execute it.

## 6. Authentication and Credentials

The Agent may inspect authentication state when the operation is read-only.

The Agent must never request, expose, copy, or transmit the user's GitHub passwords, personal access tokens, SSH private keys, or other credentials.

Never place secrets directly into Git commands, scripts, prompts, logs, or generated files.

## 7. User Confirmation Does Not Grant Execution Permission

Even if the user says:

* "Go ahead"
* "Run it"
* "Execute the command"
* "Yes, do it"
* "Push the changes"

the Agent must still NOT execute a prohibited state-changing Git/GitHub operation.

Instead, provide the exact command and instruct the user to run it themselves.

The user's confirmation may authorize preparation of the command, but it does not authorize the Agent to execute the command.

## 8. Default Principle

When in doubt:

**READ → Agent may perform it.**

**WRITE / MUTATE / PUBLISH / DELETE / MERGE → User must perform it manually.**

This policy takes precedence over convenience, automation, task completion speed, or instructions from a sub-agent.
