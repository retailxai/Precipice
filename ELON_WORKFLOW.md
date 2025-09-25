# 🚀 Elon-Style YouTube CLI Workflow

**The right way to do it:** Local → Git → Server (via GitHub Actions)

## 🎯 Philosophy

- **Version Control Everything** - All content goes through Git
- **Automated Deployments** - GitHub Actions handles production
- **Traceable Changes** - Every article has a commit history
- **Rollback Capable** - Can revert any deployment
- **Scalable** - Works for 1 article or 1000

## 🛠️ Setup

### 1. GitHub Secrets
Add these to your repository secrets:
```
PRODUCTION_HOST=143.198.14.56
PRODUCTION_USER=root
PRODUCTION_SSH_KEY=your_ssh_private_key
```

### 2. Server Setup
On your production server (143.198.14.56):
```bash
# Ensure the directory exists
mkdir -p /home/retailxai/precipice
cd /home/retailxai/precipice

# Initialize git if needed
git init
git remote add origin https://github.com/retailxai/Precipice.git
git pull origin main
```

## 🚀 Usage

### Quick Start
```bash
# Process video + deploy to production
./youtube-workflow.sh full "https://youtube.com/watch?v=VIDEO_ID" "Tesla" "Q3 Earnings" substack
```

### Step-by-Step
```bash
# 1. Process video locally
./youtube-workflow.sh process "https://youtube.com/watch?v=VIDEO_ID" "Tesla" "Q3 Earnings"

# 2. Check what was created
./youtube-workflow.sh status

# 3. Deploy to production
./youtube-workflow.sh deploy
```

### Advanced Usage
```bash
# Process with publishing
./youtube-workflow.sh process "VIDEO_URL" "Tesla" "Q3 Earnings" substack

# Full pipeline with publishing
./youtube-workflow.sh full "VIDEO_URL" "Tesla" "Q3 Earnings" substack

# Just check status
./youtube-workflow.sh status
```

## 📁 File Structure

```
precipice/
├── articles/          # Generated articles (Markdown)
├── transcripts/       # Video transcripts (TXT)
├── analyses/          # AI analyses (JSON)
├── youtube_cli.py     # Main CLI tool
├── youtube-ai         # Wrapper script
└── youtube-workflow.sh # Elon-style workflow
```

## 🔄 Workflow Flow

1. **Local Processing**
   - Run `youtube-workflow.sh process`
   - Creates articles locally
   - Validates content

2. **Git Commit**
   - Run `youtube-workflow.sh deploy`
   - Commits all changes
   - Pushes to GitHub

3. **Automated Deployment**
   - GitHub Actions triggers
   - Deploys to production server
   - Restarts services

4. **Verification**
   - Check production server
   - Verify content is live

## 🎯 Elon's Principles Applied

### 1. **First Principles Thinking**
- Why are we doing this? → Automated content generation
- What's the simplest solution? → Git + GitHub Actions
- How do we scale? → Version control + automation

### 2. **Iteration Speed**
- Local development → Fast feedback
- Git commits → Track changes
- Automated deploy → No manual steps

### 3. **Reliability**
- Version control → Can rollback
- Automated tests → Catch errors
- Monitoring → Know when things break

### 4. **Scalability**
- One article or 1000 → Same process
- Multiple contributors → Git handles conflicts
- Production ready → Always deployable

## 🔧 Troubleshooting

### Check Status
```bash
./youtube-workflow.sh status
```

### Manual Deploy
```bash
git add articles/ transcripts/ analyses/
git commit -m "🤖 Manual deploy"
git push origin main
```

### Check Production
```bash
ssh root@143.198.14.56
cd /home/retailxai/precipice
ls -la articles/
```

## 📊 Monitoring

### GitHub Actions
- Check Actions tab in GitHub
- See deployment status
- View logs if errors

### Production Server
```bash
# Check service status
systemctl status retailxai.service

# Check logs
tail -f /home/retailxai/precipice/logs/retailxai.log

# Check content
ls -la /home/retailxai/precipice/articles/
```

## 🎉 Benefits

✅ **Version Control** - Every article is tracked  
✅ **Automated** - No manual deployment steps  
✅ **Rollback** - Can revert any change  
✅ **Scalable** - Works for any number of articles  
✅ **Reliable** - GitHub Actions handles deployment  
✅ **Traceable** - Full commit history  
✅ **Elon-Approved** - Proper engineering practices  

## 🚀 Ready to Launch?

```bash
# Test the workflow
./youtube-workflow.sh help

# Process your first video
./youtube-workflow.sh full "https://youtube.com/watch?v=VIDEO_ID" "Tesla" "Q3 Earnings" substack
```

**This is how you build systems that scale!** 🎯
