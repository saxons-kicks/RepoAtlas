# Publishing RepoAtlas to GitHub

RepoAtlas is designed so the code repository is independent from the user's local data.

1. Open https://github.com/new while signed in to the intended account.
2. Create an empty repository named `RepoAtlas` (do not add an initial README, license or `.gitignore`).
3. In PowerShell, enter the extracted `RepoAtlas` folder and run:

```powershell
git init -b main
git add .
git status --short
```

4. Confirm no personal bookmark HTML/JSON, GitHub Stars export, `.env`, `.repoatlas/`, or internal work links are staged. Then commit and push:

```powershell
git commit -m "chore: initial RepoAtlas project"
git remote add origin https://github.com/saxons-kicks/RepoAtlas.git
git push -u origin main
```

If the repository is created under a different owner, replace the remote URL with that repository's clone URL.
