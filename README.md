# google-maps-list-export

For some reason Google does not provide a Maps list export function.

Supports KML and custom JSON.

## Requirements

- Python 3.6+ with pip
- Firefox
- Geckodriver

*Make sure Firefox and Geckodriver are in your PATH.*

## Installation

```shell
pip install -r requirements.txt
```

## Usage

In Google Maps create a share link for your list and copy it.

To download the items of the list as JSON:

```shell
python export.py <link>
```

Or as KML:

```shell
python export.py -f kml <link>
```

To show all available options:

```shell
python export.py -h
```
