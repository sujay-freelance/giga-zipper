#! python3
import os
import hashlib
import zipfile
import argparse
import tempfile
import shutil
from pathlib import Path
import time
import psutil
import threading

CHUNK_SIZE = 1024 * 1024 * 8  # 8MB

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()

def write_checksums(base_dir, checksum_path):
    with open(checksum_path, 'w') as chks:
        for root, _, files in os.walk(base_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base_dir)
                hash_val = compute_sha256(full_path)
                chks.write(f"{rel_path} {hash_val}\n")

def monitor_resources(process, stop_event, usage):
    while not stop_event.is_set():
        mem = process.memory_info().rss
        usage['peak_memory'] = max(usage['peak_memory'], mem)
        cpu = process.cpu_percent(interval=0.1)
        usage['cpu'].append(cpu)

def zip_folder(input_folder, output_zip):
    input_folder = Path(input_folder).resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    checksum_path = output_zip.with_suffix(".sha256.txt")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    process = psutil.Process(os.getpid())
    usage = {'peak_memory': 0, 'cpu': []}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_resources, args=(process, stop_event, usage))
    monitor_thread.start()

    start_time = time.time()

    with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_STORED) as zipf:
        for root, _, files in os.walk(input_folder):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(input_folder)
                if full_path.is_file():
                    zipf.write(full_path, arcname=rel_path)

    stop_event.set()
    monitor_thread.join()

    elapsed = time.time() - start_time
    write_checksums(input_folder, checksum_path)

    print(f"Zipped to: {output_zip}")
    print(f"Checksums written to: {checksum_path}")
    print(f"Time taken to zip: {elapsed:.2f} seconds")
    print(f"Peak memory usage during zip: {usage['peak_memory'] / (1024 * 1024):.2f} MB")
    if usage['cpu']:
        print(f"Average CPU usage during zip: {sum(usage['cpu']) / len(usage['cpu']):.2f}%")

def verify_integrity(zip_path, checksum_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(temp_dir)

        with open(checksum_path, 'r') as f:
            for line in f:
                rel_path, original_hash = line.strip().split()
                extracted_file = Path(temp_dir) / rel_path
                current_hash = compute_sha256(extracted_file)
                if current_hash != original_hash:
                    print(f"❌ Mismatch in {rel_path}")
                    return False
    print("✅ Integrity verified")
    return True

def main():
    parser = argparse.ArgumentParser(description="Memory-efficient zipping with integrity check.")
    parser.add_argument("input", help="Input folder path to zip")
    parser.add_argument("output", help="Output zip file path")
    parser.add_argument("--verify", action="store_true", help="Verify integrity after zip")

    args = parser.parse_args()
    input_folder = Path(args.input)
    output_zip = Path(args.output)

    zip_folder(input_folder, output_zip)

    if args.verify:
        checksum_path = output_zip.with_suffix(".sha256.txt")
        verify_integrity(output_zip, checksum_path)

if __name__ == "__main__":
    main()
