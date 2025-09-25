#!/bin/bash
# Daily Article Generation Script

cd /home/retailxai/precipice
export PATH="/home/retailxai/precipice/venv_new/bin:$PATH"

# Run the article generator
python3 generate_daily_article.py

# Log the execution
echo "$(date): Article generation completed" >> /home/retailxai/precipice/logs/article_generation.log

