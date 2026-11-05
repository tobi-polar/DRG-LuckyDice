# Unlucky Dice: notes for a later mod

Unlucky Dice will be a separate mod for the bad events. None of this is built yet. These notes come from the Lucky Dice planning, and nothing here has been tested in game.

## Events

All of these run on the server.

| Event | Who | How | Still to check |
|---|---|---|---|
| Half speed | Team | `TryPushActiveStatusEffect(STE_Dice_Slow, player, manager)` **[header]** | Whether 0.5 gives half speed |
| Wave spawns | Team | `GetFSDGameMode` → `GetWaveManager` → `TriggerWave(EWC_Generic)` **[header] [game]** | Whether it spawns correctly in every mission type |
| Random teleport | Picker | Set Actor Location with Teleport on, using the position history below **[engine]** | Client movement correction |
| Swap positions | All alive | Save all positions first, then move each player to the next player's position, with Sweep off and Teleport on **[engine]** | As above. With 3 or 4 players, this rotates them in a loop. |

## Slow effect

`STE_Dice_Slow` is a `StatusEffect` child with one `StatChangeStatusEffectItem` in its `StatusEffects` array:

| Copied from | `Stat` | `StatChange` | Other settings |
|---|---|---|---|
| `STE_ElecticPlant_slowdown` **[game]** (uses 0.3) | `PST_MovementSpeedEnvironmentalPenalty` | Start at 0.5 | `Duration` 15, `RefreshDurationOnApplication` on |

The game's value shows which stat to use, but not exactly how it scales, so measure it in game. Armor perks or mods that reduce environmental penalties may weaken the slow.

## Safe teleport points

A random point could land inside rock, so only use places a dwarf has actually stood:

1. Every 5 s on the server, save each player's location if they're on the ground and alive. Keep the last 30.
2. For a teleport, pick a saved point at least 20 s old, preferably from another player and not close to the picker.
3. Digging or terrain changes can still leave a point unsafe, so test in small tunnels.

## When events can't roll

Set an event's weight to 0 for the roll if:

| Event | Blocked when |
|---|---|
| Swap positions | Fewer than 2 living players, or any dwarf is carrying something, until this is tested |
| Teleport, swap, half speed | Extraction has started. `FSDGameState.OnCountdownStarted` **[header]** is the likely signal, so confirm it only fires for extraction. |
| Teleport, swap | The target is downed. Start with `PlayerCharacter.IsAlive` **[header]**, and confirm what it returns for a downed dwarf. |
| Teleport | There are no safe points yet |

## Multiplayer checks

Check these from the **client's** side, not just the host's:

- [ ] Teleport and swap don't rubber-band.
- [ ] Waves, teleports and swaps don't break during extraction, while downed, or while on a zipline or platform.
