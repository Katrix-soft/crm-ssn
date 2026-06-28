"""
Script para generar el ícono de la app como PNG simple usando PIL.
Ejecutar una vez: python generate_icon.py
"""
import os

try:
    from PIL import Image, ImageDraw
    
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Escudo azul
    shield_color = (21, 101, 192, 255)   # #1565C0
    shield_pts = [
        (size*0.5, size*0.05),   # top center
        (size*0.95, size*0.2),   # top right
        (size*0.95, size*0.55),  # mid right
        (size*0.5, size*0.97),   # bottom center
        (size*0.05, size*0.55),  # mid left
        (size*0.05, size*0.2),   # top left
    ]
    draw.polygon(shield_pts, fill=shield_color)
    
    # Lupa blanca
    lupa_color = (255, 255, 255, 255)
    cx, cy, r = size*0.45, size*0.42, size*0.2
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=lupa_color, width=int(size*0.07))
    # Mango
    angle_start = (cx + r*0.7, cy + r*0.7)
    angle_end   = (cx + r*1.5, cy + r*1.5)
    draw.line([angle_start, angle_end], fill=lupa_color, width=int(size*0.07))
    
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    img.save(os.path.join(assets_dir, "icon.png"))
    print("✓ Ícono generado en assets/icon.png")

except ImportError:
    # Si no hay PIL, crear un PNG mínimo de 1x1 como placeholder
    import struct, zlib
    
    def make_png(width=256, height=256):
        def chunk(name, data):
            c = struct.pack(">I", len(data)) + name + data
            return c + struct.pack(">I", zlib.crc32(name + data) & 0xffffffff)
        
        png_sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr = chunk(b'IHDR', ihdr_data)
        
        raw = b''
        for y in range(height):
            raw += b'\x00'
            for x in range(width):
                # Dibujar un cuadrado azul sólido
                r, g, b = 21, 101, 192
                raw += bytes([r, g, b])
        
        compressed = zlib.compress(raw, 9)
        idat = chunk(b'IDAT', compressed)
        iend = chunk(b'IEND', b'')
        return png_sig + ihdr + idat + iend
    
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "icon.png"), "wb") as f:
        f.write(make_png())
    print("✓ Ícono placeholder generado (sin PIL)")
