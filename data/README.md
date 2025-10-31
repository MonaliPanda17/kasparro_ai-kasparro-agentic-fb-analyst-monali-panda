# Data Usage

- Set environment variable `DATA_CSV` to point to the full dataset CSV, e.g.:
  - Windows PowerShell: `$Env:DATA_CSV="C:\\Users\\<you>\\Documents\\kasparro_ai\\synthetic_fb_ads_undergarments.csv"`
  - bash/zsh: `export DATA_CSV=/path/to/synthetic_fb_ads_undergarments.csv`

- For quick development, the app can use `data/sample_fb_ads.csv` when `use_sample_data: true` in `config/config.yaml`.

Expected columns:
- `campaign_name, adset_name, date, spend, impressions, clicks, ctr, purchases, revenue, roas, creative_type, creative_message, audience_type, platform, country`

