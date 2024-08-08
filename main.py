import functions as sub

def main():
  
  sub.clear()

  print("""INFO
Version: 1.3.1
Last updated: 08/08/2024

INSTRUCTION
        
You will interact with the program by choosing a number among a list of options. When prompted, type in the number
that corresponds to your choice then press the enter/return key.
        
For example, choose among the following options:
1. Option #1
2. Option #2
  
Your choice: _[type in 1 or 2 then press Enter]_

* Valid inputs: _1_ or _2_
* Invalid inputs: _abc_ ; _13_ ; _'1'_ ; _[2]_
        

To run the program, you must first upload a .csv or .xlsx file containing the organizations you wish to analyze.
You can quit the program by selecting 2 in the main menu or terminate the terminal. 
""")
  while True:
    file = sub.mainMenu()
    try:
      sub.mainActions(file)
    except:
      continue

if __name__ == '__main__':
  main()