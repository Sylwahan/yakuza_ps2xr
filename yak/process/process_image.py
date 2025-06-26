import hashlib
import os
import shutil
import subprocess

import png

import yak.meta.global_def
import yak.process.process_arc
import yak.process.process_avlz

IMAGE_TYPE_4B_PAL = 20 # 4 bits per pixel, max 64 bytes palette (16 colors)
IMAGE_TYPE_8B_PAL = 21 # 8 bits per pixel, max 1024 bytes palette (256 colors)
IMAGE_TYPE_8B_GSA = 26 # 8 bits per pixel grayscale + alpha, no palette
IMAGE_TYPE_8B_RGBA = 29 # 8 bits per pixel RGB + alpha, no palette

# reorder palette between txbp <-> png order
# option to replace pngquant default transparency
def reorder_txbp_png_palette(palette_bytes, replace_transparency=None):
    swap_palette_bytes = b""
    if len(palette_bytes) == 1024:
        weave = [0, 2, 1, 3, 4, 6, 5, 7, 8, 10, 9, 11, 12, 14, 13, 15, 16, 18, 17, 19, 20, 22, 21, 23, 24, 26, 25, 27, 28, 30, 29, 31]
    else:
        weave = [0, 1]
    for j in weave:
        pos = 32 * j
        for i in range(8):
            palette_tuple_bytes = palette_bytes[pos:pos+4]
            if replace_transparency is not None and palette_tuple_bytes == b"\x4C\x70\x47\x00":
                palette_tuple_bytes = replace_transparency
            swap_palette_bytes += palette_tuple_bytes
            pos += 4
    return swap_palette_bytes


# convert palette bytes to int tuple list for pypng
def palette_bytes_to_list(palette_bytes):
    palette_list = []
    for i in range(0, len(palette_bytes), 4):
        palette_list.append((int.from_bytes(palette_bytes[i:i + 1]), int.from_bytes(palette_bytes[i + 1:i + 2]), int.from_bytes(palette_bytes[i + 2:i + 3]), int.from_bytes(palette_bytes[i + 3:i + 4])))
    return palette_list


# convert int tuple list from pypng to palette bytes
def palette_list_to_bytes(palette_list):
    palette_bytes = b""
    for x in palette_list:
        palette_bytes += x[0].to_bytes() + x[1].to_bytes() + x[2].to_bytes() + x[3].to_bytes()
    return palette_bytes


# convert pixel bytes to int list for pypng
# split up bytes for 4-bit images
def pixel_bytes_to_list(pixel_bytes, image_type):
    pixel_list = []
    if image_type == IMAGE_TYPE_4B_PAL:
        for i in pixel_bytes:
            high, low = i >> 4, i & 0x0F
            pixel_list.append(low)
            pixel_list.append(high)
    elif image_type == IMAGE_TYPE_8B_PAL:
        for i in pixel_bytes:
            pixel_list.append(i)
    elif image_type == IMAGE_TYPE_8B_GSA:
        pix_tup = []
        for i in pixel_bytes:
            pix_tup.append(i)
            if len(pix_tup) == 2:
                pixel_list.append(pix_tup[1])
                pixel_list.append(pix_tup[0])
                pix_tup = []
    elif image_type == IMAGE_TYPE_8B_RGBA:
        for i in pixel_bytes:
            pixel_list.append(i)
    return pixel_list


# convert int list from pypng to pixel bytes
# combine bytes for 4-bit images
def pixel_list_to_bytes(pixel_list, image_type):
    pixel_bytes = b""
    if image_type == IMAGE_TYPE_4B_PAL:
        ip = 0
        while ip < len(pixel_list):
            pixel_bytes += ((pixel_list[ip + 1] << 4) + pixel_list[ip]).to_bytes(1, byteorder="little")
            ip += 2
    elif image_type == IMAGE_TYPE_8B_GSA:
        pix_tup = []
        for i in pixel_list:
            pix_tup.append(i)
            if len(pix_tup) == 2:
                pixel_bytes += pix_tup[1].to_bytes(1, byteorder="little")
                pixel_bytes += pix_tup[0].to_bytes(1, byteorder="little")
                pix_tup = []
    else:
        for i in pixel_list:
            pixel_bytes += i.to_bytes(1, byteorder="little")
    return pixel_bytes


# convert txbp pixel bytes to int list for pypng
def txbp_to_png(data_in):
    header_bytes, pic_bytes = data_in[:32], data_in[32:]
    num_subpics = int.from_bytes(header_bytes[4:8], byteorder="little")
    size_subpics = int.from_bytes(header_bytes[8:12], byteorder="little")
    subpics = []
    subpic_pos = 0
    for i in range(num_subpics):
        subpic_size = int.from_bytes(pic_bytes[subpic_pos:subpic_pos+4], byteorder="little")
        subpic_bytes = pic_bytes[subpic_pos:subpic_pos+32+subpic_size]
        resx = int.from_bytes(subpic_bytes[4:8], byteorder="little")
        resy = int.from_bytes(subpic_bytes[8:12], byteorder="little")
        image_type = int.from_bytes(subpic_bytes[12:16], byteorder="little")
        subpic_header_bytes = subpic_bytes[16:32]
        if image_type == IMAGE_TYPE_4B_PAL:
            palette_size = int(subpic_size - (resx * resy) / 2)
            # repair broken texture header and remove garbage data
            if palette_size not in (64, 32):
                palette_size = 64
                resy = resx
                subpic_bytes = subpic_bytes[:int((resx * resy) / 2) + palette_size + 32]
            bitdepth = 4
            planes = 1
        elif image_type == IMAGE_TYPE_8B_PAL:
            # repair broken texture header and remove garbage data
            palette_size = 1024
            if subpic_size - palette_size != resx * resy:
                resy = resx
                subpic_bytes = subpic_bytes[:(resx * resy) + palette_size + 32]
            bitdepth = 8
            planes = 1
        elif image_type == IMAGE_TYPE_8B_GSA:
            palette_size = 0
            bitdepth = 8
            planes = 2
        elif image_type == IMAGE_TYPE_8B_RGBA:
            palette_size = 0
            bitdepth = 8
            planes = 4
        if palette_size:
            palette_bytes, pixel_bytes = subpic_bytes[32:32 + palette_size], subpic_bytes[32 + palette_size:]
            palette_list = palette_bytes_to_list(reorder_txbp_png_palette(palette_bytes))
        else:
            pixel_bytes = subpic_bytes[32:]
            palette_list = []
        pixel_list = pixel_bytes_to_list(pixel_bytes, image_type)
        subpics.append({"header": subpic_header_bytes.hex(), "resx": resx, "resy": resy, "bitdepth": bitdepth, "planes": planes, "image_type": image_type, "palette": palette_list, "pixels": pixel_list, "subpic_bytes": subpic_bytes[:16] + b"\x00" * 16 + subpic_bytes[32:]})
        subpic_pos += 32 + subpic_size
    return subpics


# convert int list from pypng to txbp pixel bytes
def png_to_txbp(png_dict):
    subpic_bytes = b""
    for png_val in png_dict:
        if png_val["image_type"] == IMAGE_TYPE_4B_PAL:
            subpic_size = int((png_val["resx"] * png_val["resy"]) / 2 + len(png_val["palette"]) * 4)
            subpic_bytes += subpic_size.to_bytes(4, byteorder="little") + png_val["resx"].to_bytes(4, byteorder="little") + png_val["resy"].to_bytes(4, byteorder="little") + b"\x14\x00\x00\x00"
        elif png_val["image_type"] == IMAGE_TYPE_8B_PAL:
            subpic_size = int(png_val["resx"] * png_val["resy"] + 1024)
            subpic_bytes += subpic_size.to_bytes(4, byteorder="little") + png_val["resx"].to_bytes(4, byteorder="little") + png_val["resy"].to_bytes(4, byteorder="little") + b"\x15\x00\x00\x00"
        elif png_val["image_type"] == IMAGE_TYPE_8B_GSA:
            subpic_size = int(png_val["resx"] * png_val["resy"] * 2)
            subpic_bytes += subpic_size.to_bytes(4, byteorder="little") + png_val["resx"].to_bytes(4, byteorder="little") + png_val["resy"].to_bytes(4, byteorder="little") + b"\x1A\x00\x00\x00"
        elif png_val["image_type"] == IMAGE_TYPE_8B_RGBA:
            subpic_size = int(png_val["resx"] * png_val["resy"] * 4)
            subpic_bytes += subpic_size.to_bytes(4, byteorder="little") + png_val["resx"].to_bytes(4, byteorder="little") + png_val["resy"].to_bytes(4, byteorder="little") + b"\x1D\x00\x00\x00"
        subpic_bytes += png_val["header"]
        if png_val["palette"]:
            subpic_bytes += reorder_txbp_png_palette(palette_list_to_bytes(png_val["palette"]))
        subpic_bytes += pixel_list_to_bytes(png_val["pixels"], png_val["image_type"])
    txbp_bytes = "TXBP".encode("ascii") + len(png_dict).to_bytes(4, byteorder="little") + subpic_size.to_bytes(4, byteorder="little") + b"\x00" * (4 + 16) + subpic_bytes
    return txbp_bytes


# convert tiled sgt pixel bytes to int list for pypng
def sgt_to_png(data_in):
    resx = int.from_bytes(data_in[4:8], byteorder="little")
    resy = int.from_bytes(data_in[8:12], byteorder="little")
    tile_resx = int.from_bytes(data_in[12:16], byteorder="little")
    tile_resy = int.from_bytes(data_in[16:20], byteorder="little")
    tile_numx = int.from_bytes(data_in[20:24], byteorder="little")
    tile_numy = int.from_bytes(data_in[24:28], byteorder="little")
    tilenum = int.from_bytes(data_in[28:32], byteorder="little")
    txbp_data = data_in[32:]
    txbp_tiles = txbp_to_png(txbp_data)
    tiles = [[{} for x in range(tile_numx)] for y in range(tile_numy)]
    tile_headers = [[{} for x in range(tile_numx)] for y in range(tile_numy)]
    tile_bytes = b""
    x = 0
    y = 0
    for i in range(tilenum):
        tiles[y][x] = txbp_tiles[i]
        tile_headers[y][x] = txbp_tiles[i]["header"]
        tile_bytes += txbp_tiles[i]["subpic_bytes"]
        x += 1
        if x % tile_numx == 0:
            x = 0
            y += 1
    pixels_detiled = []
    for y in range(tile_numy):
        for z in range(tile_resy):
            for x in range(tile_numx):
                pixels_detiled += tiles[x][y]["pixels"][z * tile_resx:z * tile_resx + tile_resx]
    return [{"tile_headers": tile_headers, "header": "", "resx": resx, "resy": resy, "tile_numx": tile_numx, "tile_numy": tile_numy, "bitdepth": txbp_tiles[0]["bitdepth"], "image_type": txbp_tiles[0]["image_type"], "planes": txbp_tiles[0]["planes"], "palette": txbp_tiles[0]["palette"], "pixels": pixels_detiled, "subpic_bytes": tile_bytes}]


# convert int list from pypng to tiled sgt pixel bytes
def png_to_sgt(tile_headers, tile_numx, tile_numy, resx, resy, image_type, palette, pixels):
    tile_resx = int(resx/tile_numx)
    tile_resy = int(resy/tile_numy)
    tiles = [[{} for x in range(tile_numx)] for y in range(tile_numy)]
    x = 0
    y = 0
    for y in range(tile_numy):
        for x in range(tile_numx):
            tiles[x][y]["header"] = bytes.fromhex(tile_headers[x][y])
            tiles[x][y]["resx"] = tile_resx
            tiles[x][y]["resy"] = tile_resy
            tiles[x][y]["image_type"] = image_type
            tiles[x][y]["palette"] = palette
            tiles[x][y]["pixels"] = []
    pos = 0
    for y in range(tile_numy):
        for z in range(tile_resy):
            for x in range(tile_numx):
                tiles[x][y]["pixels"].extend(pixels[pos:pos + tile_resx])
                pos += tile_resx

    txbp_tiles = []
    for y in range(tile_numy):
        for x in range(tile_numx):
            txbp_tiles.append(tiles[y][x])
    
    txbp_bytes = png_to_txbp(txbp_tiles)
    sgt_bytes = "SGT".encode("ascii") + b"\x00" + resx.to_bytes(4, byteorder="little") + resy.to_bytes(4, byteorder="little") + tile_resx.to_bytes(4, byteorder="little") + \
    tile_resy.to_bytes(4, byteorder="little") + tile_numx.to_bytes(4, byteorder="little") + tile_numx.to_bytes(4, byteorder="little") + (tile_numx*tile_numy).to_bytes(4, byteorder="little") + txbp_bytes
    return sgt_bytes


# extract images/textures
def extract_images(path_in):
    image_hash_dict = {}
    image_added_dict = {}
    image_prop_ref_dict = {}
    subpic_hash_dict = {}
    subpic_prop_dict = {}

    i = 1
    img_done = 0
    for root, dirs, files in os.walk(path_in):
        for f in files:
            if f.upper().endswith("AVLZ") or f.upper().endswith("TXBP") or f.upper().endswith("SGT"):
                path_full = os.path.join(root, f)
                path_rel = os.path.relpath(path_full, path_in)
                with open(path_full, "rb") as file_in:
                    data_in = file_in.read()
                # check if the complete image already exists, and add the source path
                imghash = hashlib.sha1(data_in).hexdigest()
                try:
                    parent_img = image_hash_dict[imghash]
                    image_prop_ref_dict[path_rel] = {"path_dup": parent_img, "avlz": False, "type": "", "tile_headers": "", "tile_numx": 0, "tile_numy": 0, "subpics": []}
                    continue
                except KeyError:
                    pass
                image_hash_dict[imghash] = path_rel
                image_prop_ref = {"path_dup": "", "avlz": False, "type": "", "tile_headers": "", "tile_numx": 0, "tile_numy": 0, "subpics": []}
                # construct shorter path to putput pngs 
                path_split = path_rel.split(os.sep)
                path_use = ""
                for part in path_split:
                    path_use = os.path.join(path_use, part)
                    if ".ARC" in part.upper():
                        path_use = os.path.join(path_use, part)
                        break
                    elif ".DAT" in part.upper() or ".BIN" in part.upper():
                        break
                if path_use not in image_added_dict:
                    image_added_dict[path_use] = True
                    i = 1
                path_full = f"{path_use}_{i:04}"
                i += 1

                # add image properties
                if f.upper().endswith("AVLZ"):
                    data_in = yak.process.process_avlz.decode_avlz(data_in)
                    image_prop_ref["avlz"] = True
                if data_in[0:4].rstrip(b"\x00") == yak.process.process_arc.TXBP_MAGIC:
                    png_res = txbp_to_png(data_in)
                    image_prop_ref["type"] = "TXBP"
                else:
                    png_res = sgt_to_png(data_in)
                    image_prop_ref["type"] = "SGT"
                    image_prop_ref["tile_headers"] = png_res[0]["tile_headers"]
                    image_prop_ref["tile_numx"] = png_res[0]["tile_numx"]
                    image_prop_ref["tile_numy"] = png_res[0]["tile_numy"]

                # loop through subpics, look for already existing subpics,
                # add each to parts list, and save res/bitdepth to separate dict
                j = 0
                for subpic in png_res:
                    subpic_ref = {"header": "", "path": ""}
                    subpic_ref["header"] = subpic["header"]
                    subpic_ref["image_type"] = subpic["image_type"]
                    subpic_prop = {}
                    subpic_prop["resx"] = subpic["resx"]
                    subpic_prop["resy"] = subpic["resy"]
                    subpic_prop["bitdepth"] = subpic["bitdepth"]
                    subpic_prop["planes"] = subpic["planes"]
                    subpic_prop["image_type"] = subpic["image_type"]
                    subpic_prop["palette_size"] = len(subpic["palette"])
                    if subpic["image_type"] == IMAGE_TYPE_8B_GSA:
                        writer = png.Writer(width=subpic["resx"], height=subpic["resy"], bitdepth=subpic["bitdepth"], greyscale=True, alpha=True)
                    elif subpic["image_type"] == IMAGE_TYPE_8B_RGBA:
                        writer = png.Writer(width=subpic["resx"], height=subpic["resy"], bitdepth=subpic["bitdepth"], greyscale=False, alpha=True)
                    else:
                        writer = png.Writer(width=subpic["resx"], height=subpic["resy"], bitdepth=subpic["bitdepth"], palette=subpic["palette"])
                    pixel_rows = writer.array_scanlines(subpic["pixels"])
                    path_rel_subpic_out = f"{path_full}_{j}.png"
                    path_full_subpic_out = os.path.join(yak.meta.global_def.DIR_IMG_ORIG, path_rel_subpic_out)
                    path_full_subpic_out_work = os.path.join(yak.meta.global_def.DIR_IMG_WORK, path_rel_subpic_out)
                    subpichash = hashlib.sha1(subpic["subpic_bytes"]).hexdigest()
                    try:
                        parent_subpic = subpic_hash_dict[subpichash]
                        subpic_ref["path"] = parent_subpic
                    except KeyError:
                        subpic_hash_dict[subpichash] = path_rel_subpic_out
                        subpic_ref["path"] = path_rel_subpic_out
                        os.makedirs(os.path.dirname(path_full_subpic_out), exist_ok=True)
                        os.makedirs(os.path.dirname(path_full_subpic_out_work), exist_ok=True)
                        try:
                            with open(path_full_subpic_out, "wb") as file_out:
                                writer.write(file_out, pixel_rows)
                        except png.ProtocolError:
                            continue
                    image_prop_ref["subpics"].append(subpic_ref)
                    subpic_prop_dict[path_rel_subpic_out] = subpic_prop
                    j += 1
                image_prop_ref_dict[path_rel] = image_prop_ref
                img_done += 1
                if img_done % 100 == 0:
                    print(f"Extracted images: {img_done}...")
    return image_prop_ref_dict, subpic_prop_dict


# compress with pngquant/copy images for rebuild
def compress_images(path_input, path_output, prop_dict):
    warnings = []
    img_done = 0
    pngq_args = [yak.meta.global_def.PNGQUANT_TOOL, "--force", "--nofs", "--quality", "0-100", "--speed", "1"]
    for root, dirs, files in os.walk(path_input):
        for f in files:
            if f.lower().endswith("png"):
                if img_done and img_done % 50 == 0:
                    print(f"Processed images: {img_done}...")
                img_done += 1
                path_full = os.path.join(root, f)
                path_rel = os.path.relpath(path_full, path_input)
                # check if file is in exported dict
                try:
                    subpic_prop = prop_dict[path_rel]
                except KeyError:
                    warnings.append(f"STEP - Compress images\nERROR - Invalid path, image ignored...\nPath: {path_full}\nCheck filename/location...")
                    continue
                path_out = os.path.join(path_output, path_rel)
                os.makedirs(os.path.dirname(path_out), exist_ok=True)
                width, height, pixels, metadata = png.Reader(filename=path_full).read()
                # check if file is correct resolution
                if width != subpic_prop["resx"] or height != subpic_prop["resy"]:
                    warnings.append(f"STEP - Compress images\nERROR - Incorrect resolution, image ignored...\nPath: {path_full}\nExpected: {subpic_prop['resx']}x{subpic_prop['resy']}, Detected: {width}x{height}\nCheck image properties...")
                    continue
                # check if file is correct bitdepth, convert using pngquant if not
                try:
                    palette_size = len(metadata["palette"])
                except KeyError:
                    palette_size = 0
                if not (metadata["bitdepth"] == subpic_prop["bitdepth"] and metadata["planes"] == subpic_prop["planes"] and palette_size == subpic_prop["palette_size"]):
                    if (metadata["alpha"] == False and palette_size == 0) or (palette_size > 0 and len(metadata["palette"][0]) < 4):
                        warnings.append(f"STEP - Compress images\nERROR - File missing alpha channel, image ignored...\nPath: {path_full}\nMake sure images have an alpha channel...")
                        continue
                    if subpic_prop["image_type"] in (IMAGE_TYPE_4B_PAL, IMAGE_TYPE_8B_PAL):
                        args = pngq_args.copy()
                        args.append(str(subpic_prop["palette_size"]))
                        args.append(path_full)
                        args.append("--output")
                        args.append(path_out)
                        try:
                            result = subprocess.run(args)
                            if result.returncode:
                                raise Exception
                        except Exception:
                            warnings.append(f"STEP - Compress images\nERROR - Pngquant couldn't execute correctly, image ignored...\nPath: {path_full}\nCheck pngquant path and that it works...")
                            continue
                        width, height, pixel_rows, metadata = png.Reader(filename=path_out).read_flat()
                        new_palette = []
                        do_write = False
                        if len(metadata["palette"][0]) != 4:
                            do_write = True
                            for ptup in metadata["palette"]:
                                new_palette.append(tuple(list(ptup) + [255]))
                        else:
                            new_palette = metadata["palette"]
                        if len(new_palette) < subpic_prop["palette_size"]:
                            do_write = True
                            pal_diff = subpic_prop["palette_size"] - len(new_palette)
                            new_palette += [(0,0,0,0)] * pal_diff
                        if do_write:
                            writer = png.Writer(width=width, height=height, palette=new_palette, bitdepth=8 if len(new_palette) == 256 else 4)
                            pixel_rows = writer.array_scanlines(pixel_rows)
                            with open(path_out, "wb") as file_out:
                                writer.write(file_out, pixel_rows)
                    elif subpic_prop["image_type"] == IMAGE_TYPE_8B_GSA:
                        if not (metadata["bitdepth"] == subpic_prop["bitdepth"] and metadata["planes"] == subpic_prop["planes"] and palette_size == 0):
                            width, height, pixels, metadata = png.Reader(filename=path_full).asRGBA8()
                            pix_tup = []
                            pixels_reduce = []
                            for pa in pixels:
                                for p in pa:
                                    pix_tup.append(p)
                                    if len(pix_tup) == 4:
                                        pixels_reduce.append(int((pix_tup[0] + pix_tup[1] + pix_tup[2]) / 3))
                                        pixels_reduce.append(pix_tup[3])
                                        pix_tup = []
                            writer = png.Writer(width=width, height=height, bitdepth=subpic_prop["bitdepth"], greyscale=True, alpha=True)
                            pixel_rows = writer.array_scanlines(pixels_reduce)
                            with open(path_out, "wb") as file_out:
                                writer.write(file_out, pixel_rows)
                    elif subpic_prop["image_type"] == IMAGE_TYPE_8B_RGBA:
                        if not (metadata["bitdepth"] == subpic_prop["bitdepth"] and metadata["planes"] == subpic_prop["planes"] and palette_size == 0):
                            width, height, pixels, metadata = png.Reader(filename=path_full).asRGBA8()
                            writer = png.Writer(width=width, height=height, bitdepth=subpic_prop["bitdepth"], greyscale=False, alpha=True)
                            with open(path_out, "wb") as file_out:
                                writer.write(file_out, pixels)
                else:
                    shutil.copy2(path_full, path_out)
    return warnings


# convert images to txbp/sgt and compess to avlz
def convert_images(path_input, path_output, prop_dict):
    img_done = 0
    for key, img_prop in prop_dict.items():
        img_modified = False
        for subpic in img_prop["subpics"]:
            if os.path.isfile(os.path.join(path_input, subpic["path"])):
                img_modified = True
                break
        if not img_modified:
            continue
        texture_bytes = b""
        if img_prop["type"] == "TXBP":
            subpics = []
            for subpic in img_prop["subpics"]:
                path_subpic_full = os.path.join(path_input, subpic["path"])
                if not os.path.isfile(path_subpic_full):
                    path_subpic_full = os.path.join(yak.meta.global_def.DIR_IMG_ORIG, subpic["path"])
                width, height, pixels, metadata = png.Reader(filename=path_subpic_full).read_flat()
                try:
                    palette = metadata["palette"]
                except KeyError:
                    palette = []
                subpics.append({"header": bytes.fromhex(subpic["header"]), "resx": width, "resy": height, "image_type": subpic["image_type"], "palette": palette, "pixels": list(pixels)})
            texture_bytes = png_to_txbp(subpics)
        elif img_prop["type"] == "SGT":
            path_subpic_full = os.path.join(path_input, img_prop["subpics"][0]["path"])
            width, height, pixels, metadata = png.Reader(filename=path_subpic_full).read_flat()
            try:
                palette = metadata["palette"]
            except KeyError:
                palette = []
            texture_bytes = png_to_sgt(img_prop["tile_headers"], img_prop["tile_numx"], img_prop["tile_numy"], width, height, img_prop["subpics"][0]["image_type"], palette, list(pixels))
        if img_prop["avlz"]:
            texture_bytes = yak.process.process_avlz.encode_avlz(texture_bytes)
        path_full_out = os.path.join(path_output, key)
        os.makedirs(os.path.dirname(path_full_out), exist_ok=True)
        with open(path_full_out, "wb") as file_out:
            file_out.write(texture_bytes)
        img_done += 1
        if img_done % 5 == 0:
            print(f"Processed images: {img_done}...")


# convert icons to txbp
def convert_icons(path_input, prop_dict):
    icon_dict = []
    for key, img_prop in prop_dict.items():
        path_icon = os.path.join(path_input, key)
        if not os.path.isfile(path_icon):
            path_icon = os.path.join(yak.meta.global_def.DIR_IMG_ICON_ORIG, key)
        width, height, pixels, metadata = png.Reader(filename=path_icon).read_flat()
        try:
            palette = metadata["palette"]
        except KeyError:
            palette = []
        subpics = [{"header": bytes.fromhex(img_prop["header"]), "resx": width, "resy": height, "image_type": img_prop["image_type"], "palette": palette, "pixels": list(pixels)}]
        texture_bytes = png_to_txbp(subpics)
        icon_dict.append(texture_bytes)
    return icon_dict
