# Troubleshooting & Edge Cases

## Permission Errors

If the script cannot move a file due to permissions, it will print an error to stderr and exit with a non-zero code. The agent should catch this and report it to the user without crashing the session.

## Empty Directories

If the target directory contains no files, the `analyze` subcommand returns an empty JSON array `[]`. The agent should report "No files found to organize" and end gracefully.

## Very Large Files

Text excerpts are capped at 300 characters. Files larger than a few megabytes are still readable in chunks; only the first 300 characters are used for keyword extraction. This avoids memory issues.

## Special Characters in Filenames

The script uses `pathlib.Path` internally and handles Unicode, spaces, and most special characters correctly. On some filesystems, extremely long paths may fail; the error is surfaced in JSON output.

## Already Organized Folders

If the user runs the skill on a directory that already contains project subfolders, the script will still treat those subfolder names as regular files during analysis. To avoid this, the agent should confirm with the user whether to organize **only loose files** or also re-organize contents of existing subfolders.

## Learning Pollution

If the user makes a mistake and chooses the wrong folder, that incorrect choice is recorded. There is currently no "unlearn" command. The workaround is to manually edit `~/.smart_file_organizer/memory.json` and remove the erroneous entry.

## Cross-Device Moves

`shutil.move` is used, which automatically handles cross-device moves by copying and deleting. This may be slower but prevents "Invalid cross-device link" errors.
