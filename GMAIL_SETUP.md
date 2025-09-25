# 📧 Gmail Setup for RetailXAI Substack Integration

## 🔐 **Gmail App Password Setup**

### **Step 1: Enable 2-Factor Authentication**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. This is required to generate App Passwords

### **Step 2: Generate App Password**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **2-Step Verification** → **App passwords**
3. Select **Mail** as the app
4. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### **Step 3: Set Environment Variables**

**On your server:**
```bash
# SSH into your server
ssh root@143.198.14.56

# Navigate to project directory
cd /home/retailxai/precipice

# Create .env file
cat > config/.env << 'EOF'
# Gmail Configuration
SUBSTACK_EMAIL_USER=your-email@gmail.com
SUBSTACK_EMAIL_PASSWORD=your-16-char-app-password
SUBSTACK_EMAIL_RECIPIENT=substack@yourdomain.com

# Database Configuration
DATABASE_PASSWORD=Seattle2311
EOF

# Set proper permissions
chmod 600 config/.env
```

### **Step 4: Test the Setup**

```bash
# Test email configuration
python3 test_email_setup.py
```

## ✅ **Gmail SMTP Settings**

```yaml
# Already configured in config/config.yaml
publishing:
  substack:
    smtp_server: "smtp.gmail.com"  # ✅ Gmail SMTP
    smtp_port: 587                 # ✅ Gmail port
    use_tls: true                  # ✅ Required for Gmail
```

## 🚨 **Important Notes**

- **Use App Password**, not your regular Gmail password
- **App Password is 16 characters** with spaces (remove spaces when using)
- **2FA must be enabled** to generate App Passwords
- **Keep your .env file secure** (chmod 600)

## 🧪 **Quick Test**

```bash
# Copy updated config to server
scp config/config.yaml root@143.198.14.56:/home/retailxai/precipice/config/

# Test email setup
ssh root@143.198.14.56 "cd /home/retailxai/precipice && python3 test_email_setup.py"
```

## 🎯 **Expected Output**

When working correctly, you should see:
```
📧 Testing email configuration...
📧 Email User: your-email@gmail.com
📧 Email Recipient: substack@yourdomain.com
📧 SMTP Server: smtp.gmail.com
📧 SMTP Port: 587
✅ Draft generated: emailed-to-substack@yourdomain.com-20250908_234425
📧 Email sent successfully!
```

## 🔧 **Troubleshooting**

**"Authentication failed"**
- ✅ Make sure you're using the App Password, not your login password
- ✅ Verify 2FA is enabled on your Gmail account

**"Connection refused"**
- ✅ Check if your server allows outbound SMTP connections
- ✅ Try port 465 if 587 is blocked

**"TLS/SSL error"**
- ✅ Gmail requires TLS on port 587
- ✅ Make sure `use_tls: true` is set



