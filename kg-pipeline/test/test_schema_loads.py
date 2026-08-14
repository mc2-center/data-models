from linkml_runtime import SchemaView

from conftest import MC2_SCHEMA_PATH, SCHEMA_PATH


def test_mc2_model_schema_loads():
    sv = SchemaView(MC2_SCHEMA_PATH)
    assert len(sv.all_classes()) > 0
    assert len(sv.all_enums()) > 0


def test_cckp_portal_schema_loads():
    sv = SchemaView(SCHEMA_PATH)
    for cls_name in ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]:
        assert cls_name in sv.all_classes()


def test_cckp_portal_imports_mc2_model_enums():
    sv = SchemaView(SCHEMA_PATH)
    assert "Dataset Tumor Type Enum" in sv.all_enums()
    enum = sv.get_enum("Dataset Tumor Type Enum")
    pv = enum.permissible_values.get("Cutaneous Melanoma")
    assert pv is not None
    assert pv.meaning == "NCIT:C3510"


def test_mc2_enum_and_cckp_join_annotations_resolve():
    sv = SchemaView(SCHEMA_PATH)
    all_enum_names = set(sv.all_enums().keys())
    for cls_name in ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]:
        cls = sv.induced_class(cls_name)
        for field, slot in cls.attributes.items():
            ann = slot.annotations
            if "mc2_enum" in ann:
                assert ann["mc2_enum"].value in all_enum_names, f"{cls_name}.{field}"
            if "cckp_join" in ann:
                target_cls, target_field = ann["cckp_join"].value.split(".")
                assert target_cls in sv.all_classes()
                assert target_field in sv.induced_class(target_cls).attributes
