import copy
import os
import struct

import yak.meta.voice_patch_jp


class CutsceneEntry:
    def __init__(self, in_data):
        self._in_data = in_data
        self._is_voice = True if in_data[92:96] == b"\x15\x00\x00\x00" else False
        self._is_sub = True if (in_data[92:96] == b"\x00\x00\x00\x00" and in_data[108:112] == b"\x45\x00\x00\x00") else False
        self._index_pos = 0
        self._start_time = in_data[52:56]
        self._end_time = in_data[56:60]
        self._voice_file = int.from_bytes(in_data[140:144], byteorder="little")
        self._sub_line = int.from_bytes(in_data[124:128], byteorder="little")
        self._sub_lang = int.from_bytes(in_data[140:144], byteorder="little")
    
    def get_bytes(self):
        if self._is_voice:
            entry_data = self._in_data[:52] + self._start_time + self._end_time + self._in_data[60:140] + self._voice_file.to_bytes(4, byteorder="little")
        elif self._is_sub:
            entry_data = self._in_data[:52] + self._start_time + self._end_time + self._in_data[60:124] + self._sub_line.to_bytes(4, byteorder="little") + self._in_data[128:140] + self._sub_lang.to_bytes(4, byteorder="little")
        else:
            entry_data = self._in_data[:52] + self._start_time + self._end_time + self._in_data[60:]
        return entry_data

    @property
    def start_time(self):
        return self._start_time
    @start_time.setter
    def start_time(self, value):
        self._start_time = value

    @property
    def end_time(self):
        return self._end_time
    @end_time.setter
    def end_time(self, value):
        self._end_time = value

    @property
    def voice_file(self):
        return self._voice_file
    @voice_file.setter
    def voice_file(self, value):
        self._voice_file = value

    @property
    def sub_line(self):
        return self._sub_line
    @sub_line.setter
    def sub_line(self, value):
        self._sub_line = value

    @property
    def sub_lang(self):
        return self._sub_lang
    @sub_lang.setter
    def sub_lang(self, value):
        self._sub_lang = value

    @property
    def is_voice(self):
        return self._is_voice

    @property
    def is_sub(self):
        return self._is_sub


class CutsceneFile:
    def __init__(self, in_data, num_entry, num_splits):
        self.entry_data = in_data[:num_entry * 144]
        self.index_data = in_data[num_entry * 144:]
        self.old_length = len(in_data)
        self._num_entry = num_entry
        self._num_splits = num_splits
        self.entries = []
        self.index_splits = []
        for i in range(num_splits):
            self.index_splits.append([])
        self.fetch_entries()
        self.fetch_index_entries()
    
    @property
    def num_entry(self):
        return len(self.entries)

    @property
    def num_splits(self):
        res_num_splits = []
        for i_split in self.index_splits:
            res_num_splits.append(len(i_split))
        return res_num_splits
    
    def fetch_entries(self):
        for i in range(self._num_entry):
            entry = CutsceneEntry(self.entry_data[(i * 144):(i * 144) + 144])
            self.entries.append(entry)
    
    def fetch_index_entries(self):
        split_num = 0
        for i in range(int(len(self.index_data) / 16)):
            entry_index_data = self.index_data[i * 16:(i * 16) + 16]
            if entry_index_data == b"\x01" + b"\x00" * 15:
                split_num += 1
            else:
                entry_index_num = int.from_bytes(entry_index_data[12:], byteorder="little")
                self.index_splits[split_num].append({"start": entry_index_data[4:8], "end": entry_index_data[8:12], "entry": self.entries[entry_index_num]})
                if self.entries[entry_index_num].is_voice and (entry_index_data[4:8] != self.entries[entry_index_num].start_time or entry_index_data[8:12] != self.entries[entry_index_num].end_time):
                    print(f"MISMATCH: {entry_index_num}")
    
    def remove_entry_by_entry(self, rem_entry):
        for i_split in self.index_splits:
            rem_i_entries = []
            i = 0
            for i_entry in i_split:
                if i_entry["entry"] == rem_entry:
                    rem_i_entries.append(i)
                i += 1
            for rem_i_entry in sorted(rem_i_entries, reverse=True):
                i_split.pop(rem_i_entry)
        self.entries.remove(rem_entry)

    def remove_entry_by_index(self, i_rem):
        rem_entry = self.entries[i_rem]
        self.remove_entry_by_entry(rem_entry)
    
    def remove_entries(self, i_rems):
        for i_rem in sorted(i_rems, reverse=True):
            self.remove_entry_by_index(i_rem)
    
    def add_entry(self, i_add, new_entry, new_index_splits):
        old_entry, old_index_splits = self.get_entry(i_add)
        for i_entry in new_index_splits:
            i_split = i_entry["i_split"]
            i_pos = i_entry["i_pos"]
            for old_i_entry in old_index_splits:
                if old_i_entry["i_split"] == i_split:
                    i_pos = old_i_entry["i_pos"]
                    break
            self.index_splits[i_split].insert(i_pos, {"start": i_entry["start"], "end": i_entry["end"], "entry": new_entry})
        self.entries.insert(i_add, new_entry)
    
    def get_entry_bytes(self):
        entry_bytes = b""
        for entry in self.entries:
            entry_bytes += entry.get_bytes()
        return entry_bytes
    
    def get_entry_index_bytes(self):
        entry_index_bytes = b""
        for i_split in self.index_splits:
            for i_entry in i_split:
                entry_index_bytes += b"\x00" * 4 + i_entry["start"] + i_entry["end"] + self.entries.index(i_entry["entry"]).to_bytes(4, byteorder="little")
            entry_index_bytes += b"\x01" + b"\x00" * 15
        return entry_index_bytes
    
    def get_complete_bytes(self):
        return self.get_entry_bytes() + self.get_entry_index_bytes()
    
    def get_entry(self, i):
        entry = self.entries[i]
        index_splits = []
        i_sp = 0
        for i_split in self.index_splits:
            i_sp_e = 0
            for i_entry in i_split:
                if i_entry["entry"] == entry:
                    index_splits.append({"i_split": i_sp, "i_pos": i_sp_e, "start": i_entry["start"], "end": i_entry["end"]})
                i_sp_e += 1
            i_sp += 1
        return entry, index_splits

    def get_voice_entries(self):
        voice_entries = []
        i = 0
        for entry in self.entries:
            if entry.is_voice:
                index = self.entries.index(entry)
                entry, index_splits = self.get_entry(index)
                voice_entries.append({"entry_index": i, "entry": entry, "index_splits": index_splits})
            i += 1
        return voice_entries

    def get_sub_entries(self, jp_only=False):
        sub_entries = []
        i = 0
        for entry in self.entries:
            if entry.is_sub:
                if jp_only and entry.sub_lang != 0:
                    continue
                index = self.entries.index(entry)
                entry, index_splits = self.get_entry(index)
                sub_entries.append({"entry_index": i, "entry": entry, "index_splits": index_splits})
            i += 1
        return sub_entries

    def print_entry(self, i):
        print(self.entries[i].get_bytes().hex())
        print(f"POS: {self.entries[i].index_entries[0]["pos"]}, START: {self.entries[i].index_entries[0]["start"].hex()}, END: {self.entries[i].index_entries[0]["end"].hex()}")


def switch_voice(path_patch, path_orig, path_rel, path_base_in, path_base_out, do_sub_switch):
    file_name = os.path.basename(path_rel)
    do_audio_switch = False
    cutscene_old_sub_entry = []
    cutscene_src_voice_entry = []
    start_add_sub = 0
    start_add_voice = 0
    if os.path.isfile(path_patch):
        do_audio_switch = True
        with open(path_patch, "rb") as file_in:
            data_in = file_in.read()

        # apply voice hiccup patches before switching out voices
        try:
            for patch_pos, patch_bytes in yak.meta.voice_patch_jp.VOICE_JP_B00_PATCH[file_name]:
                data_in = data_in[:patch_pos] + bytes.fromhex(patch_bytes.replace(" ", "")) + data_in[patch_pos + 4:]
        except KeyError:
            pass

        # collect voice entries from JP
        cutscene_src_num_split = int.from_bytes(data_in[4:8], byteorder="little")
        cutscene_src_start = int.from_bytes(data_in[16:20], byteorder="little")
        cutscene_src_num_entry = int.from_bytes(data_in[20:24], byteorder="little")
        cutscene_src_end = int.from_bytes(data_in[24:28], byteorder="little")
        cutscene_src = CutsceneFile(data_in[cutscene_src_start:cutscene_src_end], cutscene_src_num_entry, cutscene_src_num_split)
        cutscene_src_voice_entry = cutscene_src.get_voice_entries()
        cutscene_src_voice_entry.reverse()

    # initialize original scenefile
    with open(path_orig, "rb") as file_in:
        data_in = file_in.read()
    cutscene_old_num_split = int.from_bytes(data_in[4:8], byteorder="little")
    cutscene_old_start = int.from_bytes(data_in[16:20], byteorder="little")
    cutscene_old_num_entry = int.from_bytes(data_in[20:24], byteorder="little")
    cutscene_old_end = int.from_bytes(data_in[24:28], byteorder="little")
    cutscene_old = CutsceneFile(data_in[cutscene_old_start:cutscene_old_end], cutscene_old_num_entry, cutscene_old_num_split)

    # collect subtitle entries from JP
    if do_sub_switch:
        cutscene_old_sub_entry = cutscene_old.get_sub_entries()
        if cutscene_old_sub_entry:
            start_add_sub = cutscene_old_sub_entry[0]["entry_index"]

    # collect voice entries from US/EUR
    if do_audio_switch:
        cutscene_old_voice_entry = cutscene_old.get_voice_entries()
        if cutscene_old_voice_entry:
            start_add_voice = cutscene_old_voice_entry[0]["entry_index"]

    # change to correct voice file index, remove old entry, add new
    if do_audio_switch and cutscene_src_voice_entry:
        for entry_dict in cutscene_src_voice_entry:
            entry_dict["entry"].voice_file = yak.meta.voice_patch_jp.VOICE_JP_INDEX[entry_dict["entry"].voice_file]["index_new"]
            cutscene_old.add_entry(start_add_voice, entry_dict["entry"], entry_dict["index_splits"])
        for entry_dict in cutscene_old_voice_entry:
            cutscene_old.remove_entry_by_entry(entry_dict["entry"])

    # get old JP sub entries, change to correct lang, add new entry, remove old entry
    if do_sub_switch and cutscene_old_sub_entry:
        exist_langs = []
        jp_entries = []
        for entry_dict in cutscene_old_sub_entry:
            if entry_dict["entry"].sub_lang == 0:
                jp_entries.append(entry_dict)
            if entry_dict["entry"].sub_lang not in exist_langs:
                exist_langs.append(entry_dict["entry"].sub_lang)
        # hacks to fix missing/incorrect entries compared to scenes from JP files
        if path_rel.endswith("AUTH_CHAPTER01_007.B00"):
            new_jp_entry = copy.deepcopy(jp_entries[0])
            new_jp_entry["entry"].start_time = b"\x00\x00\xA8\x41"
            new_jp_entry["entry"].end_time = b"\x00\x00\x01\x43"
            new_jp_entry["index_splits"][0]["start"] = new_jp_entry["entry"].start_time
            new_jp_entry["index_splits"][0]["end"] = new_jp_entry["entry"].end_time
            for entry_dict in jp_entries:
                entry_dict["entry_index"] = entry_dict["entry_index"] + 1
                entry_dict["entry"].sub_line = entry_dict["entry"].sub_line + 1
                entry_dict["index_splits"][0]["i_pos"] = entry_dict["index_splits"][0]["i_pos"] + 1
            jp_entries.insert(0, new_jp_entry)
        elif path_rel.endswith("AUTH_CHAPTER10_008.B00"):
            jp_entries[1]["entry"].start_time = b"\x00\x00\xFF\x43"
            jp_entries[1]["index_splits"][0]["start"] = jp_entries[1]["entry"].start_time
        elif path_rel.endswith("AUTH_SUB2_S02_BAR_I.B00"):
            jp_entries[3]["entry"].start_time = b"\x00\x00\x8E\x43"
            jp_entries[3]["entry"].end_time = b"\x00\x80\xAA\x43"
            jp_entries[3]["index_splits"][0]["start"] = jp_entries[3]["entry"].start_time
            jp_entries[3]["index_splits"][0]["end"] = jp_entries[3]["entry"].end_time
            jp_entries[4]["entry"].start_time = b"\x00\x80\xAA\x43"
            jp_entries[4]["entry"].end_time = b"\x00\x00\xE6\x43"
            jp_entries[4]["index_splits"][0]["start"] = jp_entries[4]["entry"].start_time
            jp_entries[4]["index_splits"][0]["end"] = jp_entries[4]["entry"].end_time
        jp_entries.reverse()
        exist_langs.reverse()
        for lang in exist_langs:
            for entry_dict in jp_entries:
                entry_dict_copy = copy.deepcopy(entry_dict)
                entry_dict_copy["entry"].sub_lang = lang
                cutscene_old.add_entry(start_add_sub, entry_dict_copy["entry"], entry_dict_copy["index_splits"])
        for entry_dict in cutscene_old_sub_entry:
            cutscene_old.remove_entry_by_entry(entry_dict["entry"])

    if not (cutscene_src_voice_entry or cutscene_old_sub_entry):
        return

    # read in modified scene, propagate to all copies
    cutscene_new_data = cutscene_old.get_complete_bytes()
    cutscene_new_num_entry = cutscene_old.num_entry
    cutscene_new_num_split = cutscene_old.num_splits
    offset_len = len(cutscene_new_data) - (cutscene_old_end - cutscene_old_start)
    offset_num = cutscene_new_num_entry - cutscene_old_num_entry
    b_num = 0
    path_b = os.path.join(path_base_in, path_rel)
    while os.path.isfile(path_b):
        with open(path_b, "rb") as file_in:
            data_in = file_in.read()
        cutscene_mod_start = int.from_bytes(data_in[16:20], byteorder="little")
        cutscene_mod_num_entry = int.from_bytes(data_in[20:24], byteorder="little")
        cutscene_mod_end = int.from_bytes(data_in[24:28], byteorder="little")
        data_in = data_in[:20] + cutscene_new_num_entry.to_bytes(4, byteorder="little") + data_in[24:]

        # add
        index_pos = cutscene_mod_start + (cutscene_new_num_entry * 144)
        for i in range(len(cutscene_new_num_split)):
            data_in = data_in[:128 + (i * 32) + 20] + index_pos.to_bytes(4, byteorder="little") + data_in[128 + (i * 32) + 20 + 4:]
            index_pos += (cutscene_new_num_split[i] + 1) * 16

        # add offset to first index bytes
        offset_bytes = [24, 32, 40, 48]
        for offset_change in offset_bytes:
            new_bytes = (int.from_bytes(data_in[offset_change:offset_change + 4], byteorder="little") + offset_len).to_bytes(4, byteorder="little")
            data_in = data_in[:offset_change] + new_bytes + data_in[offset_change + 4:]

        # find which index section to change
        offset_start = 128 + (len(cutscene_new_num_split) * 32)
        index_max_num = 0
        index_max_pos = 0
        offset_bytes = []
        num_offsets = int((cutscene_mod_start - offset_start) / 64)
        for i in range(num_offsets):
            offset_index_pos = offset_start + (i * 64) + 16
            offset_index_num = int.from_bytes(data_in[offset_index_pos + 4:offset_index_pos + 8], byteorder="little")
            if offset_index_num > index_max_num:
                index_max_num = offset_index_num
                index_max_pos = offset_index_pos + 4
            offset_bytes.append(offset_start + (i * 64) + 16)
        
        # add num entry change to correct offset pos
        data_in = data_in[:index_max_pos] + (index_max_num + offset_num).to_bytes(4, byteorder="little") + data_in[index_max_pos + 4:]

        # add offsets to all correct index pos
        prev_entry_num = 0
        prev_entry_pos = int.from_bytes(data_in[offset_bytes[0]:offset_bytes[0] + 4], byteorder="little") + offset_len
        for offset_change in offset_bytes:
            try:
                prev_entry_pos = prev_entry_pos + prev_entry_num * 4
                new_bytes = prev_entry_pos.to_bytes(4, byteorder="little")
            except OverflowError:
                new_bytes = b"\x00" * 4
            data_in = data_in[:offset_change] + new_bytes + data_in[offset_change + 4:]
            prev_entry_num = int.from_bytes(data_in[offset_change + 4:offset_change + 8], byteorder="little")
        
        # combine rest of the data
        data_in = data_in[:cutscene_mod_start] + cutscene_new_data + data_in[cutscene_mod_end:]
        data_in = data_in[:-(cutscene_mod_num_entry * 4)]
        new_index = b""
        for i in range(cutscene_new_num_entry):
            new_index += i.to_bytes(4, byteorder="little")
        data_in += new_index
        path_out = os.path.join(path_base_out, f"{path_rel[:-2]}{b_num:02}")
        os.makedirs(os.path.dirname(path_out), exist_ok=True)
        with open(path_out, "wb") as file_out:
            file_out.write(data_in)
        b_num += 1
        path_b = os.path.join(path_base_in, f"{path_rel[:-2]}{b_num:02}")
