import sys
import shelve

try:
    mutationDatabase = shelve.open(sys.argv[1], "r")

except Exception:
    print("Error opening database.")
    sys.exit(1)

lengths = list()

for key in mutationDatabase.keys():
    lengths.append(len(mutationDatabase[key]))

lengths.sort()
lengthsStr = [ str(l) for l in  lengths]

with open(sys.argv[2], 'w') as output:
    output.write("\n".join(lengthsStr))
