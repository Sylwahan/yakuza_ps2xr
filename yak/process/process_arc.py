import json
import os
import re
import shutil

import yak.process.process_avlz

MAX_ARCLEVEL = 1
AVLZ_MAGIC = b"\x41\x56\x4C\x5A"
BIN_MAGIC = b"\x42\x49\x4E"
EGTS_MAGIC = b"\x45\x47\x54\x53"
GATS_MAGIC = b"\x47\x41\x54\x53"
OCB_MAGIC = b"\x4F\x43\x42"
SGT_MAGIC = b"\x53\x47\x54"
TLFD_MAGIC = b"\x54\x4C\x46\x44"
TXBP_MAGIC = b"\x54\x58\x42\x50"
TALK_DAT_HEADER = b"\x40\x00\x00\x00"
TALK_HEADER = b"\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
TALK_HEADER2 = b"\x0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
ARC_TYPES = (TLFD_MAGIC, EGTS_MAGIC)
ARC_BIN_TYPES = (TLFD_MAGIC, GATS_MAGIC)
ARC_EXTENSIONS = ("ARC", "DAT", "SHD", "DAT000")
WRITE_TYPES = (TXBP_MAGIC, SGT_MAGIC, OCB_MAGIC, AVLZ_MAGIC)
WRITE_ALL = False
TALK_HEADERS = (TALK_HEADER, TALK_HEADER2)


# pad bytes to modulo pad_mod
def pad_bytes(data_in, pad_mod, on_zero=False):
    zeroes = pad_mod - (len(data_in) % pad_mod)
    zeroes = 0 if (zeroes == pad_mod and not on_zero) else zeroes
    return data_in + b"\x00" * zeroes


# determine if file is an archive type
def is_arc(data_in, f_name):
    if data_in[4:8] in ARC_TYPES:
        return True
    if f_name.rsplit(".", 1)[-1].upper() in ARC_EXTENSIONS and len(data_in) >= 32 and data_in[1:16].rstrip(b"\x00") == b"":
        return True
    if f_name.upper().endswith("BIN") and data_in[28:32] in ARC_BIN_TYPES:
        return True
    return False


# determine if file is a TALK file
def is_talk_bin(data_in):
    if data_in[:4]+b"\x00"+data_in[5:16] in TALK_HEADERS:
        return True
    else:
        return False


# recursive function to extract data files from a scene archive file
# MAX_ARCLEVEL determines how deep the recursion should go
# WRITE_TYPES determines which files to extract separately based on magic number
# TALK files are always extracted
# returns the archive as a dict to be saved as an intermediate json for rebuilding later
def extract_arcdat(file_dict, path_rel, path_out, extract_level):
    data_in = file_dict["f_data"]
    file_dict["f_data"] = ""
    file_dict["f_path"] = path_rel
    file_dict["f_header"] = data_in[:16].hex()
    f_files = []

    tlfd_names = True if data_in[4:8] == TLFD_MAGIC else False
    num_files = int.from_bytes(data_in[:4], byteorder="little")
    index_pos = 16
    last_pos = 0
    for i in range(num_files):
        s_pos = int.from_bytes(data_in[index_pos:index_pos+4], byteorder="little")
        s_size = int.from_bytes(data_in[index_pos+4:index_pos+8], byteorder="little")
        s_id = data_in[index_pos+8:index_pos+16]
        s_name = b""
        if tlfd_names:
            if i < (num_files - 1):
                next_s_index = int.from_bytes(data_in[index_pos+16:index_pos+16+4], byteorder="little")
            else:
                next_s_index = len(data_in)
            s_name = data_in[s_pos+s_size:next_s_index].rstrip(b"\x00")
        s_data = data_in[s_pos:s_pos+s_size]
        last_pos = s_pos+s_size
        index_pos += 16
        f_files.append({"f_id": s_id, "f_name": s_name, "f_header": "", "f_data": s_data, "f_footer": "", "f_path": "", "f_avlz": False, "f_files": []})
    if not tlfd_names:
        if last_pos % 16 != 0:
            last_pos = last_pos + (16 - (last_pos % 16))
        file_dict["f_footer"] = data_in[last_pos:].hex()

    i = 0
    for s in f_files:
        s_name_str = ""
        s_name = s["f_name"].rstrip(b"\x00")
        if s_name:
            try:
                s_name_str = s_name.decode("ascii")
                s_name_str = s_name_str.rsplit("\\", 1)[-1]
            except UnicodeDecodeError:
                pass
        if s["f_data"]:
            s["f_path"] = os.path.join(path_rel, f"{i}{'___'+s_name_str if s_name_str else ''}")
            if extract_level < MAX_ARCLEVEL and is_arc(s["f_data"], s_name_str):
                s = extract_arcdat(s, os.path.join(path_rel, f"{i}{'___'+s_name_str if s_name_str else ''}"), path_out, extract_level + 1)
            else:
                dec_data = b""
                next_magic = s["f_data"][0:4].rstrip(b"\x00")
                if next_magic == AVLZ_MAGIC:
                    dec_data = yak.process.process_avlz.decode_avlz(s["f_data"])
                    next_magic = dec_data[0:4].rstrip(b"\x00")
                do_write = False
                if next_magic in WRITE_TYPES:
                    s_name_str = next_magic.decode("ascii")
                    if dec_data:
                        s_name_str = AVLZ_MAGIC.decode("ascii")
                        avlz_length = int.from_bytes(s["f_data"][8:12], byteorder="little")
                        s["f_data"] = s["f_data"][:avlz_length]
                        s["f_avlz"] = True
                    do_write = True
                elif s_name_str.upper().endswith("BIN") and is_talk_bin(s["f_data"]):
                    do_write = True
                elif WRITE_ALL:
                    do_write = True
                    try:
                        s_name_str = next_magic.decode("ascii")
                        s_name_str = re.sub(r"[^a-zA-Z0-9]", "", s_name_str) 
                    except UnicodeDecodeError:
                        s_name_str = ""
                    if not s_name_str:
                        s_name_str = "DATA"
                if do_write:
                    s["f_path"] = os.path.join(path_rel, f"{i}___{s_name_str}")
                    path_full_out = os.path.join(path_out, s["f_path"])
                    os.makedirs(os.path.dirname(path_full_out), exist_ok=True)
                    with open(path_full_out, "wb") as file_out:
                        file_out.write(s["f_data"])
                    s["f_data"] = ""
                else:
                    s["f_data"] = s["f_data"].hex()
        else:
            s["f_data"] = ""
        s["f_id"] = s["f_id"].hex()
        s["f_name"] = s["f_name"].hex()
        i += 1
    file_dict["f_files"] = f_files
    if not file_dict["f_files"] and not file_dict["f_data"]:
        file_dict["f_path"] = ""
    return file_dict


# extract the specific type of DAT that contains TALK files
def extract_talkdat(data_in, path_rel, path_out):
    num_files = int.from_bytes(data_in[20:24], byteorder="little")
    index_pos = 16
    index_headers = []
    files = []
    found_talk = False
    for i in range(num_files+1):
        file_size = int.from_bytes(data_in[index_pos:index_pos+4], byteorder="little")
        if i == 0:
            file_data = data_in[index_pos+16:file_size]
            index_headers.append(b"".hex())
            index_pos = file_size
        else:
            file_data = data_in[index_pos+16:index_pos+16+file_size]
            index_headers.append(data_in[index_pos:index_pos+16].hex())
            index_pos += file_size+16
        if is_talk_bin(file_data):
            found_talk = True
            files.append({"f_talk": True, "f_path": "", "f_data": file_data})
        else:
            files.append({"f_talk": False, "f_path": "", "f_data": file_data.hex()})
    if not found_talk:
        return False
    i = 0
    for f in files:
        if f["f_talk"]:
            path_out_full = os.path.join(path_out, path_rel, f"{i}___FILE.BIN")
            os.makedirs(os.path.dirname(path_out_full), exist_ok=True)
            with open(path_out_full, "wb") as file_out:
                file_out.write(f["f_data"])
            f["f_path"] = os.path.join(path_rel, f"{i}___FILE.BIN")
            f["f_data"] = ""
        i += 1
    dat_dict= {}
    dat_dict["header"] = data_in[:32].hex()
    dat_dict["index_headers"] = index_headers
    dat_dict["files"] = files
    return dat_dict


# entry point for checking if a file is an archive or contains a TALK file, and perform extraction if so
def extract_arcdatbin_main(path_in, path_rel, path_out):
    with open(path_in, "rb") as file_in:
        data_in = file_in.read()
    if path_in.upper().endswith("DAT") and data_in[:4] == TALK_DAT_HEADER:
        talkdat_dict = extract_talkdat(data_in, path_rel, path_out)
        if talkdat_dict:
            full_path_out = os.path.join(path_out, path_rel, f"{os.path.basename(path_in)}.json")
            os.makedirs(os.path.dirname(full_path_out), exist_ok=True)
            with open(full_path_out, "w") as file_out:
                json.dump({"type": "TALKDAT", "f_dict": talkdat_dict}, file_out, indent=4, ensure_ascii=True)
            return True
        else:
            return False
    elif is_arc(data_in, path_rel):
        arcdat_dict = extract_arcdat({"f_id": "", "f_name": "", "f_header": "", "f_data": data_in, "f_footer": "", "f_path": "", "f_avlz": False, "f_files": []}, path_rel, path_out, 0)
        full_path_out = os.path.join(path_out, path_rel, f"{os.path.basename(path_in)}.json")
        os.makedirs(os.path.dirname(full_path_out), exist_ok=True)
        with open(full_path_out, "w") as file_out:
            json.dump({"type": "ARCDAT", "f_dict": arcdat_dict}, file_out, indent=4, ensure_ascii=True)
        return True
    elif path_in.upper().endswith("BIN") and is_talk_bin(data_in):
        path_full_out = os.path.join(path_out, path_rel)
        os.makedirs(os.path.dirname(path_full_out), exist_ok=True)
        shutil.copy2(path_in, path_full_out)
        full_path_out = os.path.join(path_out, f"{path_rel}.json")
        os.makedirs(os.path.dirname(full_path_out), exist_ok=True)
        with open(full_path_out, "w") as file_out:
            json.dump({"type": "MOVE", "f_dict": [path_rel]}, file_out, indent=4, ensure_ascii=True)
        return True
    return False


# recursive function to pack data files back to archive file
def pack_arcdat(dict_in, path_bin_orig, path_bin_rebuild, path_img_rebuild, path_arc_orig, bin_path_dict, img_prop_dict, generic_path):
    num_files = len(dict_in["f_files"])
    arc_bytes = num_files.to_bytes(4, byteorder="little") + bytes.fromhex(dict_in["f_header"])[4:]
    all_index_bytes = b""
    all_file_bytes = b""
    next_index = 16 + num_files * 16
    egts = True if arc_bytes[4:8] == EGTS_MAGIC else False
    tlfd = True if arc_bytes[4:8] == TLFD_MAGIC else False
    for file_dict in dict_in["f_files"]:
        if file_dict["f_files"]:
            file_bytes = pack_arcdat(file_dict, path_bin_orig, path_bin_rebuild, path_img_rebuild, path_arc_orig, bin_path_dict, img_prop_dict, generic_path)
        else:
            if file_dict["f_path"] and not file_dict["f_data"]:
                if file_dict["f_path"] in bin_path_dict:
                    path_rel = bin_path_dict[file_dict["f_path"]]
                    path_full = os.path.join(generic_path, path_rel)
                    if not generic_path or not os.path.isfile(path_full):
                        path_full = os.path.join(path_bin_rebuild, path_rel)
                    if not os.path.isfile(path_full):
                        path_full = os.path.join(path_bin_orig, path_rel)
                elif file_dict["f_path"] in img_prop_dict:
                    path_full = os.path.join(generic_path, file_dict["f_path"])
                    if not generic_path or not os.path.isfile(path_full):
                        path_rel = img_prop_dict[file_dict["f_path"]]["path_dup"] or file_dict["f_path"]
                        path_full = os.path.join(path_img_rebuild, path_rel)
                    if not os.path.isfile(path_full):
                        path_full = os.path.join(path_arc_orig, path_rel)
                else:
                    path_rel = file_dict["f_path"]
                    path_full = os.path.join(generic_path, path_rel)
                    if not generic_path or not os.path.isfile(path_full):
                        path_full = os.path.join(path_arc_orig, path_rel)
                with open(path_full, "rb") as file_in:
                    file_bytes = file_in.read()
                if file_dict["f_avlz"]:
                    if file_bytes[:4] != AVLZ_MAGIC:
                        file_bytes = yak.process.process_avlz.encode_avlz(file_bytes)
                    if egts:
                        file_bytes = pad_bytes(file_bytes, 16)
            else:
                file_bytes = bytes.fromhex(file_dict["f_header"]) + bytes.fromhex(file_dict["f_data"])
        if tlfd and int.from_bytes(bytes.fromhex(file_dict["f_id"])[:4], byteorder="little"):
            id_bytes = (next_index + len(file_bytes)).to_bytes(4, byteorder="little") + bytes.fromhex(file_dict["f_id"])[4:]
        else:
            id_bytes = bytes.fromhex(file_dict["f_id"])
        all_index_bytes += next_index.to_bytes(4, byteorder="little") + len(file_bytes).to_bytes(4, byteorder="little") + id_bytes
        f_name = bytes.fromhex(file_dict["f_name"])
        if not tlfd:
            file_bytes = pad_bytes(file_bytes, 16)
        file_bytes += f_name
        if f_name:
            file_bytes = pad_bytes(file_bytes, 16, on_zero=True)
        else:
            file_bytes = pad_bytes(file_bytes, 16)
        next_index += len(file_bytes)
        all_file_bytes += file_bytes
    arc_bytes += all_index_bytes + all_file_bytes + bytes.fromhex(dict_in["f_footer"])
    return arc_bytes


# pack the specific type of DAT that contains TALK files
def pack_talkdat(dat_dict, path_bin_orig, path_bin_rebuild, bin_path_dict):
    dat_data = bytes.fromhex(dat_dict["header"])
    index_headers = dat_dict["index_headers"]
    i = 0
    for f in dat_dict["files"]:
        f_header = bytes.fromhex(index_headers[i])
        if f["f_path"]:
            path_rel = bin_path_dict[f["f_path"]]
            path_full = os.path.join(path_bin_rebuild, path_rel)
            if not os.path.isfile(path_full):
                path_full = os.path.join(path_bin_orig, path_rel)
            with open(path_full, "rb") as file_in:
                f_data = file_in.read()
            f_header = len(f_data).to_bytes(4, byteorder="little") + f_header[4:]
        else:
            f_data = bytes.fromhex(f["f_data"])
        dat_data = dat_data + f_header + f_data
        i += 1
    return dat_data


# entry point for rebuilding/moving arc/dat/bin file
def rebuild_arcdatbin_main(arcdat_dict, path_out, path_bin_orig, path_bin_rebuild, path_img_rebuild, path_arc_orig, bin_path_dict, img_prop_dict, generic_path):
    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    if arcdat_dict["type"] == "MOVE":
        for f in arcdat_dict["f_dict"]:
            path_rep_full = os.path.join(path_bin_rebuild, bin_path_dict[f])
            if not os.path.isfile(path_rep_full):
                path_rep_full = os.path.join(path_bin_orig, bin_path_dict[f])
            shutil.copy2(path_rep_full, path_out)
    elif arcdat_dict["type"] == "TALKDAT":
        talkdat_bytes = pack_talkdat(arcdat_dict["f_dict"], path_bin_orig, path_bin_rebuild, bin_path_dict)
        with open(path_out, "wb") as file_out:
            file_out.write(talkdat_bytes)
    elif arcdat_dict["type"] == "ARCDAT":
        arc_bytes = pack_arcdat(arcdat_dict["f_dict"], path_bin_orig, path_bin_rebuild, path_img_rebuild, path_arc_orig, bin_path_dict, img_prop_dict, generic_path)
        with open(path_out, "wb") as file_out:
            file_out.write(arc_bytes)
