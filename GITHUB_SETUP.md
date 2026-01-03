# 🚀 GitHub Push Setup Guide

This guide will help you push the AIRP project to your GitHub repository.

---

## 📋 Prerequisites

✅ Git is already initialized and committed locally  
✅ README.md created with complete project documentation  
✅ .gitignore configured to exclude unnecessary files  

**What you need:**
- GitHub account (free at https://github.com)
- Git credentials configured (personal access token or SSH key)

---

## 🔧 Setup Steps

### Option 1: Using the Batch Script (Windows - Easiest)

**1. Create a Repository on GitHub**
- Go to https://github.com/new
- Repository name: `AIRP`
- Description: "Aviation Intelligence & Risk Prediction Platform"
- Set to **Public** (for portfolio/sharing)
- **Do NOT** initialize with README (we have one)
- Click "Create repository"

**2. Run the Push Script**
```powershell
cd d:\AIRP
.\push_to_github.bat yourusername AIRP
```

Replace `yourusername` with your GitHub username.

**3. Authenticate**
When prompted:
- If using HTTPS: Enter your GitHub username and personal access token (not password)
- If using SSH: The script will use your SSH key automatically

**Done!** Your repository is now on GitHub.

---

### Option 2: Manual Setup (Command Line)

**1. Create Repository on GitHub**
- Go to https://github.com/new
- Create repository named `AIRP`
- Copy the HTTPS or SSH URL

**2. Add Remote and Push**
```bash
cd d:\AIRP

# Set the remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/AIRP.git

# Verify remote was added
git remote -v

# Make sure we're on main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## 🔑 GitHub Authentication

### Option A: Personal Access Token (HTTPS)

**Generate Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "AIRP Push"
4. Select scopes: `repo` (full control)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

**Use Token:**
```bash
git push origin main
# When prompted for password, paste the token (not your password)
```

### Option B: SSH Key (Recommended)

**Generate SSH Key:**
```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter for default location
# Enter a passphrase (optional but recommended)
```

**Add to GitHub:**
1. Copy key: `type %USERPROFILE%\.ssh\id_ed25519.pub`
2. Go to https://github.com/settings/keys
3. Click "New SSH key"
4. Paste the public key
5. Click "Add SSH key"

**Use SSH:**
```bash
# Change remote to SSH
git remote set-url origin git@github.com:yourusername/AIRP.git

# Push (will use SSH key)
git push -u origin main
```

---

## 🎯 Complete Push Instructions

### For Windows Users (Simplest)

```powershell
# 1. Create repo on GitHub (https://github.com/new)
#    Name: AIRP
#    Do NOT check "Initialize with README"

# 2. Run this command
cd d:\AIRP
.\push_to_github.bat yourusername AIRP

# 3. Enter credentials when prompted

# 4. View your repo: https://github.com/yourusername/AIRP
```

### For Mac/Linux Users

```bash
# 1. Create repo on GitHub

# 2. From project directory
cd /path/to/AIRP
git remote add origin https://github.com/yourusername/AIRP.git
git branch -M main
git push -u origin main
```

---

## ✅ Verify Push Success

After pushing, verify everything is on GitHub:

```bash
# Check remote configuration
git remote -v

# Should show:
# origin  https://github.com/yourusername/AIRP.git (fetch)
# origin  https://github.com/yourusername/AIRP.git (push)

# Check commit history on GitHub
# Go to: https://github.com/yourusername/AIRP
```

You should see:
- ✅ All Python files
- ✅ README.md (with full documentation)
- ✅ config.yaml
- ✅ requirements.txt
- ✅ All subdirectories (1_data_ingestion/, 4_models/, etc.)
- ✅ Data files (CSV, JSON)

---

## 🐛 Troubleshooting

### "fatal: destination path already exists"
```bash
cd d:\AIRP
git remote remove origin
git remote add origin https://github.com/yourusername/AIRP.git
git push -u origin main
```

### "Authentication failed"
**For HTTPS:**
- Ensure you're using a **personal access token**, not your password
- Token needs `repo` scope

**For SSH:**
- Verify SSH key exists: `ls %USERPROFILE%\.ssh\id_ed25519`
- Add SSH key to GitHub: https://github.com/settings/keys
- Test connection: `ssh -T git@github.com`

### "refusing to merge unrelated histories"
```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### "Repository already exists"
The remote is already configured:
```bash
git remote set-url origin https://github.com/yourusername/AIRP.git
git push -u origin main
```

---

## 📊 What Gets Uploaded

**Files Included:**
- ✅ All Python source code (*.py)
- ✅ Configuration files (config.yaml)
- ✅ Requirements (requirements.txt)
- ✅ Documentation (README.md, PHASE3_QUICKSTART.md)
- ✅ Database schema (schema.sql)
- ✅ Data files (CSVs, JSON)
- ✅ Notebooks (exploratory_analysis.ipynb)
- ✅ Model visualizations (PNG charts)

**Files Excluded (.gitignore):**
- ✗ __pycache__ directories
- ✗ .pyc files
- ✗ Virtual environment (venv/)
- ✗ Large model pickle files (*.pkl)
- ✗ Real-time data snapshots

---

## 🚀 After Pushing to GitHub

### 1. Update README References
Edit README.md and replace:
```markdown
# Before:
git clone https://github.com/yourusername/AIRP.git

# After: (replace yourusername)
git clone https://github.com/yourusername/AIRP.git
```

### 2. Set Up GitHub Pages (Optional)
- Go to Settings → Pages
- Select main branch as source
- Get documentation URL

### 3. Add GitHub Actions (Optional)
Create `.github/workflows/python-tests.yml` for CI/CD

### 4. Create Issues/Milestones
- Create issues for improvements
- Organize with labels
- Track progress with milestones

### 5. Add Topics
Go to Repository Settings → About
Add topics:
- `aviation`
- `machine-learning`
- `data-science`
- `streamlit`
- `python`

---

## 📝 First Time Only Setup

If this is your first time using Git with GitHub:

### 1. Configure Git Identity
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Set Default Editor
```bash
git config --global core.editor "notepad"
```

### 3. Set Default Branch
```bash
git config --global init.defaultBranch main
```

### 4. Cache Credentials (Optional - HTTPS Only)
```bash
git config --global credential.helper store
# Next push will ask once, then cache credentials
```

---

## 🔄 Regular Updates

After making changes locally:

```bash
# Stage all changes
git add .

# Commit with message
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

---

## 📚 Additional Resources

- **GitHub Docs:** https://docs.github.com
- **Git Documentation:** https://git-scm.com/doc
- **GitHub SSH:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- **GitHub Tokens:** https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

---

## ✨ You're All Set!

Once pushed to GitHub, you can:
- ✅ Share repository with others
- ✅ Collaborate on the project
- ✅ Showcase for portfolio
- ✅ Use GitHub Pages for documentation
- ✅ Set up CI/CD workflows
- ✅ Get community feedback

---

**Questions?** Check GitHub documentation or see troubleshooting section above.

Happy coding! 🎉
