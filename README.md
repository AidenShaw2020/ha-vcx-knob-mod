# VCX-Knob Smart Toilet (Hardened) / Bezpečnější CZ/EN fork

This repository is a security-hardened Czech/English fork of `NNNNzs/ha-vcx-knob`, based on upstream **v1.0.3**.

Tento repozitář je bezpečnostně upravený česko-anglický fork `NNNNzs/ha-vcx-knob`, založený na upstream verzi **v1.0.3**.

## Čeština

Integrace ovládá kompatibilní VCX-Knob / smart-toilet zařízení **lokálně přes Bluetooth LE**. Nevyžaduje cloud ani MQTT.

### Co je upravené

- Bluetooth akce `pair_bluetooth_device`, `scan_bluetooth_device` a `get_bluetooth_device_info` jsou registrované jako **admin-only**.
- MAC adresy a timeouty u těchto akcí se validují.
- Destruktivní tlačítko **Obnovit tovární nastavení** je `disabled_by_default` a musí se ručně povolit v registru entit.
- Akční tlačítka nejsou dostupná, když BLE zařízení není připojené.
- Odstraněny nadbytečné `DEBUG print()` výpisy v inicializaci.
- Uživatelské rozhraní je lokalizované do **češtiny a angličtiny**.
- Nezveřejňuje se obecná raw `send_command` service action.
- Release workflow používá pinovaný commit `actions/checkout` a GitHub CLI namísto další third-party release action.

### Instalace přes HACS

1. Otevři HACS → Integrations → Custom repositories.
2. Přidej `https://github.com/AidenShaw2020/ha-vcx-knob-mod` jako typ **Integration**.
3. Nainstaluj **VCX-Knob Smart Toilet (Hardened)**.
4. Restartuj Home Assistant.
5. Přidej integraci přes Nastavení → Zařízení a služby → Přidat integraci.

### Bezpečnost

U Home Assistant Container nezvyšuj oprávnění kontejneru jen kvůli této integraci, pokud Bluetooth funguje s užším nastavením. Nepodložené nebo destruktivní upstream příkazy nejsou v app-backed sadě entit vystavené.

Podrobnosti jsou v [SECURITY.md](SECURITY.md).

---

## English

The integration controls compatible VCX-Knob / smart-toilet devices **locally over Bluetooth LE**. No cloud or MQTT is required.

### Hardening changes

- `pair_bluetooth_device`, `scan_bluetooth_device`, and `get_bluetooth_device_info` are registered as **administrator-only** service actions.
- Bluetooth MAC addresses and timeouts are validated.
- The destructive **Factory Reset** button is `disabled_by_default` and must be explicitly enabled in the entity registry.
- Action buttons are unavailable while the BLE device is disconnected.
- Stray `DEBUG print()` statements were removed from integration setup.
- User-facing UI is localized in **Czech and English**.
- A generic raw `send_command` Home Assistant service action is not exposed.
- The release workflow pins `actions/checkout` to a commit SHA and uses GitHub CLI instead of an additional third-party release action.

### HACS installation

1. Open HACS → Integrations → Custom repositories.
2. Add `https://github.com/AidenShaw2020/ha-vcx-knob-mod` as an **Integration** repository.
3. Install **VCX-Knob Smart Toilet (Hardened)**.
4. Restart Home Assistant.
5. Add the integration from Settings → Devices & services → Add integration.

### Security

For Home Assistant Container, avoid granting broader container privileges solely for this integration if Bluetooth works with narrower permissions. Unsupported or destructive upstream guesses are not exposed in the app-backed entity set.

See [SECURITY.md](SECURITY.md).

## Upstream / License

Based on `NNNNzs/ha-vcx-knob` v1.0.3. Upstream is MIT licensed. See `LICENSE` and `NOTICE.md`.
