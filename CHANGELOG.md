# Changelog / Přehled změn

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
