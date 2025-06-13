# PNP Subscription Bot Environment Variables
# Copy this file to .env and fill in your actual values

# REQUIRED: Telegram Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# OPTIONAL: Admin User IDs (comma-separated)
# Get your user ID by messaging @userinfobot
ADMIN_IDS=123456789,987654321

# OPTIONAL: Channel Configuration
CHANNEL_ID=@your_private_channel
CHANNEL_NAME=PNP Television

# PAYMENT LINKS: Configure these with your actual payment processor URLs
# Each plan needs its corresponding payment link

# Weekly subscription payment link
WEEK_PAYMENT_LINK=https://your-payment-processor.com/week

# Monthly subscription payment link  
MONTH_PAYMENT_LINK=https://your-payment-processor.com/month

# 3-month subscription payment link
3MONTH_PAYMENT_LINK=https://your-payment-processor.com/3month

# 6-month subscription payment link
HALFYEAR_PAYMENT_LINK=https://your-payment-processor.com/halfyear

# Yearly subscription payment link
YEAR_PAYMENT_LINK=https://your-payment-processor.com/year

# Lifetime subscription payment link
LIFETIME_PAYMENT_LINK=https://your-payment-processor.com/lifetime

# OPTIONAL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO