# RetailXAI Company and Source Configuration Guide

## 📁 Output Directory
Articles and analysis outputs are now configured to be saved in:
```
/home/retailxai/articles/
```

## 🏢 Editing Companies

### File: `/home/retailxai/precipice/config/companies.yaml`

This file defines the companies that RetailXAI tracks. Each company can have:
- YouTube channels
- RSS feeds  
- Keywords for analysis

### Current Companies:
```yaml
companies:
  - name: Walmart
    youtube_channels:
      - UCX0-FP8iPvFwIHLG2NNfNVg
    rss_feed: https://corporate.walmart.com/newsroom/rss
    keywords:
      - retail
      - grocery
      - earnings
  - name: PepsiCo
    youtube_channels:
      - UCk3f5LKLrHRr5lzh4mW_mqw
    rss_feed: https://www.pepsico.com/news/rss
    keywords:
      - CPG
      - beverage
      - earnings
  - name: Tesla
    youtube_channels:
      - UCuAj0G44lNT7wRzLdeF7l1A
    rss_feed: https://www.tesla.com/rss
    keywords:
      - electric vehicles
      - automotive
      - energy
      - earnings
```

### How to Add/Edit Companies:

1. **Add a new company:**
```yaml
  - name: "Target Corporation"
    youtube_channels:
      - "YOUR_YOUTUBE_CHANNEL_ID"
    rss_feed: "https://corporate.target.com/news/rss"
    keywords:
      - retail
      - discount
      - earnings
      - consumer goods
```

2. **Find YouTube Channel IDs:**
   - Go to the company's YouTube channel
   - Look at the URL: `https://www.youtube.com/channel/CHANNEL_ID`
   - Or use YouTube's API to search for the channel

3. **Find RSS Feeds:**
   - Look for "RSS" or "News" links on company websites
   - Common patterns:
     - `https://company.com/news/rss`
     - `https://investor.company.com/rss`
     - `https://corporate.company.com/newsroom/rss`

## 📰 Editing Data Sources

### File: `/home/retailxai/precipice/config/sources.json`

This file defines specific data sources for each company.

### Current Sources:
```json
[
    {
        "source_id": "walmart_youtube_1",
        "entity_id": "walmart",
        "source_type": "youtube",
        "details": {"channel_id": "UC7Kx9b8PDw7E_8wS7OsExmA"}
    },
    {
        "source_id": "walmart_rss_1", 
        "entity_id": "walmart",
        "source_type": "rss",
        "details": {"url": "https://corporate.walmart.com/newsroom/rss"}
    }
]
```

### How to Add/Edit Sources:

1. **Add a new YouTube source:**
```json
{
    "source_id": "target_youtube_1",
    "entity_id": "target",
    "source_type": "youtube", 
    "details": {"channel_id": "TARGET_YOUTUBE_CHANNEL_ID"}
}
```

2. **Add a new RSS source:**
```json
{
    "source_id": "target_rss_1",
    "entity_id": "target",
    "source_type": "rss",
    "details": {"url": "https://corporate.target.com/news/rss"}
}
```

## ⚙️ Main Configuration

### File: `/home/retailxai/precipice/config/config.yaml`

This file contains the main source configuration and stock symbols.

### Current Stock Symbols:
```yaml
yahoo_finance:
  enabled: true
  symbols:
    - "WMT"    # Walmart
    - "TGT"    # Target
    - "COST"   # Costco
    - "KR"     # Kroger
    - "DG"     # Dollar General
    - "DLTR"   # Dollar Tree
    - "AMZN"   # Amazon
    - "BJ"     # BJ's Wholesale
    - "FIVE"   # Five Below
    - "OLLI"   # Ollie's Bargain Outlet
    - "TSLA"   # Tesla
```

### How to Add Stock Symbols:

1. **Add new symbols to the list:**
```yaml
yahoo_finance:
  enabled: true
  symbols:
    - "WMT"
    - "TGT"
    - "COST"
    - "KR"
    - "DG"
    - "DLTR"
    - "AMZN"
    - "BJ"
    - "FIVE"
    - "OLLI"
    - "TSLA"
    - "HD"     # Home Depot
    - "LOW"    # Lowe's
    - "BBY"    # Best Buy
```

## 🔧 How to Edit Files

### Method 1: Direct SSH Editing
```bash
ssh root@143.198.14.56
cd /home/retailxai/precipice/config/
nano companies.yaml
# or
nano sources.json
# or  
nano config.yaml
```

### Method 2: Local Editing and Upload
```bash
# Download files locally
scp root@143.198.14.56:/home/retailxai/precipice/config/companies.yaml ./
scp root@143.198.14.56:/home/retailxai/precipice/config/sources.json ./

# Edit locally, then upload
scp ./companies.yaml root@143.198.14.56:/home/retailxai/precipice/config/
scp ./sources.json root@143.198.14.56:/home/retailxai/precipice/config/
```

## 🔄 After Making Changes

1. **Restart the RetailXAI service:**
```bash
ssh root@143.198.14.56 "systemctl restart retailxai.service"
```

2. **Check the service status:**
```bash
ssh root@143.198.14.56 "systemctl status retailxai.service"
```

3. **View logs to ensure changes are loaded:**
```bash
ssh root@143.198.14.56 "tail -f /home/retailxai/precipice/logs/retailxai.log"
```

## 📊 Output Files

All generated articles and analysis will be saved as markdown files in:
```
/home/retailxai/articles/
```

File naming convention:
- `analysis_YYYY-MM-DD_HH-MM-SS.md`
- `earnings_report_COMPANY_YYYY-MM-DD.md`
- `sentiment_analysis_YYYY-MM-DD.md`
- `trend_analysis_YYYY-MM-DD.md`

## 🚨 Important Notes

1. **Backup before editing:** Always backup configuration files before making changes
2. **YAML syntax:** Be careful with indentation in YAML files
3. **JSON syntax:** Ensure proper JSON formatting in sources.json
4. **Service restart:** Always restart the service after configuration changes
5. **Test changes:** Monitor logs after changes to ensure everything works correctly

## 📝 Example: Adding Target Corporation

1. **Add to companies.yaml:**
```yaml
  - name: "Target Corporation"
    youtube_channels:
      - "UC_TARGET_CHANNEL_ID"
    rss_feed: "https://corporate.target.com/news/rss"
    keywords:
      - retail
      - discount
      - earnings
      - consumer goods
```

2. **Add to sources.json:**
```json
{
    "source_id": "target_youtube_1",
    "entity_id": "target",
    "source_type": "youtube",
    "details": {"channel_id": "UC_TARGET_CHANNEL_ID"}
},
{
    "source_id": "target_rss_1",
    "entity_id": "target", 
    "source_type": "rss",
    "details": {"url": "https://corporate.target.com/news/rss"}
}
```

3. **Add stock symbol to config.yaml:**
```yaml
symbols:
  - "TGT"
```

4. **Restart service:**
```bash
systemctl restart retailxai.service
```

