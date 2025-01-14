# Reddit Community Scraper 🚀

A powerful tool for scraping and analyzing Reddit community data, tracking growth metrics, and storing historical data. Built with Python and Playwright for reliable scraping.

<img src="https://i.imgur.com/gXEpgC3.png" alt="Reddit Scraper" width="600">

## Features ✨

- 🕸️ Scrape Reddit community leaderboards
- 📈 Track subreddit growth metrics (subscribers, active users)
- 🧮 Calculate engagement ratios and growth rates
- 🕰️ Maintain historical data with timestamps
- 🔄 Deduplication and data consistency
- 📁 JSON output with incremental updates

## Installation 🛠️

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reddit-scraper.git
cd reddit-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

## Usage 🖥️

Run the script:
```bash
python subreddits_to_scrape.py
```

### Menu Options 📋

1. Scrape first page only
2. Scrape first 50 pages
3. Scrape first 250 pages
4. Scrape first 1000 pages
5. Exit

The script will create/update `subreddits.json` with the scraped data.

## Data Structure 📊

The output JSON contains the following fields for each subreddit:

```json
{
    "id": "t5_2qh33",
    "name": "r/funny",
    "active_users": 2247,
    "icon_url": "https://example.com/icon.png",
    "description": "Community description",
    "subscribers": 65970936,
    "scraped_at": "2025-01-15T00:50:06.633",
    "previous_subscribers": 65950000,
    "previous_active_users": 2200,
    "subscriber_growth_rate": 0.000317,
    "active_user_growth_rate": 0.02136,
    "engagement_ratio": 0.000034,
    "scrape_count": 15,
    "first_seen": "2025-01-01T12:00:00",
    "last_updated": "2025-01-15T00:50:06.633"
}
```

## Future Improvements Roadmap 🚧

### Core Features
- [ ] Add scheduled scraping functionality
- [ ] Implement PostgreSQL integration for structured storage
- [ ] Add vector database support (e.g., Pinecone, Weaviate)
- [ ] Create API endpoints for data access

### Advanced Analytics
- [ ] Add NSFW detection and filtering
- [ ] Implement language detection and analysis
- [ ] Add sentiment analysis for descriptions
- [ ] Create community health scores
- [ ] Add trend analysis and forecasting
- [ ] Implement community clustering
- [ ] Add anomaly detection for unusual growth

### Data Processing
- [ ] Add data validation and cleaning
- [ ] Implement data partitioning
- [ ] Add data compression for large datasets
- [ ] Create data export functionality

### User Interface
- [ ] Build web dashboard
- [ ] Add data visualization
- [ ] Create CLI interface
- [ ] Add progress tracking

### Machine Learning
- [ ] Predict future growth trends
- [ ] Detect emerging communities
- [ ] Implement recommendation system
- [ ] Add content classification

## Contributing 🤝

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License 📄

MIT License

## Disclaimer ⚠️

This project is for personal/educational use only. The developers are not responsible for:
- Any legal issues arising from the use of this software
- Any damage caused by improper use
- Any violations of Reddit's terms of service

Please use responsibly and respect Reddit's API usage policies.

## Support ❤️

For issues and feature requests, please open an issue on GitHub.
