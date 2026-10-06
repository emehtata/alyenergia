# Vihrea Alyenergia

Home Assistant custom integration for the Vihrea Alyenergia customer portal.

This is an unofficial community integration. It is not affiliated with or supported by Vihrea Alyenergia, and it is provided without warranty.

The integration retrieves consumption, billing, and invoice data from the Alyenergia portal. Spot prices are intentionally not included because they are already available through the Nordpool integration.

## Installation

### Manual installation

1. Download or clone this repository.
2. Copy the `custom_components/alyenergia` directory into your Home Assistant `config/custom_components` directory:

   ```text
   config/
   └── custom_components/
       └── alyenergia/
   ```

3. Restart Home Assistant.
4. Open **Settings > Devices & services**.
5. Select **Add integration** and search for **Vihrea Alyenergia**.
6. Enter your Alyenergia portal email address and password.

### HACS

1. Open HACS and go to **Integrations**.
2. Open the menu in the top-right corner and select **Custom repositories**.
3. Add `https://github.com/emehtata/alyenergia` as an **Integration** repository.
4. Install **Vihrea Alyenergia**.
5. Restart Home Assistant.
6. Add the integration from **Settings > Devices & services**.

## Sensors

The integration provides:

- Current month consumption
- Current month cost
- Current month mean price
- Previous month consumption
- Previous month cost
- Previous month mean price
- Latest reported day consumption
- Latest reported day date
- Latest invoice balance

Consumption values are reported in kWh. Costs and invoice balances are reported in EUR. Mean price is calculated as cost divided by consumption.

## Updates and authentication

Data is fetched once when the integration starts or reloads, and then once every 24 hours.

The access token is kept in memory. The refresh token is stored in the Home Assistant config entry and rotated when the portal provides a replacement. If the refresh token expires or is revoked, remove and add the integration again with your portal credentials.

## Requirements

- Home Assistant with custom integrations enabled
- An active Vihrea Alyenergia customer portal account
- Internet access from Home Assistant to `portal.alyenergia.fi` and its backend
