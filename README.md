# x-to-warpcast

A script to monitor tweets from specified Twitter accounts and automatically cast them to Farcaster via Warpcast.

## Prerequisites

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- [Warpcast Python SDK](https://github.com/aayushgpt/warpcast-py) (install via pip)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- A [RapidAPI](https://rapidapi.com/) account with access to the `twitter241` API
- Farcaster account and mnemonic

## Installation

1. Clone this repository or copy the script files.

2. Install dependencies:
   ```bash
   pip install requests python-dotenv warpcast-py
   ```

3. Create a `.env` file in the project directory with the following variables:
   ```
   TWEET_ID=comma,separated,twitter,user,ids
   RAPID_API_KEY=your_rapidapi_key
   FARCASTER_MNEMONIC=your_farcaster_mnemonic
   COOLDOWN_TIME=10
   ```

   - `TWEET_ID`: Comma-separated Twitter **user IDs** to monitor (e.g., `44196397,19512238`). **Do not use screen names.**
   - `RAPID_API_KEY`: Your RapidAPI key for the twitter241 API
   - `FARCASTER_MNEMONIC`: Your Farcaster wallet mnemonic
   - `COOLDOWN_TIME`: Number of seconds to wait between each polling cycle (default: `10`)

## Usage

Run the script:

```bash
python crawler.py
```

The script will:
- Fetch the latest 5 tweets from each specified Twitter account.
- Skip retweets.
- Cast new tweets to Farcaster using your mnemonic.
- Store a cache of processed tweets in `tweet_cache.json`.
- Repeat every `COOLDOWN_TIME` seconds.

## Notes

- Ensure your `.env` file is not committed to version control.
- The script logs actions to the console.
- If you encounter API limits or errors, check your RapidAPI usage and credentials.

## License

MIT
