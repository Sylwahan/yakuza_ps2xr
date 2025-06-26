import re

# 8 bytes   Text_Section
# 1-3       ident
# 4         number of text_maingroups
# 5-8       position of first text_maingroup
class Text_Section():
    def __init__(self, full_bytes):
        self._full_bytes = full_bytes
        self._ident = full_bytes[:3]
        self._num_text_maingroups = int.from_bytes(full_bytes[3:4], byteorder="little")
        self._pos_text_maingroups = int.from_bytes(full_bytes[4:8], byteorder="little")
        self._text_maingroups = []

    def num_text_maingroups(self):
        return self._num_text_maingroups

    def pos_text_maingroups(self):
        return self._pos_text_maingroups

    def add_text_maingroup(self, text_maingroup):
        self._text_maingroups.append(text_maingroup)

    def get_text_maingroups(self):
        return self._text_maingroups

    def get_as_dict(self):
        self_dict = {}
        self_dict["id"] = None
        self_dict["bytes"] = self._full_bytes.hex()
        self_dict["text_maingroups"] = []
        return self_dict

    # return bytes representation after modification
    def get_new_bytes(self, pos_first_maingroup):
        return self._ident+len(self._text_maingroups).to_bytes(1, byteorder="little")+pos_first_maingroup.to_bytes(4, byteorder="little")

# 16 bytes  Text_MainGroup
# 1-4       00000000 or position in bytes_between_text_lines_and_chars
# 5-8       position of first text_subgroup
# 9         00 ???
# 10        number of text_subgroups
# 11-16     ident B
class Text_MainGroup():
    def __init__(self, full_bytes):
        self._full_bytes = full_bytes
        self._ident_a = full_bytes[:4]
        self._ident_b = full_bytes[10:]
        self._num_text_subgroups = int.from_bytes(full_bytes[9:10], byteorder="little")
        self._pos_text_subgroups = int.from_bytes(full_bytes[4:8], byteorder="little")
        self._text_subgroups = []

    def num_text_subgroups(self):
        return self._num_text_subgroups

    def pos_text_subgroups(self):
        return self._pos_text_subgroups

    def add_text_subgroup(self, text_subgroup):
        self._text_subgroups.append(text_subgroup)

    def get_text_subgroups(self):
        return self._text_subgroups

    def get_as_dict(self):
        self_dict = {}
        self_dict["id"] = None
        self_dict["bytes"] = self._full_bytes.hex()
        self_dict["text_subgroups"] = []
        return self_dict

    # return bytes representation after modification
    def get_new_bytes(self, pos_first_subgroup, between_bytes_diff):
        between_bytes_pos = self._full_bytes[:4]
        if between_bytes_pos != b"\x00\x00\x00\x00":
            between_bytes_pos = int.from_bytes(between_bytes_pos, byteorder="little")
            between_bytes_pos -= between_bytes_diff
            between_bytes_pos = between_bytes_pos.to_bytes(4, byteorder="little")
        return between_bytes_pos+pos_first_subgroup.to_bytes(4, byteorder="little")+self._full_bytes[8:9]+len(self._text_subgroups).to_bytes(1, byteorder="little")+self._full_bytes[10:]

# 12 bytes  Text_SubGroup
# 1         number of chars in main text_line
# 2         number of text_lines
# 3-4       ident B
# 5-8       position of first char
# 9-12      position of first text_line
class Text_SubGroup():
    def __init__(self, full_bytes):
        self._full_bytes = full_bytes
        self._ident_a = full_bytes[:1]
        self._ident_b = full_bytes[2:4]
        self._num_text_lines = int.from_bytes(full_bytes[1:2], byteorder="little")
        self._pos_text_lines = int.from_bytes(full_bytes[8:12], byteorder="little")
        self._pos_chars = int.from_bytes(full_bytes[4:8], byteorder="little")
        self._main_text_line = None
        self._text_lines = []
        self._meta_text_lines = []
        self._saved_meta_lines = []

    def num_text_lines(self):
        return self._num_text_lines

    def pos_text_lines(self):
        return self._pos_text_lines

    def pos_chars(self):
        return self._pos_chars

    def add_text_line(self, text_line):
        self._text_lines.append(text_line)
        if text_line.is_meta():
            self._meta_text_lines.append(text_line)
        else:
            self._main_text_line = text_line

    def get_text_lines(self):
        return self._text_lines

    def get_main_text_line(self):
        return self._main_text_line

    def get_meta_text_lines(self):
        return self._meta_text_lines

    # set necessary meta on meta lines and inject into char list where needed
    def inject_meta_lines(self):
        main_line = self._main_text_line
        insert_meta_items = []
        delete_lines = []
        for meta_line in self._meta_text_lines:
            if meta_line._full_bytes[0:2] == b"\x02\x00": ### reset all meta
                mstring = f"{{MR:00}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x01": ### add pause of given length
                pause_length = int.from_bytes(meta_line._full_bytes[3:4], byteorder="little")
                mstring = f"{{PA:{pause_length}}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x02": ### change speed
                speed = int.from_bytes(meta_line._full_bytes[3:4], byteorder="little")
                mstring = f"{{SP:{speed}}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x06": ### choose some color
                # convert BGRA to RGB
                color = (meta_line._full_bytes[14:15]+meta_line._full_bytes[13:14]+meta_line._full_bytes[12:13]).hex()
                mstring = f"{{CU:{color}}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x07": ### defines a dynamic number section
                num_mod = meta_line._full_bytes[3:4].hex() # number modifier ???
                num_length = meta_line._full_bytes[4:5].hex() # number of digits
                num_id = meta_line._full_bytes[12:13].hex() # number identifier
                mstring = f"{{NU:{num_mod}_{num_length}_{num_id}}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x08": ### defines an icon integrated in TALK file
                unknown_byte = meta_line._full_bytes[8:9].hex() # unknown bytes
                icon_id = meta_line._full_bytes[10:11].hex() # icon identifier
                mstring = f"{{IC:{unknown_byte}_{icon_id}}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x0d": ### choose new color
                # convert BGRA to RGB
                color = (meta_line._full_bytes[14:15]+meta_line._full_bytes[13:14]+meta_line._full_bytes[12:13]).hex()
                mstring = f"{{CC:{color}}}"
            elif meta_line._full_bytes[0:2] == b"\x02\x0e": ### reset to previously used color
                mstring = f"{{CR:00}}"
            else: ### meta lines that are not possible to simplify
                if meta_line._full_bytes[6:7] in (b"\x00", main_line._full_bytes[6:7]):
                    continue
                self._saved_meta_lines.append(meta_line)
                mstring = f"{{MS:{len(self._saved_meta_lines)-1}}}"
            pos = int.from_bytes(meta_line._full_bytes[6:7], byteorder="little")
            insert_meta_items.append({"pos": pos, "mstring": mstring})
            delete_lines.append(meta_line)
        insert_meta_items.sort(key=lambda meta_item: meta_item["pos"], reverse=True)
        for meta_item in insert_meta_items:
            main_line.insert_char_utf8(meta_item["pos"], meta_item["mstring"])
        for meta_line in delete_lines:
            self._meta_text_lines.remove(meta_line)

    # get back original meta lines from the in-stream meta
    def extract_meta_lines(self, blue_kiryu_talk):
        dynamic_counter = False
        re_meta = re.compile(r"{([A-Z]{2}):([^{}:]+)}")
        main_line = self._main_text_line
        line_chars = main_line.get_chars_utf8()
        found_meta_lines = []
        add_back_chars = []
        i = 0
        while line_chars:
            c = line_chars.pop(0)
            meta_find = re_meta.match(c)
            if meta_find:
                meta_id, meta_param = meta_find.group(1,2)
                if meta_id == "MR": ### reset all meta
                    mbytes = b"\x02\x00\x00\x00\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                elif meta_id == "PA": ### add pause of given length
                    mbytes = b"\x02\x01\x00"+int(meta_param).to_bytes(1, byteorder="little")+b"\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                elif meta_id == "SP": ### change speed
                    mbytes = b"\x02\x02\x00"+int(meta_param).to_bytes(1, byteorder="little")+b"\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"			
                elif meta_id == "CU": ### choose some color
                    # convert RGB to BGRA
                    color_rgb = bytes.fromhex(meta_param)
                    color_bgra = color_rgb[2:3]+color_rgb[1:2]+color_rgb[0:1]+b"\xFF"
                    mbytes = b"\x02\x06\x00\x00\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00"+color_bgra
                elif meta_id == "NU": ### defines a dynamic counter section
                    dynamic_counter = True
                    num_mod, num_length, num_id = meta_param.split("_") # number modifier, number of digits, number identifier
                    mbytes = b"\x02\x07\x00"+bytes.fromhex(num_mod)+bytes.fromhex(num_length)+b"\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00"+bytes.fromhex(num_id)+b"\x00\x00\x00"
                elif meta_id == "IC": ### defines an icon integrated in TALK file
                    unknown_byte, icon_id = meta_param.split("_") # number of digits, number identifier
                    mbytes = b"\x02\x08\x00\x00\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00"+bytes.fromhex(unknown_byte)+b"\x00"+bytes.fromhex(icon_id)+b"\x00\x00\x00\x00\x00"
                elif meta_id == "CC": ### choose new color
                    # convert RGB to BGRA
                    color_rgb = bytes.fromhex(meta_param)
                    color_bgra = color_rgb[2:3]+color_rgb[1:2]+color_rgb[0:1]+b"\xFF"
                    mbytes = b"\x02\x0d\x00\x00\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00"+color_bgra
                elif meta_id == "CR": ### reset to previously used color
                    mbytes = b"\x02\x0e\x00\x00\x00\x00"+i.to_bytes(1, byteorder="little")+b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                else: ### saved meta lines that are not possible to simplify
                    mbytes = self._saved_meta_lines[int(meta_param)]._full_bytes
                    mbytes = mbytes[:6]+i.to_bytes(1, byteorder="little")+mbytes[7:]
                found_meta_lines.append(Text_Line(mbytes))
            else:
                add_back_chars.append(c)
                i += 1
        self._saved_meta_lines = []
        main_line._chars_utf8 = add_back_chars
        meta_lines_start = []
        meta_lines_end = []
        for meta_line in self._meta_text_lines:
            if blue_kiryu_talk and meta_line._full_bytes[0:2] == b"\x02\x09" and meta_line._full_bytes[4:5] == b"\x01":
                meta_line._full_bytes = meta_line._full_bytes[:12]+b"\xff\xc8\xc8\xff"
            if meta_line._full_bytes[6:7] == b"\x00":
                meta_lines_start.append(meta_line)
            else:
                meta_line._full_bytes = meta_line._full_bytes[:6]+len(add_back_chars).to_bytes(1, byteorder="little")+meta_line._full_bytes[7:]
                meta_lines_end.append(meta_line)
        for meta_line in found_meta_lines:
            meta_lines_start.append(meta_line)
        for meta_line in meta_lines_end:
            meta_lines_start.append(meta_line)
        self._meta_text_lines = meta_lines_start
        self._text_lines = self._meta_text_lines
        self._text_lines.append(self._main_text_line)
        return dynamic_counter

    # return dict representation of object
    def get_as_dict(self):
        self_dict = {}
        self_dict["id"] = None
        self_dict["full_id"] = None
        self_dict["bytes"] = self._full_bytes.hex()
        self_dict["main_line"] = self._main_text_line.get_string()
        self_dict["main_line_spec_op"] = self._main_text_line.get_spec_op().hex()
        self_dict["meta_lines"] = []
        for meta_line in self._meta_text_lines:
            self_dict["meta_lines"].append(meta_line._full_bytes.hex())
        self_dict["saved_meta_lines"] = []
        for meta_line in self._saved_meta_lines:
            self_dict["saved_meta_lines"].append(meta_line._full_bytes.hex())
        return self_dict

    # recreate object from dict representation
    def add_from_dict(self, subgroup_dict):
        main_line = Text_Line(b"\x00"*16)
        main_line.set_spec_op(bytes.fromhex(subgroup_dict["main_line_spec_op"]))
        main_line.from_string_utf8(subgroup_dict["main_line"])
        self._main_text_line = main_line
        for meta_line_str in subgroup_dict["meta_lines"]:
            meta_line = Text_Line(bytes.fromhex(meta_line_str))
            self._meta_text_lines.append(meta_line)
        for meta_line_str in subgroup_dict["saved_meta_lines"]:
            meta_line = Text_Line(bytes.fromhex(meta_line_str))
            self._saved_meta_lines.append(meta_line)

    # return bytes representation after modification
    def get_new_bytes(self, pos_first_text_char, pos_first_text_line):
        return len(self._main_text_line.get_chars()).to_bytes(1, byteorder="little")+len(self._text_lines).to_bytes(1, byteorder="little")+self._full_bytes[2:4]+pos_first_text_char.to_bytes(4, byteorder="little")+pos_first_text_line.to_bytes(4, byteorder="little")

# 16 bytes  Text_Line
# 1-2       ident (type of line/operation)
# 3-6       ???
# 7         length of line/position of operation
# 8-16      ???
class Text_Line():
    def __init__(self, full_bytes):
        self._full_bytes = full_bytes
        self._ident = full_bytes[:2]
        self._num_chars = int.from_bytes(full_bytes[6:7], byteorder="little")
        self._spec_op = full_bytes[8:9]
        self._end_bytes = b""
        self._chars = []
        self._chars_utf8 = []
        self._linebreak_pos = None

    def is_meta(self):
        return self._ident != b"\x01\x00"

    def num_chars(self):
        return self._num_chars

    def add_char(self, char_int):
        self._chars.append(char_int)

    def add_char_utf8(self, char_utf8):
        self._chars_utf8.append(char_utf8)

    def insert_char_utf8(self, pos, char_utf8):
        self._chars_utf8.insert(pos, char_utf8)

    # uncounted bytes outside the specified number of chars
    def add_end_bytes(self, end_bytes):
        self._end_bytes = end_bytes

    def get_end_bytes(self):
        return self._end_bytes

    def get_chars(self):
        return self._chars

    def get_chars_utf8(self):
        return self._chars_utf8

    def get_chars_as_bytes(self):
        char_bytes = b""
        for c in self._chars:
            char_bytes += c.to_bytes(2, byteorder="little")
        return char_bytes

    def get_string(self):
        complete_string = ""
        for c in self._chars_utf8:
            complete_string += c
        return complete_string

    def get_string_length(self):
        return len(self._chars_utf8)

    def set_linebreak_pos(self, i):
        self._linebreak_pos = i

    def get_linebreak_pos(self):
        return self._linebreak_pos

    def get_spec_op(self):
        return self._spec_op

    def set_spec_op(self, spec_op):
        self._spec_op = spec_op

    def from_string_utf8(self, line_utf8):
        re_meta = re.compile(r"({[A-Z]{2}:[^{}:]+}|\|\|)")
        line_split = re_meta.split(line_utf8)
        for chunk in line_split:
            if re_meta.search(chunk):
                self._chars_utf8.append(chunk)
            else:
                for c in chunk:
                    self._chars_utf8.append(c)

    def from_string_utf8_TEST(self, line_utf8):
        re_meta = re.compile(r"({[A-Z]{2}:[^{}:]+}|\|\|)")
        line_split = re_meta.split(line_utf8)
        i = 0
        for chunk in line_split:
            if re_meta.search(chunk):
                self._chars_utf8.append(chunk)
            else:
                for c in chunk:
                    self._chars_utf8.append(c)
                    if i < 10:
                        self._chars_utf8.append(c)
                        i += 1


    # return bytes representation after modification
    def get_new_bytes(self):
        if self._full_bytes == b"\x00"*16:
            return b"\x01"+b"\x00"*5+len(self._chars).to_bytes(1, byteorder="little")+b"\x00"+self._spec_op+b"\x00"*7
        else:
            return self._full_bytes

# 48 bytes  Text_Name
# 1-        name
# -48       padding
class Text_Name(Text_Line):
    def __init__(self):
        self._chars = []
        self._chars_utf8 = []

    def is_meta(self):
        return False

    def num_chars(self):
        return 0
