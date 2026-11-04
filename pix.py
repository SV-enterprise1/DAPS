"""Gera o código Pix 'copia e cola' (BR Code estático) e o QR em SVG."""
import io
import unicodedata


def _tlv(i, v):
    return f"{i}{len(v):02d}{v}"


def _ascii(s, n):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()[:n]


def _crc16(s):
    crc = 0xFFFF
    for b in s.encode():
        crc ^= b << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def pix_payload(key, name, city, amount, txid="***"):
    conta = _tlv("00", "br.gov.bcb.pix") + _tlv("01", key)
    corpo = (_tlv("00", "01") + _tlv("26", conta) + _tlv("52", "0000") + _tlv("53", "986")
             + _tlv("54", f"{amount:.2f}") + _tlv("58", "BR") + _tlv("59", _ascii(name, 25))
             + _tlv("60", _ascii(city, 15)) + _tlv("62", _tlv("05", txid[:25])) + "6304")
    return corpo + _crc16(corpo)


def pix_qr_svg(code):
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        return ""
    img = qrcode.make(code, image_factory=qrcode.image.svg.SvgPathImage, box_size=10)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]
