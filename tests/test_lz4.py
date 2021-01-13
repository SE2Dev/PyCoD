import lz4.block as block

# Attempt to mask off the python-lz4 module so PyCoD can't see it
import sys
lz4_old = sys.modules['lz4']
sys.modules['lz4'] = None

# Load PyCoD's LZ4 implementation
from PyCoD import _lz4 as lz4  # NOQA

# Restore the original lz4 module entry (just to be safe)
sys.modules['lz4'] = lz4_old

# Demo data to be used for compression
src = bytearray(
    """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Sed enim ut sem viverra
aliquet eget sit. Gravida dictum fusce ut placerat orci nulla pellentesque
dignissim. Vulputate sapien nec sagittis aliquam malesuada bibendum arcu vitae.
Fermentum dui faucibus in ornare quam viverra orci sagittis eu. Amet aliquam id
diam maecenas ultricies mi eget. Rhoncus urna neque viverra justo nec ultrices
dui sapien eget. Gravida arcu ac tortor dignissim. Cursus mattis molestie a
iaculis at erat pellentesque adipiscing commodo. A diam sollicitudin tempor id.
Ac odio tempor orci dapibus ultrices in. Commodo nulla facilisi nullam
vehicula. Leo in vitae turpis massa. Viverra ipsum nunc aliquet bibendum enim.
Feugiat nisl pretium fusce id.""",
    'utf-8')


def test_lz4_compress():
    # Attempt to use our LZ4 implementation to compress the data,
    # then use python-lz4 to try decompressing it.
    compressed = lz4.compress(src)
    decompressed = block.decompress(compressed, len(src))

    assert(decompressed == src)


def test_lz4_uncompress():
    # Compress the data using python-lz4, then attempt to decompress it
    # using out lz4 implementation.
    compressed = block.compress(src, store_size=False)
    decompressed = lz4.uncompress(compressed, offset=0)

    assert(decompressed == src)
