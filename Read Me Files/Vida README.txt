======================================================================
            VIDA - Tree and Forest Growth Simulation Software
======================================================================

Version 0.9: 2017.10.12
-----------------------

VIDA is a software suite that attempts to model the growth of individual trees using empiriclly derived--or randomly chosen--values for use with allometric relationships. By modeling the behavior of an individual tree, it is possible to model population dynamics in a spatially explicit simulationspace. 

This is a development release.

email: seanth@gmail.com

DEPENDENCIES/REQUIREMENTS
-------------------------

 * Python v2.7 (http://python.org/download/)
 * pyYAML v3.11 (http://pyyaml.org/wiki/PyYAML)
 * ContextFree v3.0.8 (optional. Needed to generate graphics. http://www.contextfreeart.org/download/ContextFreeSource3.0.8.tgz)
   * Apple users can make use of Homebrew (http://brew.sh/) to install the command line version of cfdg using the following commands:
			brew tap kn1kn1/cfdg
			brew install cfdg
 * ffmpeg for making videos.
		Apple users can make use of Homebrew (http://brew.sh/) to install ffmpeg:
			brew install ffmpeg

On an *buntu Linux system you can acquire most dependences with:

   sudo pip3 install configparser
   sudo apt install contextfree

HOW TO USE
----------
After installing all the dependencies necessary, simply `cd` to the VIDA folder and, in the simplest form, type:

    python VIDA.py

For more information, including command line options and ways to make species, event files and define planting locations, please see `VIDA HOWTO.txt`

EXAMPLES
--------
For more examples, including command line options and ways to make species, event files and define planting locations, please see `VIDA HOWTO.txt`

RECOMMENDATIONS
---------------
Previous versions of Vida used Psyco (http://psyco.sourceforge.net/) with excellent results. On going tests of using PyPy (http://pypy.org/) have yielded comparable results. Since Psyco isn't being actively developed anymore, I recommend you use PyPy.
