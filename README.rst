=======================
Scipion atlas plugin
=======================

This **scipion** plugin will import atlas information from acquisition software
and will provide some analysis tools to map image processing data
back to tits grid location.

It is working for EPU software and is making following assumptions:

1.- Movies can come from different grids
2.- Import path (form the import movies protocol) contains GRID_
3.- All grids folder are at the same level and are named like: GRID_XX
4.- The grid parts (GRID, GRIDSQUARE, HOLE) can be inferred from the movie "micname":

    GRID_#*_*_GridSquare_#*_*_FoilHole_#*"

    where #* represents any number of digits.

5.- EPU Metadata folder is located at:  GRID_#*/DATA/Metadata/

=====
Setup
=====

- **Install this plugin in devel mode:**

Using the command line:

.. code-block::

    scipion installp -p local/path/to/scipion-em-atlas --devel

