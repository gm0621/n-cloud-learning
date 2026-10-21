from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
js = (ROOT / "assets" / "lesson-practice.js").read_text(encoding="utf-8")

required = (
    "const completionKey=`${progressKey}-complete`;",
    "function completionReady()",
    "function revokeCompletionIfInvalid()",
    "localStorage.removeItem(completionKey)",
    "revokeCompletionIfInvalid();",
    "safeSet(completionKey,'true')",
)
for marker in required:
    assert marker in js, f"missing completion-lock contract: {marker}"
for marker in ("beforeprint", "scrollHeight", "afterprint", "printMirrors", "print-notes-mirror", "mirror.textContent", "printMirrors.clear()"):
    assert marker in js, f"missing long-form print support: {marker}"
css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
for marker in (".print-notes-mirror", "white-space:pre-wrap", ".worksheet-grid textarea{display:none!important}"):
    assert marker in css, f"missing printable mirror style: {marker}"

save_progress = js[js.index("function saveProgress()") : js.index("function updateProgress()")]
save_notes_start = js.index("function saveNotes()")
save_notes = js[save_notes_start : js.index("\n  }\n  updateNotesStatus();", save_notes_start)]
assert "revokeCompletionIfInvalid();" in save_progress
assert "revokeCompletionIfInvalid();" in save_notes
assert "done===boxes.length&&practicesDone===quizIds.length&&notesDone===notes.length" not in js
assert "completionReady()" in js[js.index("if(finish)") :]

print("COMPLETION_LOCK_CONTRACT_PASS invalidation=progress+notes persistent_flag=revocable")
