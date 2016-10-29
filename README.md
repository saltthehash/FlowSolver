# FlowSolver
Solves Flow Free and Flow Free Bridges puzzles.

For more information on Flow Free and Flow Free Bridges, check out [Big Duck Games](https://blog.bigduckgames.com/).

## Usage
```
./flow_bridges_sat.py
```

Once you execute the script, you have two options:
1. Read an input file (in the correct format)
2. Type the game into the command prompt (intructions are given on correct format)

If the puzzle is solvable, a color coded solution will be displayed.

## Input Format

When reading puzzle input from a text file, you must follow the specified format:
* Each empty square in the Flow puzzle grid (i.e., squares that start without any color in them) should be represented by the asterisk character "*" (without quotes)
* If inputting a Flow Bridges puzzle, a bridge must be represented by the equal sign character, "=" (without quotes)
* Each color endpoint must be represented by some character that is not "*" or "+", as these are reserved (explained above). There should be two endpoints per color, and they must be represented by the same character.
  * NOTE: currently the file input format assumes that you will use sequential hexidecimal digits starting from 0 to represent each distinct color in order to easily map the color to a number (Flow puzzles seem to have a maximum of 16 colors). However, this will be soon changed so arbitrary characters can be chosen, such as the first letter of the corresponding color.
* Every row in the grid should be separated by a newline character ("\n")
If you choose to type the puzzle directly into the program, use the same guidelines (except that you don't need to use sequential hex digits).

### Example Inputs
####Flow Free Puzzle
![Flow Free puzzle](https://github.com/saltthehash/FlowSolver/blob/master/flow_example.png)

####ASCII Input Format
```
0*1*2
**3*4
*****
*1*2*
*034*
```

Here is an example of a Bridges puzzle.
####Flow Free Bridges Puzzle
![Flow Free Bridges Puzzle](https://github.com/saltthehash/FlowSolver/blob/master/bridges_example.png)

####ASCII Input Format
```
01*23
**+**
**1**
*23*4
04***
```
