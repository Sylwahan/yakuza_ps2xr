import json
import os

import png

# extract all the 288-byte 4-char chunks as separate chars
def extract_chars(char_section, num_single_chars):
    single_chars_array = []
    single_chars = []
    wide_chars_array = []
    wide_chars = []
    offset = 0
    for i in range(int(len(char_section)/288)):
        char_tuple = char_section[offset:offset+288]
        for j in decode_char_section(char_tuple):
            single_chars_array.append(bytearray(j))
        offset += 288
    wide_chars_array = merge_chars(single_chars_array[num_single_chars:])
    single_chars_array = single_chars_array[:num_single_chars]
    for c in single_chars_array:
        single_chars.append(bytes(c))
    for c in wide_chars_array:
        wide_chars.append(bytes(c))
    return single_chars, wide_chars

# decode a 288-byte 4-char chunk and return as separate chars
def decode_char_section(char_tuple):
    four_chars = [None]*4
    four_chars[0] = []
    four_chars[1] = []
    four_chars[2] = []
    four_chars[3] = []
    first_chars = True
    j = 0
    for i in char_tuple:
        if first_chars:
            four_chars[0].append(i >> 0 & 0b11)
            four_chars[2].append(i >> 2 & 0b11)
            four_chars[0].append(i >> 4 & 0b11)
            four_chars[2].append(i >> 6 & 0b11)
        else:
            four_chars[1].append(i >> 0 & 0b11)
            four_chars[3].append(i >> 2 & 0b11)
            four_chars[1].append(i >> 4 & 0b11)
            four_chars[3].append(i >> 6 & 0b11)
        j += 1
        if j % 6 == 0:
            first_chars = not first_chars
    return four_chars

# encode all chars into groups of 4
def encode_char_section(single_chars, wide_chars):
    complete_bytes = b""
    single_chars += split_chars(wide_chars)
    char_sections = int(len(single_chars) / 4)
    for i in range(char_sections):
        four_chars = [None] * 4
        four_chars[0] = []
        four_chars[1] = []
        four_chars[2] = []
        four_chars[3] = []
        for i in range(4):
            four_chars[i] = bytearray(single_chars.pop(0))
        char_section = b""
        first_chars = True
        j = 0
        for i in range(288):
            work_byte = 0
            if first_chars:
                work_byte += four_chars[0][0]
                del four_chars[0][0]
                work_byte += (four_chars[2][0] << 2)
                del four_chars[2][0]
                work_byte += (four_chars[0][0] << 4)
                del four_chars[0][0]
                work_byte += (four_chars[2][0] << 6)
                del four_chars[2][0]
            else:
                work_byte += four_chars[1][0]
                del four_chars[1][0]
                work_byte += (four_chars[3][0] << 2)
                del four_chars[3][0]
                work_byte += (four_chars[1][0] << 4)
                del four_chars[1][0]
                work_byte += (four_chars[3][0] << 6)
                del four_chars[3][0]
            j += 1
            if j % 6 == 0:
                first_chars = not first_chars
            char_section += work_byte.to_bytes(1, byteorder="little")
        complete_bytes += char_section
    return complete_bytes

# merge two chars into one double wide char
def merge_chars(char_list_single):
    w = 12
    char_list_wide = []
    while char_list_single:
        left = char_list_single.pop(0)
        right = char_list_single.pop(0)
        wide = bytearray(b"")
        while left:
            wide += left[:w]
            wide += right[:w]
            left = left[w:]
            right = right[w:]
        char_list_wide.append(wide)
    return char_list_wide

# split wide char into two single chars
def split_chars(char_list_wide):
    w = 12
    char_list_single = []
    while char_list_wide:
        wide = char_list_wide.pop(0)
        left = bytearray(b"")
        right = bytearray(b"")
        while wide:
            left += wide[:w]
            right += wide[w:w*2]
            wide = wide[w*2:]
        char_list_single.append(left)
        char_list_single.append(right)
    return char_list_single

# write all chars as pngs
def write_char_pngs(char_list_single, char_list_wide, path_out):
    path_out_single = os.path.join(path_out, "single")
    path_out_wide = os.path.join(path_out, "wide")
    os.makedirs(path_out_single, exist_ok=True)
    os.makedirs(path_out_wide, exist_ok=True)
    i = 0
    for char in char_list_single:
        path_file_out = os.path.join(path_out_single, f"{i:05d}.png")
        charbytes_array, writer = raw_to_png(char, 12, 24)
        with open(path_file_out, "wb") as file_out:
            writer.write(file_out, charbytes_array)
        i += 1
    i = 0
    for char in char_list_wide:
        path_file_out = os.path.join(path_out_wide, f"{i:05d}.png")
        charbytes_array, writer = raw_to_png(char, 24, 24)
        with open(path_file_out, "wb") as file_out:
            writer.write(file_out, charbytes_array)
        i += 1

# create png array and writer object from raw pixel data
def raw_to_png(charbytes, w, h):
    charbytes_array = []
    for i in range(h):
        charbytes_array.append(charbytes[i*w:i*w+w])
    writer = png.Writer(width=w, height=h, bitdepth=2, greyscale=True)
    return charbytes_array, writer

# merge list of chars into one png, line by line
def merge_line(charbytes_list):
    char_num = len(charbytes_list)
    h = 24
    w_dict = {}
    for i in range(char_num):
        w_dict[i] = int(len(charbytes_list[i])/24)
    merged_string = b""
    for i in range(h):
        for j in range(char_num):
            w = w_dict[j]
            merged_string += charbytes_list[j][:w]
            charbytes_list[j] = charbytes_list[j][w:]
    w_tot = int(len(merged_string)/24)
    charbytes_array, writer = raw_to_png(merged_string, w_tot, 24)
    return charbytes_array, writer

# merge already exported pngs to a line
def merge_png():
    path_in = ""
    path_out = ""
    charlist = []
    i = 0
    j = 0
    for root, dirs, files in os.walk(path_in):
        for f in files:
            reader = png.Reader(filename=os.path.join(root, f))
            iwidth, iheight, pixels, metadata = reader.read()
            pixel_list = list(pixels)
            new_bytes = b""
            for row in pixel_list:
                for col in row:
                    new_bytes += col.to_bytes()
            if i and i % 30 == 0:
                charbytes_array, writer = merge_line(charlist)
                path_out_file = os.path.join(path_out, f"a{j}.png")
                with open(path_out_file, "wb") as file_out:
                    writer.write(file_out, charbytes_array)
                j += 1
                i += 1
                charlist = []
            else:
                charlist.append(new_bytes)
                i += 1
        break
    if charlist:
        charbytes_array, writer = merge_line(charlist)
        path_out_file = os.path.join(path_out, f"a{j}.png")
        with open(path_out_file, "wb") as file_out:
            writer.write(file_out, charbytes_array)

# read in extracted char dict, and do replacements with any override chars
def create_write_charset(path_in, path_override):
    warnings = []
    with open(path_in, "r") as file_in:
        charset_dict = json.load(file_in)
    charset_dict_bytes = {}
    for key, val in charset_dict.items():
        charset_dict_bytes[chr(int(key))] = bytes.fromhex(val)
        # charset_dict_bytes[int(key)] = bytes.fromhex(val)
    for root, dirs, files in os.walk(path_override):
        for f in files:
            try:
                char_num = chr(int(os.path.splitext(f)[0]))
            except ValueError:
                warnings.append(f"STEP - Create write charset\nERROR - Invalid name for file, override char ignored...\nPath: {f}")
                continue
            path_full = os.path.join(root, f)
            reader = png.Reader(filename=path_full)
            width, height, pixels, metadata = reader.read()
            if (width, height) not in [(12, 24), (24, 24)]:
                warnings.append(f"STEP - Create write charset\nERROR - Invalid resolution for file, override char ignored...\nPath: {f}\nDetected resolution: {width}x{height} (Only 12x24 and 24x24 supported...)")
                continue
            planes = metadata["planes"]
            if "palette" in metadata:
                palette = metadata["palette"]
                planes = len(palette[0])
                maxpval = pow(2, 8)-1
                pixels_flat = []
                for row in pixels:
                    row_flat = []
                    for col in row:
                        row_flat.extend(list(palette[col]))
                    pixels_flat.append(row_flat)
                pixels = pixels_flat
            else:
                maxpval = pow(2, metadata["bitdepth"])-1
            char_bytes = b""
            for row in pixels:
                col = []
                i = 1
                for sp in row:
                    col.append(sp)
                    if i % planes == 0:
                        avg = sum(x for x in col[:min(planes, 3)])/min(planes, 3)
                        char_bytes += int(round((avg/maxpval)*3)).to_bytes()
                        col = []
                    i += 1
            charset_dict_bytes[char_num] = char_bytes
        break
    return charset_dict_bytes, warnings
