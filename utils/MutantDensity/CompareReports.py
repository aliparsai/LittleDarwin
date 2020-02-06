import sys

r1 = open(sys.argv[1],'r')
r2 = open(sys.argv[2],'r')
r1name = sys.argv[3]
r2name = sys.argv[4]
r1dict = dict()
r2dict = dict()


for line in r1:
    name, value = line.strip('\n').split(',')
    r1dict[name] = value

for line in r2:
    name, value = line.strip('\n').split(',')
    r2dict[name] = value

names = set(r1dict.keys())
names.update(set(r2dict.keys()))

with open("result.csv", 'w') as result:
    result.write("Name,"+r1name+','+r2name+'\n')
    namesList = sorted(list(names))
    for name in namesList:
        result.write(name+','+(r1dict[name] if name in r1dict.keys() else '0')+','+(r2dict[name] if name in r2dict.keys() else '0')+'\n')
