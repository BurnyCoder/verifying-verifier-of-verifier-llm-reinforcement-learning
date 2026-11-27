"""Published and pending results must be distinguishable on every surface."""

from study.design import matched_runs, matrix
from study.inventory import inventory, inventory_markdown
from study.storage import write_json


def test_inventory_lists_every_stage_without_grading_unfinished_runs(tmp_path):
    profile = {"family": "two-add", "style": "demonstrated", "updates": 256}
    root = tmp_path / "calibrated"
    write_json(root / "top-depth2/recipe.json", {"updates": 256})
    (root / "top-depth2/cost.jsonl").write_text('{"step":13,"elapsed_seconds":12}\n')
    (root / "top-depth2/test.jsonl").write_text("deliberately unreadable sealed records")
    pending = {"name":"d1-17", "completed_development":False, "completed_final":False,
               "dev":1, "dev_n":1}
    rows = inventory(tmp_path, profile, [pending])
    by_id = {r["id"]:r for r in rows}
    assert len(rows) == len(by_id)
    assert all("calibrated/" + spec.name in by_id for spec in matrix(profile) + matched_runs(profile))
    assert by_id["calibrated/top-depth2"]["status"] == "Training started · 13/256"
    assert by_id["calibrated/d1-17"]["result"] == "Pending"
    assert by_id["calibrated/top-depth2"]["held_out"] == "Pending"
    assert by_id["new-judges/q38-27b"]["status"] == "Planned"
    assert by_id["new-judges/winner-d3"]["status"] == "Conditional"
    assert all(r["id"] in inventory_markdown(rows) for r in rows)
