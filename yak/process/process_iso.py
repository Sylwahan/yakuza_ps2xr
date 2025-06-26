import os
import pathlib
import subprocess

import pycdlib

SECTOR_SIZE = 2048
CHUNK_SIZE = 4194304


# get zero padding to sector size
def mod_sector(num):
    rem = num % SECTOR_SIZE
    if rem != 0:
        rem = SECTOR_SIZE - rem
    return rem


# list contents of ISO
def list_iso_contents(src_file, use_udf=False):
    iso = pycdlib.PyCdlib()
    iso.open(src_file)
    if use_udf:
        for dirname, dirlist, filelist in iso.walk(udf_path="/"):
            for f in filelist:
                print(f"{dirname if dirname != '/' else ''}/{f}")
    else:
        for dirname, dirlist, filelist in iso.walk(iso_path="/"):
            for f in filelist:
                print(f"{dirname if dirname != '/' else ''}/{f[:-2]}")


# extract files from ISO, either through ISO9660 or UDF
def extract_iso(src_file, trg_path, use_udf=False):
    iso = pycdlib.PyCdlib()
    iso.open(src_file)
    iso_filelist = []
    iso_dirlist = []
    if use_udf:
        for dirname, dirlist, filelist in iso.walk(udf_path="/"):
            for d in dirlist:
                iso_dirlist.append(f"{dirname if dirname != '/' else ''}/{d}")
            for f in filelist:
                iso_filelist.append(f"{dirname if dirname != '/' else ''}/{f}")
    else:
        for dirname, dirlist, filelist in iso.walk(iso_path="/"):
            for d in dirlist:
                iso_dirlist.append(f"{dirname if dirname != '/' else ''}/{d}")
            for f in filelist:
                iso_filelist.append(f"{dirname if dirname != '/' else ''}/{f}")
    for d in iso_dirlist:
        d_out_path = os.path.join(*[trg_path]+d.split("/"))
        os.makedirs(d_out_path, exist_ok=True)
    for f in iso_filelist:
        if use_udf:
            f_out_path = os.path.join(*[trg_path]+f.split("/"))
            iso.get_file_from_iso(f_out_path, udf_path=f)
        else:
            f_out_path = os.path.join(*[trg_path]+f[:-2].split("/"))
            iso.get_file_from_iso(f_out_path, iso_path=f)
    iso.close()


# rebuild using pycdlib (bad file order with 1.15.0)
def rebuild_iso_pycd_9660(file_in, dir_in, file_out, do_media=[]):
    iso = pycdlib.PyCdlib()
    iso.open(file_in)
    filter_dirs = []
    for root, dirs, files in os.walk(dir_in):
        for d in sorted(dirs):
            path_full = os.path.join(root, d)
            path_rel = os.path.relpath(path_full, dir_in)
            path_root = path_rel.split(os.path.sep)[0]
            if path_root in do_media:
                filter_dirs.append(os.path.join(root, d))
        break
    for fd in filter_dirs:
        path_rel = "/"+pathlib.Path(os.path.relpath(fd, dir_in)).as_posix()
        try:
            iso.add_directory(path_rel)
        except pycdlib.pycdlibexception.PyCdlibInvalidInput:
            pass
        for root, dirs, files in os.walk(fd):
            for d in sorted(dirs):
                path_full = os.path.join(root, d)
                path_rel = "/"+pathlib.Path(os.path.relpath(path_full, dir_in)).as_posix()
                try:
                    iso.add_directory(path_rel)
                except pycdlib.pycdlibexception.PyCdlibInvalidInput:
                    pass
            for f in sorted(files):
                path_full = os.path.join(root, f)
                path_rel = "/"+pathlib.Path(os.path.relpath(path_full, dir_in)).as_posix()+";1"
                try:
                    iso.rm_file(iso_path=path_rel)
                except pycdlib.pycdlibexception.PyCdlibInvalidInput:
                    pass
                iso.add_file(path_full, iso_path=path_rel)
    iso.write(file_out)


# build new ISO from scratch using pycd, either with ISO9660 or UDF (bad file order with 1.15.0)
def rebuild_iso_pycd(dir_in, file_out, do_media=[], use_udf=False):
    iso = pycdlib.PyCdlib()
    if not use_udf:
        iso.new(interchange_level=3)
        filter_dirs = []
        for root, dirs, files in os.walk(dir_in):
            for d in sorted(dirs):
                path_full = os.path.join(root, d)
                path_rel = os.path.relpath(path_full, dir_in)
                path_root = path_rel.split(os.path.sep)[0]
                if path_root in do_media:
                    filter_dirs.append(os.path.join(root, d))
            break
        for fd in filter_dirs:
            path_rel = "/"+pathlib.Path(os.path.relpath(fd, dir_in)).as_posix()
            iso.add_directory(path_rel)
            for root, dirs, files in os.walk(fd):
                for d in sorted(dirs):
                    path_full = os.path.join(root, d)
                    path_rel = "/"+pathlib.Path(os.path.relpath(path_full, dir_in)).as_posix()
                    iso.add_directory(path_rel)
                for f in sorted(files):
                    path_full = os.path.join(root, f)
                    path_rel = "/"+pathlib.Path(os.path.relpath(path_full, dir_in)).as_posix()
                    iso.add_file(path_full, iso_path=path_rel)
    else:
        iso.new(udf="2.60")
        for root, dirs, files in os.walk(dir_in):
            for d in sorted(dirs):
                path_full = os.path.join(root, d)
                path_rel = "/"+pathlib.Path(os.path.relpath(path_full, dir_in)).as_posix()
                iso.add_directory(path_rel.upper(), udf_path=path_rel)
            for f in sorted(files):
                path_full = os.path.join(root, f)
                path_rel = "/"+pathlib.Path(os.path.relpath(path_full, dir_in)).as_posix()
                # print(path_rel)
                iso.add_file(path_full, iso_path=path_rel.upper()+";1", udf_path=path_rel)
    iso.write(file_out)
    return True


# collect LBAs, positions and metadata of the directory records for the ISO9660 file system for simple rebuild later
def collect_lba_iso9660(file_in):
    iso = pycdlib.PyCdlib()
    iso.open(file_in)
    file_lba_list = []
    dir_rec_list = {}
    for dirname, dirlist, filelist in iso.walk(iso_path="/"):
        all_bytes = b""
        children = []
        for c in iso.list_children(iso_path=dirname):
            children.append(c)
        children = children[:2] + sorted(children[2:], key=lambda x: x.extent_location())
        for c in children:
            if c.is_file():
                path_full = dirname + "/" + c.file_ident.decode("ascii") if dirname != "/" else dirname + c.file_ident.decode("ascii")
                path_full = path_full[1:-2]
                f_ext = c.extent_location()
                f_dirrec_offset = c.parent.extent_location() * SECTOR_SIZE + len(all_bytes)
                file_lba_list.append({"LBA": f_ext, "SIZE": c.get_data_length(), "PATH": path_full, "DIRREC_OFFSET": f_dirrec_offset})
            rec = c.record()
            all_bytes += rec + (b"\x00" * (c.directory_record_length() - len(rec)))
        d_rec = iso.get_record(iso_path=dirname)
        dir_rec_list[d_rec.extent_location()] = all_bytes.hex()
    iso.close()

    file_lba_list.sort(key=lambda x: x["LBA"])
    last_pos = file_lba_list[-1]["LBA"] * SECTOR_SIZE + file_lba_list[-1]["SIZE"]
    with open(file_in, "rb") as file_in:
        iso_header = file_in.read(file_lba_list[0]["LBA"] * SECTOR_SIZE)
        file_in.seek(last_pos)
        iso_footer = file_in.read()
    return file_lba_list, dir_rec_list, iso_header, iso_footer


# collect LBAs, positions and metadata of the directory records for the UDF file system for simple rebuild later
def collect_lba_udf(file_in):
    iso = pycdlib.PyCdlib()
    iso.open(file_in)
    file_lba_udf_dict = {}
    for dirname, dirlist, filelist in iso.walk(udf_path="/"):
        for c in iso.list_children(udf_path=dirname):
            if c and c.is_file():
                path_full = dirname + "/" + c.file_identifier().decode("UTF-16 BE").upper() if dirname != "/" else dirname + c.file_identifier().decode("UTF-16 BE").upper()
                path_full = path_full[1:]
                f_ext = c.extent_location()
                lba = c.alloc_descs[0].log_block_num
                file_lba_udf_dict[path_full] = {"LBA": lba, "SIZE": c.get_data_length(), "DIRREC_OFFSET": f_ext}
    iso.close()
    return file_lba_udf_dict


# rebuild ISO using collected LBAs and metadata, only updating file sizes and positions in the directory records
def rebuild_iso_lba(path_in, path_out, iso_header, iso_footer, file_lba_list, dir_rec_list, file_lba_udf_dict={}):
    for key, val in dir_rec_list.items():
        val_bytes = bytes.fromhex(val)
        iso_header = iso_header[:int(key) * SECTOR_SIZE] + val_bytes + iso_header[int(key) * SECTOR_SIZE + len(val_bytes):]
    sector_offset = int(len(iso_header) / SECTOR_SIZE)
    if file_lba_udf_dict:
        udf_sector_init = file_lba_udf_dict[file_lba_list[0]["PATH"]]["LBA"]
        udf_sector_offset = sector_offset - udf_sector_init
    with open(path_out, "wb") as file_out:
        file_out.seek(0)
        file_out.write(iso_header)
        for f in file_lba_list:
            path_full = os.path.join(path_in, pathlib.Path(f["PATH"]))
            file_size = os.path.getsize(path_full)
            iso_header = iso_header[:f["DIRREC_OFFSET"] + 2] + sector_offset.to_bytes(4, byteorder="little") + sector_offset.to_bytes(4, byteorder="big") + file_size.to_bytes(4, byteorder="little") + file_size.to_bytes(4, byteorder="big") + iso_header[f["DIRREC_OFFSET"] + 2 + 16:]
            if file_lba_udf_dict:
                udf_pos = file_lba_udf_dict[f["PATH"]]["DIRREC_OFFSET"] * SECTOR_SIZE
                iso_header = iso_header[:udf_pos + 56] + file_size.to_bytes(4, byteorder="little") + iso_header[udf_pos + 56 + 4:udf_pos + 308] + file_size.to_bytes(4, byteorder="little") + (sector_offset - udf_sector_offset).to_bytes(4, byteorder="little") + iso_header[udf_pos + 308 + 8:]
            if not os.path.isfile(path_full):
                raise Exception(f"STEP - Rebuild main ISO\nERROR - File needed for ISO does not exist...\nPath: {path_full}")
            with open(path_full, "rb") as file_in:
                while True:
                    chunk = file_in.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    file_out.write(chunk)
            padding = mod_sector(file_size)
            file_out.write(b"\x00" * padding)
            sector_offset += int((file_size + padding) / SECTOR_SIZE)
        # fix UDF logical volume size / pos of reserve descriptor
        if file_lba_udf_dict:
            iso_header = iso_header[:69824] + (sector_offset - udf_sector_offset).to_bytes(4, byteorder="little") + iso_header[69824 + 4:]
            iso_header = iso_header[:102592] + (sector_offset - udf_sector_offset).to_bytes(4, byteorder="little") + iso_header[102592 + 4:]
            iso_header = iso_header[:131156] + (sector_offset - udf_sector_offset).to_bytes(4, byteorder="little") + iso_header[131156 + 4:]
        file_out.write(iso_footer)
        file_size = int(file_out.tell() / SECTOR_SIZE)
        # fix ISO size
        iso_header = iso_header[:32848] + file_size.to_bytes(4, byteorder="little") + file_size.to_bytes(4, byteorder="big") + iso_header[32848 + 8:]
        file_out.seek(0)
        file_out.write(iso_header)
    return True


# rebuild internal ISO using mkisofs
def rebuild_internal_iso(mkisofs_tool, path_use_file, path_sort_file, iso_root, do_media, path_file_out):
    graft_points = []
    use_files = []
    sort_files = []
    i = 0

    for media in do_media:
        graft_points.append(os.path.join(iso_root, media))

    for graft_point in graft_points:
        for root, dirs, files in os.walk(graft_point):
            dirs.sort()
            files.sort()
            if not dirs:
                path_rel = os.path.relpath(root, iso_root)
                use_files.append(f"{pathlib.Path(path_rel).as_posix()}={pathlib.Path(root).as_posix()}")
            elif files:
                for f in files:
                    path_full = os.path.join(root, f)
                    path_rel = os.path.relpath(path_full, iso_root)
                    use_files.append(f"{pathlib.Path(path_rel).as_posix()}={pathlib.Path(path_full).as_posix()}")
            for f in files:
                path_full = os.path.join(root, f)
                sort_files.append(f"{pathlib.Path(path_full).as_posix()} {i}")
                i -= 1

    with open(path_use_file, "w") as file_out:
        file_out.write("\n".join(use_files))
    with open(path_sort_file, "w") as file_out:
        file_out.write("\n".join(sort_files))

    mkisofs_args = [mkisofs_tool, "-o", path_file_out, "-sort", path_sort_file, "-iso-level", "3", "-graft-points", "-path-list", path_use_file]
    try:
        result = subprocess.run(mkisofs_args)
        if result.returncode:
            raise Exception
    except Exception:
        raise Exception("STEP - Rebuild internal ISO\nERROR - mkisofs couldn't execute properly...\nCheck mkisofs path and that it works...")
