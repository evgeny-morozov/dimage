import os.path
from tempfile import TemporaryDirectory
from .partition import Partition
from typing import List, BinaryIO
import subprocess


class MakeImageError(Exception):
    def __init__(self, message: str):
        self.message = message


class Image(object):
    def __init__(self,
                 partitions: List[Partition],
                 mbr_size: int = 1024,
                 io_block_size: int = 1024):
        self.partitions = partitions
        self.mbr_size = mbr_size
        self.io_block_size = io_block_size * 1024

        self.kib = 1024
        self.partition_files = []

    def make(self, file: str) -> None:
        with open(file, 'wb') as image_file:
            with TemporaryDirectory() as partitions_dir:
                self.make_mbr(image_file)
                self.make_partitions(image_file, partitions_dir)
                self.fill_mbr(file)
                self.write_partitions(image_file, partitions_dir)

    def make_mbr(self, image_file: BinaryIO) -> None:
        image_file.write(bytes(self.mbr_size * self.kib))

    def make_partitions(self, image_file: BinaryIO, partitions_dir: str) -> None:
        start = self.mbr_size

        for i, partition in enumerate(self.partitions):
            partition_file_name = os.path.join(partitions_dir, f'partition{ i }')
            partition.make(partition_file_name)
            partition.start = start

            # calculate padding to 1 MiB
            remainder = partition.size % 1024
            if remainder > 0:
                padding_size = 1024 - remainder
            else:
                padding_size = 0

            #
            full_size = partition.size + padding_size
            start += full_size

            image_file.write(bytes(full_size * self.kib))

        # Extra sector to avoid "All space for primary partitions is in use" error
        image_file.write(bytes(1024))
        image_file.flush()

    def write_partitions(self, image_file, partitions_dir):
        for i, partition in enumerate(self.partitions):
            partition_file_name = os.path.join(partitions_dir, f'partition{ i }')
            with open(partition_file_name, 'rb') as partition_file:
                self.write_file_with_offset(image_file, partition.start * self.kib, partition_file)

    def fill_mbr(self, file):
        commands = 'label: dos\n\n'

        for partition in self.partitions:
            commands += f'start= { partition.start }k, size= { partition.size }k, type= 83\n'

        sfdisk_input = commands.encode()

        try:
            subprocess.run(['sfdisk', file],
                           input=sfdisk_input,
                           capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise MakeImageError(e.stderr.decode())

    def write_file_with_offset(self, file: BinaryIO, offset: int, another_file: BinaryIO) -> None:
        file.seek(offset)
        another_file.seek(0)

        while True:
            block = another_file.read(self.io_block_size)
            if not block:
                break
            file.write(block)
        pass



