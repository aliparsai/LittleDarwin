from JavaListener import JavaListener
from antlr4.InputStream import InputStream
from antlr4 import *
from JavaLexer import JavaLexer
from JavaParser import JavaParser


class JavaParse(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    # antlr-based parser


    def parse(self, file_content):
        inputS = InputStream.InputStream(file_content)
        lexer = JavaLexer(inputS)
        stream = CommonTokenStream(lexer)
        parser = JavaParser(stream)
        tree = parser.compilationUnit()
        # tree.getText()
        return tree


    def numerify(self, tree):
        numerifyCounter = 1
        stack = list()
        stack.append(tree)
        while len(stack) > 0:
            tmp = stack.pop()
            tmp.nodeIndex = numerifyCounter
            numerifyCounter += 1
            if tmp.getChildCount() > 0:
                stack.extend(tmp.children)

    def toString(self, tree):
        try:
            for child in tree.getChildren():
                self.toString(child)
        except AttributeError:
            print "Index: ", tree.nodeIndex, "Text: ", tree.getText()


    def seek(self, tree, type):
        seekList = list()

        if isinstance(tree, type):
            seekList.append(tree.nodeIndex)

        try:
            for child in tree.getChildren():
                seekList.extend(self.seek(child, type))
        except AttributeError:
            pass

        return seekList

    def getNode(self, myTree, index):
        stack = list()
        stack.append(myTree)

        while len(stack) > 0:
            tmp = stack.pop()

            if tmp.nodeIndex == index:
                return tmp
            else:
                if tmp.getChildCount() != 0:
                    stack.extend(tmp.children)

        return None

    def setNode(self, myTree, index, node):
        if myTree.nodeIndex == index:
            myTree = node

        if myTree.getChildCount() != 0:
            for child in myTree.children:
                # print myTree.nodeIndex, child.nodeIndex
                self.setNode(child, index, node)



