import json
from pathlib import Path

from markdownviewer.recent import RECENT_LIMIT, RecentFiles


def make_store(tmp_path: Path) -> RecentFiles:
    return RecentFiles(tmp_path / "state" / "recent.json")


def paths(count: int, base: Path) -> list[Path]:
    return [base / f"doc{i}.md" for i in range(count)]


def test_recent_limit_is_ten():
    assert RECENT_LIMIT == 10


def test_new_store_is_empty(tmp_path):
    assert make_store(tmp_path).paths == []


def test_add_puts_newest_first(tmp_path):
    store = make_store(tmp_path)
    first, second = paths(2, tmp_path)

    store.add(first)
    store.add(second)

    assert store.paths == [second, first]


def test_adding_an_existing_path_moves_it_to_the_top_without_duplicating(tmp_path):
    store = make_store(tmp_path)
    a, b, c = paths(3, tmp_path)
    for p in (a, b, c):
        store.add(p)

    store.add(a)

    assert store.paths == [a, c, b]


def test_list_is_circular_the_oldest_drops_out_after_ten(tmp_path):
    store = make_store(tmp_path)
    opened = paths(RECENT_LIMIT + 2, tmp_path)

    for p in opened:
        store.add(p)

    assert len(store.paths) == RECENT_LIMIT
    assert store.paths[0] == opened[-1]
    assert store.paths[-1] == opened[2]
    assert opened[0] not in store.paths and opened[1] not in store.paths


def test_list_persists_across_instances(tmp_path):
    first_run = make_store(tmp_path)
    a, b = paths(2, tmp_path)
    first_run.add(a)
    first_run.add(b)

    second_run = make_store(tmp_path)

    assert second_run.paths == [b, a]


def test_remove_drops_the_entry_and_persists(tmp_path):
    store = make_store(tmp_path)
    a, b = paths(2, tmp_path)
    store.add(a)
    store.add(b)

    store.remove(a)

    assert store.paths == [b]
    assert make_store(tmp_path).paths == [b]


def test_remove_of_unknown_path_is_a_no_op(tmp_path):
    store = make_store(tmp_path)
    a, b = paths(2, tmp_path)
    store.add(a)

    store.remove(b)

    assert store.paths == [a]


def test_clear_empties_the_list_and_persists(tmp_path):
    store = make_store(tmp_path)
    for p in paths(3, tmp_path):
        store.add(p)

    store.clear()

    assert store.paths == []
    assert make_store(tmp_path).paths == []


def test_corrupt_state_file_is_treated_as_empty(tmp_path):
    state = tmp_path / "state" / "recent.json"
    state.parent.mkdir()
    state.write_text("{ not json", encoding="utf-8")

    assert RecentFiles(state).paths == []


def test_wrong_shaped_state_file_keeps_only_valid_entries(tmp_path):
    state = tmp_path / "state" / "recent.json"
    state.parent.mkdir()
    good = str(tmp_path / "ok.md")
    state.write_text(json.dumps({"files": [good, 42, None, ""]}), encoding="utf-8")

    assert RecentFiles(state).paths == [Path(good)]


def test_state_file_with_too_many_entries_is_trimmed_to_the_limit(tmp_path):
    state = tmp_path / "state" / "recent.json"
    state.parent.mkdir()
    many = [str(tmp_path / f"f{i}.md") for i in range(RECENT_LIMIT + 5)]
    state.write_text(json.dumps({"files": many}), encoding="utf-8")

    assert [str(p) for p in RecentFiles(state).paths] == many[:RECENT_LIMIT]


def test_unwritable_location_does_not_raise_and_keeps_the_list_in_memory(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a folder", encoding="utf-8")
    store = RecentFiles(blocker / "recent.json")
    a = tmp_path / "a.md"

    store.add(a)

    assert store.paths == [a]
