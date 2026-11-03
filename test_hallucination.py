"""Test script to diagnose hallucination issues in the pipeline."""
import httpx
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

TEST_QUERIES = [
    "Đi từ Mỹ Đình đến Giáp Bát bằng xe buýt",
    "Đi từ Cầu Giấy đến Bách Khoa",
    "Đi từ sân bay Nội Bài về trung tâm Hà Nội",
    "Giá vé xe buýt Hà Nội bao nhiêu",
    "Metro Cát Linh Hà Đông giá vé bao nhiêu",
]

def test_single(query: str):
    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print(f"{'='*70}")
    
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{BASE_URL}/api/chat/direct",
                json={"query": query, "messages": []},
            )
            
            if resp.status_code != 200:
                print(f"ERROR: HTTP {resp.status_code}")
                print(resp.text[:500])
                return
                
            data = resp.json()
            print(f"INTENT: {data.get('intent', 'N/A')}")
            print(f"MODE: {data.get('mode', 'N/A')}")
            print(f"SOURCES: {data.get('sources', [])}")
            print(f"LATENCY: {data.get('latency_ms', 0)}ms")
            print(f"\nREPLY (first 1000 chars):")
            print(data.get('reply', 'N/A')[:1000])
            print(f"\n--- END ---")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Test specific query or all
    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        test_single(TEST_QUERIES[idx])
    else:
        for q in TEST_QUERIES:
            test_single(q)
