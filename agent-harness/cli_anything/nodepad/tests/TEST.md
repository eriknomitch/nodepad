# TEST.md — cli-anything-nodepad Test Plan & Results

## Test Inventory

### Unit Tests (`test_core.py`)
1. **Content Type Detection** — All 14 types detected correctly from heuristic patterns
2. **Project CRUD** — Create, load, save, add/delete/edit blocks
3. **TextBlock serialisation** — to_dict/from_dict round-trip
4. **GhostNote serialisation** — to_dict/from_dict round-trip
5. **SubTask serialisation** — to_dict/from_dict round-trip
6. **Project stats** — Correct counts by type, enriched, pinned
7. **Export Markdown** — Correct structure, YAML front matter, type grouping
8. **.nodepad format** — Serialise/parse round-trip
9. **Config management** — Load/save config, env var overrides
10. **Output formatting** — JSON mode vs human mode

### E2E Tests (`test_full_e2e.py`)
1. **Full workflow** — Create project -> add blocks -> detect types -> export markdown -> export .nodepad
2. **Import/export round-trip** — Save .nodepad -> reload -> verify data integrity
3. **CLI subprocess** — Test installed CLI via subprocess (TestCLISubprocess)
4. **REPL help** — Verify REPL responds to help command

### Realistic Workflow Scenarios
1. **Research session** — Add 10 notes across categories, export markdown, verify structure
2. **Import existing project** — Load a pre-built .nodepad file, inspect, modify, re-export

## Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.12.1, pytest-8.3.5, pluggy-1.6.0

cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_quote PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_task PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_question PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_definition PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_comparison PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_reference PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_idea PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_reflection PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_opinion PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_entity PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_claim PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_narrative PASSED
cli_anything/nodepad/tests/test_core.py::TestDetectContentType::test_general_fallback PASSED
cli_anything/nodepad/tests/test_core.py::TestProject::test_create PASSED
cli_anything/nodepad/tests/test_core.py::TestProject::test_add_block PASSED
cli_anything/nodepad/tests/test_core.py::TestProject::test_get_block PASSED
cli_anything/nodepad/tests/test_core.py::TestProject::test_delete_block PASSED
cli_anything/nodepad/tests/test_core.py::TestProject::test_stats PASSED
cli_anything/nodepad/tests/test_core.py::TestProject::test_save_load_roundtrip PASSED
cli_anything/nodepad/tests/test_core.py::TestTextBlock::test_to_dict_from_dict PASSED
cli_anything/nodepad/tests/test_core.py::TestTextBlock::test_summary PASSED
cli_anything/nodepad/tests/test_core.py::TestTextBlock::test_optional_fields_omitted PASSED
cli_anything/nodepad/tests/test_core.py::TestGhostNote::test_roundtrip PASSED
cli_anything/nodepad/tests/test_core.py::TestExport::test_empty_project PASSED
cli_anything/nodepad/tests/test_core.py::TestExport::test_markdown_structure PASSED
cli_anything/nodepad/tests/test_core.py::TestExport::test_claims_table PASSED
cli_anything/nodepad/tests/test_core.py::TestExport::test_pinned_section PASSED
cli_anything/nodepad/tests/test_core.py::TestConfig::test_load_defaults PASSED
cli_anything/nodepad/tests/test_core.py::TestConfig::test_env_override PASSED
cli_anything/nodepad/tests/test_core.py::TestOutput::test_json_mode_toggle PASSED
cli_anything/nodepad/tests/test_core.py::TestNodepadFormat::test_to_nodepad_structure PASSED
cli_anything/nodepad/tests/test_core.py::TestNodepadFormat::test_from_nodepad_invalid PASSED
cli_anything/nodepad/tests/test_core.py::TestNodepadFormat::test_from_nodepad_missing_blocks PASSED
cli_anything/nodepad/tests/test_core.py::TestNodepadFormat::test_full_roundtrip_json PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestFullWorkflow::test_create_populate_export PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestFullWorkflow::test_import_export_roundtrip PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestFullWorkflow::test_project_stats_accuracy PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_help PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_info_types PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_info_types_json PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_info_detect PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_project_create_and_list PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_block_add_and_list PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_export_markdown PASSED
cli_anything/nodepad/tests/test_full_e2e.py::TestCLISubprocess::test_config_show PASSED

============================== 45 passed in 0.86s ==============================
```

### Summary
- **Total tests:** 45
- **Passed:** 45
- **Failed:** 0
- **Pass rate:** 100%

### Subprocess tests (CLI_ANYTHING_FORCE_INSTALLED=1)
- **Total:** 8
- **Passed:** 8
- **Pass rate:** 100%
