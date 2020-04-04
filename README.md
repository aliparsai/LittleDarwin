![](https://github.com/aliparsai/LittleDarwin/workflows/LittleDarwin%20Test%20Suite/badge.svg)
![](https://github.com/aliparsai/LittleDarwin/workflows/Build%20and%20Deploy/badge.svg)
# LittleDarwin 

Java Mutation Analysis Framework
Copyright (C) 2014-2020 Ali Parsai

## How to Use:
On your selected python platform use:

    pip3 install littledarwin

You can use the program by executing it as a module:

    python3 -m littledarwin [options]

For a maven project, all you need to do is to pass the required arguments to LittleDarwin:

    python3 -m littledarwin -m -b \
			    -p [path to production code (usually in src/main)] \
			    -t [path to build directory (usually the one containing pom.xml)] \
			    --timeout=[in seconds, the duration of a normal test execution] \
			    -c [build command separated by commas (usually mvn,clean,test)]


------------------------------------------------------------------------------------
## License
This program is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT 
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

------------------------------------------------------------------------------------
Find me at:

[parsai.net](http://www.parsai.net)

------------------------------------------------------------------------------------


