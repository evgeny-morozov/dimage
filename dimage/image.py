from tempfile import NamedTemporaryFile
from .partition import Partition
from typing import List
import subprocess


class MakeImageError(Exception):
    def __init__(self, message: str):
        self.message = message


class Image(object):
    def __init__(self,
                 partitions: List[Partition],
                 mbr_size: int = 1,
                 io_block_size: int = 1024):
        self.partitions = partitions
        self.mbr_size = mbr_size
        self.io_block_size = io_block_size * 1024

    def make(self, file: str):
        with open(file, 'wb') as image_file:
            self.make_mbr(image_file)
            self.make_partitions(image_file)
            self.fill_mbr(file)

    def make_mbr(self, image_file):
        image_file.write(bytes(self.mbr_size * 1024))

    def make_partitions(self, image_file):
        for partition in self.partitions:
            with NamedTemporaryFile() as partition_file:
                partition.make(partition_file.name)
                self.append(partition_file.file, image_file)

    def fill_mbr(self, file):
        commands = 'label: dos\n\n'
        start = self.mbr_size

        for partition in self.partitions:
            commands += f'start= { start }k, size= { partition.size }k, type= 83\n'
            start += partition.size

        sfdisk_input = commands.encode()

        try:
            subprocess.run(['sfdisk', file],
                           input=sfdisk_input,
                           capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise MakeImageError(e.stderr.decode())

    def append(self, from_file, to_file):
        from_file.seek(0)
        to_file.seek(0, 2)

        while True:
            block = from_file.read(self.io_block_size)
            if not block:
                break
            to_file.write(block)
        pass
