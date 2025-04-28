# Norgesnett

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**Integrasjon for å hente ut informasjon fra nettlevrandøren Norgesnett.**
Den er tilpasset et målerpunkt, api'et til Norgesnett vil hente ut informasjon fra flere.

Jeg har bare et målerpunkt så jeg har ikke sett for mye på hvordan det bør løses om man har fler.

**This component will set up the following platforms.**

| Platform | Description                    |
| -------- | ------------------------------ |
| `sensor` | Show info from Norgesnett API. |

**Componenten tilbyr disse entitetene.**
| Entitet | Beskrivelse |
| --------------- | ---------------------------------------------------- |
| `currentFixedPriceLevel` | Viser prisnivået. |
| `monthlyTotal` | Viser månedspåslaget for gjeldende prisnivå |
| `monthlyTotalExVat` | Samme påslag, ekskl. mva. |
| `monthlyExTaxes` | Samme påslag, ekskl. skatter. |
| `monthlyTaxes` | Skatter denne måneden. |
| `monthlyUnitOfMeasure` | Kr/month |
| `hourly_prices` | Liste over timesprisene (JSON) |
| `current_price` | Gjeldende pris denne timen |

Prisene lastes ned daglig, current_price oppdateres fortløpende

## Installation

Bruk HACS!

Alternativt:

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `norgesnett`.
4. Download _all_ the files from the `custom_components/norgesnett/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Norgesnett"

## Template for å vise total strømpris

Denne legger sammen nettleie for den aktuelle timen, spot pbis fra norgesnett og evt. påslag fra strømleverandøren din. Sensoren for nordpool og spotpris må oppdateres før bruk.

Den skal vise riktig pris når strømstøtten er fratrukke.

```yaml
- platform: template
  sensors:
    nettleie_plus_spot_og_paaslag_pris:
      friendly_name: "Norgesnett + Nordpool"
      unit_of_measurement: "NOK/kWh"
      icon_template: mdi:cash-fast
      value_template: >-
        {%- set nettleie = states('sensor.norgesnett_current_hour_price') | float(0) -%}
        {%- set spotpris  = states('sensor.nordpool_kwh_no1_nok_3_10_025') | float(0) -%}
        {%- set paaslag  = -0.01 -%}
        {%- if spotpris > 0.9375 -%}
          {{ ((pool - 0.9375) * 0.90) + 0.9375 + nettleie + paaslag }}
        {%- else -%}
          {{ nettleie + spotpris + paaslag }}
        {%- endif -%}
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/MrFjellstad
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/MrFjellstad/norgesnett.svg?style=for-the-badge
[commits]: https://github.com/MrFjellstad/norgesnett/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/MrFjellstad/norgesnett.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40MrFjellstad-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/MrFjellstad/norgesnett.svg?style=for-the-badge
[releases]: https://github.com/MrFjellstad/norgesnett/releases
[user_profile]: https://github.com/MrFjellstad
