import copy
import json
import os
import re

import png

import yak.meta.global_def
import yak.meta.voice_patch_jp
import yak.process.process_image
import yak.talk.talk_chars
import yak.talk.talk_decoder


# extract all chars from a set of TALK files to single/double-width json
def extract_complete_charset(path_in, path_out):
    all_single = []
    all_wide = []
    i = 0
    imax = 999999999
    for root, dirs, files in os.walk(path_in):
        for f in files:
            if i > imax:
                break
            if not f.upper().endswith(".BIN"):
                continue
            path_full = os.path.join(root, f)
            talk_dec = yak.talk.talk_decoder.TALK_Decoder(path_full, {}, {})
            if talk_dec.find_talk_file():
                chars_single, chars_wide = talk_dec.find_chars(return_chars=True)
                for c in chars_single:
                    if c not in all_single:
                        all_single.append(c)
                for c in chars_wide:
                    if c not in all_wide:
                        all_wide.append(c)
            i += 1
    yak.talk.talk_chars.write_char_pngs(all_single, all_wide, yak.meta.global_def.DIR_REC_CHAR_EXTRACT)
    all_single_hex = []
    all_wide_hex = []
    for c in all_single:
        all_single_hex.append(c.hex())
    for c in all_wide:
        all_wide_hex.append(c.hex())
    with open(os.path.join(path_out, "single.json"), "w") as file_out:
        json.dump(all_single_hex, file_out, indent=4, ensure_ascii=True)
    with open(os.path.join(path_out, "wide.json"), "w") as file_out:
        json.dump(all_wide_hex, file_out, indent=4, ensure_ascii=True)


# merge multiple extracted single/double-width charsets
def merge_charsets(charset_path_list_single, charset_path_list_wide, path_out):
    os.makedirs(path_out, exist_ok=True)
    charset_list_single = []
    charset_list_wide = []
    for csp in charset_path_list_single:
        with open(csp, "r") as file_in:
            data_in_hex = json.load(file_in)
        data_in = []
        for c in data_in_hex:
            data_in.append(bytes.fromhex(c))
        charset_list_single.append(data_in)
    for csp in charset_path_list_wide:
        with open(csp, "r") as file_in:
            data_in_hex = json.load(file_in)
        data_in = []
        for c in data_in_hex:
            data_in.append(bytes.fromhex(c))
        charset_list_wide.append(data_in)
    charset_all_single = []
    charset_all_wide = []
    for cs in charset_list_single:
        for c in cs:
            if c not in charset_all_single:
                charset_all_single.append(c)
    for cs in charset_list_wide:
        for c in cs:
            if c not in charset_all_wide:
                charset_all_wide.append(c)
    charset_all_single_hex = []
    charset_all_wide_hex = []
    for c in charset_all_single:
        charset_all_single_hex.append(c.hex())
    for c in charset_all_wide:
        charset_all_wide_hex.append(c.hex())
    with open(os.path.join(path_out, "single.json"), "w") as file_out:
        json.dump(charset_all_single_hex, file_out, indent=4, ensure_ascii=True)
    with open(os.path.join(path_out, "wide.json"), "w") as file_out:
        json.dump(charset_all_wide_hex, file_out, indent=4, ensure_ascii=True)
    yak.talk.talk_chars.write_char_pngs(charset_all_single, charset_all_wide, path_out)


# extract text lines to complete png images
def extract_image_lines(path_in, path_out, icon_mode):
    i = 0
    imax = 9999999999
    for root, dirs, files in os.walk(path_in):
        for f in files:
            if i > imax:
                break
            if not f.upper().endswith(".BIN"):
                continue
            path_full_in = os.path.join(root, f)
            path_rel = os.path.relpath(path_full_in, path_in)
            path_full_out = os.path.join(path_out, path_rel)
            talk_dec = yak.talk.talk_decoder.TALK_Decoder(path_full_in, icon_mode)
            if talk_dec.find_talk_file():
                try:
                    talk_dec.set_pal_mode(False)
                    chars_single, chars_wide = talk_dec.find_chars(return_chars=True)
                    talk_dec.create_local_charset()
                    talk_dec.extract_langs()
                    talk_dec.calc_line_strings()
                    talk_dec.write_line_png(path_full_out)
                except KeyError:
                    talk_dec = yak.talk.talk_decoder.TALK_Decoder(path_full_in, icon_mode)
                    talk_dec.find_talk_file()
                    talk_dec.set_pal_mode(True)
                    chars_single, chars_wide = talk_dec.find_chars(return_chars=True)
                    talk_dec.create_local_charset()
                    talk_dec.extract_langs()
                    talk_dec.calc_line_strings()
                    talk_dec.write_line_png(path_full_out)
                yak.talk.talk_chars.write_char_pngs(chars_single, chars_wide, path_full_out)
            i += 1


# extract data from TALK files to json
def extract_talk_dict(path_in, path_out, icon_mode, iso_id=""):
    i = 0
    imax = 999999999
    complete_charset = {}
    write_charset = {}
    unknkown_chars = []
    icon_list = []
    icon_ref_dict = {}
    icon_prop_dict = {}
    warnings = []
    for root, dirs, files in os.walk(path_in):
        for f in files:
            if i >= imax:
                break
            if not f.upper().endswith(".BIN"):
                continue
            # if "TALK_FAILED.BIN" not in f:
            #     continue
            path_full_in = os.path.join(root, f)
            path_rel = os.path.relpath(path_full_in, path_in)
            path_full_out = os.path.join(path_out, path_rel)
            talk_dec = yak.talk.talk_decoder.TALK_Decoder(path_full_in, icon_mode, iso_id=iso_id)
            if talk_dec.find_talk_file():
                if i and i % 100 == 0:
                    print(f"Extracted TALK files: {i}...")
                try:
                    talk_dec.set_pal_mode(False)
                    talk_dec.find_chars()
                    talk_dec.create_local_charset()
                    talk_dec.extract_langs()
                    talk_dec.calc_line_strings()
                except KeyError:
                    talk_dec = yak.talk.talk_decoder.TALK_Decoder(path_full_in, icon_mode, iso_id=iso_id)
                    talk_dec.find_talk_file()
                    talk_dec.set_pal_mode(True)
                    talk_dec.find_chars()
                    talk_dec.create_local_charset()
                    talk_dec.extract_langs()
                    talk_dec.calc_line_strings()
                talk_dec.calc_meta_lines()
                talk_dec.write_talk_struct(path_full_out)
                talk_icons = talk_dec.get_icons()
                local_charset = talk_dec.get_local_charset()
                # extract chars
                for localkey, localval in local_charset.items():
                    if localval["utf8"] == chr(10062):
                        if localval["img_bytes"] not in unknkown_chars:
                            unknkown_chars.append(localval["img_bytes"])
                    elif localval["utf8"] not in complete_charset:
                        complete_charset[localval["utf8"]] = [{"img_bytes": localval["img_bytes"], "dupnum": localval["dupnum"]}]
                    else:
                        add_char = True
                        for ccval in complete_charset[localval["utf8"]]:
                            if ccval["dupnum"] == localval["dupnum"]:
                                add_char = False
                                break
                        if add_char:
                            complete_charset[localval["utf8"]].append({"img_bytes": localval["img_bytes"], "dupnum": localval["dupnum"]})
                # extract embedded icons
                if talk_icons:
                    icon_ref = []
                    for ti in talk_icons:
                        try:
                            icon_index = icon_list.index(ti)
                        except ValueError:
                            icon_list.append(ti)
                            icon_index = icon_list.index(ti)
                        icon_ref.append(icon_index)
                    icon_ref_dict[path_rel] = icon_ref
                i += 1
    
    if complete_charset:
        print("Extracting all chars to PNG...")
        for cckey, ccval in complete_charset.items():
            sortval = sorted(ccval, key=lambda x: x["dupnum"])
            write_charset[ord(cckey)] = sortval[0]["img_bytes"].hex()
            for val in sortval:
                charbytes_array, writer = yak.talk.talk_chars.raw_to_png(val["img_bytes"], int(len(val["img_bytes"])/24), 24)
                path_file_out = os.path.join(yak.meta.global_def.DIR_REC_CHAR_EXTRACT, f"{ord(cckey):08}{f'_{val["dupnum"]}' if val['dupnum'] != 0 else ''}.png")
                with open(path_file_out, "wb") as file_out:
                    writer.write(file_out, charbytes_array)
        print("Saving char dict for rebuild...")
        with open(yak.meta.global_def.FILE_CHARSET_WRITE, "w") as file_out:
            json.dump(write_charset, file_out, indent=4, ensure_ascii=True)

    if unknkown_chars:
        print("Extracting unknown chars to PNG...")
        warnings.append(f"STEP - Extract TALK files\nERROR - Unknown characters detected...\nCheck {yak.meta.global_def.DIR_REC_CHAR_UNKNOWN} for unknown char bitmaps...")
        zfill_num = int(len(unknkown_chars)/10)
        i = 0
        for val in unknkown_chars:
            charbytes_array, writer = yak.talk.talk_chars.raw_to_png(val, int(len(val)/24), 24)
            path_file_out = os.path.join(yak.meta.global_def.DIR_REC_CHAR_UNKNOWN, f"{i:0{zfill_num}}.png")
            with open(path_file_out, "wb") as file_out:
                writer.write(file_out, charbytes_array)
            i += 1
    
    if icon_list:
        os.makedirs(yak.meta.global_def.DIR_REC_IMG_ICON_ORIG, exist_ok=True)
        os.makedirs(yak.meta.global_def.DIR_REC_IMG_ICON_WORK, exist_ok=True)
        os.makedirs(yak.meta.global_def.DIR_IMG, exist_ok=True)
        i = 0
        for ti in icon_list:
            png_data = yak.process.process_image.txbp_to_png(ti)
            j = 0
            for png_sp in png_data:
                if png_sp["image_type"] == yak.process.process_image.IMAGE_TYPE_8B_GSA:
                    writer = png.Writer(width=png_sp["resx"], height=png_sp["resy"], bitdepth=png_sp["bitdepth"], greyscale=True, alpha=True)
                elif png_sp["image_type"] == yak.process.process_image.IMAGE_TYPE_8B_RGBA:
                    writer = png.Writer(width=png_sp["resx"], height=png_sp["resy"], bitdepth=png_sp["bitdepth"], greyscale=False, alpha=True)
                else:
                    writer = png.Writer(width=png_sp["resx"], height=png_sp["resy"], bitdepth=png_sp["bitdepth"], palette=png_sp["palette"])
                pixel_rows = writer.array_scanlines(png_sp["pixels"])
                path_out = os.path.join(yak.meta.global_def.DIR_REC_IMG_ICON_ORIG, f"{i:04}{'_{j}' if len(png_data) > 1 else ''}.png")
                with open(path_out, "wb") as file_out:
                    writer.write(file_out, pixel_rows)
                icon_prop_dict[os.path.basename(path_out)] = {"header": png_sp["header"], "resx": png_sp["resx"], "resy": png_sp["resy"], "bitdepth": png_sp["bitdepth"], "planes": png_sp["planes"], "image_type": png_sp["image_type"], "palette_size": len(png_sp["palette"])}
                j += 1
            i += 1
        with open(yak.meta.global_def.FILE_TALK_ICON_PROP_DICT, "w") as file_out:
            json.dump(icon_prop_dict, file_out, indent=4, ensure_ascii=True)
        with open(yak.meta.global_def.FILE_TALK_ICON_REF_DICT, "w") as file_out:
            json.dump(icon_ref_dict, file_out, indent=4, ensure_ascii=True)
    return warnings


# consolidate and convert a json dict to editable text file
def write_talk_text_from_json(path_in, path_rel, path_out_full, path_out_clean, prev_names, prev_lines, dup_mode=0):
    with open(path_in, encoding="utf8", mode="r") as file_in:
        file_dict = json.load(file_in)
    if dup_mode == 2:
        bypass_names = prev_names
        bypass_lines = prev_lines
        prev_names = {}
        prev_lines = {}
    for text_struct in file_dict["text_structs"]:
        lang_id = text_struct["lang_id"]
        if lang_id not in prev_names:
            prev_names[lang_id] = {}
        if lang_id not in prev_lines:
            prev_lines[lang_id] = {}
        names_full = []
        names_dup = []
        names_clean = []
        lines_full = []
        lines_dup = []
        lines_clean = []
        name_id = 0
        for name in text_struct["names"]:
            names_full.append(f"{name_id: <2} ::: {name}")
            if dup_mode == 1:
                names_clean.append(f"{name_id: <2} ::: {name}")
            else:
                try:
                    dup_name = prev_names[lang_id][name]
                    names_dup.append(f"{name_id} ::: {dup_name['file']} ::: {dup_name['name_id']} ::: {name}")
                except KeyError:
                    names_clean.append(f"{name_id: <2} ::: {name}")
                    prev_names[lang_id][name] = {"file": path_rel[:-5], "name_id": name_id}
            name_id += 1
        for text_section in text_struct["text_sections"]:
            for text_maingroup in text_section["text_maingroups"]:
                for text_subgroup in text_maingroup["text_subgroups"]:
                    line = text_subgroup["main_line"]
                    line_id = text_subgroup["full_id"]
                    lines_full.append(f"{line_id: <9} ::: {line}")
                    if dup_mode == 1:
                        lines_clean.append(f"{line_id: <9} ::: {line}")
                    else:
                        try:
                            dup_line = prev_lines[lang_id][line]
                            lines_dup.append(f"{line_id} ::: {dup_line['file']} ::: {dup_line['line_id']} ::: {line}")
                        except KeyError:
                            if line:
                                lines_clean.append(f"{line_id: <9} ::: {line}")
                                prev_lines[lang_id][line] = {"file": path_rel[:-5], "line_id": line_id}
                            else:
                                lines_dup.append(f"{line_id} :::  :::  ::: ")
        w_dict = {}
        w_dict["names_full"] = {"str_list": names_full, "path": path_out_full}
        w_dict["names_dup"] = {"str_list": names_dup, "path": path_out_full}
        w_dict["names_clean"] = {"str_list": names_clean, "path": path_out_clean}
        w_dict["lines_full"] = {"str_list": lines_full, "path": path_out_full}
        w_dict["lines_dup"] = {"str_list": lines_dup, "path": path_out_full}
        w_dict["lines_clean"] = {"str_list": lines_clean, "path": path_out_clean}
        w_dict["lines_override"] = {"str_list": [], "path": path_out_full}
        for wkey, wval in w_dict.items():
            path_out_file = f"{os.path.join(wval['path'], path_rel)[:-5]}_{lang_id}_{wkey}.txt"
            if wval["str_list"] or wkey == "lines_override":
                os.makedirs(os.path.dirname(path_out_file), exist_ok=True)
                with open(path_out_file, encoding="utf8", mode="w") as file_out:
                    file_out.write("\n".join(wval["str_list"]))
    if dup_mode == 2:
        return bypass_names, bypass_lines
    else:
        return prev_names, prev_lines


# consolidate and convert all json dicts to editable text files
def extract_talk_text(path_in, path_out_full, path_out_clean, talk_skip=[], talk_self=[], talk_hold=[]):
    i = 0
    imax = 999999999
    for mroot, mdirs, mfiles in os.walk(path_in):
        for md in mdirs:
            for smroot, smdirs, smfiles in os.walk(os.path.join(mroot, md)):
                for smd in smdirs:
                    hold_files = []
                    media_names = {}
                    media_lines = {}
                    for root, dirs, files in os.walk(os.path.join(smroot, smd)):
                        dirs.sort()
                        files.sort()
                        for f in files:
                            if i >= imax:
                                break
                            if not f.lower().endswith(".json"):
                                continue
                            path_in_full = os.path.join(root, f)
                            path_rel = os.path.relpath(path_in_full, path_in)
                            if any(x in path_rel for x in talk_hold):
                                hold_files.append((path_in_full, path_rel))
                                continue
                            if i and i % 100 == 0:
                                print(f"Consolidated TALK files: {i}...")
                            if any(x in path_rel for x in talk_skip):
                                media_names, media_lines = write_talk_text_from_json(path_in_full, path_rel, path_out_full, path_out_clean, media_names, media_lines, dup_mode=1)
                            elif any(x in path_rel for x in talk_self):
                                media_names, media_lines = write_talk_text_from_json(path_in_full, path_rel, path_out_full, path_out_clean, media_names, media_lines, dup_mode=2)
                            else:
                                media_names, media_lines = write_talk_text_from_json(path_in_full, path_rel, path_out_full, path_out_clean, media_names, media_lines, dup_mode=0)
                            i += 1
                    for path_in_full, path_rel in hold_files:
                        if i and i % 100 == 0:
                            print(f"Consolidated TALK files: {i}...")
                        media_names, media_lines = write_talk_text_from_json(path_in_full, path_rel, path_out_full, path_out_clean, media_names, media_lines, dup_mode=0)
                        i += 1
                break
        break


# make characters within {i} tags italic by assigning the decimal unicode value of the character + 6000
# requires italic custom override bitmap characters with those values, and precludes use of any of those actual unicode characters
def italicize_line(line):
	split_line = re.split(r"{i}", line)
	reconst_line = ""
	i = 0
	for part_line in split_line:
		if i % 2 != 0:
			new_part_line = ""
			for c in part_line:
				if ord(c) == 32:
					new_part_line += c
				else:
					new_part_line += chr(ord(c) + 6000)
			part_line = new_part_line
		reconst_line += part_line
		i += 1
	return reconst_line


# rebuild all edited text files to json dicts
def rebuild_talk_text(path_in_dict, path_out_dict, path_in_txt_orig, path_in_txt_clean, do_media=[], talk_hold=[]):
    warnings = []
    re_div_clean = re.compile(r"([0-9_]+) +::: (.*)")
    re_div_dup = re.compile(r"(.*) ::: (.*) ::: (.*) ::: (.*)")
    all_names = {}
    all_lines = {}
    do_paths = []
    hold_paths = []
    # collect all paths first so files in talk_hold can be moved later, according to how they were extracted
    for root, dirs, files in os.walk(path_in_dict):
        dirs.sort()
        files.sort()
        for f in files:
            if not f.lower().endswith(".json"):
                continue
            path_in_full = os.path.join(root, f)
            path_rel = os.path.relpath(path_in_full, path_in_dict)[:-5]
            path_root = path_rel.split(os.path.sep)[0]
            if path_root not in do_media:
                continue
            if any(x in path_rel for x in talk_hold):
                hold_paths.append((path_in_full, path_rel))
            else:
                do_paths.append((path_in_full, path_rel))
    do_paths.extend(hold_paths)

    talk_done = 0
    for path_in_full, path_rel in do_paths:
        with open(path_in_full, encoding="utf8", mode="r") as file_in:
            file_dict = json.load(file_in)
        for text_struct in file_dict["text_structs"]:
            lang_id = text_struct["lang_id"]
            if lang_id not in all_names:
                all_names[lang_id] = {}
            if lang_id not in all_lines:
                all_lines[lang_id] = {}
            all_names[lang_id][path_rel] = {}
            all_lines[lang_id][path_rel] = {}
            lines_dict = {}
            for text_section in text_struct["text_sections"]:
                for text_maingroup in text_section["text_maingroups"]:
                    for text_subgroup in text_maingroup["text_subgroups"]:
                        lines_dict[text_subgroup["full_id"]] = text_subgroup
            r_dict = {}
            r_dict["names_full"] = {"str_list": [], "path": path_in_txt_orig}
            r_dict["names_dup"] = {"str_list": [], "path": path_in_txt_orig}
            r_dict["names_clean"] = {"str_list": [], "path": path_in_txt_clean}
            r_dict["names_override"] = {"str_list": [], "path": path_in_txt_clean}
            r_dict["lines_full"] = {"str_list": [], "path": path_in_txt_orig}
            r_dict["lines_dup"] = {"str_list": [], "path": path_in_txt_orig}
            r_dict["lines_clean"] = {"str_list": [], "path": path_in_txt_clean}
            r_dict["lines_override"] = {"str_list": [], "path": path_in_txt_clean}
            for rkey, rval in r_dict.items():
                path_in_file = f"{os.path.join(rval['path'], path_rel)}_{lang_id}_{rkey}.txt"
                if os.path.isfile(path_in_file):
                    with open(path_in_file, encoding="utf8", mode="r") as file_in:
                        rval["str_list"] = file_in.read().splitlines()
            names_full = r_dict["names_full"]["str_list"]
            names_dup = r_dict["names_dup"]["str_list"]
            names_clean = r_dict["names_clean"]["str_list"]
            names_override = r_dict["names_override"]["str_list"]
            lines_full = r_dict["lines_full"]["str_list"]
            lines_dup = r_dict["lines_dup"]["str_list"]
            lines_clean = r_dict["lines_clean"]["str_list"]
            lines_override = r_dict["lines_override"]["str_list"]
            names_rebuild = {}
            lines_rebuild = {}
            names_override_dict = {}
            lines_override_dict = {}
            for name_str in names_override:
                name_id, name = re_div_clean.match(name_str).group(1,2)
                names_override_dict[name_id] = name
            for name_str in names_clean:
                name_id, name = re_div_clean.match(name_str).group(1,2)
                names_rebuild[name_id] = name
                try:
                    name = names_override_dict[name_id]
                except KeyError:
                    pass
                all_names[lang_id][path_rel][name_id] = name
            for name_str in names_dup:
                name_id, dup_path, dup_id = re_div_dup.match(name_str).group(1,2,3)
                if dup_path:
                    name = all_names[lang_id][dup_path][dup_id]
                else:
                    name = ""
                if name_id not in names_rebuild:
                    names_rebuild[name_id] = name
            for line_str in lines_override:
                line_id, line = re_div_clean.match(line_str).group(1,2)
                lines_override_dict[line_id] = line
            for line_str in lines_clean:
                line_id, line = re_div_clean.match(line_str).group(1,2)
                lines_rebuild[line_id] = line
                try:
                    line = lines_override_dict[line_id]
                except KeyError:
                    pass
                all_lines[lang_id][path_rel][line_id] = line
            for line_str in lines_dup:
                line_id, dup_path, dup_id = re_div_dup.match(line_str).group(1,2,3)
                if dup_path:
                    try:
                        line = all_lines[lang_id][dup_path][dup_id]
                    except KeyError as e:
                        em = f"STEP - Rebuild TALK text\nERROR - Line in TALK file is referencing a source line that doesn't exist...\nPath: {path_in_full}\nLine ID: {line_id}\nSource file path: {dup_path}\nSource line ID: {dup_id}\n"
                        em += "Possible error in the Python os.walk order, or mismatch between extraction/rebuild metadata..."
                        raise Exception(em)
                else:
                    line = ""
                if line_id not in lines_rebuild:
                    lines_rebuild[line_id] = line
            for name_id, name in names_rebuild.items():
                text_struct["names"][int(name_id)] = name
            
            # remove all old entries and create new ones if replacing the JP subtitle timings, to prevent original lines in the json from reappearing
            if yak.meta.global_def.REPLACE_VOICE_JP and yak.meta.global_def.SUB_TIMING_JP and os.path.basename(os.path.dirname(path_rel)) in  yak.meta.voice_patch_jp.SUB_JP_BIN:
                text_struct["text_sections"] = []
                for line_id, line in lines_rebuild.items():
                    split_id = line_id.split("_")
                    t_sec = int(split_id[0])
                    t_mg = int(split_id[1])
                    t_sg = int(split_id[2])
                    if t_sec > (len(text_struct["text_sections"]) - 1):
                        text_struct["text_sections"].append({"id": t_sec, "bytes": f"{t_sec.to_bytes(2, byteorder='little').hex()}000100000000", "text_maingroups": []})
                    if t_mg > (len(text_struct["text_sections"][t_sec]["text_maingroups"]) - 1):
                        text_struct["text_sections"][t_sec]["text_maingroups"].append({"id": t_sec, "bytes": "000000000000000000010f6400040000", "text_subgroups": []})
                    line_entry = {"id": t_sg, "full_id": line_id, "bytes": "000116160000000000000000", "main_line": line, "main_line_spec_op": "00", "meta_lines": [], "saved_meta_lines": []}
                    text_struct["text_sections"][t_sec]["text_maingroups"][t_mg]["text_subgroups"].append(line_entry)
                for t_sec in text_struct["text_sections"]:
                    for t_mg in t_sec["text_maingroups"]:
                        if len(t_mg["text_subgroups"]) > 1:
                            t_mg["bytes"] = "000000000000000000020f6400040000"
                            for t_sg in t_mg["text_subgroups"]:
                                t_sg["bytes"] = "000112160000000000000000"
            else:
                for line_id, line in lines_rebuild.items():
                    try:
                        # lines_dict[line_id]["main_line"] = italicize_line(line) # process internal italic tag
                        lines_dict[line_id]["main_line"] = line
                    # if new lines has been added for the edited text, copy values from the previous one, and create a new entry
                    except KeyError:
                        if line == "Locate(BottomCenter)" or line == " " or line == "":
                            continue
                        # disable adding new lines outside subtitles
                        if not path_rel.startswith("MEDIA2"):
                            em = f"STEP - Rebuild TALK text\nERROR - Line in TALK file doesn't exist in the original...\nPath: {path_in_full}\nLine ID: {line_id}\nLine: {line}\n"
                            em += "Check the line ID, that the formatting is correct, and that no new lines have been added..."
                            raise Exception(em)
                        split_id = line_id.split("_")
                        t_sec = int(split_id[0])
                        t_mg = int(split_id[1])
                        t_sg = int(split_id[2])
                        parent_mg = text_struct["text_sections"][t_sec]["text_maingroups"][t_mg]
                        try:
                            prev_sg = parent_mg["text_subgroups"][t_sg-1]
                            # if not path_rel.startswith("MEDIA2"):
                            #     wm = f"STEP - Rebuild TALK text\nWARNING - Line in TALK file doesn't exist in the original...\nPath: {path_in_full}\nLine ID: {line_id}\nLine: {line}\n"
                            #     wm += f"The new line was added, but this might break some dialogue scripts, so make sure it's not a mistake..."
                            #     warnings.append(wm)
                        except IndexError:
                            em = f"STEP - Rebuild TALK text\nERROR - Line in TALK file doesn't exist in the original...\nPath: {path_in_full}\nLine ID: {line_id}\nLine: {line}\n"
                            em += "Check the line ID, that the formatting is correct, and that no new lines have been added..."
                            raise Exception(em)
                        new_sg = copy.deepcopy(prev_sg)
                        new_sg["id"] = t_sg
                        new_sg["full_id"] = line_id
                        # new_sg["main_line"] = italicize_line(line) # process internal italic tag
                        new_sg["main_line"] = line
                        parent_mg["text_subgroups"].append(new_sg)


        path_out_file = f"{os.path.join(path_out_dict, path_rel)}.json"
        os.makedirs(os.path.dirname(path_out_file), exist_ok=True)
        with open(path_out_file, encoding="utf8", mode="w") as file_out:
            json.dump(file_dict, file_out, indent=4, ensure_ascii=False)
        talk_done += 1
        if talk_done % 50 == 0:
            print(f"Processed TALK files: {talk_done}...")
    return warnings


def rebuild_talk_bin(path_in_dict, path_out_bin, charset_dict, icon_dict, icon_ref_dict, icon_mode, do_media=[], blue_kiryu_talk=False):
    bin_done = 0
    bin_max = 999999
    all_missing_chars = set()
    warnings = []
    for root, dirs, files in os.walk(path_in_dict):
        for f in files:
            if not f.lower().endswith("json"):
                continue
            if bin_done == bin_max:
                break
            path_full_in = os.path.join(root, f)
            path_rel = os.path.relpath(path_full_in, path_in_dict)[:-5]
            path_root = path_rel.split(os.path.sep)[0]
            if path_root not in do_media:
                continue
            icon_bytes = b""
            try:
                for icon in icon_ref_dict[path_rel]:
                    icon_bytes += icon_dict[icon]
            except KeyError:
                pass
            path_full_out = os.path.join(path_out_bin, path_rel)
            talk_dec = yak.talk.talk_decoder.TALK_Decoder(path_full_in, icon_mode, write_charset=charset_dict, icon_bytes=icon_bytes, blue_kiryu_talk=blue_kiryu_talk)
            talk_dec.read_talk_struct(path_full_in)
            talk_dec.decalc_meta_lines()
            talk_dec.recreate_local_charset()
            ic_warning = talk_dec.insert_icons()
            if ic_warning:
                warnings.append(ic_warning)
            all_missing_chars = all_missing_chars.union(talk_dec.get_missing_chars())
            talk_bytes = talk_dec.recreate_talk_file()
            os.makedirs(os.path.dirname(path_full_out), exist_ok=True)
            with open(path_full_out, "wb") as file_out:
                file_out.write(talk_bytes)
            bin_done += 1
            if bin_done % 50 == 0:
                print(f"Processed TALK files: {bin_done}...")
    if all_missing_chars:
        wm = "STEP - Rebuild TALK bin\nERROR - Bitmaps missing for some characters, placeholder used instead...\n"
        for c in all_missing_chars:
            wm += f"Char: {c}, Unicode code value: {ord(c)}\n"
        wm += f"Make sure custom character bitmaps are placed and named correctly in {yak.meta.global_def.DIR_REC_CHAR_OVERRIDE})"
        warnings.append(wm)
    return warnings
