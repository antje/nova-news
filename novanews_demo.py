#!/usr/bin/env python3
"""
NovaNews Sample CLI

Small harness that exercises the production NovaNews topic search pipeline.
Intended for ad-hoc validation of scraping behaviour from the command line.
"""

import os
from novanews import AGENTCORE_BROWSER_MODE, NovaNews

# Try to load environment variables from .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ℹ️ python-dotenv not installed, using system environment variables only")


def main():
    """Run a sample NovaNews topic search from the CLI."""
    print("📰 Welcome to the NovaNews sample run!")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("NOVA_ACT_API_KEY")
    if not api_key:
        print("❌ Please set NOVA_ACT_API_KEY in your .env file")
        print("Get your API key from: https://nova.amazon.com/act")
        return
    
    # Initialize NovaNews with custom logs directory
    logs_dir = os.path.join(os.getcwd(), "sample_logs")
    client = NovaNews(api_key, logs_directory=logs_dir, headless=False)
    
    # Run the sample workflow
    print("\n🚀 Starting NovaNews sample run...")
    print("This run demonstrates:")
    print("1. Parallel scraping of AI news sources:")
    print("   - Swyx's Latent Space (https://latent.space/)")
    print("   - Matthew Berman's Forward Future (https://www.forwardfuture.ai/)")
    print("2. Topic-scoped extraction with schema validation")
    print("3. Log capture in the configured NovaNews log directory")
    print("\n📱 LOGS: Watch this terminal for detailed progress logs!")
    if client.browser_mode == AGENTCORE_BROWSER_MODE:
        print("☁️ BROWSER: Nova Act runs inside the Bedrock AgentCore Browser tool. Use Live View to observe sessions.")
    else:
        print("🌐 BROWSER: Watch the local browser window for Nova Act SDK in action!")
    print(f"📁 FILE LOGS: Detailed logs saved to: {logs_dir}")
    print(f"🔗 LOG FOLDER: file://{os.path.abspath(logs_dir)}")
    print("\nLet's go! 🎭")
    
    try:
        # Perform a topic search and print the returned articles
        articles = client.search_articles_by_topic(topic="nova act", headless=False, max_items_per_site=3)
        if not articles:
            print("❌ No articles found.")
            return
        # Simple display of scraped articles only
        print("\n=== Articles ===")
        for i, a in enumerate(articles, 1):
            print(f"{i}. [{a.source}] {a.title}")
            print(f"   {a.url}")
    except KeyboardInterrupt:
        print("\n⏹️ Run interrupted by user")
    except Exception as e:
        print(f"\n❌ Run failed: {e}")
        print("Check NovaNews logs for diagnostics.")


if __name__ == "__main__":
    main()
