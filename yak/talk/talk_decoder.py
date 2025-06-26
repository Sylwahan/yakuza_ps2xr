import json
import os
import zlib

import yak.meta.char_hash
import yak.meta.opening_sub
import yak.talk.talk_chars
import yak.talk.talk_text

# TALK STRUCTURE
#
# TALK HEADER                   144 bytes
# PRE EXTRA BYTES HEADER        16 bytes
# PRE EXTRA BYTES               varying bytes, padded to % 16 (optional)
# 4-CHAR SECTIONS               288 bytes each
# LANG TEXT STRUCTURE HEADERS   16 bytes each
# LANG TEXT STRUCTURES          varying bytes each
# POST EXTRA BYTES              varying bytes, recorded in ARCs (optional)
# EXTRA END PAD BYTES           varying bytes, unrecorded extra bytes in MEDIA1 SHOP and PRESENT and MEDIA2 DATs (optional)

# TALK HEADER
# 144 bytes
#
# 1-4       magic number 0E000000
# 4-8       00000000 to 06000000, 01000000 = cutscene subtitle, 
# 8-16      00000000 00000000
# 16-20     pos of 4-CHAR SECTION
# 20-22     number of 4-CHAR SECTIONS
# 22-24     number of single characters in 4-CHAR SECTIONS
# 24-32     00000000 00000000
# 32-36     lang 0 (JP) - pos of lang text structure header
# 36-40     lang 1 (US) - pos of lang text structure header
# 40-44     lang 2 (UK) - pos of lang text structure header
# 44-48     lang 3 (FR) - pos of lang text structure header
# 48-52     lang 4 (DE) - pos of lang text structure header
# 52-56     lang 5 (ES) - pos of lang text structure header
# 56-60     lang 6 (IT) - pos of lang text structure header
# 60-64     lang 7 (xx) - pos of lang text structure header
# 64-68     pos of PRE EXTRA BYTES HEADER (90000000) (No recalc!)
# 68-70     0100 if there are PRE EXTRA BYTES, else 0000
# 70-72     (0000-0600) (No recalc!)
# 72-76     (some size of PRE EXTRA BYTES) (No recalc!)
# 76-80     (some OTHER size of PRE EXTRA BYTES) (No recalc!)
# 80-84     (00000000-09000000) (No recalc!)
# 84-88     size of TALK file excluding POST EXTRA BYTES
# 88-92     same as 84-88
# 92-94     0000
# 94-96     number of 32-byte entries in POST EXTRA BYTES (No recalc!)
# 96-100    same as 84-88
# 100-104   size of TALK file including POST EXTRA BYTES
# 104-108   00000000
# 108-112   same as 100-104

# YAKUZA
# 112-116   same as 100-104
# 116-118   0000
# 118-120   number of icon files
# 120-124   position of icon files (if exist) / some other pos (No recalc!)
# 124-128   end of icon files (if exist) / some other pos (No recalc!)

# YAKUZA 2
# 112-116   position of icon files (if exist) / some other pos (No recalc!)
# 116-120   end of icon files (if exist) / some other pos (No recalc!)
# 120-122   number of icon files
# 122-128   0000 00000000

# 128-136   00000000 00000000
# 136-140   (02000000 or 00000000) (No recalc!)
# 140-144   same as 100-104 if 136-140 is not 0

# PRE EXTRA BYTES HEADER
# 16 bytes
# 1-4       pos of PRE EXTRA BYTES (A0000000)
# 4-8       (some size of PRE EXTRA BYTES) (No recalc!)
# 8-16      00000000 00000000

# PRE EXTRA BYTES (optional)
# varying bytes, padded to % 16

# 4-CHAR SECTIONS
# 288 bytes each

# LANG TEXT STRUCTURE HEADER
# 16 bytes (per lang)
#
# 1-4       pos of first Text_Section
# 4-8       pos of Text_Name index (points to first Text_MainGroup if no names exist)
# 8-12      pos of Text_Name strings (points to first Text_MainGroup if no names exist)
# 12-14     number of Text_Sections
# 14-16     number of Text_Names

# LANG TEXT STRUCTURE
#
# Text_Sections         8 bytes each
# Text_Name index       2 bytes per Text_Name, padded to % 4 (optional)
# Text_Name strings     48 bytes per Text_Name (optional)
# Text_MainGroups       16 bytes each
# Text_SubGroups        12 bytes each
# Text_Lines            16 bytes each
# extra bytes           varying bytes (optional)
# text chars            2 bytes each, padded to % 4 (1 byte each on PAL Yakuza 1)

# in case of multiple languages, the lang text structure headers are clumped together,
# then each complete lang text structure is sequentially laid out

# POST EXTRA BYTES (optional)
# varying bytes

# EXTRA END BYTES (optional)
# varying bytes, padded to % 16

class TALK_Decoder():
    def __init__(self, input_path, icon_mode, write_charset=None, icon_bytes=b"", blue_kiryu_talk=False, iso_id=""):
        # main bytes
        self.input_path = input_path
        self.talk_bytes = b""
        self.header_bytes = b""
        self.extra_pre_bytes_header = b""
        self.output_bytes = b""

        # extra bytes
        self.extra_pre_bytes = b""
        self.extra_post_bytes = b""
        self.extra_end_pad_bytes = b""
        self.extra_end_pad_bytes_old_pos = 0
        self.icon_bytes = icon_bytes

        # 4-char section
        self.pos_char_section = 0
        self.num_char_sections = 0
        self.num_single_chars = 0
        self.chars_single_bytes = []
        self.chars_wide_bytes = []
        self.write_charset = write_charset
        self.local_charset = {}
        self.dynamic_counter_en = False
        self.dynamic_counter_jp = False
        self.char_rebuild_bytes = b""
        self.missing_chars = set()

        self.char_size = 2
        self.widespace_num = 65533
        self.space_num = 65534
        self.linebreak_num = 65535
        self.icon_mode = icon_mode
        self.orig_single = 0
        self.orig_wide = 0
        self.langs = []
        self.langcode = {0: "jp", 1: "us", 2: "uk", 3: "fr", 4: "de", 5: "es", 6: "it", 7: "xx"}
        self.langcode_rev = {"jp": 0, "us": 1, "uk": 2, "fr": 3, "de": 4, "es": 5, "it": 6, "xx": 7}
        self.text_sections = {}
        self.text_names = {}
        self.text_name_lengths = {}
        self.bytes_between_text_lines_and_chars = {}
        self.bytes_between_text_lines_and_chars_old_pos = {}
        self.blue_kiryu_talk = blue_kiryu_talk
        self.iso_id = iso_id


    # pad sequence of bytes to specified number
    def pad_bytes(self, input_bytes, pad_num, extra_pad_on_zero=False):
        mod = (len(input_bytes) % pad_num)
        if mod == 0 and extra_pad_on_zero:
            input_bytes += b"\x00" * pad_num
        elif mod == 0:
            return input_bytes
        else:
            input_bytes += b"\x00" * (pad_num - mod)
        return input_bytes


    # find the header of talk file and add extra end bytes
    def find_talk_file(self):
        with open(self.input_path, "rb") as input_file:
            input_bytes = input_file.read()
        if input_bytes[:4] == b"\x0E\x00\x00\x00":
            talk_size = int.from_bytes(input_bytes[96:100], byteorder="little")
            full_talk_size = int.from_bytes(input_bytes[100:104], byteorder="little")
            pos_char_sec = int.from_bytes(input_bytes[16:20], byteorder="little")
            self.talk_bytes = input_bytes[:talk_size]
            self.header_bytes = input_bytes[:144]
            self.extra_pre_bytes_header = input_bytes[144:160]
            self.extra_pre_bytes = input_bytes[160:pos_char_sec]
            self.extra_post_bytes = input_bytes[talk_size:full_talk_size]
            self.extra_end_pad_bytes = input_bytes[full_talk_size:]
            self.extra_end_pad_bytes_old_pos = full_talk_size
            return True
        return False


    # set which mode to use, 2 bytes per char, or 1 byte
    def set_pal_mode(self, mode):
        for i_lang in range(8):
            lang_pos = int.from_bytes(self.talk_bytes[32 + i_lang * 4:32 + i_lang * 4 + 4], byteorder="little")
            if lang_pos != 0:
                self.langs.append(self.langcode[i_lang])
        if mode:
            self.char_size = 1
            self.widespace_num = 253
            self.space_num = 254
            self.linebreak_num = 255


    # find single and wide chars from the char section
    def find_chars(self, return_chars=False):
        self.pos_char_section = int.from_bytes(self.talk_bytes[16:20], byteorder="little")
        self.num_char_sections = int.from_bytes(self.talk_bytes[20:22], byteorder="little")
        self.num_single_chars = int.from_bytes(self.talk_bytes[22:24], byteorder="little")
        char_section = self.talk_bytes[self.pos_char_section:self.pos_char_section + 288 * self.num_char_sections]
        self.chars_single_bytes, self.chars_wide_bytes = yak.talk.talk_chars.extract_chars(char_section, self.num_single_chars)
        self.orig_single = len(self.chars_single_bytes)
        self.orig_wide = len(self.chars_wide_bytes)
        if return_chars:
            return self.chars_single_bytes, self.chars_wide_bytes


    # create local charset by comparing crc32 hash of bytes against known set
    def create_local_charset(self):
        i = 0
        for c in self.chars_single_bytes:
            try:
                char, dupnum = yak.meta.char_hash.CHAR_HASH[zlib.crc32(c)]
                self.local_charset[i] = {"utf8": chr(char), "img_bytes": c, "dupnum": dupnum}
            except KeyError:
                self.local_charset[i] = {"utf8": chr(10062), "img_bytes": c, "dupnum": 0}
            i += 1
        for c in self.chars_wide_bytes:
            try:
                char, dupnum = yak.meta.char_hash.CHAR_HASH[zlib.crc32(c)]
                self.local_charset[i] = {"utf8": chr(char), "img_bytes": c, "dupnum": dupnum}
            except KeyError:
                self.local_charset[i] = {"utf8": chr(10062), "img_bytes": c, "dupnum": 0}
            i += 2
        self.local_charset[self.widespace_num] = {"utf8": chr(10175), "img_bytes": b"\x03" * 288, "dupnum": 0} # extra-wide space/icon placeholder
        self.local_charset[self.space_num] = {"utf8": " ", "img_bytes": b"\x03" * 288, "dupnum": 0} # space
        self.local_charset[self.linebreak_num] = {"utf8": "||", "img_bytes": b"\x03" * 288, "dupnum": 0} # line break


    # return the analyzed chars
    def get_local_charset(self):
        clean_charset = self.local_charset.copy()
        clean_charset.pop(self.widespace_num)
        clean_charset.pop(self.space_num)
        clean_charset.pop(self.linebreak_num)
        return clean_charset


    # extract text structures for all languages
    def extract_langs(self):
        for i_lang in self.langs:
            lang_text = self.extract_text(32 + self.langcode_rev[i_lang] * 4)
            self.text_sections[i_lang] = lang_text[0]
            self.text_names[i_lang] = lang_text[1]
            self.text_name_lengths[i_lang] = lang_text[2]
            self.bytes_between_text_lines_and_chars[i_lang] = lang_text[3]
            self.bytes_between_text_lines_and_chars_old_pos[i_lang] = lang_text[4]
        return self.text_sections, self.text_names, self.text_name_lengths, self.bytes_between_text_lines_and_chars, self.bytes_between_text_lines_and_chars_old_pos


    # extract text structure for one language
    def extract_text(self, lang_offset):
        start_text = int.from_bytes(self.talk_bytes[lang_offset:lang_offset + 4], byteorder="little")
        start_text_sections = int.from_bytes(self.talk_bytes[start_text:start_text + 4], byteorder="little")
        start_text_name_header = int.from_bytes(self.talk_bytes[start_text + 4:start_text + 8], byteorder="little")
        start_text_name_strings = int.from_bytes(self.talk_bytes[start_text + 8:start_text + 12], byteorder="little")
        num_text_sections = int.from_bytes(self.talk_bytes[start_text + 12:start_text + 14], byteorder="little")
        num_text_names = int.from_bytes(self.talk_bytes[start_text + 14:start_text + 16], byteorder="little")

        start_text_maingroups = 0
        start_chars = 0
        prev_text_line_end = 0
        prev_text_line = None
        all_text_sections = []
        all_text_names = []
        global_text_name_length = 0
        bytes_between_text_lines_and_chars = b""

        for i_text_section in range(num_text_sections):
            offset = start_text_sections + i_text_section * 8
            text_section = yak.talk.talk_text.Text_Section(self.talk_bytes[offset:offset + 8])
            for i_text_maingroup in range(text_section.num_text_maingroups()):
                text_maingroup_offset = text_section.pos_text_maingroups() + i_text_maingroup * 16
                if start_text_maingroups == 0:
                    start_text_maingroups = text_maingroup_offset # remember first maingroup pos for later
                text_maingroup = yak.talk.talk_text.Text_MainGroup(self.talk_bytes[text_maingroup_offset:text_maingroup_offset + 16])
                for i_text_subgroup in range(text_maingroup.num_text_subgroups()):
                    text_subgroup_offset = text_maingroup.pos_text_subgroups() + i_text_subgroup * 12
                    text_subgroup = yak.talk.talk_text.Text_SubGroup(self.talk_bytes[text_subgroup_offset:text_subgroup_offset + 12])
                    char_offset = text_subgroup.pos_chars()
                    if start_chars == 0:
                        start_chars = char_offset # remember first char pos for later
                    for i_text_line in range(text_subgroup.num_text_lines()):
                        text_line_offset = text_subgroup.pos_text_lines() + i_text_line * 16
                        text_line = yak.talk.talk_text.Text_Line(self.talk_bytes[text_line_offset:text_line_offset + 16])
                        if not text_line.is_meta():
                            num_chars = text_line.num_chars()
                            if prev_text_line_end and prev_text_line_end != char_offset: # this will never get here???
                                prev_text_line.add_end_bytes(self.talk_bytes[prev_text_line_end:char_offset])
                            for i_char in range(num_chars):
                                text_line.add_char(int.from_bytes(self.talk_bytes[char_offset:char_offset + self.char_size], byteorder="little"))
                                char_offset += self.char_size
                            prev_text_line_end = char_offset
                            prev_text_line = text_line
                        text_subgroup.add_text_line(text_line)
                    text_maingroup.add_text_subgroup(text_subgroup)
                text_section.add_text_maingroup(text_maingroup)
            all_text_sections.append(text_section)

        if start_text_name_header != start_text_name_strings:
            global_text_name_length = int((start_text_maingroups - start_text_name_strings) / num_text_names)
            for i_text_name in range(num_text_names):
                text_name_offset = start_text_name_header + i_text_name * 2
                local_text_name_length = int.from_bytes(self.talk_bytes[text_name_offset:text_name_offset + 2], byteorder="little")
                text_name = yak.talk.talk_text.Text_Name()
                char_offset = start_text_name_strings + i_text_name * global_text_name_length
                for i_char in range(local_text_name_length):
                    text_name.add_char(int.from_bytes(self.talk_bytes[char_offset + i_char * self.char_size:char_offset + i_char * self.char_size + self.char_size], byteorder="little"))
                all_text_names.append(text_name)

        if num_text_sections:
            text_line_end = text_line_offset + 16
            bytes_between_text_lines_and_chars = self.talk_bytes[text_line_end:start_chars]
            bytes_between_text_lines_and_chars_old_pos = text_line_end

        return all_text_sections, all_text_names, global_text_name_length, bytes_between_text_lines_and_chars, bytes_between_text_lines_and_chars_old_pos


    # get utf8 chars from char numbers for Text_Lines
    def calc_line_strings(self):
        for i in self.langs:
            for text_section in self.text_sections[i]:
                for text_maingroup in text_section.get_text_maingroups():
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        main_line = text_subgroup.get_main_text_line()
                        if main_line:
                            ci = 0
                            for c in main_line.get_chars():
                                c_utf8 = self.local_charset[c]["utf8"]
                                main_line.add_char_utf8(c_utf8)
                                if c == self.linebreak_num:
                                    main_line.set_linebreak_pos(ci)
                                ci += 1

            for text_name in self.text_names[i]:
                for c in text_name.get_chars():
                    c_utf8 = self.local_charset[c]["utf8"]
                    text_name.add_char_utf8(c_utf8)


    # analyze and add meta text lines into the char list where necessary
    def calc_meta_lines(self):
        for i in self.langs:
            for text_section in self.text_sections[i]:
                for text_maingroup in text_section.get_text_maingroups():
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        text_subgroup.inject_meta_lines()


    # write out the text lines as pngs
    def write_line_png(self, path_out):
        # yak.talk.talk_chars.write_char_pngs(self.chars_single_bytes, self.chars_wide_bytes, path_out) #write charset
        for i in self.langs:
            tx_i = 0
            for text_section in self.text_sections[i]:
                tx_j = 0
                for text_maingroup in text_section.get_text_maingroups():
                    tx_k = 0
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        main_line = text_subgroup.get_main_text_line()
                        if main_line and main_line.num_chars() > 0:
                            charbytes_list = []
                            for c in main_line.get_chars():
                                try:
                                    charbytes_list.append(self.local_charset[c]["img_bytes"])
                                except KeyError:
                                    charbytes_list.append(b"\x00" * 288)
                            charbytes_array, writer = yak.talk.talk_chars.merge_line(charbytes_list)
                            path_out_file = os.path.join(path_out, f"{i}_{tx_i:03d}_{tx_j:03d}_{tx_k:03d}.png")
                            os.makedirs(os.path.dirname(path_out_file), exist_ok=True)
                            with open(path_out_file, "wb") as file_out:
                                writer.write(file_out, charbytes_array)
                        tx_k += 1
                    tx_j += 1
                tx_i += 1

            n_i = 0
            for text_name in self.text_names[i]:
                charbytes_list = []
                for c in text_name.get_chars():
                    try:
                        charbytes_list.append(self.local_charset[c]["img_bytes"])
                    except KeyError:
                        charbytes_list.append(b"\x00" * 288)
                if not charbytes_list:
                    charbytes_list.append(b"\x00" * 288)
                charbytes_array, writer = yak.talk.talk_chars.merge_line(charbytes_list)
                path_out_file = os.path.join(path_out, "names", f"{i}_{n_i:03d}.png")
                os.makedirs(os.path.dirname(path_out_file), exist_ok=True)
                with open(path_out_file, "wb") as file_out:
                    writer.write(file_out, charbytes_array)
                n_i += 1


    # write out the text lines as json
    def write_talk_struct(self, path_out):
        talk_struct = {}
        talk_struct["header_bytes"] = self.header_bytes.hex()
        talk_struct["extra_pre_bytes_header"] = self.extra_pre_bytes_header.hex()
        talk_struct["extra_pre_bytes"] = self.extra_pre_bytes.hex()
        talk_struct["extra_post_bytes"] = self.extra_post_bytes.hex()
        talk_struct["extra_end_pad_bytes"] = self.extra_end_pad_bytes.hex()
        talk_struct["extra_end_pad_bytes_old_pos"] = self.extra_end_pad_bytes_old_pos
        talk_struct["orig_single"] = self.orig_single
        talk_struct["orig_wide"] = self.orig_wide
        talk_struct["pal_mode"] = True if self.char_size == 1 else False
        talk_struct["dynamic_counter_jp"] = self.dynamic_counter_jp
        talk_struct["dynamic_counter_en"] = self.dynamic_counter_en
        talk_struct["text_structs"] = []
        for i in self.langs:
            text_struct = {}
            text_struct["lang_id"] = i
            text_struct["name_length"] = self.text_name_lengths[i]
            text_struct["bytes_between_text_lines_and_chars"] = self.bytes_between_text_lines_and_chars[i].hex()
            text_struct["bytes_between_text_lines_and_chars_old_pos"] = self.bytes_between_text_lines_and_chars_old_pos[i]
            text_struct["names"] = []
            for name in self.text_names[i]:
                text_struct["names"].append(name.get_string())
            text_struct["text_sections"] = []
            tx_sc = 0
            for text_section in self.text_sections[i]:
                text_section_dict = text_section.get_as_dict()
                text_section_dict["id"] = tx_sc
                tx_mg = 0
                for text_maingroup in text_section.get_text_maingroups():
                    text_maingroup_dict = text_maingroup.get_as_dict()
                    text_maingroup_dict["id"] = tx_mg
                    tx_sg = 0
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        text_subgroup_dict = text_subgroup.get_as_dict()
                        text_subgroup_dict["id"] = tx_sg
                        text_subgroup_dict["full_id"] = f"{tx_sc}_{tx_mg}_{tx_sg}"
                        tx_sg += 1
                        text_maingroup_dict["text_subgroups"].append(text_subgroup_dict)
                    tx_mg += 1
                    text_section_dict["text_maingroups"].append(text_maingroup_dict)
                tx_sc += 1
                text_struct["text_sections"].append(text_section_dict)
            talk_struct["text_structs"].append(text_struct)
        path_out += ".json"

        # patch in structure for yakuza 1 OPENING
        out_dir = os.path.dirname(path_out)
        if out_dir.endswith("OPENING_MOVIE.DAT") and talk_struct["text_structs"] == []:
            talk_struct = yak.meta.opening_sub.generate_opening_talk(talk_struct, self.iso_id)
        os.makedirs(out_dir, exist_ok=True)
        with open(path_out, encoding="utf8", mode="w") as out_file:
            json.dump(talk_struct, out_file, indent=4, ensure_ascii=False)


    # get txbp icons embedded in file:
    def get_icons(self):
        if self.icon_mode == 1:
            num_icons = int.from_bytes(self.talk_bytes[118:120], byteorder="little")
            pos_start = int.from_bytes(self.talk_bytes[120:124], byteorder="little")
            pos_end = int.from_bytes(self.talk_bytes[124:128], byteorder="little")
        elif self.icon_mode == 2:
            num_icons = int.from_bytes(self.talk_bytes[120:124], byteorder="little")
            pos_start = int.from_bytes(self.talk_bytes[112:116], byteorder="little")
            pos_end = int.from_bytes(self.talk_bytes[116:120], byteorder="little")
        if num_icons == 0:
            return None
        icon_list = []
        icon_step = int((pos_end - pos_start) / num_icons)
        for i in range(num_icons):
            icon_list.append(self.talk_bytes[pos_start:pos_start + icon_step])
            pos_start += icon_step
        return icon_list


    # read in text lines from json
    def read_talk_struct(self, path_in):
        talk_struct = {}
        with open(path_in, encoding="utf8", mode="r") as in_file:
            talk_struct = json.load(in_file)
        self.header_bytes = bytes.fromhex(talk_struct["header_bytes"])
        self.extra_pre_bytes_header = bytes.fromhex(talk_struct["extra_pre_bytes_header"])
        self.extra_pre_bytes = bytes.fromhex(talk_struct["extra_pre_bytes"])
        self.extra_post_bytes = bytes.fromhex(talk_struct["extra_post_bytes"])
        self.extra_end_pad_bytes = bytes.fromhex(talk_struct["extra_end_pad_bytes"])
        self.extra_end_pad_bytes_old_pos = int(talk_struct["extra_end_pad_bytes_old_pos"])
        self.orig_single = int(talk_struct["orig_single"])
        self.orig_wide = int(talk_struct["orig_wide"])
        self.dynamic_counter_jp = talk_struct["dynamic_counter_jp"]
        self.dynamic_counter_en = talk_struct["dynamic_counter_en"]
        if talk_struct["pal_mode"]:
            self.char_size = 1
            self.widespace_num = 253
            self.space_num = 254
            self.linebreak_num = 255
        for text_struct in talk_struct["text_structs"]:
            i = self.langcode_rev[text_struct["lang_id"]]
            self.langs.append(i)
            self.text_sections[i] = []
            self.text_names[i] = []
            self.text_name_lengths[i] = int(text_struct["name_length"])
            self.bytes_between_text_lines_and_chars[i] = bytes.fromhex(text_struct["bytes_between_text_lines_and_chars"])
            self.bytes_between_text_lines_and_chars_old_pos[i] = int(text_struct["bytes_between_text_lines_and_chars_old_pos"])
            for name in text_struct["names"]:
                text_name = yak.talk.talk_text.Text_Name()
                # truncate name for length
                name = name[:int(self.text_name_lengths[i] / self.char_size)]
                text_name.from_string_utf8(name)
                self.text_names[i].append(text_name)
            for text_section_dict in text_struct["text_sections"]:
                text_section = yak.talk.talk_text.Text_Section(bytes.fromhex(text_section_dict["bytes"]))
                for text_maingroup_dict in text_section_dict["text_maingroups"]:
                    text_maingroup = yak.talk.talk_text.Text_MainGroup(bytes.fromhex(text_maingroup_dict["bytes"]))
                    text_section.add_text_maingroup(text_maingroup)
                    for text_subgroup_dict in text_maingroup_dict["text_subgroups"]:
                        text_subgroup = yak.talk.talk_text.Text_SubGroup(bytes.fromhex(text_subgroup_dict["bytes"]))
                        text_subgroup.add_from_dict(text_subgroup_dict)
                        text_maingroup.add_text_subgroup(text_subgroup)
                self.text_sections[i].append(text_section)


    # analyze and add meta text lines into the char list where necessary
    def decalc_meta_lines(self):
        for i in self.langs:
            for text_section in self.text_sections[i]:
                for text_maingroup in text_section.get_text_maingroups():
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        main_line = text_subgroup.get_main_text_line()
                        dynamic_counter = text_subgroup.extract_meta_lines(self.blue_kiryu_talk)
                        if i == 0 and dynamic_counter:
                            self.dynamic_counter_jp = True
                        elif i > 0 and dynamic_counter:
                            self.dynamic_counter_en = True


    # recreate the local charset using string chars
    def recreate_local_charset(self):
        self.chars_single_bytes = []
        self.chars_wide_bytes = []
        chars_single_dict = {}
        chars_wide_dict = {}
        chars_merge_dict = {}
        if self.dynamic_counter_en:
            for c in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ","]:
                self.chars_single_bytes.append(self.write_charset[c])
                chars_single_dict[c] = len(self.chars_single_bytes) - 1
        if self.dynamic_counter_jp:
            for c in [chr(120792), chr(120793), chr(120794), chr(120795), chr(120796), chr(120797), chr(120798), chr(120799), chr(120800), chr(120801), chr(10068)]:
                try:
                    self.chars_wide_bytes.append(self.write_charset[c])
                    chars_wide_dict[c] = (len(self.chars_wide_bytes) - 1) * 2
                except KeyError:
                    pass
        for i in self.langs:
            for name in self.text_names[i]:
                for c in name.get_chars_utf8():
                    if c in (chr(10175), " ", "||") or (c in chars_single_dict) or (c in chars_wide_dict):
                        continue
                    try:
                        c_bytes = self.write_charset[c]
                        if len(c_bytes) == 288:
                            self.chars_single_bytes.append(c_bytes)
                            chars_single_dict[c] = len(self.chars_single_bytes) - 1
                        elif len(c_bytes) == 576:
                            self.chars_wide_bytes.append(c_bytes)
                            chars_wide_dict[c] = (len(self.chars_wide_bytes) - 1) * 2
                    except KeyError:
                        self.chars_wide_bytes.append(self.write_charset[chr(9587)])
                        chars_wide_dict[c] = (len(self.chars_wide_bytes) - 1) * 2
                        self.missing_chars.add(c)
            for text_section in self.text_sections[i]:
                for text_maingroup in text_section.get_text_maingroups():
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        main_line = text_subgroup.get_main_text_line()
                        for c in main_line.get_chars_utf8():
                            if c in (chr(10175), " ", "||") or (c in chars_single_dict) or (c in chars_wide_dict):
                                continue
                            try:
                                c_bytes = self.write_charset[c]
                                if len(c_bytes) == 288:
                                    self.chars_single_bytes.append(c_bytes)
                                    chars_single_dict[c] = len(self.chars_single_bytes)-1
                                elif len(c_bytes) == 576:
                                    self.chars_wide_bytes.append(c_bytes)
                                    chars_wide_dict[c] = (len(self.chars_wide_bytes) - 1) * 2
                            except KeyError:
                                self.chars_wide_bytes.append(self.write_charset[chr(9587)])
                                chars_wide_dict[c] = (len(self.chars_wide_bytes) - 1) * 2
                                self.missing_chars.add(c)
        # pad single/wide charsets with spaces to be divisible by 2/4
        if len(self.chars_single_bytes) % 2 != 0:
            self.chars_single_bytes.append(self.write_charset[chr(32)]) # pad with single space
        if (len(self.chars_single_bytes) + len(self.chars_wide_bytes) * 2) % 4 != 0:
            self.chars_wide_bytes.append(self.write_charset[chr(12288)]) # pad with wide space
        # merge char dicts and offset the positions for wide chars
        single_length_offset = len(self.chars_single_bytes)
        for key, value in chars_wide_dict.items():
            chars_wide_dict[key] = value + single_length_offset
        chars_merge_dict.update(chars_single_dict)
        chars_merge_dict.update(chars_wide_dict)

        for i in self.langs:
            for name in self.text_names[i]:
                for c in name.get_chars_utf8():
                    if c == chr(10175):
                        name.add_char(self.widespace_num)
                    elif c == " ":
                        name.add_char(self.space_num)
                    elif c == "||":
                        name.add_char(self.linebreak_num)
                    else:
                        name.add_char(chars_merge_dict[c])
            for text_section in self.text_sections[i]:
                for text_maingroup in text_section.get_text_maingroups():
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        main_line = text_subgroup.get_main_text_line()
                        for c in main_line.get_chars_utf8():
                            if c == chr(10175):
                                main_line.add_char(self.widespace_num)
                            elif c == " ":
                                main_line.add_char(self.space_num)
                            elif c == "||":
                                main_line.add_char(self.linebreak_num)
                            else:
                                main_line.add_char(chars_merge_dict[c])

        self.char_rebuild_bytes = yak.talk.talk_chars.encode_char_section(self.chars_single_bytes.copy(), self.chars_wide_bytes.copy())


    # replace TXBP icons in pre bytes
    def insert_icons(self):
        if self.icon_bytes:
            if self.icon_mode == 1:
                pos_start = int.from_bytes(self.header_bytes[120:124], byteorder="little") - (144 + 16)
                pos_end = int.from_bytes(self.header_bytes[124:128], byteorder="little") - (144 + 16)
            elif self.icon_mode == 2:
                pos_start = int.from_bytes(self.header_bytes[112:116], byteorder="little") - (144 + 16)
                pos_end = int.from_bytes(self.header_bytes[116:120], byteorder="little") - (144 + 16)
            if pos_end - pos_start != len(self.icon_bytes):
                return(f"STEP - Add TALK icon\nERROR - New icon length does not match previous value, icons ignored...\nPath: {self.input_path}")
            self.extra_pre_bytes = self.extra_pre_bytes[:pos_start] + self.icon_bytes + self.extra_pre_bytes[pos_end:]
        return None


    # return any missing chars detected during rebuild
    def get_missing_chars(self):
        return self.missing_chars


    # rebuild the TALK BIN structure
    def recreate_talk_file(self):
        # define values needed for header later
        NUM_LANGS = len(self.langs)
        NUM_SINGLE_CHARS = len(self.chars_single_bytes)
        NUM_4CHAR_SECTIONS = int(len(self.char_rebuild_bytes) / 288)
        NUM_TEXT_SECTIONS = {}
        NUM_TEXT_NAMES = {}
        POS_EXTRA_PRE_BYTES_HEADER = 0
        POS_EXTRA_PRE_BYTES = 0
        POS_EXTRA_POST_BYTES = 0
        POS_EOF = 0
        POS_4CHAR_SECTIONS = 0
        POS_LANG_HEADERS = 0
        POS_TEXT_SECTION = {}
        POS_TEXT_NAME_INDEX = {}
        POS_TEXT_NAME_OFFSET = {}
        # add initial and some placeholder bytes
        self.output_bytes += self.header_bytes
        POS_EXTRA_PRE_BYTES_HEADER = len(self.output_bytes)
        self.output_bytes += self.extra_pre_bytes_header
        POS_EXTRA_PRE_BYTES = len(self.output_bytes)
        self.output_bytes += self.extra_pre_bytes
        POS_4CHAR_SECTIONS = len(self.output_bytes)
        self.output_bytes += self.char_rebuild_bytes
        POS_LANG_HEADERS = len(self.output_bytes)
        self.output_bytes += b"\x00" * (16 * NUM_LANGS)
        # build text structure for each language
        for i in self.langs:
            LEN_TEXT_SECTIONS = 0
            LEN_TEXT_MAINGROUPS = 0
            LEN_TEXT_SUBGROUPS = 0
            LEN_TEXT_LINES = 0
            LEN_TEXT_NAMES = 0
            NUM_TEXT_NAMES[i] = len(self.text_names[i])
            NUM_TEXT_SECTIONS[i] = len(self.text_sections[i])
            POS_TEXT_SECTION[i] = len(self.output_bytes)
            POS_TEXT_NAME_INDEX[i] = 0
            POS_TEXT_NAME_OFFSET[i] = 0
            DIFF_BETWEEN_BYTES_POS = 0
            text_name_bytes = b""
            text_section_bytes = b""
            text_maingroup_bytes = b""
            text_subgroup_bytes = b""
            text_line_bytes = b""
            text_char_bytes = b""
            for name in self.text_names[i]:
                text_name_bytes += len(name.get_chars()).to_bytes(2, byteorder="little")
            text_name_bytes = self.pad_bytes(text_name_bytes, 4)
            POS_TEXT_NAME_OFFSET[i] = len(text_name_bytes)
            for name in self.text_names[i]:
                name_char_bytes = b""
                for c in name.get_chars():
                    name_char_bytes += c.to_bytes(self.char_size, byteorder="little")
                if self.char_size == 2:
                    name_char_bytes += b"\xFE\xFF" * int((self.text_name_lengths[i] - len(name_char_bytes)) / 2)
                elif self.char_size == 1:
                    name_char_bytes += b"\xFE" * (self.text_name_lengths[i] - len(name_char_bytes))
                text_name_bytes += name_char_bytes
            LEN_TEXT_NAMES = len(text_name_bytes)
            for text_section in self.text_sections[i]:
                LEN_TEXT_SECTIONS += 8
                for text_maingroup in text_section.get_text_maingroups():
                    LEN_TEXT_MAINGROUPS += 16
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        LEN_TEXT_SUBGROUPS += 12
                        LEN_TEXT_LINES += len(text_subgroup.get_text_lines()) * 16
            if self.bytes_between_text_lines_and_chars[i]:
                DIFF_BETWEEN_BYTES_POS = self.bytes_between_text_lines_and_chars_old_pos[i] - (len(self.output_bytes) + LEN_TEXT_SECTIONS + LEN_TEXT_NAMES + LEN_TEXT_MAINGROUPS + LEN_TEXT_SUBGROUPS + LEN_TEXT_LINES)
            tx_mg = 0
            tx_sg = 0
            tx_li = 0
            tx_ch = 0
            for text_section in self.text_sections[i]:
                pos_next_maingroup = len(self.output_bytes) + LEN_TEXT_SECTIONS + LEN_TEXT_NAMES + tx_mg * 16
                text_section_bytes += text_section.get_new_bytes(pos_next_maingroup)
                for text_maingroup in text_section.get_text_maingroups():
                    tx_mg += 1
                    pos_next_subgroup = len(self.output_bytes) + LEN_TEXT_SECTIONS + LEN_TEXT_NAMES + LEN_TEXT_MAINGROUPS + tx_sg * 12
                    text_maingroup_bytes += text_maingroup.get_new_bytes(pos_next_subgroup, DIFF_BETWEEN_BYTES_POS)
                    for text_subgroup in text_maingroup.get_text_subgroups():
                        tx_sg += 1
                        pos_next_ch = len(self.output_bytes) + LEN_TEXT_SECTIONS + LEN_TEXT_NAMES + LEN_TEXT_MAINGROUPS + LEN_TEXT_SUBGROUPS + LEN_TEXT_LINES + len(self.bytes_between_text_lines_and_chars[i]) + tx_ch * self.char_size
                        pos_next_line = len(self.output_bytes) + LEN_TEXT_SECTIONS + LEN_TEXT_NAMES + LEN_TEXT_MAINGROUPS + LEN_TEXT_SUBGROUPS + tx_li * 16
                        text_subgroup_bytes += text_subgroup.get_new_bytes(pos_next_ch, pos_next_line)
                        for text_line in text_subgroup.get_text_lines():
                            tx_li += 1
                            text_line_bytes += text_line.get_new_bytes()
                            for c in text_line.get_chars():
                                tx_ch += 1
                                text_char_bytes += c.to_bytes(self.char_size, byteorder="little")
            self.output_bytes += text_section_bytes
            POS_TEXT_NAME_INDEX[i] = len(self.output_bytes)
            self.output_bytes += text_name_bytes + text_maingroup_bytes + text_subgroup_bytes + text_line_bytes + self.bytes_between_text_lines_and_chars[i] + text_char_bytes
            self.output_bytes = self.pad_bytes(self.output_bytes, 4)
        # add extra bytes to end
        POS_EXTRA_POST_BYTES = len(self.output_bytes)
        self.output_bytes += self.extra_post_bytes
        POS_EOF = len(self.output_bytes)
        if self.extra_end_pad_bytes:
            if self.output_bytes[4:8] == b"\x04\x00\x00\x00": # recalc pos ref in extra end bytes for SHOP and PRESENT files
                extra_end_pad_bytes_pos_diff = self.extra_end_pad_bytes_old_pos - POS_EOF
                extra_end_pad_bytes_ref = int.from_bytes(self.extra_end_pad_bytes[4:8], byteorder="little") - extra_end_pad_bytes_pos_diff
                self.extra_end_pad_bytes = self.extra_end_pad_bytes[:4] + extra_end_pad_bytes_ref.to_bytes(4, byteorder="little") + self.extra_end_pad_bytes[8:]
            self.output_bytes += self.extra_end_pad_bytes
            if self.output_bytes[4:8] == b"\x01\x00\x00\x00": # only pad for cutscene subtitles from DAT files
                self.output_bytes = self.pad_bytes(self.output_bytes, 16)
        # fill in correct values in header
        header_bytes = self.output_bytes[:16]
        header_bytes += POS_4CHAR_SECTIONS.to_bytes(4, byteorder="little")
        header_bytes += NUM_4CHAR_SECTIONS.to_bytes(2, byteorder="little")
        header_bytes += NUM_SINGLE_CHARS.to_bytes(2, byteorder="little")
        header_bytes += self.output_bytes[24:32]
        lang_offset = POS_LANG_HEADERS
        for i in range(8):
            if i in self.langs:
                header_bytes += lang_offset.to_bytes(4, byteorder="little")
                lang_offset += 16
            else:
                header_bytes += b"\x00" * 4
        header_bytes += self.output_bytes[64:84]
        header_bytes += POS_EXTRA_POST_BYTES.to_bytes(4, byteorder="little") + POS_EXTRA_POST_BYTES.to_bytes(4, byteorder="little")
        header_bytes += self.output_bytes[92:96]
        header_bytes += POS_EXTRA_POST_BYTES.to_bytes(4, byteorder="little") + POS_EOF.to_bytes(4, byteorder="little")
        header_bytes += self.output_bytes[104:108]
        header_bytes += POS_EOF.to_bytes(4, byteorder="little")
        if self.icon_mode == 1:
            header_bytes += POS_EOF.to_bytes(4, byteorder="little")
            header_bytes += self.output_bytes[116:136]
        else:
            header_bytes += self.output_bytes[112:136]
        if self.output_bytes[136:140] != b"\x00" * 4:
            header_bytes += self.output_bytes[136:140]
            header_bytes += POS_EOF.to_bytes(4, byteorder="little")
        else:
            header_bytes += self.output_bytes[136:144]
        # fill in correct values in language headers
        lang_header_bytes = b""
        for i in self.langs:
            lang_header_bytes += POS_TEXT_SECTION[i].to_bytes(4, byteorder="little")
            lang_header_bytes += POS_TEXT_NAME_INDEX[i].to_bytes(4, byteorder="little")
            lang_header_bytes += (POS_TEXT_NAME_INDEX[i] + POS_TEXT_NAME_OFFSET[i]).to_bytes(4, byteorder="little")
            lang_header_bytes += NUM_TEXT_SECTIONS[i].to_bytes(2, byteorder="little") + NUM_TEXT_NAMES[i].to_bytes(2, byteorder="little")
        self.output_bytes = header_bytes + self.output_bytes[144:POS_LANG_HEADERS] + lang_header_bytes + self.output_bytes[POS_LANG_HEADERS + len(lang_header_bytes):]
        return self.output_bytes#+b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"*32768
