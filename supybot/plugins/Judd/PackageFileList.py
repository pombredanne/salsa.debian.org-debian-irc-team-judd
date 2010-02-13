class PackageFileList:

    def __init__(self):
        self.packages = {}

    #def moo(self):
        #print "moo"

    def add(self, f, p):
        for pack in p:
            if not pack in self.packages.keys():
                self.packages[pack] = []
            self.packages[pack].append(f)

    def toString(self, boldfn):
        s = []
        for p in self.packages.keys():
            section,name = p.split('/')
            s.append("%s: %s" % (boldfn(name), ", ".join(self.packages[p])))
        return "; ".join(s)

    def __len__(self):
        return len(self.packages.keys())

    def __str__(self):
        s = []
        for p in self.packages.keys():
            section,name = p.split('/')
            s.append("%s: %s" % (name, ", ".join(self.packages[p])))
        return "; ".join(s)
