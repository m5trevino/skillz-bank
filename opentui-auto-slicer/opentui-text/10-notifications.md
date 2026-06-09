# Notifications

OpenTUI can ask the terminal emulator to show a desktop notification using OSC escape sequences. Use this for long-running tasks, background work, or prompts that need attention.

``` astro-code
const ok = renderer.triggerNotification("Build finished", "OpenTUI")
```

`triggerNotification(message, title?)` returns `true` when OpenTUI has detected a supported notification protocol, and `false` otherwise.

## Capability

Check detection state through renderer capabilities:

``` astro-code
if (renderer.capabilities?.notifications) {
  renderer.triggerNotification("Tests passed", "CI")
}
```

OpenTUI detects and emits terminal OSC notification protocols only. It does not call platform tools such as `notify-send`, AppleScript, or PowerShell toasts.

## Terminal behavior

Terminal and OS settings decide how the notification is presented. Some terminals only show banners when the terminal is unfocused, and macOS may store notifications in Notification Center without showing a banner depending on app notification settings.

See `packages/examples/src/notification-demo.ts` for an interactive example.


---

_Source: https://opentui.com/docs/core-concepts/notifications
_Downloaded: 2026-05-21 19:04:41 UTC_
