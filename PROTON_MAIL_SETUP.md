# 📧 Proton Mail Setup for RetailXAI Substack Integration

## 🔐 **Proton Mail Configuration**

Proton Mail uses different SMTP settings than Gmail. Here's how to set it up:

### **1. Enable IMAP/SMTP in Proton Mail**

1. **Log into Proton Mail** (web or app)
2. **Go to Settings** → **Go to Settings** → **Mail** → **IMAP/SMTP**
3. **Enable IMAP/SMTP** (you may need to verify your identity)
4. **Note your credentials** (they'll be different from your login password)

### **2. Proton Mail SMTP Settings**

```yaml
# In config/config.yaml
publishing:
  substack:
    enabled: true
    draft_mode: true
    draft_directory: "drafts/substack"
    email_drafts: true
    email_user: ${SUBSTACK_EMAIL_USER}           # your-proton-email@proton.me
    email_password: ${SUBSTACK_EMAIL_PASSWORD}   # IMAP/SMTP password (not login password)
    email_recipient: ${SUBSTACK_EMAIL_RECIPIENT} # where to send drafts
    smtp_server: "mail.proton.me"                # Proton Mail SMTP server
    smtp_port: 587                               # Proton Mail SMTP port
    use_tls: true                                # Required for Proton Mail
```

### **3. Environment Variables**

**Create `config/.env` on the server:**
```bash
# Proton Mail Configuration
SUBSTACK_EMAIL_USER=your-email@proton.me
SUBSTACK_EMAIL_PASSWORD=your-imap-smtp-password
SUBSTACK_EMAIL_RECIPIENT=substack@yourdomain.com

# Database Configuration
DATABASE_PASSWORD=Seattle2311
```

### **4. Alternative Proton Mail Settings**

If the default settings don't work, try these alternatives:

**Option A: Port 465 with SSL**
```yaml
smtp_server: "mail.proton.me"
smtp_port: 465
use_tls: false  # Use SSL instead
```

**Option B: Port 25 (if 587/465 blocked)**
```yaml
smtp_server: "mail.proton.me"
smtp_port: 25
use_tls: true
```

### **5. Testing Your Setup**

```bash
# Test the email configuration
python3 test_email_setup.py
```

### **6. Common Issues & Solutions**

**Issue: "Authentication failed"**
- ✅ Make sure you're using the **IMAP/SMTP password**, not your login password
- ✅ Verify IMAP/SMTP is enabled in Proton Mail settings

**Issue: "Connection refused"**
- ✅ Try port 465 instead of 587
- ✅ Check if your server allows outbound SMTP connections

**Issue: "TLS/SSL error"**
- ✅ Set `use_tls: true` for port 587
- ✅ Set `use_tls: false` for port 465 (uses SSL)

### **7. Security Notes**

- 🔒 **Never use your Proton Mail login password** for SMTP
- 🔒 **Use the dedicated IMAP/SMTP password** from Proton Mail settings
- 🔒 **Keep your `.env` file secure** (chmod 600)

### **8. Quick Setup Commands**

```bash
# SSH into your server
ssh root@143.198.14.56

# Navigate to project directory
cd /home/retailxai/precipice

# Create .env file with Proton Mail credentials
cat > config/.env << 'EOF'
# Proton Mail Configuration
SUBSTACK_EMAIL_USER=your-email@proton.me
SUBSTACK_EMAIL_PASSWORD=your-imap-smtp-password
SUBSTACK_EMAIL_RECIPIENT=substack@yourdomain.com

# Database Configuration
DATABASE_PASSWORD=Seattle2311
EOF

# Set proper permissions
chmod 600 config/.env

# Test the setup
python3 test_email_setup.py
```

## 🎯 **Key Differences from Gmail**

| Setting | Gmail | Proton Mail |
|---------|-------|-------------|
| SMTP Server | smtp.gmail.com | mail.proton.me |
| Port | 587 | 587 or 465 |
| Authentication | App Password | IMAP/SMTP Password |
| TLS | Required | Required |
| SSL | Optional | Required for port 465 |

## ✅ **Verification**

Once set up, you should see:
- ✅ Draft files generated in `drafts/substack/`
- ✅ Emails sent successfully to your recipient
- ✅ No authentication errors in logs



