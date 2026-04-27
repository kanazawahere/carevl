# OMR Modules - lazy imports

def __getattr__(name):
    if name == "omr_form_gen":
        from modules.omr_form_gen import generate_form, generate_form_to_file
        return {"generate_form": generate_form, "generate_form_to_file": generate_form_to_file}
    if name == "omr_reader":
        from modules.omr_reader import read_batch, read_batch_to_file
        return {"read_batch": read_batch, "read_batch_to_file": read_batch_to_file}
    if name == "omr_bridge":
        from modules.omr_bridge import map_to_record, map_batch, save_records_from_omr
        return {"map_to_record": map_to_record, "map_batch": map_batch, "save_records_from_omr": save_records_from_omr}
    raise AttributeError(f"module has no attribute '{name}'")