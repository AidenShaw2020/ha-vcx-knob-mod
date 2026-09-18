# Changelog / Přehled změn

## 1.0.10 - úplná oprava BLE helperů / complete BLE helper fix

### CZ
- Opraven chybějící import `establish_connection`.
- `async_ble_device_from_address` a `async_last_service_info` se volají přes modul `homeassistant.components.bluetooth`.
- Odstraněn paralelní background `_async_initial_connect()`, takže inicializace BLE probíhá jedinou cestou přes coordinator refresh.
- Odstraněna již nepoužívaná metoda `_async_initial_connect`.
- Nahrazen neexistující `async_get_service_info_from_name` za `async_last_service_info`.
- Opraven `bluetooth.Change` na `bluetooth.BluetoothChange`.
- GitHub Actions nově kontroluje Ruff `F821` a nevydá release s nedefinovaným Python jménem.

### EN
- Added the missing `establish_connection` import.
- `async_ble_device_from_address` and `async_last_service_info` are accessed through Home Assistant's Bluetooth module.
- Removed the parallel `_async_initial_connect()` background task so BLE initialization has one path through coordinator refresh.
- Removed the now-unused `_async_initial_connect` method.
- Replaced obsolete `async_get_service_info_from_name` with `async_last_service_info`.
- Fixed `bluetooth.Change` to `bluetooth.BluetoothChange`.
- GitHub Actions now runs Ruff `F821` and blocks releases containing undefined Python names.
## 1.0.9 - oprava předání Home Assistant instance / Home Assistant instance wiring fix

### CZ
- Opraven pád `VCXKnobBLEClient.__init__() missing 1 required positional argument: 'hass'`.
- `async_setup_entry()` nyní předává klientovi `hass=hass`.
- Testovací připojení v config flow nyní předává `hass=self.hass`.
- Po vytvoření coordinatoru se provede okamžitý první refresh stavu před načtením entit.
- Přidána validační kontrola, aby v repozitáři nezůstalo volání nového BLE klienta bez parametru `hass`.

### EN
- Fixed `VCXKnobBLEClient.__init__() missing 1 required positional argument: 'hass'`.
- `async_setup_entry()` now passes `hass=hass`.
- The config-flow connection test now passes `hass=self.hass`.
- An immediate coordinator refresh is performed before entity platforms are forwarded.
- Added validation to catch calls to the new BLE client that omit `hass`.
## 1.0.8 - BLE proxy a stavová data / BLE proxy and status data

### CZ
- Připojení nyní používá Home Assistant Bluetooth manager a `bleak_retry_connector.establish_connection()`, takže správně podporuje ESPHome Bluetooth Proxy.
- Opravena chybná kontrola GATT služby přes `str(services)`.
- Integrace validuje skutečné služby a charakteristiky FFA0/FFA1/FFA2 přes Bleak API.
- Při nesouladu GATT profilu vypíše do logu všechny nalezené služby, charakteristiky a jejich properties.
- BLE notifikace se nyní skládají jako stream; neúplný 8bajtový paket se již nezahodí mezi dvěma notifikacemi.
- Po setupu se okamžitě provede první status refresh místo čekání na další periodický interval.

### EN
- Connections now use Home Assistant's Bluetooth manager with `bleak_retry_connector.establish_connection()` for proper ESPHome Bluetooth Proxy support.
- Fixed the invalid GATT service check based on `str(services)`.
- FFA0/FFA1/FFA2 are validated through the Bleak GATT API.
- On GATT mismatch, all discovered services, characteristics and properties are logged.
- BLE notifications are now reassembled as a byte stream, preserving fragmented 8-byte packets across notifications.
- The integration performs an immediate status refresh after setup.
## 1.0.7 - runtime-safe oprava config flow / runtime-safe config-flow fix

### CZ
- `async_abort(reason="no_devices_found")` nyní vždy předává `device_name`.
- Oprava funguje i v případě, že Home Assistant stále drží starší překladovou šablonu v cache.
- Překlady `no_devices_found` zároveň zůstávají bez povinného placeholderu.

### EN
- `async_abort(reason="no_devices_found")` now always provides `device_name`.
- This also protects against an older translation template still being cached by Home Assistant.
- `no_devices_found` translations remain placeholder-free as an additional safeguard.
## 1.0.6 - oprava config-flow překladu / config-flow translation fix

### CZ
- Opravena chyba FormatJS `MISSING_VALUE` při nenalezení žádného zařízení.
- Překlad `no_devices_found` již nevyžaduje placeholder `{device_name}`, protože abort větev config flow jej neposílá.
- Oprava je provedena v `strings.json`, `translations/cs.json` a `translations/en.json`.

### EN
- Fixed the FormatJS `MISSING_VALUE` error when no device is found.
- The `no_devices_found` translation no longer requires the `{device_name}` placeholder because the abort branch of the config flow does not provide it.
- The fix is applied to `strings.json`, `translations/cs.json`, and `translations/en.json`.
# Changelog / PĹ™ehled zmÄ›n

## 1.0.5 - HACS a UTF-8 hotfix

### CZ
- Opraveno kĂłdovĂˇnĂ­ `CHANGELOG.md` do ÄŤistĂ©ho UTF-8 bez BOM.
- Opraven `manifest.json` do ÄŤistĂ©ho UTF-8 bez BOM.
- Opraven release workflow tak, aby vytvĂˇĹ™el HACS ZIP se soubory integrace pĹ™Ă­mo v koĹ™eni archivu.
- PĹ™idĂˇna kontrola struktury release ZIPu pĹ™ed vytvoĹ™enĂ­m GitHub release.
- Verze integrace zvĂ˝Ĺˇena na `1.0.5`.

### EN
- Fixed `CHANGELOG.md` encoding to plain UTF-8 without BOM.
- Fixed `manifest.json` to plain UTF-8 without BOM.
- Fixed the release workflow so the HACS ZIP contains integration files at the archive root.
- Added release archive layout validation before creating the GitHub release.
- Bumped integration version to `1.0.5`.

## 1.0.4 - neĂşspÄ›ĹˇnĂ˝ release / failed release

Tag `v1.0.4` byl vytvoĹ™en, ale GitHub Actions release selhal kvĹŻli UTF-8 BOM v `manifest.json`.
HACS proto tuto verzi nikdy nenabĂ­zel jako release.

The `v1.0.4` tag was created, but the GitHub Actions release failed because `manifest.json` contained a UTF-8 BOM.
As a result, HACS never saw this version as an available release.

## 1.0.3-mod.1

### CZ
- ZaloĹľeno na upstream `NNNNzs/ha-vcx-knob` v1.0.3.
- Bluetooth pomocnĂ© akce jsou pouze pro administrĂˇtory.
- Validace MAC adres a timeoutĹŻ.
- Factory Reset je ve vĂ˝chozĂ­m stavu zakĂˇzanĂ˝.
- OvlĂˇdacĂ­ tlaÄŤĂ­tka vyĹľadujĂ­ aktivnĂ­ BLE spojenĂ­.
- ÄŚeskĂ© a anglickĂ© uĹľivatelskĂ© rozhranĂ­.
- Raw command service nenĂ­ zveĹ™ejnÄ›nĂˇ.
- Hardened GitHub release workflow.

### EN
- Based on upstream `NNNNzs/ha-vcx-knob` v1.0.3.
- Bluetooth helper actions are administrator-only.
- MAC address and timeout validation.
- Factory Reset is disabled by default.
- Action buttons require an active BLE connection.
- Czech and English user interface.
- Raw command service is not exposed.
- Hardened GitHub release workflow.
