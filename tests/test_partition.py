from dimage import Partition, MakePartitionError
from tempfile import NamedTemporaryFile, TemporaryDirectory
from os.path import getsize
import subprocess
import pytest


def test_make_partition_with_specified_size():
    with NamedTemporaryFile() as f:
        p = Partition('ext2', size=100)
        p.make(f.name)

        assert getsize(f.name) == 1024 * 100
        subprocess.run(['fsck.ext2', '-p', f.name],
                       capture_output=True, check=True)


def test_make_partition_from_directory():
    with TemporaryDirectory() as d:
        with NamedTemporaryFile() as f:
            p = Partition('ext2', directory=d)
            p.make(f.name)

            size = getsize(f.name)
            assert size % 1024 == 0
            subprocess.run(['fsck.ext2', '-p', f.name],
                           capture_output=True, check=True)


def test_make_partition_error():
    with NamedTemporaryFile() as f:
        with pytest.raises(MakePartitionError):
            p = Partition('ext2', size=1)
            p.make(f.name)
