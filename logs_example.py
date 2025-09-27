#!/usr/bin/env python3
"""
NovaNews Logs Example

This script demonstrates how to access both NovaNews logs and Nova Act SDK logs.
"""

import os
from dotenv import load_dotenv
from novanews import NovaNews

# Load environment variables
load_dotenv()


def main():
    """Demonstrate logging capabilities"""
    print("📁 NovaNews Logging Demo")
    print("=" * 40)
    
    # Check for API key
    api_key = os.getenv("NOVA_ACT_API_KEY")
    if not api_key:
        print("❌ Please set NOVA_ACT_API_KEY in your .env file")
        return
    
    # Initialize NovaNews with custom logs directory
    logs_dir = os.path.join(os.getcwd(), "example_logs")
    client = NovaNews(api_key, logs_directory=logs_dir)
    
    print(f"✅ NovaNews logs directory: {logs_dir}")
    print(f"📝 Log file: {os.path.join(logs_dir, 'novanews_*.log')}")
    
    # Show how to access Nova Act logs
    print("\n🔍 Nova Act SDK Logging:")
    print("=" * 30)
    
    # Create a simple Nova Act instance to show logs directory
    from nova_act import NovaAct
    
    with NovaAct(
        nova_act_api_key=api_key,
        starting_page="https://example.com",
        headless=True
    ) as nova:
        # Get Nova Act's logs directory
        nova_logs_dir = nova.get_session_logs_directory()
        print(f"✅ Nova Act logs directory: {nova_logs_dir}")
        print(f"📝 Nova Act log files: {os.path.join(nova_logs_dir, '*.html')}")
        print(f"📝 Nova Act trace files: {os.path.join(nova_logs_dir, '*.json')}")
    
    print("\n📊 Log Types Available:")
    print("1. NovaNews logs: Detailed application logs")
    print("2. Nova Act logs: Browser automation logs (HTML)")
    print("3. Nova Act traces: API call traces (JSON)")
    print("4. Console output: Real-time progress logs")
    
    print(f"\n🎯 To view logs after running this script:")
    print(f"   ls -la {logs_dir}")
    print(f"   cat {logs_dir}/novanews_*.log")


if __name__ == "__main__":
    main()
