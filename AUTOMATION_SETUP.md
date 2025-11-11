# ETL Automation Setup Guide

## 🎯 Overview

This repository includes automated daily updates of FX rate data using GitHub Actions. Data is fetched from Ambito.com and Argentina Datos API, then pushed to DoltHub.

## 🔐 Security Setup

### Quick Start (Automated Script)

We've created a helper script to make this easier:

```bash
cd /Users/user/uva
./setup_dolthub_creds.sh
```

This script will:
1. ✅ Generate Dolt credentials in the correct format
2. ✅ Show you the public key to add to DoltHub
3. ✅ Show you the private key to add to GitHub Secrets

### Manual Setup (Detailed Instructions)

See `DOLTHUB_CREDENTIALS_GUIDE.md` for complete step-by-step instructions.

**Quick version:**

#### 1. Generate Dolt Keypair (using Dolt's format)

DoltHub requires a special key format. Use Dolt to generate it:

```bash
# Navigate to your Dolt database directory
cd /path/to/your/macroeconomia

# Generate a keypair specifically for GitHub Actions
dolt creds new

# This will output something like:
# Credential added successfully.
# pub key: dolt-ed25519-pub-base32 abc123def456...
# Grab your last secret key (you will this need this to provide it to GH Actions)
ls -lt ~/.dolt/creds/*.jwk | head -1

```

**IMPORTANT**: Save both keys somewhere safe temporarily:

### 2. Add Public Key to DoltHub

1. Go to https://www.dolthub.com/settings/credentials
2. Click "Create Credential"
3. **Public Key**: Paste the public key from step 1
4. **Description**: "GitHub Actions ETL" 
5. Click "Create"

### 3. Export Private Key for GitHub

The private key is stored in your Dolt config. To get it:

```bash
# Find the credential ID
dolt creds ls

# Export the private key
# The key file is usually at: ~/.dolt/creds/<key_id>
# Or use dolt creds export:
dolt creds use github-actions
cat ~/.dolt/creds/<key_id>
```

Or generate it directly in the format needed:

```bash
# Generate and immediately export
dolt creds new -r github-actions --print-keys
# This will print both public and private keys
```

### 4. Add Private Key to GitHub Secrets

1. Copy the PRIVATE key from step 3
2. Go to your GitHub repository
3. Settings → Secrets and variables → Actions
4. Click "New repository secret"
5. **Name**: `DOLT_CREDS_PRIVATE_KEY`
6. **Value**: Paste the private key
7. Click "Add secret"

**🔒 Security Notes:**
- NEVER commit the private key to the repository
- NEVER share the private key with anyone
- PUBLIC key goes to DoltHub, PRIVATE key stays secret
- The private key is encrypted in GitHub Secrets
- Only GitHub Actions can access it
- You can revoke access anytime by deleting the credential on DoltHub

## 📅 Automated Schedule

### Daily Updates
- **Schedule**: Every day at 2:00 AM UTC (11:00 PM Argentina time)
- **What it updates**: Last 7 days of data
- **Duration**: ~2-3 minutes

### Manual Trigger
You can also run the workflow manually:
1. Go to Actions tab in GitHub
2. Select "Daily ETL Update"
3. Click "Run workflow"
4. Optionally change "days_back" parameter

## 🏃 Local Testing

### Test the daily update script locally:

```bash
cd /Users/user/uva
source .venv/bin/activate

# Set environment variable
export DOLT_DB='mysql://user:@localhost:3306/macroeconomia'

# Run update (last 7 days)
python etl/daily_update.py

# Or update more days
UPDATE_DAYS=30 python etl/daily_update.py
```

### Test with DoltHub push (local):

```bash
# The daily_update.py script only commits locally
# To push to DoltHub, you need to do it manually from your Dolt database directory

# 1. Run the update
python etl/daily_update.py

# 2. Navigate to your Dolt database directory
cd /path/to/your/macroeconomia/dolt/database

# 3. Push to DoltHub (uses your SSH key)
dolt push origin main
```

### Configure SSH for local Dolt push:

If you haven't set up SSH for DoltHub yet:

```bash
# 1. Generate SSH key (if you haven't already)
ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/dolthub

# 2. Add public key to DoltHub
cat ~/.ssh/dolthub.pub
# Copy and paste at https://www.dolthub.com/settings/credentials

# 3. Configure SSH
cat >> ~/.ssh/config <<EOF
Host doltremoteapi.dolthub.com
  IdentityFile ~/.ssh/dolthub
  StrictHostKeyChecking no
EOF

# 4. Test connection
ssh -T doltremoteapi.dolthub.com
```

## 📊 Monitoring

### Check if automation is working:

1. **GitHub Actions tab**: See workflow runs and logs
2. **DoltHub commits**: https://www.dolthub.com/repositories/rbasa/macroeconomia/commits/main
3. **Email notifications**: GitHub sends emails on workflow failures

### What gets updated daily:

- ✅ UVA index (last 7 days)
- ✅ USD Official (last 7 days)
- ✅ USD Blue (last 7 days)
- ✅ USD MEP (last 7 days)
- ✅ USD Crypto (last 7 days)

## 🔧 Configuration

### Change update frequency:

Edit `.github/workflows/daily_etl.yml`:

```yaml
on:
  schedule:
    # Current: Daily at 2 AM UTC
    - cron: '0 2 * * *'
    
    # Every 6 hours:
    # - cron: '0 */6 * * *'
    
    # Twice daily (2 AM and 2 PM UTC):
    # - cron: '0 2,14 * * *'
    
    # Weekly on Mondays:
    # - cron: '0 2 * * 1'
```

### Change update window:

Edit `etl/daily_update.py`:

```python
# Current: Updates last 7 days
def update_recent_data(days_back=7):

# Change to update last 30 days:
def update_recent_data(days_back=30):
```

Or set via environment variable:
```bash
UPDATE_DAYS=30 python etl/daily_update.py
```

## 🐛 Troubleshooting

### Workflow fails with "Authentication failed"
- Check that `DOLTHUB_TOKEN` secret is set correctly
- Token may have expired - generate a new one

### Workflow fails with "No data fetched"
- Source API (Ambito.com) may be down
- Check API is accessible: `curl https://mercados.ambito.com/dolar/informal/historico-general/2024-01-01/2024-01-02`

### Workflow succeeds but no new data
- Check if there's actually new data for today
- Some dates (weekends/holidays) may not have data
- View workflow logs in Actions tab

### Local script works but GitHub Actions fails
- Check that all dependencies are in `requirements.txt`
- Verify Python version compatibility (using 3.12 in Actions)
- Check environment variables are set correctly

## 📝 Manual Operations

### Full historical update (run locally, not in Actions):

```bash
python etl/populate_usd_uva.py
```

### Fix specific data issues:

```bash
# Fix USD Blue for specific period
python etl/fix_usdb_data.py
```

### Validate data quality:

```bash
python etl/validate_fx_data.py
```

## 🚀 Deployment Checklist

### Local Setup
- [x] Create `etl/daily_update.py` script
- [x] Create `.github/workflows/daily_etl.yml`
- [x] Create `.gitignore` to protect secrets
- [ ] Generate SSH key pair: `ssh-keygen -t ed25519 -f ~/.ssh/dolthub_actions`
- [ ] Add public key to DoltHub: https://www.dolthub.com/settings/credentials

### GitHub Setup
- [ ] Push code to GitHub repository
- [ ] Add `DOLTHUB_SSH_KEY` secret (Settings → Secrets → Actions)
  - Value: Contents of `~/.ssh/dolthub_actions` (private key)
- [ ] Test workflow with manual trigger (Actions → Daily ETL Update → Run workflow)
- [ ] Verify first automated run succeeds
- [ ] Check data in DoltHub after first run: https://www.dolthub.com/repositories/rbasa/macroeconomia

### Security Verification
- [ ] Verify `.gitignore` excludes sensitive files
- [ ] Confirm no tokens/keys in git history: `git log --all -p | grep -i "BEGIN"`
- [ ] Test that workflow fails gracefully without secrets
- [ ] Verify SSH key has proper description on DoltHub (for easy revocation)

## 📧 Notifications

### Enable email notifications:
1. Go to GitHub Settings → Notifications
2. Enable "Actions" notifications
3. You'll receive emails on workflow failures

### Disable notifications:
Add this to your workflow file:
```yaml
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

# No notifications on success, only on failure
jobs:
  update-data:
    if: github.event_name != 'schedule' || failure()
```

## 🔄 Rollback

If automation pushes bad data:

```bash
# Clone your DoltHub repo
dolt clone rbasa/macroeconomia
cd macroeconomia

# View recent commits
dolt log -n 10

# Revert to a good commit
dolt reset --hard <commit_hash>

# Force push to DoltHub
dolt push --force origin main
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dolt Documentation](https://docs.dolthub.com/)
- [DoltHub API Docs](https://docs.dolthub.com/products/dolthub/api)
- [Cron Schedule Examples](https://crontab.guru/)

---

**Last Updated**: 2025-01-11  
**Maintained By**: Rodrigo Basa

