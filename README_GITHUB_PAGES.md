# RetailXAI GitHub Pages Setup

This document explains how to set up GitHub Pages for the RetailXAI staging dashboard.

## Overview

The GitHub Pages deployment provides a static version of the RetailXAI staging dashboard that:
- Fetches data from the production server (143.198.14.56)
- Displays real-time statistics and content
- Updates automatically via GitHub Actions
- Provides a public staging environment for testing

## Setup Instructions

### 1. Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to "Pages" in the left sidebar
3. Under "Source", select "GitHub Actions"
4. Save the settings

### 2. Configure Repository Secrets (Optional)

If you want to customize the production server URL, add these secrets:
- `PRODUCTION_SERVER_URL`: The URL of your production server (default: http://143.198.14.56:5000)

### 3. Deploy

The deployment happens automatically when you push to the `master` branch. The workflow will:
1. Install dependencies
2. Generate static site from production server data
3. Deploy to GitHub Pages

## Manual Deployment

To manually generate the static site:

```bash
# Install dependencies
pip install -r requirements.txt

# Generate static site
python3 generate_static_site.py

# The static site will be in the docs/ directory
```

## Files Structure

```
.github/workflows/deploy-pages.yml    # GitHub Actions workflow
generate_static_site.py               # Script to generate static site
docs/                                 # Generated static site (auto-created)
├── index.html                        # Main dashboard page
└── ...
```

## Customization

### Modify Data Sources

Edit `generate_static_site.py` to change:
- Production server URL
- Data fetching endpoints
- HTML styling and layout
- Update frequency

### Change Update Schedule

Edit `.github/workflows/deploy-pages.yml` to modify:
- Trigger conditions (push, schedule, manual)
- Update frequency
- Build process

## Testing

### Local Testing

```bash
# Test static site generation
python3 generate_static_site.py

# Serve locally
cd docs
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Production Server Testing

```bash
# Test with historical data from production server
python3 test_historical_data_server.py
```

## Troubleshooting

### Common Issues

1. **Build Fails**: Check GitHub Actions logs for errors
2. **No Data**: Verify production server is accessible
3. **Styling Issues**: Check HTML generation in `generate_static_site.py`

### Debug Commands

```bash
# Test production server connection
curl http://143.198.14.56:5000/api/health

# Test data endpoints
curl http://143.198.14.56:5000/api/stats
curl http://143.198.14.56:5000/api/transcripts
```

## Security Notes

- The static site only displays data, no sensitive information is exposed
- API keys are not included in the static site
- Production server should have proper access controls

## Monitoring

- GitHub Actions workflow runs on every push
- Check Actions tab for deployment status
- Monitor production server health for data availability
