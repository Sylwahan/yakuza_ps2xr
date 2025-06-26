# LZSS encoder/decoder (AVLZ format)
# Ported from Haruhiko Okumura's LZSS.C

class LZSS_Codec():
    N = 4096
    F = 18
    THRESHOLD = 2
    NIL = N

    def __init__(self):
        self.match_position = 0
        self.match_length = 0
        self.lson = [0] * (self.N + 1)
        self.rson = [0] * (self.N + 1) + [self.NIL] * 256
        self.dad = [self.NIL] * self.N + [0]
        self.text_buf = [0] * (self.N + self.F - 1)

    def insert_node(self, r):
        cmp = 1
        p = self.N + 1 + self.text_buf[r]
        self.rson[r] = self.NIL
        self.lson[r] = self.NIL
        self.match_length = 0
        while True:
            if cmp >= 0:
                if self.rson[p] != self.NIL:
                    p = self.rson[p]
                else:
                    self.rson[p] = r
                    self.dad[r] = p
                    return
            else:
                if self.lson[p] != self.NIL:
                    p = self.lson[p]
                else:
                    self.lson[p] = r
                    self.dad[r] = p
                    return
            i = 1
            while i < self.F:
                cmp = self.text_buf[r + i] - self.text_buf[p + i]
                if cmp != 0:
                    break
                i += 1
            if i > self.match_length:
                self.match_position = p
                self.match_length = i
                if self.match_length >= self.F:
                    break
        self.dad[r] = self.dad[p]
        self.lson[r] = self.lson[p]
        self.rson[r] = self.rson[p]
        self.dad[self.lson[p]] = r
        self.dad[self.rson[p]] = r
        if self.rson[self.dad[p]] == p:
            self.rson[self.dad[p]] = r
        else:
            self.lson[self.dad[p]] = r
        self.dad[p] = self.NIL

    def delete_node(self, p):
        q = 0
        if self.dad[p] == self.NIL:
            return
        if self.rson[p] == self.NIL:
            q = self.lson[p]
        elif self.lson[p] == self.NIL:
            q = self.rson[p]
        else:
            q = self.lson[p]
            if self.rson[q] != self.NIL:
                do_loop = True
                while do_loop:
                    q = self.rson[q]
                    if self.rson[q] == self.NIL:
                        do_loop = False
                self.rson[self.dad[q]] = self.lson[q]
                self.dad[self.lson[q]] = self.dad[q]
                self.lson[q] = self.lson[p]
                self.dad[self.lson[p]] = q
            self.rson[q] = self.rson[p]
            self.dad[self.rson[p]] = q
        self.dad[q] = self.dad[p]
        if self.rson[self.dad[p]] == p:
            self.rson[self.dad[p]] = q
        else:
            self.lson[self.dad[p]] = q
        self.dad[p] = self.NIL

    def encode_lzss(self, decoded_bytes):
        code_buf = [0] * 17
        mask = 1
        code_buf_ptr = 1
        s = 0
        r = self.N - self.F
        length = 0
        inbytes_max = len(decoded_bytes)
        inbytes_curr = 0
        lzss_list = []

        while (length < self.F) and (inbytes_curr < inbytes_max):
            c = decoded_bytes[inbytes_curr]
            inbytes_curr += 1
            self.text_buf[r + length] = c
            length += 1

        for i in range(1, self.F + 1):
            self.insert_node(r - i)
        self.insert_node(r)

        do_loop = True
        while do_loop:
            if self.match_length > length:
                self.match_length = length
            if self.match_length <= self.THRESHOLD:
                self.match_length = 1
                code_buf[0] = (code_buf[0] | mask) % 256 #unsigned char
                code_buf[code_buf_ptr] = self.text_buf[r]
                code_buf_ptr += 1
            else:
                code_buf[code_buf_ptr] = self.match_position % 256 #unsigned char
                code_buf_ptr += 1
                code_buf[code_buf_ptr] = (((self.match_position >> 4) & 0xF0) | (self.match_length - (self.THRESHOLD + 1))) % 256 #unsigned char
                code_buf_ptr += 1
            mask = (mask << 1) % 256 #unsigned char
            if mask == 0:
                lzss_list.extend(code_buf[:code_buf_ptr])
                code_buf[0] = 0
                code_buf_ptr = 1
                mask = 1
            last_match_length = self.match_length
            i = 0
            while (i < last_match_length) and (inbytes_curr < inbytes_max):
                c = decoded_bytes[inbytes_curr]
                inbytes_curr += 1
                self.delete_node(s)
                self.text_buf[s] = c
                if s < (self.F - 1):
                    self.text_buf[s + self.N] = c
                s = (s + 1) & (self.N - 1)
                r = (r + 1) & (self.N - 1)
                self.insert_node(r)
                i += 1
            while i < last_match_length:
                i += 1
                self.delete_node(s)
                s = (s + 1) & (self.N - 1)
                r = (r + 1) & (self.N - 1)
                length -= 1
                if length:
                    self.insert_node(r)
            if length <= 0:
                do_loop = False

        if code_buf_ptr > 1:
            lzss_list.extend(code_buf[:code_buf_ptr])

        return bytes(bytearray(lzss_list))

    @classmethod
    def decode_lzss(cls, lzss_bytes):
        r = cls.N - cls.F
        flags = 0
        text_buf = [0] * (cls.N + cls.F - 1)
        inbytes_max = len(lzss_bytes)
        inbytes_curr = 0
        decoded_list = []

        for i in range(cls.N - cls.F):
            text_buf[i] = 0

        while True:
            flags = flags >> 1
            if flags & 256 == 0:
                if inbytes_curr == inbytes_max:
                    break
                c = lzss_bytes[inbytes_curr]
                inbytes_curr += 1
                flags = c | 0xFF00
            if flags & 1:
                if inbytes_curr == inbytes_max:
                    break
                c = lzss_bytes[inbytes_curr]
                inbytes_curr += 1
                decoded_list.append(c)
                text_buf[r] = c
                r = (r + 1) & (cls.N - 1)
            else:
                if inbytes_curr == inbytes_max:
                    break
                i = lzss_bytes[inbytes_curr]
                inbytes_curr += 1
                if inbytes_curr == inbytes_max:
                    break
                j = lzss_bytes[inbytes_curr]
                inbytes_curr += 1
                i |= ((j & 0xF0) << 4)
                j = (j & 0x0F) + cls.THRESHOLD
                for k in range(j + 1):
                    c = text_buf[(i + k) & (cls.N - 1)]
                    decoded_list.append(c)
                    text_buf[r] = c
                    r = (r + 1) & (cls.N - 1)

        return bytes(bytearray(decoded_list))


def decode_avlz(avlz_bytes):
    # remove padding
    avlz_length = int.from_bytes(avlz_bytes[8:12], byteorder="little")
    return LZSS_Codec.decode_lzss(avlz_bytes[12:avlz_length])

def encode_avlz(decoded_bytes):
    lzss_encoder = LZSS_Codec()
    lzss_bytes = lzss_encoder.encode_lzss(decoded_bytes)
    # AVLZ magic number + decoded size (4 bytes) + encoded avlz size (4 bytes) + lzss encoded bytes
    return b"\x41\x56\x4C\x5A"+len(decoded_bytes).to_bytes(4, byteorder="little")+(len(lzss_bytes)+12).to_bytes(4, byteorder="little")+lzss_bytes
