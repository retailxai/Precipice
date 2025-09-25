# RetailXAI Dashboard

A modern web-based dashboard for managing and publishing RetailXAI content across multiple channels.

## Features

- 📊 **Real-time Dashboard**: View system status, statistics, and data collection metrics
- 📝 **Draft Management**: Preview, edit, and manage content drafts
- 🚀 **One-Click Publishing**: Publish content to Substack, LinkedIn, Twitter, and more
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🔄 **Auto-refresh**: Automatically updates data every 5 minutes
- 🎨 **Modern UI**: Clean, professional interface with smooth animations

## Quick Start

### Option 1: Deploy to Production Server

1. **Copy files to production server:**
   ```bash
   scp dashboard.html web_server.py publish_api.py requirements_web.txt deploy_dashboard.sh root@143.198.14.56:/home/retailxai/precipice/
   ```

2. **Run deployment script:**
   ```bash
   ssh root@143.198.14.56
   cd /home/retailxai/precipice
   chmod +x deploy_dashboard.sh
   ./deploy_dashboard.sh
   ```

3. **Access dashboard:**
   - Open browser to `http://143.198.14.56:5000`
   - Or configure nginx for custom domain

### Option 2: Deploy to GitHub Pages

1. **Push to GitHub repository:**
   ```bash
   git add dashboard.html web_server.py publish_api.py .github/
   git commit -m "Add RetailXAI Dashboard"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Select "GitHub Actions" as source
   - The workflow will automatically deploy the dashboard

3. **Access dashboard:**
   - Visit `https://your-username.github.io/your-repo`

## Configuration

### API Endpoints

The dashboard connects to these API endpoints:

- `GET /api/drafts` - Get all drafts
- `GET /api/drafts/{id}` - Get specific draft
- `POST /api/publish` - Publish draft to channel
- `GET /api/stats` - Get dashboard statistics
- `GET /api/system-status` - Get system status

### Environment Variables

Make sure these are set in your `.env` file:

```bash
# Twitter API
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Email (for Substack/LinkedIn)
DAILY_REPORT_SENDER=your_email@gmail.com
DAILY_REPORT_PASSWORD=your_app_password
DRAFT_EMAIL_RECIPIENT=recipient@example.com
```

## Usage

### Viewing Drafts

1. Open the dashboard in your browser
2. All available drafts will be displayed in cards
3. Click "Preview" to see full content
4. Use filters to find specific content types

### Publishing Content

1. Find the draft you want to publish
2. Click the "Publish to [Channel]" button
3. The system will:
   - Format content for the target channel
   - Send to appropriate API or email
   - Update draft status
   - Show success/error message

### Supported Channels

- **Twitter**: Direct API posting (requires valid API keys)
- **LinkedIn**: Email-based publishing (manual posting required)
- **Substack**: Email-based newsletter publishing
- **Custom**: Easy to add new channels

## Development

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements_web.txt
   ```

2. **Run development server:**
   ```bash
   python web_server.py
   ```

3. **Access dashboard:**
   - Open `http://localhost:5000`

### Adding New Channels

1. **Add channel to `publish_api.py`:**
   ```python
   def publish_to_new_channel(self, content, draft_id):
       # Implementation here
       pass
   ```

2. **Update `publish_draft` method:**
   ```python
   elif channel == 'new_channel':
       return self.publish_to_new_channel(draft, draft_id)
   ```

3. **Add UI button in `dashboard.html`:**
   ```html
   <button class="btn btn-success" onclick="publishDraft(${draft.id}, 'new_channel')">
       📤 Publish to New Channel
   </button>
   ```

## Troubleshooting

### Common Issues

1. **Dashboard not loading:**
   - Check if web server is running: `sudo systemctl status retailxai-dashboard`
   - Check logs: `journalctl -u retailxai-dashboard -f`

2. **Publishing fails:**
   - Verify API keys in `.env` file
   - Check network connectivity
   - Review server logs for errors

3. **No drafts showing:**
   - Ensure drafts exist in `drafts/` or `test_drafts/` directories
   - Check file permissions
   - Verify JSON format is valid

### Logs

- **Web server logs:** `journalctl -u retailxai-dashboard -f`
- **Application logs:** `tail -f logs/retailxai.log`
- **Nginx logs:** `sudo tail -f /var/log/nginx/access.log`

## Security Notes

- The dashboard is designed for internal use
- API keys are stored in environment variables
- Consider using HTTPS in production
- Restrict access with firewall rules if needed

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify configuration settings
3. Test API endpoints individually
4. Review the troubleshooting section above

---

**Built with ❤️ for RetailXAI**
