import queue
import threading
import os
import shutil
import argparse
from tqdm import tqdm
from typing import List


class FastCopy:
    file_queue = queue.Queue()
    totalFiles = 0
    copy_count = 0
    lock = threading.Lock()
    progress_bar = None

    def __init__(self,
                 src_dir: str,
                 dest_dir: str):

        self.src_dir = os.path.abspath(src_dir)
        if not os.path.exists(self.src_dir):
            raise ValueError('Error: source directory {} does not exist.'.format(self.src_dir))
        self.dest_dir = os.path.abspath(dest_dir)
        # create output dir
        if not os.path.exists(self.dest_dir):
            print('Destination folder {} does not exist - creating now.'.format(self.dest_dir))
            os.makedirs(self.dest_dir)

        file_list = []
        for root, _, files in os.walk(os.path.abspath(self.src_dir)):
            for file in files:
                file_list.append(os.path.join(root, file))
        self.total_files = len(file_list)
        print("{} files to copy from {} to {}".format(self.total_files,
                                                      self.src_dir,
                                                      self.dest_dir))
        self.dispatch_workers(file_list)

    def single_copy(self):
        while True:
            file = self.file_queue.get()
            shutil.copy(file, self.dest_dir)
            self.file_queue.task_done()
            with self.lock:
                self.progress_bar.update(1)

    def dispatch_workers(self,
                         file_list: List[str]):
        n_threads = 16
        for i in range(n_threads):
            t = threading.Thread(target=self.single_copy)
            t.daemon = True
            t.start()
        print('{} copy deamons started.'.format(16))
        self.progress_bar = tqdm(total=self.total_files)
        for file_name in file_list:
            self.file_queue.put(file_name)
        self.file_queue.join()
        self.progress_bar.close()
        print('{}/{} files copied successfully.'.format(len(os.listdir(self.dest_dir)),
                                                        self.total_files))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fast multi-threaded copy.')
    parser.add_argument('src_dir',
                        help='Path of the source directory (location to be copy from).')
    parser.add_argument('dest_dir',
                        help='Path of the destination directory (location to copy to).')
    args = parser.parse_args()
    FastCopy(src_dir=args.src_dir,
             dest_dir=args.dest_dir)
