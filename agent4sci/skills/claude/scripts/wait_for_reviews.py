import sys, os, time

dirs = sys.argv[1:]
print(f"Waiting for {len(dirs)} reviews to complete...")
print(f"Directories: {dirs}")

while True:
    done = []
    for d in dirs:
        review_path = os.path.join(d, "REVIEW.md")
        exists = os.path.isfile(review_path)
        size = os.path.getsize(review_path) if exists else 0
        done.append(exists and size > 100)
        status = f"✓ ({size}B)" if (exists and size > 100) else ("partial" if exists else "pending")
        print(f"  {d}: {status}")
    
    if all(done):
        print("\nAll reviews complete!")
        break
    
    print(f"\n{sum(done)}/{len(done)} complete. Waiting 30s...")
    time.sleep(30)

