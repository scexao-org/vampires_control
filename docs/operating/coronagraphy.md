# Coronagraphy

VAMPIRES has a suite of classic Lyot-style coronagraphs (CLC) comprised of four focal plane masks and a single Lyot stop.

## Focal Plane Masks

The focal plane masks for VAMPIRES are comprised of four opaque circular masks, each with their own 3" x 3" fieldstop. Each mask corresponds to roughly 2, 3, 5, and 7 $\lambda/D$ inner working angle (IWA).

| Mask | IWA (mas) | Notes |
| - | - | - |
| CLC-2 | 37 | Hard to use, lots of leakage |
| CLC-3 | 59 | Typical mask for polarimetric observations or good wavefront correction |
| CLC-5 | 104 | Typical mask for mediocre wavefront correction |
| CLC-7 | 150 | Not well-matched to Lyot stop |

```{image} 20230913_vampires_iwa.png
```

### Alignment

## Lyot Stops

There is currently one Lyot stop designed for use with the coronagraphs, however we note that you can run without a Lyot stop for maximum sensitivity when diffraction control is less necessary.

| Stop | Throughput (%) | Notes |
| - | - | - |
| LyotStop | 62.8 | |

```{image} lyotstop.png
```

### Alignment

It is best to align the Lyot stop with `vpupcam`- the viewer has built-in keyboard shortcuts for roughly and finely adjusting x, y, and theta of the mask wheel.

```
sonne $ vpupcam.py &
```
To insert the 

### Advanced Details

The focal plane masks and Lyot stop are patterned using metalliv vapor deposition on top of an AR-coated optical flat (EO #)

```{image} focal_plane_masks.jpeg
:width: 600 px
```


