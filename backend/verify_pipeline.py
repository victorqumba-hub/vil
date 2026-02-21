import asyncio
import sys
import os

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.services.orchestrator import run_pipeline
from app.config import settings
from datetime import datetime

async def main():
    print(f"[{datetime.now()}] Starting Pipeline Verification...")
    
    # We will test with a few major pairs to verify ingestion
    test_symbols = ["EUR_USD", "GBP_USD", "USD_JPY"]
    
    print(f"Target Symbols: {test_symbols}")
    
    try:
        signals = await run_pipeline(
            symbols=test_symbols,
            timeframe="H1",
            candle_limit=200, # Increased for better indicator stability
            top_n=3
        )
        
        print(f"\n[{datetime.now()}] Pipeline Completed.")
        print(f"Generated {len(signals)} signals.")
        
        for s in signals:
            print(f"\nSymbol: {s['symbol']}")
            print(f"Score: {s['score']}")
            print(f"Status: {s['status']} | Classification: {s['classification']} | Direction: {s['direction']}")
            print(f"Price: {round(s['entry_price'], 5)}")
            print(f"Regime: {s['regime_detail']['regime']} (Stability: {s['regime_detail']['stability']}%)")
            print(f"Structure: {s['structure_detail']['bias']} (Strength: {s['structure_detail']['strength']}%)")
            print(f"Confluence: MTF Alignment Score: {s['features']['mtf_alignment_score']}")
            print(f"Data: Session: {s['features']['session']} | ATR: {s['features']['atr']}")
            
    except Exception as e:
        print(f"Pipeline Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
