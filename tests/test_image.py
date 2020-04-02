import subprocess
from os.path import getsize
from tempfile import (
    TemporaryFile,
    TemporaryDirectory,
    NamedTemporaryFile)
from dimage import Image, Partition


def test_append_file():
    with TemporaryFile() as f1, TemporaryFile() as f2:
        f1.write(b'foo')
        f2.write(b'bar')
        image = Image([])
        image.append(f2, f1)

        f1.seek(0)
        assert f1.read() == b'foobar'


def test_make_image():
    with TemporaryDirectory() as d:
        image = Image([
            Partition('ext2', directory=d),
            Partition('ext3', size=100),
        ])

        with NamedTemporaryFile() as image_file:
            image.make(image_file.name)

            # check total size
            image_size = getsize(image_file.name)
            assert image_size == (1 + 57 + 100) * 1024

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
                b'start=           2, size=         114, type=83',
                b'start=         116, size=         200, type=83'
            ]

            # check partitions
            image_data = image_file.file.read()
            part1_data = image_data[1 * 1024: 58 * 1024]
            part2_data = image_data[58 * 1024: 158 * 1024]

            assert len(part1_data) == 57 * 1024
            assert len(part2_data) == 100 * 1024

            with NamedTemporaryFile() as part1_file:
                part1_file.file.write(part1_data)
                subprocess.run(['fsck.ext2', '-p', part1_file.name],
                               capture_output=True, check=True)

            with NamedTemporaryFile() as part2_file:
                part2_file.file.write(part2_data)
                subprocess.run(['fsck.ext3', '-p', part2_file.name],
                               capture_output=True, check=True)
