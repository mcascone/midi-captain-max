# Screen Cheat Sheet

Serial console utility for monitoring CircuitPython devices.

## Connecting

```bash
# Connect to a specific device
screen /dev/tty.usbmodem141301 115200

# Auto-reconnect loop (survives device resets)
while true; do screen /dev/tty.usbmodem141301 115200; sleep 1; done
```

## Session Control

All commands start with `Ctrl+A` (the prefix key), then the action key:

| Keys | Action |
|------|--------|
| `Ctrl+A` `D` | Detach (leave running in background) |
| `Ctrl+A` `K` | Kill current window (prompts Y/n) |
| `Ctrl+A` `\` | Kill all windows and exit screen |

## From Shell (outside screen)

| Command | Action |
|---------|--------|
| `screen -ls` | List sessions |
| `screen -r` | Reattach (if only one) |
| `screen -r <id>` | Reattach to specific session |
| `screen -X -S <id> quit` | Kill a detached session |
| `screen -wipe` | Clean up dead sessions |

## Scrolling

| Keys | Action |
|------|--------|
| `Ctrl+A` `[` | Enter scroll/copy mode |
| `↑` `↓` `PgUp` `PgDn` | Scroll while in copy mode |
| `Esc` or `Q` | Exit copy mode |

## Other Useful

| Keys | Action |
|------|--------|
| `Ctrl+A` `?` | Help (list all commands) |
| `Ctrl+A` `A` | Send literal `Ctrl+A` to the app |

## Troubleshooting

### "Resource busy" error
Another process is holding the port:
```bash
lsof /dev/tty.usbmodem*     # See what's using it
screen -ls                   # Check for detached sessions
screen -X -S <id> quit       # Kill the session
```

### "Sorry, could not find a PTY"
Too many screen sessions. Clean up:
```bash
screen -wipe
```

### Multiple devices connected
List ports and connect to specific one:
```bash
ls /dev/tty.usbmodem*
screen /dev/tty.usbmodem141301 115200  # STD10
screen /dev/tty.usbmodem142201 115200  # Mini6
```
