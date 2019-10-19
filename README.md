# Mopidy-Lagukan

Lagukan is a music recommendation service, and this extension allows it to
control which songs Mopidy plays. Lagukan will learn your preferences based on
what you skip. See https://lagukan.com.

[![Lagukan Demo](https://lagukan.com/img/desktop_cropped.png)](https://youtu.be/Rr2R1fSZwPo)

## Installation

Install by running:

```
pip install Mopidy-Lagukan
```

## Configuration

By default, Lagukan will open in your browser automatically when you start mopidy. This is because
Lagukan will only work while the browser window is open. You can disable this by setting the `autorun`
config option:

```
[lagukan]
autostart = false
```
