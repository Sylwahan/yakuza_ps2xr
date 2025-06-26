import os
import pathlib

import yak.process.process_avlz


def mod64(num):
    rem = num % 64
    if rem != 0:
        rem = 64 - rem
    return rem


# pad number to sector size
def pad_to_sector(num):
    whole, remain = divmod(num, 2048)
    return whole + 1 * min(1, remain)


# collect unknown bytes/metadata for recreating the ogredir later
def collect_init_bytes(data_in):
    out_dict = {}
    out_dict["OGRE_HEADER"] = data_in[:4].hex()
    out_dict["UNKNOWN_A"] = data_in[4:6].hex()
    out_dict["UNKNOWN_B"] = data_in[68:72].hex()
    out_dict["MYSTERY_BYTES"] = {}
    init_seek = False
    start_avlz = int.from_bytes(data_in[188:188 + 4], byteorder="little")
    data_in = data_in[start_avlz:]
    while len(data_in) >= 4:
        if data_in[:4] == b"\x41\x56\x4C\x5A":
            avlz_size = int.from_bytes(data_in[8:12], byteorder="little")
            avlz = data_in[:avlz_size]
            dirlst = yak.process.process_avlz.decode_avlz(avlz)
            if not init_seek:
                out_dict["INIT_SEEK"] = int.from_bytes(dirlst[8:12], byteorder="little")
                init_seek = True
            num_files = int.from_bytes(dirlst[:2], byteorder="little") - 2
            dirlst = dirlst[120:]
            for i in range(num_files):
                mystery_byte = dirlst[13:14]
                name = dirlst[14:48].split(b"\x00", 1)[0].decode("ascii")
                out_dict["MYSTERY_BYTES"][name] = mystery_byte.hex()
                dirlst = dirlst[48:]
            data_in = data_in[avlz_size + mod64(avlz_size):]
        else:
            data_in = data_in[4:]
    return out_dict


class Ogre_Rebuilder():
    def __init__(self, do_media, path_in, init_dict, ogredir_start):
        self.do_media = do_media
        self.path_in = path_in
        self.init_dict = init_dict
        self.ogredir_start = ogredir_start
        self.dirlst_list = []
        self.DIR_NUM = 0
        # unknown/mystery/header bytes
        # init_seek: bytes 8-12 of the first avlz-decoded DirLst in the (OGRE)DIR.bin (on the ISO, the LBA of the root directory)
        # ogre_header: bytes 0-4 of the original (OGRE)DIR.bin #ROFS timestamp
        # unknown_a: bytes 4-6 of the original (OGRE)DIR.bin #ROFS timestamp
        # unknown_b: bytes 68-72 of the original (OGRE)DIR.bin
        # mystery_dict: byte 14 of each file/folder entry in DirLst

    # create index
    def fileindex(self, filename_b, size, file_pos, isdir, mystery_dict=False):
        indexbytes = size.to_bytes(4, byteorder="little")
        indexbytes += b"\x00" * 4
        indexbytes += file_pos.to_bytes(4, byteorder="little")
        if isdir:
            indexbytes += b"\x02"
        else:
            indexbytes += b"\x00"
        if mystery_dict:
            filename_str = filename_b.decode("ascii")
            # HARDCODED FIX?
            if filename_str == "A":
                filename_str = "A."
            try:
                indexbytes += bytes.fromhex(self.init_dict["MYSTERY_BYTES"][filename_str])
            except KeyError:
                indexbytes += b"\x36"
        else:
            indexbytes += b"\x36"
        indexbytes += filename_b
        indexbytes += b"\x00" * (34 - len(filename_b))
        return indexbytes


    # collects the size of file/folder index entries in an ISO file
    def get_dir_size(self, dir_path, root_dir=False):
        for root, dirs, files in os.walk(dir_path):
            break
        dirs.sort()
        files.sort()
        dir_size = 68
        i = 1
        if root_dir:
            new_d = []
            for d in dirs:
                if d in self.do_media:
                    new_d.append(d)
            dirs = new_d
        for d in dirs:
            dir_len = 33 + len(d)
            dir_len += dir_len % 2
            if (dir_size + dir_len) >= (2048 * i):
                dir_size += 2048 * i - dir_size
                i += 1
            dir_size += dir_len
        for f in files:
            if "." not in f:
                f += "."
            file_len = 33 + len(f) + 2
            file_len += file_len % 2
            if (dir_size + file_len) >= (2048 * i):
                dir_size += 2048 * i - dir_size
                i += 1
            dir_size += file_len
            
        return pad_to_sector(dir_size)


    # recursive collection of dirs
    def rec_dirlst_dir(self, curr_path, next_file_pos, prev_dir_pos, prev_dir_size, root_dir=False):
        curr_dir_num = self.DIR_NUM
        self.DIR_NUM += 1
        for root, dirs, files in os.walk(curr_path):
            break
        dirs.sort()
        files.sort()
        if root_dir:
            new_d = []
            for d in dirs:
                if d in self.do_media:
                    new_d.append(d)
            dirs = new_d
        dirlst_bytes = b""
        curr_dir_pos = next_file_pos
        curr_dir_size = self.get_dir_size(curr_path, root_dir=root_dir)
        dircontent = (len(files) + len(dirs) + 2).to_bytes(4, byteorder="little")
        path_for_ogre = pathlib.Path(os.path.relpath(curr_path, self.path_in)).as_posix()
        if len(path_for_ogre) == 1:
            path_for_ogre = "/"
        else:
            path_for_ogre = "/"+path_for_ogre+"/"
        self.dirlst_list.append({"dirlst_bytes": b"", "path_for_ogre": path_for_ogre, "dircontent": dircontent, "file_pos": 0})
        dirlst_bytes += dircontent
        dirlst_bytes += dircontent
        dirlst_bytes += next_file_pos.to_bytes(4, byteorder="little")
        dirlst_bytes += b"\x23\x44\x69\x72\x4C\x73\x74\x23"
        dirlst_bytes += b"\x00" * 4

        dirlst_bytes += self.fileindex(b"\x2E\x00", curr_dir_size * 2048, curr_dir_pos, True)
        dirlst_bytes += self.fileindex(b"\x2E\x2E", prev_dir_size * 2048, prev_dir_pos, True)
        
        next_file_pos += curr_dir_size
        for d in dirs:
            dirpath = os.path.join(root, d)
            dirsize = self.get_dir_size(dirpath)
            dirlst_bytes += self.fileindex(d.encode("ascii"), dirsize * 2048, next_file_pos, True, mystery_dict=True)
            next_file_pos = self.rec_dirlst_dir(dirpath, next_file_pos, curr_dir_pos, curr_dir_size)
        self.dirlst_list[curr_dir_num]["dirlst_bytes"] = dirlst_bytes
        return next_file_pos


    # recursive collection of files
    def rec_dirlst_file(self, curr_path, next_file_pos, root_dir=False):
        curr_dir_num = self.DIR_NUM
        self.DIR_NUM += 1
        for root, dirs, files in os.walk(curr_path):
            break
        dirs.sort()
        files.sort()
        if root_dir:
            new_d = []
            for d in dirs:
                if d in self.do_media:
                    new_d.append(d)
            dirs = new_d
        for f in files:
            f_size = os.stat(os.path.join(root, f)).st_size
            if "." not in f:
                f += "."
            self.dirlst_list[curr_dir_num]["dirlst_bytes"] += self.fileindex(f.encode("ascii"), f_size, next_file_pos, False, mystery_dict=True)
            next_file_pos += pad_to_sector(f_size)
        for d in dirs:
            next_file_pos = self.rec_dirlst_file(os.path.join(root, d), next_file_pos)
        
        self.dirlst_list[curr_dir_num]["dirlst_bytes"] += "GN".encode("ascii")
        self.dirlst_list[curr_dir_num]["dirlst_bytes"] += b"\x00" * mod64(len(self.dirlst_list[curr_dir_num]["dirlst_bytes"]))
        return next_file_pos


    # sort the entries by path
    def sort_dirlst(self, dirlst_bytes):
        entry_list = []
        num_entry = int.from_bytes(dirlst_bytes[:4], byteorder="little") - 2
        header = dirlst_bytes[:120]
        i = 0
        while i < num_entry:
            entry_start = 120 + i * 48
            entry_name_start = 120 + i * 48 + 14
            entry_name = dirlst_bytes[entry_name_start:entry_name_start + 34].decode().rstrip("\x00")
            entry_data = dirlst_bytes[entry_start:entry_start + 48]
            entry_list.append([entry_name, entry_data])
            i += 1
        tail = dirlst_bytes[120 + num_entry * 48:]
        entry_list.sort(key=lambda e_name: e_name[0])
        dirlst_bytes_sorted = header
        for entry in entry_list:
            dirlst_bytes_sorted += entry[1]
        dirlst_bytes_sorted += tail
        return dirlst_bytes_sorted


    # do rebuild of ogredir
    def build_ogredir(self):
        curr_dir_pos = self.ogredir_start # self.init_dict["INIT_SEEK"] 
        if not curr_dir_pos:
            raise Exception("STEP - Rebuild OGREDIR\nERROR - Couldn't get initial seek position...")
        curr_dir_size = self.get_dir_size(self.path_in, root_dir=True)
        next_file_pos = curr_dir_pos
        prev_dir_pos = curr_dir_pos
        prev_dir_size = curr_dir_size

        next_file_pos = self.rec_dirlst_dir(self.path_in, next_file_pos, prev_dir_pos, prev_dir_size, root_dir=True)
        self.DIR_NUM = 0
        next_file_pos = self.rec_dirlst_file(self.path_in, next_file_pos, root_dir=True)

        dir_done = 0
        ogre_avlz_bytes = b""
        for dirlst in self.dirlst_list:
            dirlst["file_pos"] = len(ogre_avlz_bytes)
            avlz_bytes = yak.process.process_avlz.encode_avlz(self.sort_dirlst(dirlst["dirlst_bytes"]))
            avlz_bytes += b"\x00" * 61
            avlz_bytes += b"\x00" * mod64(len(avlz_bytes))
            ogre_avlz_bytes += avlz_bytes
            dir_done += 1
            if dir_done % 50 == 0:
                print(f"Processed directory listings: {dir_done}...")

        ogre_bytes = b""
        header_size = 128 + self.DIR_NUM * 64
        ogre_bytes = bytes.fromhex(self.init_dict["OGRE_HEADER"])
        ogre_bytes += bytes.fromhex(self.init_dict["UNKNOWN_A"])
        ogre_bytes += b"\x24\x00"
        ogre_bytes += b"\x00" * 56
        ogre_bytes += self.DIR_NUM.to_bytes(4, byteorder="little")
        ogre_bytes += bytes.fromhex(self.init_dict["UNKNOWN_B"])
        ogre_bytes += b"\x00" * 56
        for dirlst in self.dirlst_list:
            ogre_bytes += dirlst["path_for_ogre"].encode("ascii")
            ogre_bytes += b"\x00" * (56 - len(dirlst["path_for_ogre"]))
            ogre_bytes += dirlst["dircontent"]
            ogre_bytes += (dirlst["file_pos"] + header_size).to_bytes(4, byteorder="little")
        ogre_bytes += ogre_avlz_bytes
        ogre_bytes += b"\x2D\x31"
        return ogre_bytes
