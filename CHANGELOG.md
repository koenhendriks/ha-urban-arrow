# Changelog

All notable changes to this integration are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-24

### Added

- **Location updated** sensor (diagnostic) showing when the bike last reported
  its GPS position. The position can be much older than the other values while
  the bike is parked.

### Changed

- The **Location** tracker is now a regular entity instead of a diagnostic one,
  so it appears with the other sensors on the device page and on
  auto-generated dashboards. Its entity ID does not change.

### Fixed

- When the bike has no GPS fix it reports position 0, 0; the tracker now shows
  the location as unknown instead of placing the bike off the coast of West
  Africa.

## [0.1.0] - 2026-11-24

### Added

- First release. Sign in with the email and password of your Urban Arrow app
  account; every bike on the account becomes a device.
- Sensors: battery, range, odometer, assist level (Off, Eco, Tour, Sport,
  Turbo), module battery, protection level, last online and subscription end.
- Charging binary sensor and GPS location tracker.
- Flash lights button.
- Switches for theft protection, auto protection, module battery management
  and the app notifications.
- Diagnostics download with personal data removed.
- English and Dutch translations.

[0.2.0]: https://github.com/koenhendriks/ha-urban-arrow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/koenhendriks/ha-urban-arrow/releases/tag/v0.1.0
