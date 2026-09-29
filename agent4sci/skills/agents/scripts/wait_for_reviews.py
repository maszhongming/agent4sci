import sys, os, time

dirs = sys.argv[1:]
print(f"Waiting for {len(dirs)} reviews to complete...")
print(f"Directories: {dirs}")

while True:
    done = []
    for d in dirs:
        # Codex subagents create .md files as they work and spawn a sentinel file when finalized
        sentinel_path = os.path.join(d, "done.json")
        exists = os.path.isfile(sentinel_path)
        size = os.path.getsize(sentinel_path) if exists else 0
        done.append(exists and size > 10) # only contains a timestamp
        status = f"✓ ({size}B)" if (exists and size > 10) else ("partial" if exists else "pending")
        print(f"  {d}: {status}")
    
    if all(done):
        print("\nAll reviews complete!")
        break
    
    print(f"\n{sum(done)}/{len(done)} complete. Waiting 30s...")
    time.sleep(30)

