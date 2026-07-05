# GitHub Setup Guide - Collections Voice Bot

This document explains step-by-step how this repository was set up and pushed to GitHub, and how to use Git/GitHub for this project.

## 1. Install Git

Git was installed using Windows Package Manager (winget):

```
winget install --id Git.Git -e --source winget
```

After installation, Git is available at: `C:\Program Files\Git\cmd\git.exe`

## 2. Configure Git User Identity

Set your name and email for commits:

```powershell
& "C:\Program Files\Git\cmd\git.exe" config user.name "Punit Mohapatra"
& "C:\Program Files\Git\cmd\git.exe" config user.email "mail2punit.m@gmail.com"
```

## 3. Install GitHub CLI

GitHub CLI helps create repos and authenticate:

```
winget install --id GitHub.cli -e --source winget
```

GitHub CLI is available at: `C:\Program Files\GitHub CLI\gh.exe`

## 4. Authenticate GitHub CLI

Login to GitHub via browser:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
gh auth login
```

This will:
- Prompt for GitHub.com or other
- Ask for preferred protocol (HTTPS or SSH)
- Generate an SSH key if needed
- Open browser for one-time code authentication
- Upload SSH key to GitHub account

## 5. Initialize Repository

Create a new Git repository in the project folder:

```powershell
& "C:\Program Files\Git\cmd\git.exe" init
& "C:\Program Files\Git\cmd\git.exe" add .
& "C:\Program Files\Git\cmd\git.exe" commit -m "Initial commit: collections-voice-bot project"
```

## 6. Create GitHub Repository

Create a new repository on GitHub and link it:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
gh repo create PunitMohapatra/collections-voice-bot --public --source=. --remote=origin
```

This:
- Creates a public repository at `https://github.com/PunitMohapatra/collections-voice-bot`
- Adds remote `origin` pointing to the new repository

## 7. Handle Large Generated Artifacts

Large generated files caused GitHub to reject the push. To fix this:

1. Update `.gitignore` to exclude large generated artifacts:
   ```
   bot/models/
   bot/whisper_cache/
   rasa/.rasa/cache/
   rasa/models/
   graphify-out/cache/
   tools/maven/apache-maven-3.9.6
   ```

2. Remove already-tracked large files from the index:
   ```powershell
   & "C:\Program Files\Git\cmd\git.exe" rm -r --cached bot/models bot/whisper_cache rasa/.rasa/cache rasa/models graphify-out/cache tools/maven/apache-maven-3.9.6
   ```

3. Commit the cleanup:
   ```powershell
   & "C:\Program Files\Git\cmd\git.exe" commit -m "Remove large generated artifacts from repo and update .gitignore"
   ```

## 8. Rewrite History to Permanently Remove Large Files

Even after removing files from the current commit, they still exist in Git history. To permanently remove them from all commits:

1. Install git-filter-repo:
   ```
   pip install git-filter-repo
   ```

2. Rewrite history to remove large paths:
   ```powershell
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
   python -m git_filter_repo --path bot/models --path bot/whisper_cache --path rasa/.rasa/cache --path rasa/models --path graphify-out/cache --path tools/maven/apache-maven-3.9.6 --invert-paths --force
   ```

3. Re-add the remote if it was removed:
   ```powershell
   & "C:\Program Files\Git\cmd\git.exe" remote add origin https://github.com/PunitMohapatra/collections-voice-bot.git
   ```

4. Force push the cleaned history:
   ```powershell
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
   & "C:\Program Files\Git\cmd\git.exe" push --force --set-upstream origin master
   ```

## 9. Daily Git Workflow

### Check status
```powershell
& "C:\Program Files\Git\cmd\git.exe" status
```

### Stage changes
```powershell
& "C:\Program Files\Git\cmd\git.exe" add .
```

### Commit changes
```powershell
& "C:\Program Files\Git\cmd\git.exe" commit -m "Your commit message"
```

### Push to GitHub
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
& "C:\Program Files\Git\cmd\git.exe" push
```

### Pull changes from GitHub
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
& "C:\Program Files\Git\cmd\git.exe" pull
```

## 10. Important Notes

- **SSH vs HTTPS**: We used HTTPS for push. SSH requires additional key setup.
- **Large files**: Generated models and caches should not be committed. They are excluded in `.gitignore`.
- **Maven distribution**: `tools/maven/apache-maven-3.9.6` is excluded because it can be downloaded during build.
- **Force push**: Rewriting history requires force push, which changes commit IDs. Use with caution on shared repositories.
- **Authentication**: Once logged in via `gh auth login`, Git operations use stored credentials.

## 11. Useful Git Commands

| Command | Purpose |
|---------|---------|
| `git init` | Initialize new repository |
| `git clone <url>` | Clone existing repository |
| `git add .` | Stage all changes |
| `git add <file>` | Stage specific file |
| `git commit -m "msg"` | Commit staged changes |
| `git status` | Show working tree status |
| `git log` | Show commit history |
| `git diff` | Show unstaged changes |
| `git remote -v` | Show remote URLs |
| `git remote set-url origin <url>` | Change remote URL |
| `git push` | Push commits to remote |
| `git pull` | Pull changes from remote |
| `git branch` | List branches |
| `git checkout -b <branch>` | Create and switch branch |
| `git rm --cached <file>` | Remove file from index but keep locally |

## 12. GitHub CLI Commands

| Command | Purpose |
|---------|---------|
| `gh auth login` | Authenticate with GitHub |
| `gh repo create <user/repo> --public --source=. --remote=origin` | Create repo and link |
| `gh repo view` | View repo details |
| `gh repo list` | List your repos |

## Repository Info

- **URL**: https://github.com/PunitMohapatra/collections-voice-bot
- **Branch**: master
- **Commit Author**: Punit Mohapatra <mail2punit.m@gmail.com>
- **Latest Commit**: Remove requirements files from repo