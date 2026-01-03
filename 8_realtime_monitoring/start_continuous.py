"""
Continuous Real-Time Streaming
Runs indefinitely, updating every 30 seconds
Press Ctrl+C to stop
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from realtime_streamer import RealTimeFlightStreamer

def main():
    """Start continuous streaming"""
    streamer = RealTimeFlightStreamer()
    
    print("\n" + "="*70)
    print("STARTING CONTINUOUS REAL-TIME STREAMING")
    print("="*70)
    print("\n📡 This will:")
    print("   - Fetch live flight data every 30 seconds")
    print("   - Calculate real-time risk scores")
    print("   - Save snapshots to data/realtime/")
    print("   - Run indefinitely until stopped")
    
    print("\n⚠️  IMPORTANT:")
    print("   - OpenSky API has rate limits (~100 requests/hour anonymous)")
    print("   - Keep this running for dashboard auto-refresh")
    print("   - Press Ctrl+C to stop streaming")
    
    input("\nPress ENTER to start streaming...")
    
    # Start streaming
    streamer.run_continuous_stream(
        interval=30,      # Update every 30 seconds
        duration=None     # Run indefinitely
    )


if __name__ == "__main__":
    main()