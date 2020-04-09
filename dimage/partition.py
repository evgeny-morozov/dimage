import subprocess
from typing import Optional


class MakePartitionError(Exception):
    def __init__(self, message: str):
        self.message = message


class Partition(object):
    def __init__(self,
                 filesystem: str,
                 directory: Optional[str] = None,
                 size: Optional[int] = None,
                 size_factor: float = 1.2,
                 min_size: int = 100) -> None:
        self.filesystem = filesystem
        self.directory = directory
        self.size_factor = size_factor
        self.min_size = min_size

        self.start = 0
        self.size = size

    def make(self, device: str) -> None:
        if self.directory:
            try:
                du_output = subprocess.check_output(['du', '-sk', self.directory])
                dir_size = int(du_output.split(b'\t')[0])

            except subprocess.CalledProcessError:
                raise MakePartitionError('Can\'t get size of files in directory')

            size = int(dir_size * self.size_factor)

            if size < self.min_size:
                size = self.min_size

            try:
                subprocess.run([
                    'mke2fs',
                    '-t', self.filesystem,
                    '-d', self.directory,
                    device, str(size),
                ], capture_output=True, check=True)

            except subprocess.CalledProcessError as e:
                raise MakePartitionError(e.stderr.decode())

            # shrinking with resize2fs -M can corrupt files =C

            self.size = size

        else:
            try:
                subprocess.run([
                    'mke2fs', '-t', self.filesystem, device, str(self.size),
                ], capture_output=True, check=True)

            except subprocess.CalledProcessError as e:
                raise MakePartitionError(e.stderr.decode())



