# Slider

A draggable slider for continuous values. Supports vertical and horizontal orientations.

## Basic usage

### Renderable API

``` astro-code
import { SliderRenderable, createCliRenderer } from "@opentui/core"

const renderer = await createCliRenderer()

const slider = new SliderRenderable(renderer, {
  id: "volume",
  orientation: "horizontal",
  width: 30,
  height: 1,
  min: 0,
  max: 100,
  value: 25,
  onChange: (value) => {
    console.log("Value:", value)
  },
})

renderer.root.add(slider)
```

## Vertical slider

``` astro-code
const slider = new SliderRenderable(renderer, {
  orientation: "vertical",
  width: 2,
  height: 10,
  min: 0,
  max: 1,
  value: 0.5,
})
```

## Construct API

> Not available yet. Use `SliderRenderable` for now.

## Properties

| Property          | Type                           | Default      | Description                    |
|-------------------|--------------------------------|--------------|--------------------------------|
| `orientation`     | `"vertical"` or `"horizontal"` | \-           | Slider direction               |
| `value`           | `number`                       | `min`        | Current value                  |
| `min`             | `number`                       | `0`          | Minimum value                  |
| `max`             | `number`                       | `100`        | Maximum value                  |
| `viewPortSize`    | `number`                       | range \* 0.1 | Thumb size relative to content |
| `backgroundColor` | `string` or `RGBA`             | \-           | Track color                    |
| `foregroundColor` | `string` or `RGBA`             | \-           | Thumb color                    |
| `onChange`        | `(value: number) => void`      | \-           | Fired when value changes       |


---

_Source: https://opentui.com/docs/components/slider
_Downloaded: 2026-05-21 19:04:57 UTC_
