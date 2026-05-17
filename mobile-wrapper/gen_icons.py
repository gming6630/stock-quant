"""生成 PWA 图标 (纯 Python，无依赖)"""
import struct, zlib, os

def create_png(size, output_path):
    """创建纯色蓝色图标 PNG"""
    width = height = size

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    # IHDR
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

    # IDAT - simple blue gradient
    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter none
        for x in range(width):
            r, g, b = 31, 119, 180  # #1f77b4
            # subtle gradient
            r = min(255, r + int((y / height) * 20))
            g = min(255, g + int((y / height) * 15))
            b = min(255, b + int((x / width) * 25))
            raw += struct.pack('BBB', r, g, b)

    compressed = zlib.compress(raw)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')

    with open(output_path, 'wb') as f:
        f.write(png)
    print(f'Created {output_path} ({size}x{size})')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
create_png(192, 'icon-192.png')
create_png(512, 'icon-512.png')
