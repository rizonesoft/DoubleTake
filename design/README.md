# DoubleTake design

Everything needed to build DoubleTake's interface exactly as designed.

Start with [`SPEC.md`](SPEC.md). It is the source of truth: every screen, state, measurement, key and line of text.

| Path | Contents |
| --- | --- |
| [`SPEC.md`](SPEC.md) | The interface specification for the chosen direction, Darkroom |
| [`tokens.json`](tokens.json) | Colours, type styles, radii and sizes, read by the build to generate the app's theme |
| [`mockups/darkroom/`](mockups/darkroom/) | One `.dc.html` file per screen, with every measurement as an inline style, and `canvas.json`, their layout on the design canvas |
| [`brand/`](brand/) | The icon sources. Every raster (the `.ico`, banners, installer images) is generated from these and `tokens.json`, never drawn by hand |

## Reading a mockup

Each `.dc.html` file is plain HTML with inline styles, so sizes, gaps, colours and text can be read straight from the source. The sample data sits in the script block at the end of the file. The files render on the design canvas they came from; a browser alone shows them unstyled, because the canvas supplies the runtime script.

| Screen | Mockup | SPEC |
| --- | --- | --- |
| Scan | `Scan.dc.html` | 4 |
| Scanning | `Scanning.dc.html` | 5 |
| Review | `Review.dc.html` | 6 |
| History | `History.dc.html` | 7 |
| Settings and About | `Settings.dc.html` | 8 |
| Recycle dialog and update notice | `Dialogs.dc.html` | 9 |
| Icon, wordmark and colours | `Brand.dc.html` | 13 |
| GitHub banner, social preview and share card | `Banners.dc.html` | 13 |

Three directions were explored on 2026-11-16 (Twin Frame, Darkroom, Contact Sheet). The owner chose Darkroom; the other two are not kept in the repository.
