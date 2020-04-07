import os
import subprocess
from os.path import getsize, join
from tempfile import (
    TemporaryFile,
    TemporaryDirectory,
    NamedTemporaryFile)
from dimage import Image, Partition


def test_write_file_with_offset():
    with TemporaryFile() as f1, TemporaryFile() as f2, TemporaryFile() as f3:
        f1.write(b' ' * (3 + 6))
        f2.write(b'foo')
        f3.write(b'bar')
        image = Image([])
        image.write_file_with_offset(f1, 1, f2)
        image.write_file_with_offset(f1, 5, f3)

        f1.seek(0)
        assert f1.read() == b' foo bar '


def test_make_image():
    mib = 1024 ** 2

    with TemporaryDirectory() as d:
        open(os.path.join(d, 'foobar'), 'wb').write(os.urandom(10 * mib))

        image = Image([
            Partition('ext2', directory=d),
            Partition('ext2', size=100),
        ])

        with NamedTemporaryFile() as image_file:
            image.make(image_file.name)

            # check total size
            image_size = getsize(image_file.name)
            assert image_size == 13 * mib + 1024

            # check mbr contents
            result = subprocess.run(['sfdisk', '-d', image_file.name],
                                    capture_output=True, check=True)

            device = image_file.name.encode()
            lines = result.stdout.split(b'\n')
            assert b'label: dos' in lines

            part_lines = [
                line.split(b' : ')[1]
                for line in lines
                if b'start=' in line
            ]

            assert part_lines == [
                b'start=        2048, size=       22528, type=83',
                b'start=       24576, size=         200, type=83',
            ]

            # check partitions
            image_data = image_file.file.read()
            part1_data = image_data[1 * mib: 12 * mib]
            part2_data = image_data[12 * mib: 13 * mib]

            assert len(part1_data) == 11 * mib
            assert len(part2_data) == 1 * mib

            with NamedTemporaryFile() as part1_file:
                part1_file.file.write(part1_data)
                subprocess.run(['fsck.ext2', '-p', part1_file.name],
                               capture_output=True, check=True)

            with NamedTemporaryFile() as part2_file:
                part2_file.file.write(part2_data)
                subprocess.run(['fsck.ext3', '-p', part2_file.name],
                               capture_output=True, check=True)
