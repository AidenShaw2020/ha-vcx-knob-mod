# DM Toilet Control 1.0.6 protocol notes

This document records behavior verified from the Android package
**DM Toilet Control 1.0.6** (`app-service.js`). It intentionally separates
app-verified behavior from the independent FFA2 reverse engineering inherited
from upstream.

## BLE connection used by the app

The app:

1. opens a BLE connection,
2. waits about 2 seconds,
3. discovers services and selects the service whose UUID starts with `0000FFA0`,
4. discovers characteristics and selects a writable characteristic whose UUID
   starts with `0000FFA1`,
5. waits about 1 second and considers the device connected.

The 1.0.6 app does **not** reference `FFA2`, `FF00`, or `FF01`, and does not call
the UniApp BLE read/notification APIs.

Our physical-device GATT discovery additionally found:

- `FF00 / FF01`: write-only,
- `FFA0 / FFA1`: write,
- `FFA0 / FFA2`: notify.

FFA2 remains supported by the HA integration as a best-effort optional status
channel because independent reverse engineering describes `AA 08 88 ...`
status packets, but it is not required for app-compatible control.

## Command frame

The app builds normal commands as:

```text
AA 08 02 CMD D1 D2 D3 CHECKSUM
```

where `CHECKSUM` is the low 8 bits of the sum of the preceding seven bytes.

For most commands, DM Toilet Control sends the app's current local temperature
tuple in the three data bytes:

```text
D1 = water temperature level
D2 = dryer temperature level
D3 = seat temperature level
```

For water pressure and nozzle/position commands, it instead sends:

```text
D1 = selected level
D2 = 0
D3 = 0
```

The app does not first read these values from the toilet. Its process-local
defaults are:

```text
water temperature = 1
dryer temperature = 0
seat temperature = 0
water pressure = 0
position = 0
```

The HA integration mirrors this behavior for command construction while only
publishing an optimistic select state after a successful BLE write.

## Verified command map

| App function | Command |
|---|---:|
| Feminine wash | `01` |
| Rear/butt wash | `02` |
| Child wash | `03` |
| Dry | `04` |
| Flip lid | `05` |
| Flip seat/ring | `06` |
| Flush | `07` |
| Auto | `08` |
| Stop | `09` |
| Power | `0E` |
| Light | `0F` |
| Water temperature | `10` |
| Self clean | `11` |
| Foam | `12` |
| ECO | `13` |
| Massage | `14` |
| Dryer temperature | `20` |
| Water pressure | `21` |
| Nozzle/position | `22` |
| Seat temperature | `30` |

### Temperature levels

Water and seat:

```text
0 = off
1 = 34 °C
2 = 37 °C
3 = 40 °C
```

Dryer:

```text
0 = off
1 = 45 °C
2 = 50 °C
3 = 55 °C
```

## Advanced-setting commands present in the app

These are documented for future work but are not exposed as HA entities in
v1.0.13 because they are increment/decrement or configuration actions and have
not yet been hardware-tested individually.

| Setting | Increase / ON | Decrease / OFF |
|---|---:|---:|
| Lid opening torque | `41` | `42` |
| Lid closing torque | `51` | `52` |
| Seat opening torque | `61` | `62` |
| Seat closing torque | `71` | `72` |
| Voice volume | `81` | `82` |
| Flush time | `91` | `92` |
| Automatic night light | `A1` | `A2` |
| Radar level | `B1` | `B2` |
| Automatic flush | `C1` | `C2` |
| Automatic lid-close time | `D1` | `D2` |
| Automatic foam | `E1` | `E2` |
| Aging mode | `F1` | `F2` |
| Reserved 1 | `F3` | `F4` |
| Reserved 2 | `F5` | `F6` |
| Virtual seating | `46` | `47` |

## Ambient-light frame

The app also has a second frame type:

```text
AA 08 03 MODE R G B CHECKSUM
```

Modes observed in the UI are 0-7 (off, static, flashing, breathing, flowing,
colorful flowing, colorful gradient, welcome), with bit 7 of `MODE` used by the
app's separate control-mode toggle.

In v1.0.13 this frame is exposed as an optimistic Home Assistant RGB light.
The integration always sets bit 7 for manual control, matching the app's default
control mode; the device does not report ambient-light state back.