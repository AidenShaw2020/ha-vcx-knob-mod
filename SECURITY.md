# Security notes / Bezpečnostní poznámky

## CZ

Tento fork vznikl po statické kontrole upstream verze `v1.0.3`. Upstream runtime kód komunikuje s WC lokálně přes BLE a nebyly v něm nalezeny HTTP/MQTT/cloud klienty, práce se secrets, `eval/exec` ani zápis do filesystemu.

Tento fork navíc:

- registruje Bluetooth pairing/scan/info akce přes `async_register_admin_service`,
- validuje formát MAC adresy a délku timeoutu,
- používá `asyncio.create_subprocess_exec` bez shellu,
- nechává Factory Reset ve výchozím stavu zakázaný,
- nepřidává raw obecnou command service,
- pinne GitHub Actions checkout na konkrétní commit SHA.

### Zbytková rizika

Jde o custom integration běžící uvnitř procesu Home Assistantu, takže libovolná budoucí změna Python kódu má stejná oprávnění jako Home Assistant. Aktualizace proto neinstaluj bez kontroly změn. Bluetooth zařízení samotné používá proprietární protokol a bezpečnost jeho firmware tento fork nemůže garantovat.

## EN

This fork was created after a static review of upstream `v1.0.3`. The upstream runtime code communicates locally over BLE; no HTTP/MQTT/cloud client, secrets access, `eval/exec`, or filesystem writes were found in the integration runtime.

This fork additionally:

- registers pairing/scan/info actions through `async_register_admin_service`,
- validates MAC addresses and timeout ranges,
- uses `asyncio.create_subprocess_exec` without a shell,
- keeps Factory Reset disabled by default,
- does not expose a generic raw command service,
- pins GitHub Actions checkout to an exact commit SHA.

### Residual risk

This is a Home Assistant custom integration running inside the Home Assistant process. Any future Python update therefore runs with Home Assistant's permissions. Review changes before updating. The toilet itself uses a proprietary BLE protocol and this fork cannot guarantee the security of the device firmware.
