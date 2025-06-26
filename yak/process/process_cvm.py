# CVM <-> ISO converter (scrambled PVD+TOC decoder/encoder)
# Ported from roxfan's cvm_tool
import os

PRIMES = [
  16411, 16417, 16421, 16427, 16433, 16447, 16451, 16453,
  16477, 16481, 16487, 16493, 16519, 16529, 16547, 16553,
  16561, 16567, 16573, 16603, 16607, 16619, 16631, 16633,
  16649, 16651, 16657, 16661, 16673, 16691, 16693, 16699,
  16703, 16729, 16741, 16747, 16759, 16763, 16787, 16811,
  16823, 16829, 16831, 16843, 16871, 16879, 16883, 16889,
  16901, 16903, 16921, 16927, 16931, 16937, 16943, 16963,
  16979, 16981, 16987, 16993, 17011, 17021, 17027, 17029,
  17033, 17041, 17047, 17053, 17077, 17093, 17099, 17107,
  17117, 17123, 17137, 17159, 17167, 17183, 17189, 17191,
  17203, 17207, 17209, 17231, 17239, 17257, 17291, 17293,
  17299, 17317, 17321, 17327, 17333, 17341, 17351, 17359,
  17377, 17383, 17387, 17389, 17393, 17401, 17417, 17419,
  17431, 17443, 17449, 17467, 17471, 17477, 17483, 17489,
  17491, 17497, 17509, 17519, 17539, 17551, 17569, 17573,
  17579, 17581, 17597, 17599, 17609, 17623, 17627, 17657,
  17659, 17669, 17681, 17683, 17707, 17713, 17729, 17737,
  17747, 17749, 17761, 17783, 17789, 17791, 17807, 17827,
  17837, 17839, 17851, 17863, 17881, 17891, 17903, 17909,
  17911, 17921, 17923, 17929, 17939, 17957, 17959, 17971,
  17977, 17981, 17987, 17989, 18013, 18041, 18043, 18047,
  18049, 18059, 18061, 18077, 18089, 18097, 18119, 18121,
  18127, 18131, 18133, 18143, 18149, 18169, 18181, 18191,
  18199, 18211, 18217, 18223, 18229, 18233, 18251, 18253,
  18257, 18269, 18287, 18289, 18301, 18307, 18311, 18313,
  18329, 18341, 18353, 18367, 18371, 18379, 18397, 18401,
  18413, 18427, 18433, 18439, 18443, 18451, 18457, 18461,
  18481, 18493, 18503, 18517, 18521, 18523, 18539, 18541,
  18553, 18583, 18587, 18593, 18617, 18637, 18661, 18671,
  18679, 18691, 18701, 18713, 18719, 18731, 18743, 18749,
  18757, 18773, 18787, 18793, 18797, 18803, 18839, 18859,
  18869, 18899, 18911, 18913, 18917, 18919, 18947, 18959,
  18973, 18979, 19001, 19009, 19013, 19031, 19037, 19051,
  19069, 19073, 19079, 19081, 19087, 19121, 19139, 19141,
  19157, 19163, 19181, 19183, 19207, 19211, 19213, 19219,
  19231, 19237, 19249, 19259, 19267, 19273, 19289, 19301,
  19309, 19319, 19333, 19373, 19379, 19381, 19387, 19391,
  19403, 19417, 19421, 19423, 19427, 19429, 19433, 19441,
  19447, 19457, 19463, 19469, 19471, 19477, 19483, 19489,
  19501, 19507, 19531, 19541, 19543, 19553, 19559, 19571,
  19577, 19583, 19597, 19603, 19609, 19661, 19681, 19687,
  19697, 19699, 19709, 19717, 19727, 19739, 19751, 19753,
  19759, 19763, 19777, 19793, 19801, 19813, 19819, 19841,
  19843, 19853, 19861, 19867, 19889, 19891, 19913, 19919,
  19927, 19937, 19949, 19961, 19963, 19973, 19979, 19991,
  19993, 19997, 20011, 20021, 20023, 20029, 20047, 20051,
  20063, 20071, 20089, 20101, 20107, 20113, 20117, 20123,
  20129, 20143, 20147, 20149, 20161, 20173, 20177, 20183,
  20201, 20219, 20231, 20233, 20249, 20261, 20269, 20287,
  20297, 20323, 20327, 20333, 20341, 20347, 20353, 20357,
  20359, 20369, 20389, 20393, 20399, 20407, 20411, 20431,
  20441, 20443, 20477, 20479, 20483, 20507, 20509, 20521,
  20533, 20543, 20549, 20551, 20563, 20593, 20599, 20611,
  20627, 20639, 20641, 20663, 20681, 20693, 20707, 20717,
  20719, 20731, 20743, 20747, 20749, 20753, 20759, 20771,
  20773, 20789, 20807, 20809, 20849, 20857, 20873, 20879,
  20887, 20897, 20899, 20903, 20921, 20929, 20939, 20947,
  20959, 20963, 20981, 20983, 21001, 21011, 21013, 21017,
  21019, 21023, 21031, 21059, 21061, 21067, 21089, 21101,
  21107, 21121, 21139, 21143, 21149, 21157, 21163, 21169,
  21179, 21187, 21191, 21193, 21211, 21221, 21227, 21247,
  21269, 21277, 21283, 21313, 21317, 21319, 21323, 21341,
  21347, 21377, 21379, 21383, 21391, 21397, 21401, 21407,
  21419, 21433, 21467, 21481, 21487, 21491, 21493, 21499,
  21503, 21517, 21521, 21523, 21529, 21557, 21559, 21563,
  21569, 21577, 21587, 21589, 21599, 21601, 21611, 21613,
  21617, 21647, 21649, 21661, 21673, 21683, 21701, 21713,
  21727, 21737, 21739, 21751, 21757, 21767, 21773, 21787,
  21799, 21803, 21817, 21821, 21839, 21841, 21851, 21859,
  21863, 21871, 21881, 21893, 21911, 21929, 21937, 21943,
  21961, 21977, 21991, 21997, 22003, 22013, 22027, 22031,
  22037, 22039, 22051, 22063, 22067, 22073, 22079, 22091,
  22093, 22109, 22111, 22123, 22129, 22133, 22147, 22153,
  22157, 22159, 22171, 22189, 22193, 22229, 22247, 22259,
  22271, 22273, 22277, 22279, 22283, 22291, 22303, 22307,
  22343, 22349, 22367, 22369, 22381, 22391, 22397, 22409,
  22433, 22441, 22447, 22453, 22469, 22481, 22483, 22501,
  22511, 22531, 22541, 22543, 22549, 22567, 22571, 22573,
  22613, 22619, 22621, 22637, 22639, 22643, 22651, 22669,
  22679, 22691, 22697, 22699, 22709, 22717, 22721, 22727,
  22739, 22741, 22751, 22769, 22777, 22783, 22787, 22807,
  22811, 22817, 22853, 22859, 22861, 22871, 22877, 22901,
  22907, 22921, 22937, 22943, 22961, 22963, 22973, 22993,
  23003, 23011, 23017, 23021, 23027, 23029, 23039, 23041,
  23053, 23057, 23059, 23063, 23071, 23081, 23087, 23099,
  23117, 23131, 23143, 23159, 23167, 23173, 23189, 23197,
  23201, 23203, 23209, 23227, 23251, 23269, 23279, 23291,
  23293, 23297, 23311, 23321, 23327, 23333, 23339, 23357,
  23369, 23371, 23399, 23417, 23431, 23447, 23459, 23473,
  23497, 23509, 23531, 23537, 23539, 23549, 23557, 23561,
  23563, 23567, 23581, 23593, 23599, 23603, 23609, 23623,
  23627, 23629, 23633, 23663, 23669, 23671, 23677, 23687,
  23689, 23719, 23741, 23743, 23747, 23753, 23761, 23767,
  23773, 23789, 23801, 23813, 23819, 23827, 23831, 23833,
  23857, 23869, 23873, 23879, 23887, 23893, 23899, 23909,
  23911, 23917, 23929, 23957, 23971, 23977, 23981, 23993,
  24001, 24007, 24019, 24023, 24029, 24043, 24049, 24061,
  24071, 24077, 24083, 24091, 24097, 24103, 24107, 24109,
  24113, 24121, 24133, 24137, 24151, 24169, 24179, 24181,
  24197, 24203, 24223, 24229, 24239, 24247, 24251, 24281,
  24317, 24329, 24337, 24359, 24371, 24373, 24379, 24391,
  24407, 24413, 24419, 24421, 24439, 24443, 24469, 24473,
  24481, 24499, 24509, 24517, 24527, 24533, 24547, 24551,
  24571, 24593, 24611, 24623, 24631, 24659, 24671, 24677,
  24683, 24691, 24697, 24709, 24733, 24749, 24763, 24767,
  24781, 24793, 24799, 24809, 24821, 24841, 24847, 24851,
  24859, 24877, 24889, 24907, 24917, 24919, 24923, 24943,
  24953, 24967, 24971, 24977, 24979, 24989, 25013, 25031,
  25033, 25037, 25057, 25073, 25087, 25097, 25111, 25117,
  25121, 25127, 25147, 25153, 25163, 25169, 25171, 25183,
  25189, 25219, 25229, 25237, 25243, 25247, 25253, 25261,
  25301, 25303, 25307, 25309, 25321, 25339, 25343, 25349,
  25357, 25367, 25373, 25391, 25409, 25411, 25423, 25439,
  25447, 25453, 25457, 25463, 25469, 25471, 25523, 25537,
  25541, 25561, 25577, 25579, 25583, 25589, 25601, 25603,
  25609, 25621, 25633, 25639, 25643, 25657, 25667, 25673,
  25679, 25693, 25703, 25717, 25733, 25741, 25747, 25759,
  25763, 25771, 25793, 25799, 25801, 25819, 25841, 25847,
  25849, 25867, 25873, 25889, 25903, 25913, 25919, 25931,
  25933, 25939, 25943, 25951, 25969, 25981, 25997, 25999,
  26003, 26017, 26021, 26029, 26041, 26053, 26083, 26099,
  26107, 26111, 26113, 26119, 26141, 26153, 26161, 26171,
  26177, 26183, 26189, 26203, 26209, 26227, 26237, 26249,
  26251, 26261, 26263, 26267, 26293, 26297, 26309, 26317,
  26321, 26339, 26347, 26357, 26371, 26387, 26393, 26399,
  26407, 26417, 26423, 26431, 26437, 26449, 26459, 26479,
  26489, 26497, 26501, 26513, 26539, 26557, 26561, 26573,
  26591, 26597, 26627, 26633, 26641, 26647, 26669, 26681
]

SCRAMBLES = [
# t 0  1  2  3  4  5  6  7
  "^03 .0 37 .4 .1 26 .2 15",  # 0
  "^12 .7 .5 23 00 .6 .4 31",  # 1
  "^.1 27 .6 12 35 .3 00 .4",  # 2
  "+23 .6 .0 .2 04 11 .7 35",  # 3
  "+.7 30 02 16 .4 .3 .5 21",  # 4
  "+.2 23 .6 07 .0 11 .4 35",  # 5
  "+03 .7^12 .6 .1 25 .0+34",  # 6
  " .7^34 .3+21 .0 .2 15^06",  # 7
  " .3^10 .6+04^32 .7 .1+25",  # 8
]

CHUNK_SIZE = 4194304
SECTOR_SIZE = 2048
ISO_DIRECTORY = 2
# pre-calculated key bytes from the password qi2o@9a!
# the result of calling:
# calc_key_from_string("qi2o@9a!")
KEY_PRECALC = b"\x66\x9B\x65\xF3\x4A\xB1\x68\x17"

def put_word(val, buf):
    i = 2
    bitno = 0
    while bitno < 16:
        i -= 1
        buf[i] = (val >> bitno) % 256 # unsigned char
        bitno += 8
    return buf

def put_dword(val, buf):
    i = 4
    bitno = 0
    while (bitno < 32):
        i -= 1
        buf[i] = (val >> bitno) % 256 # unsigned char
        bitno += 8
    return buf

def calc_one_val(buf, length, start_val):
    val = start_val
    for i in range(length):
        # convert to signed char
        if ((buf[i] & (1 << (8 - 1))) != 0):
            b = buf[i] - (1 << 8)
        else:
            b = buf[i]
        p = PRIMES[128 + b] * val
        val = PRIMES[p & 0x3FF]
    return val

def calc_hash_vals(buf, length):
    val1 = calc_one_val(buf, length, 18973) % 65536 # unsigned short
    val2 = calc_one_val(buf, length, 21503) % 65536 # unsigned short
    val3 = calc_one_val(buf, length, 24001) % 65536 # unsigned short
    return val1, val2, val3

def calc_hash(seed, hash, idx):
    buf = [0] * 4
    buf = put_dword(0x100001 * seed, buf)
    val1, val2, val3 = calc_hash_vals(buf, 4)
    idx = val1 % 9
    hash = put_word(val2, hash)
    hash = hash[:2] + put_word(val3, hash[2:])
    return hash, idx

def apply_scramble(src, hash, dst, scramble):
    p = 0
    type_char = ord("^")
    for i in range(8):
        while (ord(scramble[p]) == ord(" ")):
            p += 1
        if (ord(scramble[p]) == ord("^")) or (ord(scramble[p]) == ord("+")):
            type_char = ord(scramble[p])
            p += 1
        o1 = ord(scramble[p])
        p += 1
        o2 = ord(scramble[p])
        p += 1
        b = src[o2 - ord("0")] % 256 # unsigned char
        if (o1 != ord(".")):
            if (type_char == ord("^")):
                b = (b ^ hash[o1 - ord("0")]) % 256 # unsigned char
            else:
                b = (b + hash[o1 - ord("0")]) % 256 # unsigned char
        dst[i] = b
    return dst

def calc_local_key(key, hash, idx, local_key):
    local_key = apply_scramble(key, hash, local_key, SCRAMBLES[idx])
    return local_key

def decrypt_sectors(buf, start_sec, n_secs, sec_size, key, key_len):
    ptr = list(buf)
    buf = []
    hash = [0] * 4
    idx = 0
    local_key = [0] * 8
    for i_sec in range(start_sec, start_sec + n_secs):
        seed = key[5]
        off = 0
        while (off < sec_size):
            hash, idx = calc_hash(i_sec * seed, hash, idx)
            local_key = calc_local_key(key, hash, idx, local_key)
            seed = idx + off
            for i in range(key_len):
                ptr[off + i] = (ptr[off + i] ^ local_key[i]) % 256 # unsigned char
                seed *= local_key[i]
            off += key_len
        buf += ptr[:sec_size]
        ptr = ptr[sec_size:]
    return bytes(buf)

def extra_hash(buf):
    cnt = 4
    new_buf = []
    while cnt:
        hv1 = calc_hash_vals(buf, 2)[0]
        buf = put_word(hv1, buf)
        new_buf.append(buf[0])
        new_buf.append(buf[1])
        buf = buf[2:]
        cnt -= 1
    return new_buf

def calc_key_from_string(password):
    password = password.encode("ascii")
    key = [0] * 8
    tmp = [0] * 4
    sum = 0
    length = len(password)
    for k in range(length):
        sum = password[k] * (password[k] + sum)
        for i in range(k + 1, length):
            sum += password[i]
    tmp = put_dword(0x100001 * sum, tmp)
    for j in range(4):
        key[j * 2] = tmp[j]
        key[j * 2 + 1] = tmp[3 - j]
    key = extra_hash(key)
    return bytes(key)


class ISO_TOC_Parser():
    def __init__(self, in_file, key, sector_size, iso_dir_val, cvm_offset, decrypt):
        self.in_file = in_file
        self.key = key
        self.key_len = len(key)
        self.sector_size = sector_size
        self.iso_dir_val = iso_dir_val
        self.cvm_offset = cvm_offset
        self.decrypt = decrypt
        self.crypted_toc_dict = {}
        self.end_dir_sect = 0

    def parse_dir_tree(self):
        in_data = self.in_file.read(self.sector_size)
        self.crypted_toc_dict[16] = decrypt_sectors(in_data, 16, 1, self.sector_size, self.key, self.key_len)
        if self.decrypt:
            rootdir_rec = self.crypted_toc_dict[16][156:190]
        else:
            rootdir_rec = in_data[156:190]
        rootdir_sect = int.from_bytes(rootdir_rec[2:6], byteorder="little") + int.from_bytes(rootdir_rec[1:2], byteorder="little")
        rootdir_size = int.from_bytes(rootdir_rec[10:14], byteorder="little")
        for i in range(16 + 1, rootdir_sect):
            self.crypted_toc_dict[i] = decrypt_sectors(self.in_file.read(self.sector_size), i, 1, self.sector_size, self.key, self.key_len)
        self.parse_dir(rootdir_sect, rootdir_size)
        crypted_toc = b""
        for i in range(16, 16+len(self.crypted_toc_dict)):
            crypted_toc += self.crypted_toc_dict[i]
        return crypted_toc

    def parse_dir(self, dir_sect, dir_size):
        while (dir_size > 0):
            self.in_file.seek(dir_sect*self.sector_size+self.cvm_offset)
            in_data = self.in_file.read(self.sector_size)
            self.crypted_toc_dict[dir_sect] = decrypt_sectors(in_data, dir_sect, 1, self.sector_size, self.key, self.key_len)
            if not self.crypted_toc_dict[dir_sect]:
                return False
            if self.decrypt:
                dir_rec = self.crypted_toc_dict[dir_sect]
            else:
                dir_rec = in_data
            dir_sect += 1

            dirchunk = self.sector_size
            if (dirchunk > dir_size):
                dirchunk = dir_size
            dir_size -= dirchunk

            while (dirchunk > 0):
                rec_len = int.from_bytes(dir_rec[0:1], byteorder="little")
                if (rec_len == 0):
                    break
                if (rec_len < 0x22):
                    return False
                nlen = int.from_bytes(dir_rec[32:33], byteorder="little")
                flags = int.from_bytes(dir_rec[25:26], byteorder="little")
                extent = int.from_bytes(dir_rec[2:6], byteorder="little")
                size = int.from_bytes(dir_rec[10:14], byteorder="little")
                extattrlen = int.from_bytes(dir_rec[1:2], byteorder="little")
                name_first_char = int.from_bytes(dir_rec[33:34], byteorder="little")
                if (flags & self.iso_dir_val):
                    # ignore . and .. entries
                    if ((nlen != 1) or ((name_first_char != 0) and (name_first_char != 1))):
                        result = self.parse_dir(extent + extattrlen, size)
                        if not result:
                            return False
                dirchunk -= rec_len
                dir_rec = dir_rec[rec_len:]

        if (self.end_dir_sect < dir_sect):
            self.end_dir_sect = dir_sect
        
        return True


def cvm_to_iso(cvm_path, iso_path, header_path):
    with open(cvm_path, "rb") as file_cvm:
        cvm_magic = file_cvm.read(4)
        if cvm_magic != b"\x43\x56\x4D\x48": # CVMH magic number
            raise Exception(f"STEP - Convert CVM to ISO\nERROR - Input file is not a CVM\nPath: {cvm_path}")
        file_cvm.seek(136)
        iso_start = int.from_bytes(file_cvm.read(4), byteorder="big")*SECTOR_SIZE
        file_cvm.seek(0)
        cvm_header = file_cvm.read(iso_start)
        iso_system = file_cvm.read(16*SECTOR_SIZE)
        iso_toc_parser = ISO_TOC_Parser(file_cvm, KEY_PRECALC, SECTOR_SIZE, ISO_DIRECTORY, iso_start, True)
        decrypted_toc = iso_toc_parser.parse_dir_tree()
        with open(iso_path, "wb") as file_iso:
            file_iso.write(iso_system+decrypted_toc)
            while True:
                chunk = file_cvm.read(CHUNK_SIZE)
                if not chunk:
                    break
                file_iso.write(chunk)

    with open(header_path, "wb") as out_file:
        out_file.write(cvm_header)

def iso_to_cvm(iso_path, cvm_path, header_path):
    with open(header_path, "rb") as file_header:
        cvm_header = file_header.read()

    iso_size = os.path.getsize(iso_path)
    with open(iso_path, "rb") as file_iso:
        iso_system = file_iso.read(16*SECTOR_SIZE)
        iso_toc_parser = ISO_TOC_Parser(file_iso, KEY_PRECALC, SECTOR_SIZE, ISO_DIRECTORY, 0, False)
        encrypted_toc = iso_toc_parser.parse_dir_tree()
        # patch cvm header according to iso size
        cvm_header = cvm_header[:28]+(iso_size+len(cvm_header)).to_bytes(8, byteorder="big")+cvm_header[28+8:]
        cvm_header = cvm_header[:2052]+(iso_size+len(cvm_header)-SECTOR_SIZE-12).to_bytes(8, byteorder="big")+cvm_header[2052+8:]
        cvm_header = cvm_header[:2096]+iso_size.to_bytes(8, byteorder="big")+cvm_header[2096+8:]
        with open(cvm_path, "wb") as file_cvm:
            file_cvm.write(cvm_header+iso_system+encrypted_toc)
            while True:
                chunk = file_iso.read(CHUNK_SIZE)
                if not chunk:
                    break
                file_cvm.write(chunk)
    return True
