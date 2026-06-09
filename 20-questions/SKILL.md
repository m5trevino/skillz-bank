---
name: 20-questions
description: "Questionnaire-driven config file editor. When a user wants to customize, edit, or create any config file (dotfiles, terminal configs, editor configs, shell configs, app configs), this skill takes over. It backs up the working config first, then asks thorough questions about workflow, OS, DE/WM, preferences, and desired features. Edits iteratively based on answers with follow-up questions until the user is satisfied. Handles kitty.conf, .bashrc, .zshrc, .tmux.conf, init.vim/lua, alacritty.yml, and any other config file."
category: workflow
risk: safe
source: community
tags: "[config, dotfiles, questionnaire, personalization, workflow, editing]"
allowed-tools: "*"
date_added: "2026-05-30"
---

# 20-Questions

## Purpose

Eliminate generic, one-size-fits-all config dumps. Every config file should be tailored to the actual human using it. This skill interviews the user thoroughly before touching a single line, backs up their working config as insurance, and iterates until the config is truly theirs.

## When to Use This Skill

Activate immediately when the user says anything like:
- "edit my config" / "customize my config" / "fix my config"
- "set up [tool]" where [tool] uses a config file
- "create a config for [tool]"
- "I want to configure [tool]"
- "my [tool] config is broken"
- "dotfiles" / "dotfile" / "rc file" / "conf file"
- Any mention of: kitty, alacritty, tmux, zsh, bash, fish, nvim, vim, helix, wezterm, ghostty, hyprland, i3, sway, rofi, waybar, polybar, dunst, picom, compton, starship, fzf, fd, ripgrep, bat, eza, lazygit, lazydocker, btop, htop, yazi, ranger

## The Golden Rule

**NEVER edit a config file without backing it up first.**

## Workflow

### Step 1: Detect the Target Config File

Determine which config file the user wants to edit. Parse their message for:
- Explicit paths (`~/.config/kitty/kitty.conf`)
- Tool names (infer standard config path)
- Generic requests (ask user to specify)

Standard paths by tool:
| Tool | Config Path |
|------|-------------|
| Kitty | `~/.config/kitty/kitty.conf` |
| Bash | `~/.bashrc` |
| Zsh | `~/.zshrc` |
| Fish | `~/.config/fish/config.fish` |
| Tmux | `~/.tmux.conf` |
| Neovim | `~/.config/nvim/init.lua` or `init.vim` |
| Vim | `~/.vimrc` |
| Alacritty | `~/.config/alacritty/alacritty.toml` |
| WezTerm | `~/.wezterm.lua` |
| Hyprland | `~/.config/hypr/hyprland.conf` |
| i3 | `~/.config/i3/config` |
| Sway | `~/.config/sway/config` |
| Rofi | `~/.config/rofi/config.rasi` |
| Waybar | `~/.config/waybar/config` |
| Polybar | `~/.config/polybar/config.ini` |
| Dunst | `~/.config/dunst/dunstrc` |
| Picom | `~/.config/picom/picom.conf` |
| Starship | `~/.config/starship.toml` |
| Yazi | `~/.config/yazi/yazi.toml` |
| Lazygit | `~/.config/lazygit/config.yml` |
| Btop | `~/.config/btop/btop.conf` |

### Step 2: Backup the Working Config

Before any read or edit operation:

```bash
# Create timestamped backup
cp /path/to/config /path/to/config.backup.$(date +%Y%m%d_%H%M%S)
```

Tell the user: `"Backed up your working config to [path].backup.[timestamp]. If we fuck this up, we can restore it."`

### Step 3: The Questionnaire

Ask the user questions using `AskUserQuestion`. The questionnaire must be thorough but chunked — never dump 20 questions at once. Ask 3-4 questions per turn, process answers, then ask follow-ups.

**Universal questions (ask these for EVERY config):**
1. What OS? (Linux/macOS/Windows-WSL)
2. Do you use this tool locally, remotely (SSH), or both?
3. Are you replacing an existing config or building from scratch?
4. What's your biggest frustration with the current setup?

**Category-specific questions** (see `references/questionnaire-templates.md` for detailed per-tool questionnaires):

**For terminal emulators:** shell, font, cursor style, transparency, decorations, tiling vs floating DE, tab/window behavior, copy behavior, bell, scrollback size, remote control, images in terminal, startup session.

**For shells (bash/zsh/fish):** aliases, prompts, completions, history size, plugins (oh-my-zsh, starship, etc.), PATH additions, sudo behavior, keybinds.

**For editors (nvim/vim/helix):** color scheme, font, line numbers, tabs vs spaces, LSP, fuzzy finder, file tree, status line, keybind philosophy (vim-native vs IDE-like).

**For WMs (i3/hyprland/sway):** monitor setup, key modifier, gaps, borders, bar, startup apps, window rules, scratchpad, workspace behavior.

**For multiplexer (tmux):** prefix key, status bar, pane navigation, session management, copy mode, integrations.

### Step 4: Build the Config Iteratively

After each questionnaire round:
1. Read the current config (or create new)
2. Apply changes based on answers
3. Show the user what changed
4. Ask: `"Good? Want anything else? Or change something?"`

If they want changes, go back to Step 3 with targeted follow-up questions.

### Step 5: Validate and Hand Off

Before finishing:
- Verify the config syntax where possible (e.g., `kitty --config ~/.config/kitty/kitty.conf --hold`)
- Show the user key shortcuts or commands they should know
- Remind them of the backup location
- Tell them how to reload/apply the config

## Anti-Patterns (NEVER Do These)

- **Never** dump a generic config and call it done.
- **Never** skip the backup.
- **Never** ask all 20 questions in one turn — chunk them.
- **Never** assume the user knows what a setting does — explain in plain terms.
- **Never** ignore "I don't care" answers — make a reasonable choice and move on.
- **Never** leave the user with a broken config — test or validate before finishing.

## Common Mistakes

- Assuming the user wants the latest trendy theme instead of asking.
- Forgetting to ask about their shell, which breaks shell integration features.
- Not checking if the user runs tools over SSH — this changes recommendations.
- Over-configuring: giving them 50 features when they use 5.
- Under-configuring: missing critical quality-of-life settings because you rushed.

## Example Interaction

**User:** "I want to configure Kitty"

**Agent:** (backs up kitty.conf) "Backed up. Let's build YOUR config. What OS? Floating DE or tiling WM? What shell?"

**User:** "Linux, floating, zsh"

**Agent:** (asks 3-4 more questions about appearance, behavior, features)

**User:** (answers)

**Agent:** (edits config, shows result) "Done. Green phosphor theme, JetBrains Mono, single-instance mode so you don't lose windows at 4 AM. Reload with Ctrl+Shift+F5. Good?"

**User:** "Yeah but can you add image previews?"

**Agent:** (adds icat alias and image support) "Done. Added `alias icat='kitten icat'` to your zshrc. Anything else?"
