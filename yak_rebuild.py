import configparser
import json
import os
import shutil
import sys

import yak.meta.bin_patch
import yak.meta.extract_def
import yak.meta.global_def
import yak.meta.iso_id_meta
import yak.meta.opening_sub
import yak.meta.voice_patch_kr
import yak.meta.voice_patch_jp
import yak.process.process_arc
import yak.process.process_cvm
import yak.process.process_image
import yak.process.process_iso
import yak.process.process_ogredir
import yak.process.process_scene
import yak.process.process_talk
import yak.talk.talk_chars

CHUNK_SIZE = 4194304
ISO_ID = ""
HAS_LAYERS = False
ISO_META = {}
DO_MEDIA = []
OGREDIR_START_L1 = {}
OGREDIR_START_L2 = {}
WARNINGS = []
VOICE_LIST = b""


# get metadata from extraction
def get_metadata():
    global ISO_ID, HAS_LAYERS, ISO_META, DO_MEDIA
    if os.path.isfile(yak.meta.global_def.FILE_ISO_INFO_DICT):
        with open(yak.meta.global_def.FILE_ISO_INFO_DICT, "r") as file_in:
            info_dict = json.load(file_in)
        try:
            ISO_ID = info_dict["iso_id"]
            HAS_LAYERS = info_dict["has_layers"]
            ISO_META = yak.meta.iso_id_meta.ISO_ID_META[ISO_ID]
            filter_media = {}
            for media_key in yak.meta.global_def.REBUILD_MEDIA:
                try:
                    filter_media[media_key] = ISO_META["MEDIA"][media_key]
                    DO_MEDIA += filter_media[media_key]
                except KeyError:
                    pass
            ISO_META["MEDIA"] = filter_media
        except KeyError:
            raise Exception("STEP - Get metadata\nERROR - KeyError during metadata fetch...")
    else:
        raise Exception(f"STEP - Get metadata\nERROR - ISO metadata file missing...\nPath: {yak.meta.global_def.FILE_ISO_INFO_DICT}")


# force a clean rebuild by removing all intermediate files from previous rebuilds
def clean_rebuild():
    print("Cleaning up previous rebuild...")
    shutil.rmtree(yak.meta.global_def.DIR_ISO_MOD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_ENC_MOD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_DEC_MOD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_FILES_MOD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_ARC_BIN_REBUILD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_ARC_DICT_REBUILD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_ARC_REBUILD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_IMG_ICON_WORK, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_IMG_REBUILD, ignore_errors=True)
    shutil.rmtree(yak.meta.global_def.DIR_IMG_WORK, ignore_errors=True)


# rebuild images by first reducing bitdepth with pngquant if needed, and then converting to TXBP/SGT/AVLZ
def rebuild_images():
    print("Compressing/copying modified textures...")
    global WARNINGS
    with open(yak.meta.global_def.FILE_SUBPIC_PROP_DICT, "r") as file_in:
        subpic_prop_dict = json.load(file_in)
    warnings = yak.process.process_image.compress_images(yak.meta.global_def.DIR_REC_IMG_WORK, yak.meta.global_def.DIR_IMG_WORK, subpic_prop_dict)
    WARNINGS += warnings
    print("Converting textures to internal format...")
    with open(yak.meta.global_def.FILE_IMG_PROP_REF_DICT, "r") as file_in:
        img_prop_dict = json.load(file_in)
    yak.process.process_image.convert_images(yak.meta.global_def.DIR_IMG_WORK, yak.meta.global_def.DIR_IMG_REBUILD, img_prop_dict)


# rebuild TALK BIN files from original dicts and modified text files
def rebuild_talk():
    print("Rebuilding TALK dicts...")
    global WARNINGS
    os.makedirs(yak.meta.global_def.DIR_ARC_DICT_REBUILD, exist_ok=True)
    talk_hold = ISO_META["TALK_HOLD"]
    warnings = yak.process.process_talk.rebuild_talk_text(yak.meta.global_def.DIR_ARC_DICT_ORIG, yak.meta.global_def.DIR_ARC_DICT_REBUILD, yak.meta.global_def.DIR_ARC_TALK_ORIG, yak.meta.global_def.DIR_REC_TALK_WORK, do_media=DO_MEDIA, talk_hold=talk_hold)
    WARNINGS += warnings

    print("Compressing/copying modified TALK icons...")
    with open(yak.meta.global_def.FILE_TALK_ICON_PROP_DICT, "r") as file_in:
        icon_prop_dict = json.load(file_in)
    warnings = yak.process.process_image.compress_images(yak.meta.global_def.DIR_REC_IMG_ICON_WORK, yak.meta.global_def.DIR_IMG_ICON_WORK, icon_prop_dict)
    WARNINGS += warnings

    print("Converting TALK icons to internal format...")
    with open(yak.meta.global_def.FILE_TALK_ICON_PROP_DICT, "r") as file_in:
        icon_prop_dict = json.load(file_in)
    icon_dict = yak.process.process_image.convert_icons(yak.meta.global_def.DIR_IMG_ICON_WORK, icon_prop_dict)

    print("Creating write charset using override characters...")
    charset_dict, warnings = yak.talk.talk_chars.create_write_charset(yak.meta.global_def.FILE_CHARSET_WRITE, yak.meta.global_def.DIR_REC_CHAR_OVERRIDE)
    WARNINGS += warnings

    print("Rebuilding TALK BIN files...")
    with open(yak.meta.global_def.FILE_TALK_ICON_REF_DICT, "r") as file_in:
        icon_ref_dict = json.load(file_in)
    warnings = yak.process.process_talk.rebuild_talk_bin(yak.meta.global_def.DIR_ARC_DICT_REBUILD, yak.meta.global_def.DIR_ARC_BIN_REBUILD, charset_dict, icon_dict, icon_ref_dict, ISO_META["ICON_MODE"], do_media=DO_MEDIA, blue_kiryu_talk=(ISO_ID in ["SLUS_217.69", "SLES_552.42"] and yak.meta.global_def.BLUE_KIRYU_TALK))
    WARNINGS += warnings

    if yak.meta.global_def.OPENING_SUB and ISO_ID in ["SLUS_213.48", "SLES_541.71"]:
        print("Patching OPENING subtitles...")
        op_file = yak.meta.opening_sub.generate_opening_scene(ISO_ID)
        path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, "MEDIA2", "AUTHOR", "OPENING", "OPENING_MOVIE.B00")
        os.makedirs(os.path.dirname(path_out), exist_ok=True)
        with open(path_out, "wb") as file_out:
            file_out.write(op_file)


# rebuild ARC/DAT/BIN files
def rebuild_arc():
    print("Rebuilding ARC/DAT/BIN files...")
    with open(yak.meta.global_def.FILE_ARC_BINCOPY_DICT, "r") as file_in:
        bin_path_dict = json.load(file_in)
    with open(yak.meta.global_def.FILE_IMG_PROP_REF_DICT, "r") as file_in:
        img_prop_dict = json.load(file_in)
    arc_done = 0
    for root, dir, files in os.walk(yak.meta.global_def.DIR_ARC_ORIG):
        for f in files:
            if f.lower().endswith("json"):
                path_full_in = os.path.join(root, f)
                path_rel = os.path.relpath(path_full_in, yak.meta.global_def.DIR_ARC_ORIG)
                path_root = path_rel.split(os.path.sep)[0]
                if path_root not in DO_MEDIA:
                    continue
                with open(path_full_in, "r") as file_in:
                    arcdat_dict = json.load(file_in)
                if arcdat_dict["type"] != "MOVE":
                    path_rel = os.path.dirname(path_rel)
                else:
                    path_rel = path_rel[:-5]
                path_full_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, path_rel)
                with open(path_full_in, "r") as file_in:
                    arcdat_dict = json.load(file_in)
                if "GENERIC" in yak.meta.global_def.REBUILD_RESOURCE:
                    generic_path = yak.meta.global_def.DIR_REC_GEN_ARC_WORK
                else:
                    generic_path = ""
                yak.process.process_arc.rebuild_arcdatbin_main(arcdat_dict, path_full_out, yak.meta.global_def.DIR_ARC_BIN_ORIG, yak.meta.global_def.DIR_ARC_BIN_REBUILD, yak.meta.global_def.DIR_IMG_REBUILD, yak.meta.global_def.DIR_ARC_ORIG, bin_path_dict, img_prop_dict, generic_path)
                arc_done += 1
                if arc_done % 10 == 0:
                    print(f"Processed ARC/BIN/DAT files: {arc_done}...")


# copy movie files from work dir depending on rebuild options
def rebuild_movies():
    print("Copying MOVIE files...")
    path_mov = ""
    match yak.meta.global_def.WIDESCREEN_MODE, yak.meta.global_def.LITE_MODE:
        case True, False:
            path_mov = yak.meta.global_def.DIR_REC_MOV_WORK_WS
        case True, True:
            path_mov = yak.meta.global_def.DIR_REC_MOV_WORK_WS_LITE
        case False, False:
            path_mov = yak.meta.global_def.DIR_REC_MOV_WORK_FS
        case False, True:
            path_mov = yak.meta.global_def.DIR_REC_MOV_WORK_FS_LITE
    files_done = 0
    for root, dirs, files in os.walk(path_mov):
        for f in files:
            path_in = os.path.join(root, f)
            path_rel = os.path.relpath(path_in, path_mov)
            path_root = path_rel.split(os.path.sep)[0]
            if path_root not in DO_MEDIA:
                continue
            path_verify = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, path_rel)
            if os.path.isfile(path_verify):
                path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, path_rel)
                os.makedirs(os.path.dirname(path_out), exist_ok=True)
                shutil.copy2(path_in, path_out)
                files_done += 1
                if files_done % 50 == 0:
                    print(f"Processed files: {files_done}...")


# replace the English dub with the original Japanese for Yakuza
def replace_voice_jp():
    if ISO_ID in ["SLUS_213.48", "SLES_541.71"] and "MEDIA2" in DO_MEDIA:
        global WARNINGS, VOICE_LIST
        print("Replacing English dub with Japanese...")
        paths_se = []
        paths = []
        for f in yak.meta.extract_def.VOICE_SE_Y1_JP:
            path_in = os.path.join(yak.meta.global_def.DIR_REC_VOICE_WORK, f)
            if not os.path.isfile(path_in):
                WARNINGS.append(f"STEP - Replace English dub\nERROR - Voice file not found...\nPath: {path_in}\nEnglish dub replacement canceled...")
                return
            path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, f)
            paths_se.append({"path_in": path_in, "path_out": path_out})
        for f in yak.meta.voice_patch_jp.VOICE_JP_B00:
            path_in = os.path.join(yak.meta.global_def.DIR_REC_VOICE_WORK, "MEDIA2", "AUTHOR", f)
            if not os.path.isfile(path_in):
                WARNINGS.append(f"STEP - Replace English dub\nERROR - Voice file not found...\nPath: {path_in}\nEnglish dub replacement canceled...")
                return
        voice_list = b""
        for fkey, f in yak.meta.voice_patch_jp.VOICE_JP_INDEX.items():
            path_in = os.path.join(yak.meta.global_def.DIR_REC_VOICE_WORK, "MEDIA2", "SOUND", f["name"])
            if not os.path.isfile(path_in):
                WARNINGS.append(f"STEP - Replace English dub\nERROR - Voice file not found...\nPath: {path_in}\nEnglish dub replacement canceled...")
                return
            path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, "MEDIA2", "SOUND", f"{f['index_new']:04}.AHX")
            paths.append({"path_in": path_in, "path_out": path_out})
            voice_path = f"Media2\\Sound\\{f['index_new']:04}.ahx".encode("ascii")
            voice_path += (32 - len(voice_path)) * b"\x00"
            voice_list += voice_path
        sound_dir = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, "MEDIA2", "SOUND")
        if os.path.isdir(sound_dir):
            shutil.rmtree(sound_dir)
        files_done = 0
        for f in paths_se + paths:
            os.makedirs(os.path.dirname(f["path_out"]), exist_ok=True)
            shutil.copy2(f["path_in"], f["path_out"])
            files_done += 1
            if files_done % 500 == 0:
                print(f"Processed files: {files_done}...")
        for root, dirs, files in os.walk(os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, "MEDIA2", "AUTHOR")):
            for f in files:
                if f.upper().endswith("B00"):
                    path_orig = os.path.join(root, f)
                    path_rel = os.path.relpath(path_orig, yak.meta.global_def.DIR_FILES_ORIG_MERGE)
                    path_patch = os.path.join(yak.meta.global_def.DIR_REC_VOICE_WORK, path_rel)
                    yak.process.process_scene.switch_voice(path_patch, path_orig, path_rel, yak.meta.global_def.DIR_FILES_ORIG_MERGE, yak.meta.global_def.DIR_FILES_MOD_MERGE, yak.meta.global_def.SUB_TIMING_JP)
                    files_done += 1
                    if files_done % 50 == 0:
                        print(f"Processed files: {files_done}...")
        VOICE_LIST = voice_list + (yak.meta.voice_patch_jp.VOICE_LIST[ISO_ID]["path_length"] - len(voice_list)) * b"\x00"


# replace the korean re-dubbed voice lines for yakuza 2
def replace_voice_kr():
    if ISO_ID in ["SLPM_666.02", "SLPM_666.03", "SLPM_743.01", "SLUS_217.69", "SLES_552.42"] and "MEDIA2" in DO_MEDIA:
        global WARNINGS
        print("Replacing Korean voice lines...")
        paths = []
        for f in yak.meta.extract_def.VOICE_Y2_KR:
            path_in = os.path.join(yak.meta.global_def.DIR_REC_VOICE_WORK, f)
            if not os.path.isfile(path_in):
                WARNINGS.append(f"STEP - Replace Korean voices\nERROR - Voice file not found...\nPath: {path_in}\nKorean voice replacement canceled...")
                return
            path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, f)
            paths.append({"path_in": path_in, "path_out": path_out})
        for f in paths:
            os.makedirs(os.path.dirname(f["path_out"]), exist_ok=True)
            shutil.copy2(f["path_in"], f["path_out"])
        for patch in yak.meta.voice_patch_kr.VOICE_KR:
            path_in = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, patch["path"])
            path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, patch["path"])
            with open(path_in, "rb") as file_in:
                data_in = file_in.read()
            for bin_mod in patch["mod"]:
                data_in = data_in.replace(bytes.fromhex(bin_mod["source"]), bytes.fromhex(bin_mod["replace"]))
            os.makedirs(os.path.dirname(path_out), exist_ok=True)
            with open(path_out, "wb") as file_out:
                file_out.write(data_in)


# copy generic files from work dir
def rebuild_generic():
    print("Copying generic files...")
    files_done = 0
    for root, dirs, files in os.walk(yak.meta.global_def.DIR_REC_GEN_FILES_WORK):
        for f in files:
            path_in = os.path.join(root, f)
            path_rel = os.path.relpath(path_in, yak.meta.global_def.DIR_REC_GEN_FILES_WORK)
            path_root = path_rel.split(os.path.sep)[0]
            if path_root not in DO_MEDIA:
                continue
            path_verify = os.path.join(yak.meta.global_def.DIR_FILES_ORIG_MERGE, path_rel)
            if os.path.isfile(path_verify):
                path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, path_rel)
                os.makedirs(os.path.dirname(path_out), exist_ok=True)
                shutil.copy2(path_in, path_out)
                files_done += 1
                if files_done % 50 == 0:
                    print(f"Processed files: {files_done}...")


# copy internal files from original to mod dir
def rebuild_filecopy_internal():
    print("Copying internal game files...")
    files_done = 0
    for root, dirs, files in os.walk(yak.meta.global_def.DIR_FILES_ORIG_MERGE):
        for f in files:
            path_full = os.path.join(root, f)
            path_rel = os.path.relpath(path_full, yak.meta.global_def.DIR_FILES_ORIG_MERGE)
            path_out = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, path_rel)
            path_root = path_rel.split(os.path.sep)[0]
            if path_root not in DO_MEDIA:
                continue
            if VOICE_LIST and os.path.join("MEDIA2", "SOUND") in path_rel:
                continue
            if not os.path.isfile(path_out):
                os.makedirs(os.path.dirname(path_out), exist_ok=True)
                shutil.copy2(path_full, path_out)
                files_done += 1
                if files_done % 500 == 0:
                    print(f"Processed files: {files_done}...")


# copy internal files from merged mod dir to separate layer dirs
def propagate_layer_files():
    print("Recreating separate layer file structure...")
    with open(yak.meta.global_def.FILE_LAYER_COPY_DICT_L1, "r") as file_in:
        dict_l1 = json.load(file_in)
    with open(yak.meta.global_def.FILE_LAYER_COPY_DICT_L2, "r") as file_in:
        dict_l2 = json.load(file_in)
    layer_split = [{"PATH_OUT": yak.meta.global_def.DIR_FILES_MOD_L1, "DICT": dict_l1}, {"PATH_OUT": yak.meta.global_def.DIR_FILES_MOD_L2, "DICT": dict_l2}]
    files_done = 0
    for layer_vals in layer_split:
        for key, val in layer_vals["DICT"].items():
            for f in val:
                path_root = f.split(os.path.sep)[0]
                if path_root not in DO_MEDIA:
                    continue
                path_full_in = os.path.join(yak.meta.global_def.DIR_FILES_MOD_MERGE, f)
                path_full_out = os.path.join(layer_vals["PATH_OUT"], f)
                os.makedirs(os.path.dirname(path_full_out), exist_ok=True)
                shutil.copy2(path_full_in, path_full_out)
                files_done += 1
                if files_done % 100 == 0:
                    print(f"Processed files: {files_done}...")


# rebuild internal ISO files from new files using mkisofs
def rebuild_internal_iso():
    print("Rebuilding internal ISOs...")
    global OGREDIR_START_L1, OGREDIR_START_L2
    iso_done = 0
    os.makedirs(yak.meta.global_def.DIR_DEC_MOD_L1, exist_ok=True)
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        os.makedirs(yak.meta.global_def.DIR_DEC_MOD_L2, exist_ok=True)
        layer_iso = [{"PATH_IN": yak.meta.global_def.DIR_FILES_MOD_L1, "PATH_OUT": yak.meta.global_def.DIR_DEC_MOD_L1, "PATH_ORIG": yak.meta.global_def.DIR_DEC_ORIG_L1, "CVMS": ISO_META["CVMS_L1"], "OGRESTART": OGREDIR_START_L1},
                     {"PATH_IN": yak.meta.global_def.DIR_FILES_MOD_L2, "PATH_OUT": yak.meta.global_def.DIR_DEC_MOD_L2, "PATH_ORIG": yak.meta.global_def.DIR_DEC_ORIG_L2, "CVMS": ISO_META["CVMS_L2"], "OGRESTART": OGREDIR_START_L2}]
    else:
        layer_iso = [{"PATH_IN": yak.meta.global_def.DIR_FILES_MOD_MERGE, "PATH_OUT": yak.meta.global_def.DIR_DEC_MOD_L1, "PATH_ORIG": yak.meta.global_def.DIR_DEC_ORIG_L1, "CVMS": ISO_META["CVMS_L1"], "OGRESTART": OGREDIR_START_L1}]
    for layer_vals in layer_iso:
        for media_key, do_media in ISO_META["MEDIA"].items():
            path_out = os.path.join(layer_vals["PATH_OUT"], layer_vals["CVMS"][media_key][:-3]+"iso")
            path_orig = os.path.join(layer_vals["PATH_ORIG"], layer_vals["CVMS"][media_key][:-3]+"iso")
            yak.process.process_iso.rebuild_internal_iso(yak.meta.global_def.MKISOFS_TOOL, yak.meta.global_def.FILE_ISO_USE, yak.meta.global_def.FILE_ISO_SORT, layer_vals["PATH_IN"], do_media, path_out)
            with open(path_orig, "rb") as file_orig:
                file_orig.seek(32768)
                data_a = file_orig.read(80)
                file_orig.seek(32958)
                data_b = file_orig.read(1858)
            with open(path_out, "r+b") as file_mod:
                file_mod.seek(32768)
                file_mod.write(data_a)
                file_mod.seek(32926)
                ogredir_start = int.from_bytes(file_mod.read(1))
                file_mod.seek(32958)
                file_mod.write(data_b)
                file_mod.seek(36864)
                file_mod.write(b"\x00" * 2048)
            layer_vals["OGRESTART"][media_key] = ogredir_start
            iso_done += 1
            print(f"Processed internal ISO: {layer_vals['CVMS'][media_key][:-3]+'iso'}...")


# convert internal ISO files to CVMs by scrambling the TOC
def convert_iso_to_cvm():
    print("Converting internal ISOs to CVMs...")
    iso_done = 0
    os.makedirs(yak.meta.global_def.DIR_ENC_MOD_L1, exist_ok=True)
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        os.makedirs(yak.meta.global_def.DIR_ENC_MOD_L2, exist_ok=True)
        layer_iso = [{"PATH_IN": yak.meta.global_def.DIR_DEC_MOD_L1, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L1, "CVMS": ISO_META["CVMS_L1"]},
                     {"PATH_IN": yak.meta.global_def.DIR_DEC_MOD_L2, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L2, "CVMS": ISO_META["CVMS_L2"]}]
    else:
        layer_iso = [{"PATH_IN": yak.meta.global_def.DIR_DEC_MOD_L1, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L1, "CVMS": ISO_META["CVMS_L1"]}]
    for layer_vals in layer_iso:
        for media_key, do_media in ISO_META["MEDIA"].items():
            path_in = os.path.join(layer_vals["PATH_IN"], layer_vals["CVMS"][media_key][:-3]+"iso")
            path_out = os.path.join(layer_vals["PATH_OUT"], layer_vals["CVMS"][media_key])
            path_header = os.path.join(yak.meta.global_def.DIR_CVM_HEADER, layer_vals["CVMS"][media_key][:-3]+"bytes")
            result = yak.process.process_cvm.iso_to_cvm(path_in, path_out, path_header)
            if not result:
                raise Exception
            iso_done += 1
            print(f"Processed CVM: {layer_vals['CVMS'][media_key][:-3]}...")


# recalculate the orgedir indexes from the new files
def rebuild_ogredir():
    print("Rebuilding OGREDIR index files...")
    with open(yak.meta.global_def.FILE_OGREDIR_INIT_L1, "r") as file_in:
        init_dict_L1 = json.load(file_in)
    os.makedirs(yak.meta.global_def.DIR_ENC_MOD_L1, exist_ok=True)
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        with open(yak.meta.global_def.FILE_OGREDIR_INIT_L2, "r") as file_in:
            init_dict_L2 = json.load(file_in)
        os.makedirs(yak.meta.global_def.DIR_ENC_MOD_L2, exist_ok=True)
        layer_ogre = [{"PATH_IN": yak.meta.global_def.DIR_FILES_MOD_L1, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L1, "DICT": init_dict_L1, "OGREDIRS": ISO_META["OGREDIRS_L1"], "OGRESTART": OGREDIR_START_L1},
                      {"PATH_IN": yak.meta.global_def.DIR_FILES_MOD_L2, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L2, "DICT": init_dict_L2, "OGREDIRS": ISO_META["OGREDIRS_L2"], "OGRESTART": OGREDIR_START_L2}]
    else:
        layer_ogre = [{"PATH_IN": yak.meta.global_def.DIR_FILES_MOD_MERGE, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L1, "DICT": init_dict_L1, "OGREDIRS": ISO_META["OGREDIRS_L1"], "OGRESTART": OGREDIR_START_L1}]
    for layer_vals in layer_ogre:
        for media_key, do_media in ISO_META["MEDIA"].items():
            ogre_rebuilder = yak.process.process_ogredir.Ogre_Rebuilder(do_media, layer_vals["PATH_IN"], layer_vals["DICT"][str(media_key)], layer_vals["OGRESTART"][media_key])
            ogre_bytes = ogre_rebuilder.build_ogredir()
            path_out = os.path.join(layer_vals["PATH_OUT"], layer_vals["OGREDIRS"][media_key])
            with open(path_out, "wb") as file_out:
                file_out.write(ogre_bytes)


# copy external files from original to mod dir
def rebuild_filecopy_external():
    print("Copying external game files...")
    files_done = 0
    layer_iso = [{"PATH_IN": yak.meta.global_def.DIR_ENC_ORIG_L1, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L1}]
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        layer_iso.append({"PATH_IN": yak.meta.global_def.DIR_ENC_ORIG_L2, "PATH_OUT": yak.meta.global_def.DIR_ENC_MOD_L2})
    for layer_vals in layer_iso:
        for root, dirs, files in os.walk(layer_vals["PATH_IN"]):
            for f in files:
                path_full = os.path.join(root, f)
                path_rel = os.path.relpath(path_full, layer_vals["PATH_IN"])
                path_out = os.path.join(layer_vals["PATH_OUT"], path_rel)
                if not os.path.isfile(path_out):
                    os.makedirs(os.path.dirname(path_out), exist_ok=True)
                    shutil.copy2(path_full, path_out)
                files_done += 1
                if files_done % 10 == 0:
                    print(f"Processed files: {files_done}...")


# perform any binary modifications to the executables
def modify_executables():
    print("Patching executables...")
    do_mods = []
    if yak.meta.global_def.FLATTEN_ISO:
        do_mods.append("FLATTEN_ISO")
    if yak.meta.global_def.RAISE_SUBTITLES:
        do_mods.append("RAISE_SUBTITLES")
    if yak.meta.global_def.WIDESCREEN_MODE:
        do_mods.append("WIDESCREEN_MODE")
    patch_dict = yak.meta.bin_patch.BIN_PATCH[ISO_ID]
    layer_bin_dirs = [{"DIR_IN": yak.meta.global_def.DIR_ENC_ORIG_L1, "DIR_OUT": yak.meta.global_def.DIR_ENC_MOD_L1}]
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        layer_bin_dirs.append({"DIR_IN": yak.meta.global_def.DIR_ENC_ORIG_L2, "DIR_OUT": yak.meta.global_def.DIR_ENC_MOD_L2})
    for layer_bin_dir in layer_bin_dirs:
        for binkey, binval in patch_dict.items():
            path_full_in = os.path.join(layer_bin_dir["DIR_IN"], ISO_META[binkey])
            if not os.path.isfile(path_full_in):
                continue
            with open(path_full_in, "rb") as file_in:
                data_bin = file_in.read()
            for do_mod in do_mods:
                if do_mod not in binval:
                    continue
                for patch_pos, patch_data in binval[do_mod].items():
                    patch_data = bytes.fromhex(patch_data)
                    data_bin = data_bin[:patch_pos] + patch_data + data_bin[patch_pos + len(patch_data):]
            if VOICE_LIST:
                num_index = yak.meta.voice_patch_jp.VOICE_LIST[ISO_ID]["num_index"]
                num_index_pos = yak.meta.voice_patch_jp.VOICE_LIST[ISO_ID]["num_index_pos"]
                index_src_pos = yak.meta.voice_patch_jp.VOICE_LIST[ISO_ID]["index_src_pos"]
                index_trg_pos = yak.meta.voice_patch_jp.VOICE_LIST[ISO_ID]["index_trg_pos"]
                path_src_pos = yak.meta.voice_patch_jp.VOICE_LIST[ISO_ID]["path_src_pos"]
                # modify number of voice files
                data_bin = data_bin[:num_index_pos] + (num_index).to_bytes(2, byteorder="little") + data_bin[num_index_pos + 2:]
                # add voice index
                i = 0
                for fkey, f in yak.meta.voice_patch_jp.VOICE_JP_INDEX.items():
                    data_bin = data_bin[:index_src_pos + (f["index_new"] * 4)] + (index_trg_pos + (i * 32)).to_bytes(4, byteorder="little") + data_bin[index_src_pos + (f["index_new"] * 4) + 4:]
                    i += 1
                # add voice path list
                data_bin = data_bin[:path_src_pos] + VOICE_LIST + data_bin[path_src_pos + len(VOICE_LIST):]
            path_full_out = os.path.join(layer_bin_dir["DIR_OUT"], ISO_META[binkey])
            with open(path_full_out, "wb") as file_out:
                file_out.write(data_bin)


# rebuild the main game ISO file
def rebuild_main_iso():
    os.makedirs(yak.meta.global_def.DIR_ISO_MOD, exist_ok=True)
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        print("Rebuilding main game ISO (Layer 1)...")
    else:
        print("Rebuilding main game ISO...")
    with open(yak.meta.global_def.FILE_ISO_HEADER_L1, "rb") as file_in:
        iso_header = file_in.read()
    with open(yak.meta.global_def.FILE_ISO_FOOTER_L1, "rb") as file_in:
        iso_footer = file_in.read()
    with open(yak.meta.global_def.FILE_LBA_ISO_L1, "r") as file_in:
        file_lba_list = json.load(file_in)
    with open(yak.meta.global_def.FILE_DIR_REC_L1, "r") as file_in:
        dir_rec_list = json.load(file_in)
    with open(yak.meta.global_def.FILE_LBA_UDF_L1, "r") as file_in:
        file_lba_udf_dict = json.load(file_in)
    result = yak.process.process_iso.rebuild_iso_lba(yak.meta.global_def.DIR_ENC_MOD_L1, yak.meta.global_def.FILE_ISO_MOD_L1, iso_header, iso_footer, file_lba_list, dir_rec_list, file_lba_udf_dict)
    if not result:
        raise Exception
    if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
        print("Rebuilding main game ISO (Layer 2)...")
        with open(yak.meta.global_def.FILE_ISO_HEADER_L2, "rb") as file_in:
            iso_header = file_in.read()
        with open(yak.meta.global_def.FILE_ISO_FOOTER_L2, "rb") as file_in:
            iso_footer = file_in.read()
        with open(yak.meta.global_def.FILE_LBA_ISO_L2, "r") as file_in:
            file_lba_list = json.load(file_in)
        with open(yak.meta.global_def.FILE_DIR_REC_L2, "r") as file_in:
            dir_rec_list = json.load(file_in)
        with open(yak.meta.global_def.FILE_LBA_UDF_L2, "r") as file_in:
            file_lba_udf_dict = json.load(file_in)
        result = yak.process.process_iso.rebuild_iso_lba(yak.meta.global_def.DIR_ENC_MOD_L2, yak.meta.global_def.FILE_ISO_MOD_L2, iso_header, iso_footer, file_lba_list, dir_rec_list, file_lba_udf_dict)
        if not result:
            raise Exception
        print("Merging main game ISO layers...")
        with open(yak.meta.global_def.FILE_ISO_MOD_MERGE, "wb") as iso_mod_merge:
            with open(yak.meta.global_def.FILE_ISO_MOD_L1, "rb") as iso_mod_L1:
                iso_mod_L1.seek(0)
                while True:
                    chunk = iso_mod_L1.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    iso_mod_merge.write(chunk)
            with open(yak.meta.global_def.FILE_ISO_MOD_L2, "rb") as iso_mod_L2:
                iso_mod_L2.seek(32768)
                while True:
                    chunk = iso_mod_L2.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    iso_mod_merge.write(chunk)
        os.remove(yak.meta.global_def.FILE_ISO_MOD_L1)
        os.remove(yak.meta.global_def.FILE_ISO_MOD_L2)
    else:
        if os.path.isfile(yak.meta.global_def.FILE_ISO_MOD_MERGE):
            os.remove(yak.meta.global_def.FILE_ISO_MOD_MERGE)
        os.rename(yak.meta.global_def.FILE_ISO_MOD_L1, yak.meta.global_def.FILE_ISO_MOD_MERGE)


# rebuild ISO according to rebuild options
def rebuild():
    try:
        get_metadata()
        if yak.meta.global_def.CLEAN_REBUILD:
            clean_rebuild()
        if "TALK" in yak.meta.global_def.REBUILD_RESOURCE:
            rebuild_talk()
        if "IMAGE" in yak.meta.global_def.REBUILD_RESOURCE:
            rebuild_images()
        rebuild_arc()
        if yak.meta.global_def.REPLACE_VOICE_JP:
            replace_voice_jp()
        if yak.meta.global_def.REPLACE_VOICE_KR:
            replace_voice_kr()
        if "MOVIE" in yak.meta.global_def.REBUILD_RESOURCE:
            rebuild_movies()
        if "GENERIC" in yak.meta.global_def.REBUILD_RESOURCE:
            rebuild_generic()
        rebuild_filecopy_internal()
        if HAS_LAYERS and not yak.meta.global_def.FLATTEN_ISO:
            propagate_layer_files()
        rebuild_internal_iso()
        convert_iso_to_cvm()
        rebuild_ogredir()
        rebuild_filecopy_external()
        modify_executables()
        rebuild_main_iso()
    except Exception as e:
        print("---------------- ERROR ----------------")
        print("Rebuild canceled due to errors...")
        raise e
    if WARNINGS:
        for w in WARNINGS:
            print("---------------- WARNING ----------------")
            print(w)
        print("Rebuild completed, with warnings...")
    else:
        print("Rebuild completed...")
    print(f"Rebuilt ISO: {yak.meta.global_def.FILE_ISO_MOD_MERGE}")


# check for path to ini file, either first argument or yak_pref.ini if not supplied
# initialize global variables
def main(argv):
    if len(argv) == 1:
        path_ini = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yak_pref.ini")
        if not os.path.isfile(path_ini):
            print("No ini file specified, and yak_pref.ini does not exist, exiting...")
            return
    else:
        path_ini = argv[1]
        if not os.path.isfile(path_ini):
            print("Specified ini file does not exist, exiting...")
            print(f"Path {path_ini}")
            return
    config = configparser.ConfigParser()
    config.read(path_ini)
    work_dir = os.path.join(config["Path"]["WORK"], os.path.splitext(os.path.basename(config["Path"]["ISO"]))[0].lower().replace(" ", "_"))
    if not os.path.isdir(work_dir):
        print("Specified work directory does not exist, exiting...")
        print(f"Path {work_dir}")
        return
    if not os.path.isfile(config["Path"]["MKISOFS"]):
        print("Specified mkisofs program does not exist, exiting...")
        print(f"Path {config["Path"]["MKISOFS"]}")
        return
    yak.meta.global_def.init(config["Path"])
    yak.meta.global_def.init_rebuild(config["Rebuild"])
    rebuild()


if __name__ == "__main__":
    main(sys.argv)
    sys.exit()
