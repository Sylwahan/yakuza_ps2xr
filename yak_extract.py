import configparser
import json
import os
import shutil
import sys

import yak.meta.global_def
import yak.meta.iso_id_meta
import yak.meta.voice_patch_jp
import yak.process.process_arc
import yak.process.process_cvm
import yak.process.process_image
import yak.process.process_iso
import yak.process.process_ogredir
import yak.process.process_talk

CHUNK_SIZE = 4194304
ISO_IDS = ["SLPM_661.68", "SLUS_213.48", "SLES_541.71", "SLKA_253.42", "SLPM_666.02", "SLPM_666.03", "SLPM_743.01", "SLUS_217.69", "SLES_552.42", "SLKA_252.80", "SLKA_252.81"]
ISO_ID = ""
ISO_META = {}
HAS_LAYERS = False
LAYER_END = 0
ISO_LAYER_PAD = b""
RESUME_STAGE = 0
WARNINGS = []


# get metadata from extraction
def get_metadata():
    global ISO_ID, ISO_META, HAS_LAYERS, RESUME_STAGE
    if os.path.isfile(yak.meta.global_def.FILE_ISO_INFO_DICT):
        with open(yak.meta.global_def.FILE_ISO_INFO_DICT, "r") as file_in:
            info_dict = json.load(file_in)
        try:
            ISO_ID = info_dict["iso_id"]
            HAS_LAYERS = info_dict["has_layers"]
            RESUME_STAGE = info_dict["resume_stage"]
            ISO_META = yak.meta.iso_id_meta.ISO_ID_META[ISO_ID]
        except KeyError:
            raise Exception("STEP - Get metadata\nERROR - KeyError during metadata fetch...")


# write iso info file, keeping track in case extraction terminates
def write_iso_info(resume_stage):
    global RESUME_STAGE
    os.makedirs(yak.meta.global_def.DIR_INFO_DICT, exist_ok=True)
    with open(yak.meta.global_def.FILE_ISO_INFO_DICT, "w") as file_out:
        json.dump({"iso_id": ISO_ID, "has_layers": HAS_LAYERS, "resume_stage": resume_stage}, file_out, indent=4, ensure_ascii=True)
    RESUME_STAGE = resume_stage


# analyze main game ISO, extract headers, split layers if needed
def analyze_iso():
    global LAYER_END, HAS_LAYERS, ISO_LAYER_PAD
    print("Checking for game ISO type...")
    with open(yak.meta.global_def.ISO_ORIGINAL, "rb") as file_iso_orig:
        file_iso_orig.seek(32848)
        LAYER_END = int.from_bytes(file_iso_orig.read(4), byteorder="little") * 2048
    if os.path.getsize(yak.meta.global_def.ISO_ORIGINAL) > LAYER_END:
        print("Dual-layer ISO detected...")
        HAS_LAYERS = True
    os.makedirs(yak.meta.global_def.DIR_ISO_HEADER, exist_ok=True)
    if HAS_LAYERS:
        with open(yak.meta.global_def.ISO_ORIGINAL, "rb") as file_iso_orig:
            data_iso_header_layer1 = file_iso_orig.read(32768)
            ISO_LAYER_PAD = data_iso_header_layer1
        with open(yak.meta.global_def.FILE_ISO_LAYER_PAD, "wb") as file_iso_header:
            file_iso_header.write(data_iso_header_layer1)


# extract main game ISO
def extract_main_iso():
    os.makedirs(yak.meta.global_def.DIR_ISO_ORIG, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_ENC_ORIG_L1, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_INFO_DICT, exist_ok=True)
    if HAS_LAYERS:
        print("Splitting main game ISO layers...")
        chunks_layer1, last_chunk_layer1 = divmod(LAYER_END, CHUNK_SIZE)
        chunks_layer2, last_chunk_layer2 = divmod((os.path.getsize(yak.meta.global_def.ISO_ORIGINAL) - LAYER_END), CHUNK_SIZE)
        with open(yak.meta.global_def.ISO_ORIGINAL, "rb") as file_iso_orig:
            with open(yak.meta.global_def.FILE_ISO_ORIG_L1, "wb") as file_iso_orig_layer1:
                file_iso_orig.seek(0)
                for i in range(chunks_layer1):
                    file_iso_orig_layer1.write(file_iso_orig.read(CHUNK_SIZE))
                file_iso_orig_layer1.write(file_iso_orig.read(last_chunk_layer1))
            with open(yak.meta.global_def.FILE_ISO_ORIG_L2, "wb") as file_iso_orig_layer2:
                file_iso_orig_layer2.write(ISO_LAYER_PAD)
                for i in range(chunks_layer2):
                    file_iso_orig_layer2.write(file_iso_orig.read(CHUNK_SIZE))
                file_iso_orig_layer2.write(file_iso_orig.read(last_chunk_layer2))
        print("Collecting ISO metadata from layer 1...")
        file_lba_list, dir_rec_list, iso_header, iso_footer = yak.process.process_iso.collect_lba_iso9660(yak.meta.global_def.FILE_ISO_ORIG_L1)
        with open(yak.meta.global_def.FILE_LBA_ISO_L1, "w") as file_out:
            json.dump(file_lba_list, file_out)
        with open(yak.meta.global_def.FILE_DIR_REC_L1, "w") as file_out:
            json.dump(dir_rec_list, file_out)
        with open(yak.meta.global_def.FILE_ISO_HEADER_L1, "wb") as file_out:
            file_out.write(iso_header)
        with open(yak.meta.global_def.FILE_ISO_FOOTER_L1, "wb") as file_out:
            file_out.write(iso_footer)
        file_lba_udf_dict = yak.process.process_iso.collect_lba_udf(yak.meta.global_def.FILE_ISO_ORIG_L1)
        with open(yak.meta.global_def.FILE_LBA_UDF_L1, "w") as file_out:
            json.dump(file_lba_udf_dict, file_out)
        print("Collecting ISO metadata from layer 2...")
        file_lba_list, dir_rec_list, iso_header, iso_footer = yak.process.process_iso.collect_lba_iso9660(yak.meta.global_def.FILE_ISO_ORIG_L2)
        with open(yak.meta.global_def.FILE_LBA_ISO_L2, "w") as file_out:
            json.dump(file_lba_list, file_out)
        with open(yak.meta.global_def.FILE_DIR_REC_L2, "w") as file_out:
            json.dump(dir_rec_list, file_out)
        with open(yak.meta.global_def.FILE_ISO_HEADER_L2, "wb") as file_out:
            file_out.write(iso_header)
        with open(yak.meta.global_def.FILE_ISO_FOOTER_L2, "wb") as file_out:
            file_out.write(iso_footer)
        file_lba_udf_dict = yak.process.process_iso.collect_lba_udf(yak.meta.global_def.FILE_ISO_ORIG_L2)
        with open(yak.meta.global_def.FILE_LBA_UDF_L2, "w") as file_out:
            json.dump(file_lba_udf_dict, file_out)
        print("Extracting main game ISO layer 1...")
        yak.process.process_iso.extract_iso(yak.meta.global_def.FILE_ISO_ORIG_L1, yak.meta.global_def.DIR_ENC_ORIG_L1)#, use_udf=True)
        print("Extracting main game ISO layer 2...")
        os.makedirs(yak.meta.global_def.DIR_ENC_ORIG_L2, exist_ok=True)
        yak.process.process_iso.extract_iso(yak.meta.global_def.FILE_ISO_ORIG_L2, yak.meta.global_def.DIR_ENC_ORIG_L2)#, use_udf=True)
    else:
        print("Copying main game ISO...")
        shutil.copy2(yak.meta.global_def.ISO_ORIGINAL, yak.meta.global_def.FILE_ISO_ORIG_L1)
        print("Collecting ISO metadata from layer 1...")
        file_lba_list, dir_rec_list, iso_header, iso_footer = yak.process.process_iso.collect_lba_iso9660(yak.meta.global_def.FILE_ISO_ORIG_L1)
        with open(yak.meta.global_def.FILE_LBA_ISO_L1, "w") as file_out:
            json.dump(file_lba_list, file_out)
        with open(yak.meta.global_def.FILE_DIR_REC_L1, "w") as file_out:
            json.dump(dir_rec_list, file_out)
        with open(yak.meta.global_def.FILE_ISO_HEADER_L1, "wb") as file_out:
            file_out.write(iso_header)
        with open(yak.meta.global_def.FILE_ISO_FOOTER_L1, "wb") as file_out:
            file_out.write(iso_footer)
        file_lba_udf_dict = yak.process.process_iso.collect_lba_udf(yak.meta.global_def.FILE_ISO_ORIG_L1)
        with open(yak.meta.global_def.FILE_LBA_UDF_L1, "w") as file_out:
            json.dump(file_lba_udf_dict, file_out)
        print("Extracting main game ISO...")
        yak.process.process_iso.extract_iso(yak.meta.global_def.FILE_ISO_ORIG_L1, yak.meta.global_def.DIR_ENC_ORIG_L1)#, use_udf=True)


# get ISO id from the game executable name
def get_iso_id():
    global ISO_ID, ISO_META
    for (rootdir, dirs, files) in os.walk(yak.meta.global_def.DIR_ENC_ORIG_L1):
        for f in files:
            if f in ISO_IDS:
                ISO_ID = f
                ISO_META = yak.meta.iso_id_meta.ISO_ID_META[ISO_ID]
                break
        break
    if not ISO_ID:
        raise Exception(f"STEP - Get ISO ID\nERROR - Unsupported ISO...\nThe following ISOs are supported: {', '.join(ISO_IDS)}")


# convert CVM to ISO
def convert_cvm_to_iso():
    os.makedirs(yak.meta.global_def.DIR_CVM_HEADER, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_DEC_ORIG_L1, exist_ok=True)
    for (rootdir, dirs, files) in os.walk(yak.meta.global_def.DIR_ENC_ORIG_L1):
        for f in sorted(files):
            if f.lower().endswith(".cvm"):
                print(f"Converting CVM to ISO: {f[:-4]} (Layer 1)...")
                yak.process.process_cvm.cvm_to_iso(os.path.join(yak.meta.global_def.DIR_ENC_ORIG_L1, f), os.path.join(yak.meta.global_def.DIR_DEC_ORIG_L1, f[:-4]+".iso"), os.path.join(yak.meta.global_def.DIR_CVM_HEADER, f[:-4]+".bytes"))
        break
    if HAS_LAYERS:
        os.makedirs(yak.meta.global_def.DIR_DEC_ORIG_L2, exist_ok=True)
        for (rootdir, dirs, files) in os.walk(yak.meta.global_def.DIR_ENC_ORIG_L2):
            for f in sorted(files):
                if f.lower().endswith(".cvm"):
                    print(f"Converting CVM to ISO: {f[:-4]} (Layer 2)...")
                    yak.process.process_cvm.cvm_to_iso(os.path.join(yak.meta.global_def.DIR_ENC_ORIG_L2, f), os.path.join(yak.meta.global_def.DIR_DEC_ORIG_L2, f[:-4]+".iso"), os.path.join(yak.meta.global_def.DIR_CVM_HEADER, f[:-4]+".bytes"))
            break   


# extract internal ISO
def extract_internal_iso():
    os.makedirs(yak.meta.global_def.DIR_FILES_ORIG_L1, exist_ok=True)
    for (rootdir, dirs, files) in os.walk(yak.meta.global_def.DIR_DEC_ORIG_L1):
        for f in files:
            if f.lower().endswith(".iso"):
                print(f"Extracting internal ISO: {f[:-4]} (Layer 1)...")
                yak.process.process_iso.extract_iso(os.path.join(yak.meta.global_def.DIR_DEC_ORIG_L1, f), yak.meta.global_def.DIR_FILES_ORIG_L1)
        break
    if HAS_LAYERS:
        os.makedirs(yak.meta.global_def.DIR_FILES_ORIG_L2, exist_ok=True)
        for (rootdir, dirs, files) in os.walk(yak.meta.global_def.DIR_DEC_ORIG_L2):
            for f in files:
                if f.lower().endswith(".iso"):
                    print(f"Extracting internal ISO: {f[:-4]} (Layer 2)...")
                    yak.process.process_iso.extract_iso(os.path.join(yak.meta.global_def.DIR_DEC_ORIG_L2, f), yak.meta.global_def.DIR_FILES_ORIG_L2)
            break


# merge extracted files from layers
def merge_layer_files():
    print("Merging ISO layer files...")
    layer1_copy_dict = {}
    layer2_copy_dict = {}
    do_media = ISO_META["MEDIA"]
    layer_merge = [{"FILES_ORIG": yak.meta.global_def.DIR_FILES_ORIG_L1, "FILE_OUT": yak.meta.global_def.FILE_LAYER_COPY_DICT_L1, "DICT": layer1_copy_dict}]
    if HAS_LAYERS:
        layer_merge.append({"FILES_ORIG": yak.meta.global_def.DIR_FILES_ORIG_L2, "FILE_OUT": yak.meta.global_def.FILE_LAYER_COPY_DICT_L2, "DICT": layer2_copy_dict})
    for layer_vals in layer_merge:
        for (rootdir, dirs, files) in os.walk(layer_vals["FILES_ORIG"]):
            for f in files:
                file_path = os.path.join(rootdir, f)
                rel_path = os.path.relpath(file_path, layer_vals["FILES_ORIG"])
                media_dir = rel_path.split(os.path.sep)[0]
                for media_key, media_val in do_media.items():
                    if media_dir in media_val:
                        if media_key not in layer_vals["DICT"]:
                            layer_vals["DICT"][media_key] = []
                        layer_vals["DICT"][media_key].append(rel_path)
                out_path = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, rel_path)
                if not os.path.isfile(out_path):
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    shutil.copy2(file_path, out_path)
        with open(layer_vals["FILE_OUT"], "w") as out_file:
            json.dump(layer_vals["DICT"], out_file, indent=4, ensure_ascii=True)


# copy over movie/voice files to resource dir
def copy_movie_voice_files():
    print("Copying MOVIE/VOICE files...")
    os.makedirs(yak.meta.global_def.DIR_REC_VOICE_ORIG, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_VOICE_WORK, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_GEN_ARC_WORK, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_GEN_FILES_WORK, exist_ok=True)
    for f in ISO_META["VOICE"]:
        path_in = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, f)
        if os.path.isfile(path_in):
            path_out = os.path.join(yak.meta.global_def.DIR_REC_VOICE_ORIG, f)
            os.makedirs(os.path.dirname(path_out), exist_ok=True)
            shutil.copy2(path_in, path_out)
    os.makedirs(yak.meta.global_def.DIR_REC_MOV_ORIG, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_MOV_WORK_FS, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_MOV_WORK_WS, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_MOV_WORK_FS_LITE, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_MOV_WORK_WS_LITE, exist_ok=True)
    for f in ISO_META["MOVIE"]:
        path_in = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, f)
        if os.path.isfile(path_in):
            path_out = os.path.join(yak.meta.global_def.DIR_REC_MOV_ORIG, f)
            os.makedirs(os.path.dirname(path_out), exist_ok=True)
            shutil.copy2(path_in, path_out)
    if ISO_ID in ["SLPM_661.68", "SLKA_253.42"]:
        for fkey, f in yak.meta.voice_patch_jp.VOICE_JP_INDEX.items():
            path_in = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, "MEDIA2", "SOUND", f["name"])
            if os.path.isfile(path_in):
                path_out = os.path.join(yak.meta.global_def.DIR_REC_VOICE_ORIG, "MEDIA2", "SOUND", f["name"])
                os.makedirs(os.path.dirname(path_out), exist_ok=True)
                shutil.copy2(path_in, path_out)
        for f in yak.meta.voice_patch_jp.VOICE_JP_B00:
            path_in = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, "MEDIA2", "AUTHOR", f)
            if os.path.isfile(path_in):
                path_out = os.path.join(yak.meta.global_def.DIR_REC_VOICE_ORIG, "MEDIA2", "AUTHOR", f)
                os.makedirs(os.path.dirname(path_out), exist_ok=True)
                shutil.copy2(path_in, path_out)


# collect bytes needed to rebuild ogredir TOC later
def collect_ogredir():
    print("Collecting OGREDIRs...")
    ogredirs_L1 = {}
    for ogre_key, ogre_value in ISO_META["OGREDIRS_L1"].items():
        with open(os.path.join(yak.meta.global_def.DIR_ENC_ORIG_L1, ogre_value), "rb") as file_in:
            data_in = file_in.read()
        out_dict = yak.process.process_ogredir.collect_init_bytes(data_in)
        ogredirs_L1[ogre_key] = out_dict
    if HAS_LAYERS:
        ogredirs_L2 = {}
        for ogre_key, ogre_value in ISO_META["OGREDIRS_L2"].items():
            with open(os.path.join(yak.meta.global_def.DIR_ENC_ORIG_L2, ogre_value), "rb") as file_in:
                data_in = file_in.read()
            out_dict = yak.process.process_ogredir.collect_init_bytes(data_in)
            ogredirs_L2[ogre_key] = out_dict
        with open(yak.meta.global_def.FILE_OGREDIR_INIT_L2, "w") as file_out:
            json.dump(ogredirs_L2, file_out, indent=4, ensure_ascii=True)
        for ogre_key, ogre_dict in ogredirs_L1.items():
            ogredirs_L2[ogre_key]["MYSTERY_BYTES"].update(ogre_dict["MYSTERY_BYTES"])
            ogre_dict["MYSTERY_BYTES"] = ogredirs_L2[ogre_key]["MYSTERY_BYTES"]
    with open(yak.meta.global_def.FILE_OGREDIR_INIT_L1, "w") as file_out:
        json.dump(ogredirs_L1, file_out, indent=4, ensure_ascii=True)


# extract ARC/DAT/BIN files
def extract_arc():
    print("Extracting ARC/DAT/BIN files...")
    os.makedirs(yak.meta.global_def.DIR_ARC_ORIG, exist_ok=True)
    arc_done = 0
    for root, dirs, files in os.walk(yak.meta.global_def.DIR_FILES_ORIG_MERGE):
        for f in files:
            f_ext = f.upper()[-3:]
            if f_ext in ("ARC", "DAT", "BIN"):
                path_in_full = os.path.join(root, f)
                do_arc = False
                for f_do in ISO_META["ARC_DO"]:
                    if f_do in path_in_full:
                        do_arc = True
                        break
                path_rel = os.path.relpath(path_in_full, yak.meta.global_def.DIR_FILES_ORIG_MERGE)
                if do_arc:
                    res = yak.process.process_arc.extract_arcdatbin_main(path_in_full, path_rel, yak.meta.global_def.DIR_ARC_ORIG)
                    if res:
                        arc_done += 1
                        if arc_done % 50 == 0:
                            print(f"Extracted files: {arc_done}...")


# move TALK (BIN) files to clean dir
def move_talk():
    print("Moving TALK BIN files...")
    arc_bin_dict = {}
    for root, dirs, files in os.walk(yak.meta.global_def.DIR_ARC_ORIG):
        for f in files:
            if f.upper().endswith("BIN"):
                path_full = os.path.join(root, f)
                path_rel = os.path.relpath(path_full, yak.meta.global_def.DIR_ARC_ORIG)
                if ".ARC" in path_rel:
                    path_rel_out = os.path.join(os.path.dirname(os.path.dirname(path_rel)), f.split("___")[1])
                else:
                    path_rel_out = path_rel
                path_out_full = os.path.join(yak.meta.global_def.DIR_ARC_BIN_ORIG, path_rel_out)
                arc_bin_dict[path_rel] = path_rel_out
                os.makedirs(os.path.dirname(path_out_full), exist_ok=True)
                shutil.move(path_full, path_out_full)
    with open(yak.meta.global_def.FILE_ARC_BINCOPY_DICT, "w") as file_out:
        json.dump(arc_bin_dict, file_out, indent=4, ensure_ascii=True)


# extract TALK (BIN) files to json, and character bitmaps
def extract_talk():
    print("Extracting TALK files...")
    if os.path.isdir(yak.meta.global_def.DIR_REC_IMG_ICON_WORK):
        em = f"STEP - Extract TALK icons\nERROR - Target directory for TALK icon extraction already exist...\nPath: {yak.meta.global_def.DIR_REC_IMG_ICON_WORK}\n"
        em += "Extraction canceled to prevent accidental overwrite..."
        raise Exception(em)
    global WARNINGS
    os.makedirs(yak.meta.global_def.DIR_ARC_DICT_ORIG, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_CHAR_OVERRIDE, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_CHAR_EXTRACT, exist_ok=True)
    os.makedirs(yak.meta.global_def.DIR_REC_CHAR_UNKNOWN, exist_ok=True)
    warnings = yak.process.process_talk.extract_talk_dict(yak.meta.global_def.DIR_ARC_BIN_ORIG, yak.meta.global_def.DIR_ARC_DICT_ORIG, ISO_META["ICON_MODE"], iso_id=ISO_ID)
    WARNINGS += warnings


# consolidate TALK json
def consolidate_talk():
    print("Consolidating TALK files...")
    if os.path.isdir(yak.meta.global_def.DIR_REC_TALK_WORK):
        em = f"STEP - Consolidating TALK files\nERROR - Target directory for TALK consolidation already exists...\nPath: {yak.meta.global_def.DIR_REC_TALK_WORK}\n"
        em += "Extraction canceled to prevent accidental overwrite..."
        raise Exception(em)
    talk_skip = ISO_META["TALK_SKIP"]
    talk_self = ISO_META["TALK_SELF"]
    talk_hold = ISO_META["TALK_HOLD"]
    yak.process.process_talk.extract_talk_text(yak.meta.global_def.DIR_ARC_DICT_ORIG, yak.meta.global_def.DIR_REC_TALK_ORIG, yak.meta.global_def.DIR_REC_TALK_WORK, talk_skip=talk_skip, talk_self=talk_self, talk_hold=talk_hold)
    if os.path.isdir(yak.meta.global_def.DIR_ARC_TALK_ORIG):
        shutil.rmtree(yak.meta.global_def.DIR_ARC_TALK_ORIG)
    shutil.copytree(yak.meta.global_def.DIR_REC_TALK_ORIG, yak.meta.global_def.DIR_ARC_TALK_ORIG)
    if os.path.isdir(yak.meta.global_def.DIR_IMG_ICON_ORIG):
        shutil.rmtree(yak.meta.global_def.DIR_IMG_ICON_ORIG)
    shutil.copytree(yak.meta.global_def.DIR_REC_IMG_ICON_ORIG, yak.meta.global_def.DIR_IMG_ICON_ORIG)


# extract images
def extract_images():
    print("Extracting images...")
    if os.path.isdir(yak.meta.global_def.DIR_REC_IMG_WORK):
        em = f"STEP - Extract images\nERROR - Target directory for image extraction already exist...\nPath: {yak.meta.global_def.DIR_REC_IMG_WORK}\n"
        em += "Extraction canceled to prevent accidental overwrite..."
        raise Exception(em)
    
    if os.path.isdir(yak.meta.global_def.DIR_IMG_ORIG):
        shutil.rmtree(yak.meta.global_def.DIR_IMG_ORIG)
    if os.path.isdir(yak.meta.global_def.DIR_IMG_WORK):
        shutil.rmtree(yak.meta.global_def.DIR_IMG_WORK)
    if os.path.isdir(yak.meta.global_def.DIR_REC_IMG_ORIG):
        shutil.rmtree(yak.meta.global_def.DIR_REC_IMG_ORIG)
    
    image_prop_ref_dict, subpic_prop_dict = yak.process.process_image.extract_images(yak.meta.global_def.DIR_ARC_ORIG)
    with open(yak.meta.global_def.FILE_IMG_PROP_REF_DICT, "w") as file_out:
        json.dump(image_prop_ref_dict, file_out, indent=4, ensure_ascii=True)
    with open(yak.meta.global_def.FILE_SUBPIC_PROP_DICT, "w") as file_out:
        json.dump(subpic_prop_dict, file_out, indent=4, ensure_ascii=True)
    shutil.copytree(yak.meta.global_def.DIR_IMG_ORIG, yak.meta.global_def.DIR_REC_IMG_ORIG)
    shutil.copytree(yak.meta.global_def.DIR_IMG_WORK, yak.meta.global_def.DIR_REC_IMG_WORK)
    shutil.rmtree(yak.meta.global_def.DIR_IMG_WORK)


# extraction entry point
def extract():
    global RESUME_STAGE
    try:
        # read in info files for resume if exists
        get_metadata()
        # resume and loop through stages until done
        if 11 > RESUME_STAGE > 0:
            print(f"Previous export for ISO {os.path.basename(yak.meta.global_def.ISO_ORIGINAL)} detected, resuming...")
        while RESUME_STAGE < 12:
            match RESUME_STAGE:
                case 0:
                    analyze_iso()
                    extract_main_iso()
                    get_iso_id()
                    write_iso_info(1)
                case 1:
                    convert_cvm_to_iso()
                    write_iso_info(2)
                case 2:
                    extract_internal_iso()
                    write_iso_info(3)
                case 3:
                    merge_layer_files()
                    write_iso_info(4)
                case 4:
                    copy_movie_voice_files()
                    write_iso_info(5)
                case 5:
                    collect_ogredir()
                    write_iso_info(6)
                case 6:
                    extract_arc()
                    write_iso_info(7)
                case 7:
                    move_talk()
                    write_iso_info(8)
                case 8:
                    extract_talk()
                    write_iso_info(9)
                case 9:
                    consolidate_talk()
                    write_iso_info(10)
                case 10:
                    extract_images()
                    write_iso_info(11)
                case 11:
                    if WARNINGS:
                        for w in WARNINGS:
                            print("---------------- WARNING ----------------")
                            print(w)
                        print("Extraction completed, with warnings...")
                    else:
                        print("Extraction completed...")
                    print(f"Modifiable resource path: {yak.meta.global_def.DIR_RESOURCE}")
                    break
                case _:
                    print("Invalid RESUME STAGE detected, canceling...")
                    break
    except Exception as e:
        print("---------------- ERROR ----------------")
        print("Extraction canceled due to errors...")
        raise e


# check for path to config file, either first argument or yak_pref.ini if not supplied
# initialize global variables
def main(argv):
    if len(argv) == 1:
        path_ini = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yak_pref.ini")
        if not os.path.isfile(path_ini):
            print("No config file specified, and yak_pref.ini does not exist, exiting...")
            return
    else:
        path_ini = argv[1]
        if not os.path.isfile(path_ini):
            print("Specified config file does not exist, exiting...")
            print(f"Path {path_ini}")
            return
    config = configparser.ConfigParser()
    config.read(path_ini)
    if not os.path.isfile(config["Path"]["ISO"]):
        print("Specified ISO file does not exist, exiting...")
        print(f"Path {config["Path"]["ISO"]}")
        return
    yak.meta.global_def.init(config["Path"])
    extract()

if __name__ == "__main__":
    main(sys.argv)
    sys.exit()
