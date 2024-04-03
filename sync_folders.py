import argparse
import time
import os
import shutil
import hashlib
import logging
from logging.handlers import RotatingFileHandler

def parse_args():
    """
    Parse command-line arguments to configure the synchronization process.
    - source: The directory to synchronize from.
    - replica: The target directory to synchronize to, mirroring the source.
    - interval: How often (in seconds) the synchronization should occur.
    - log_path: File path for logging detailed operations.
    """
    parser = argparse.ArgumentParser(description='Synchronize two folders using relative or absolute paths.')
    parser.add_argument('source', help='The source folder path.')
    parser.add_argument('replica', help='The replica folder path.')
    parser.add_argument('interval', type=int, help='Synchronization interval in seconds.')
    parser.add_argument('log_path', help='Path to the log file.')
    return parser.parse_args()

def resolve_path(path):
    """
    Convert relative paths to absolute paths to ensure consistent file handling
    across different operating system environments and working directories.
    """
    return os.path.abspath(path)

def ensure_log_dir_exists(log_path):
    """
    Checks if the log file directory exists and creates it if it does not.
    This prevents errors when attempting to write to a log file in a non-existent directory.
    """
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

def setup_logging(log_path):
    """
    Configure logging to output both to a file and to the console.
    - log_path: Where the log file should be stored. Includes rotating logs to manage log size.
    """
    log_path = resolve_path(log_path)
    ensure_log_dir_exists(log_path)  # Check and create log directory if necessary.
    logger = logging.getLogger('FolderSync')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_path, maxBytes=10240, backupCount=5)
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(console)
    return logger

def calculate_md5(file_path):
    """
    Calculate and return the MD5 checksum of a file. Used to detect changes in file content
    by comparing checksums of the source and replica files.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def sync_folders(source, replica, logger):
    """
    Main synchronization function. Performs three key operations:
    1. Copies new or modified files from source to replica.
    2. Creates missing directories in the replica to match the source structure.
    3. Removes files and directories in the replica that are no longer present in the source.
    """
    source = resolve_path(source)
    replica = resolve_path(replica)

    # Directory and file synchronization logic
    for dirpath, dirnames, filenames in os.walk(source):
        replica_path = dirpath.replace(source, replica, 1)
        if not os.path.exists(replica_path):
            os.makedirs(replica_path)
            logger.info(f'Created directory: {replica_path}')

        for filename in filenames:
            source_file = os.path.join(dirpath, filename)
            replica_file = os.path.join(replica_path, filename)
            if not os.path.exists(replica_file) or calculate_md5(source_file) != calculate_md5(replica_file):
                shutil.copy2(source_file, replica_file)
                logger.info(f'Copied file: {source_file} to {replica_file}')

    for dirpath, dirnames, filenames in os.walk(replica, topdown=False):
        for filename in filenames:
            replica_file = os.path.join(dirpath, filename)
            source_file = replica_file.replace(replica, source, 1)
            if not os.path.exists(source_file):
                os.remove(replica_file)
                logger.info(f'Removed file: {replica_file}')

def main():
    """
    Entrypoint of the script. Parses arguments, sets up logging, and enters the main synchronization loop,
    which runs indefinitely until manually stopped.
    """
    args = parse_args()
    logger = setup_logging(args.log_path)

    # Main synchronization loop
    while True:
        logger.info('Starting synchronization')
        sync_folders(args.source, args.replica, logger)
        logger.info('Synchronization complete. Sleeping...')
        time.sleep(args.interval)

if __name__ == "__main__":
    main()


"""
    To run: python sync_folders.py ./source ./replica 60 ./logs/logfile.log
"""