# from __future__ import print_function
# from __future__ import absolute_import
# from builtins import str
# from builtins import object
from custom_antlr4 import *
from custom_antlr4.InputStream import InputStream
from custom_antlr4.tree.Tree import TerminalNodeImpl
from .JavaLexer import JavaLexer
from .JavaParser import JavaParser
try:
    import graphviz

    noGraphviz = False

except ImportError as e:
    noGraphviz = True


class JavaParse(object):
    """

    """
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.lookupTable = dict()

    # antlr-based parser

    def parse(self, file_content):
        """

        :param file_content:
        :type file_content:
        :return:
        :rtype:
        """
        inputS = InputStream(file_content)
        lexer = JavaLexer(inputS)
        stream = CommonTokenStream(lexer)
        parser = JavaParser(stream)
        tree = parser.compilationUnit()
        self.lookupTable = dict()
        self.numerify(tree)
        return tree

    def numerify(self, tree):
        """

        :param tree:
        :type tree:
        """
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
        """

        :param tree:
        :type tree:
        """
        try:
            for child in tree.getChildren():
                self.toString(child)
        except AttributeError:
            print("Index: ", tree.nodeIndex, "Text: ", tree.getText())

    def seekAllNodes(self, subTree, nodeType):
        """

        :param subTree:
        :type subTree:
        :param nodeType:
        :type nodeType:
        :return:
        :rtype:
        """
        seekList = list()

        if isinstance(subTree, nodeType):
            seekList.append(subTree)

        try:
            for child in subTree.getChildren():
                seekList.extend(self.seekAllNodes(child, nodeType))
        except AttributeError:
            pass

        return seekList

    ## Deprecated
    def seek(self, myTree, type):
        """

        :param myTree:
        :type myTree:
        :param type:
        :type type:
        :return:
        :rtype:
        """
        seekList = list()

        if isinstance(myTree, type):
            seekList.append(myTree.nodeIndex)

        try:
            for child in myTree.getChildren():
                seekList.extend(self.seek(child, type))
        except AttributeError:
            pass

        return seekList

    def seekFirstMatchingParent(self, node, type):
        """

        :param node:
        :type node:
        :param type:
        :type type:
        :return:
        :rtype:
        """
        try:
            parent = node.parentCtx
        except:
            return None

        if isinstance(parent, type):
            return parent

        return self.seekFirstMatchingParent(parent, type)

    def seekNode(self, myTree, nodeIndex):
        """

        :param myTree:
        :type myTree:
        :param nodeIndex:
        :type nodeIndex:
        :return:
        :rtype:
        """
        if myTree.nodeIndex == nodeIndex:
            return 0

        try:
            for child in myTree.getChildren():
                nodeFound = self.seekNode(child, nodeIndex)
                if nodeFound is not None:
                    return nodeFound + 1
        except AttributeError:
            pass

        return None

    def getNode(self, myTree, index):
        """

        :param myTree:
        :type myTree:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        if index in self.lookupTable:
            return self.lookupTable[index]

        stack = list()
        stack.append(myTree)

        while len(stack) > 0:
            tmp = stack.pop()
            if tmp.nodeIndex not in self.lookupTable:
                self.lookupTable[tmp.nodeIndex] = tmp

            if tmp.nodeIndex == index:
                return tmp
            else:
                if tmp.getChildCount() != 0:
                    stack.extend(tmp.children)

        return None

    def setNode(self, myTree, index, node):
        """

        :param myTree:
        :type myTree:
        :param index:
        :type index:
        :param node:
        :type node:
        """
        if myTree.nodeIndex == index:
            myTree = node

        if myTree.getChildCount() != 0:
            for child in myTree.children:
                # print myTree.nodeIndex, child.nodeIndex
                self.setNode(child, index, node)

    def distance(self, myTree, node1, node2):
        """

        :param myTree:
        :type myTree:
        :param node1:
        :type node1:
        :param node2:
        :type node2:
        :return:
        :rtype:
        """
        rootDistance1 = self.seekNode(myTree, node1)
        rootDistance2 = self.seekNode(myTree, node2)

        if rootDistance1 > rootDistance2:
            distance = self.seekNode(self.getNode(myTree, node2), node1)

        elif rootDistance1 < rootDistance2:
            distance = self.seekNode(self.getNode(myTree, node1), node2)

        else:
            distance = 0 if node1 == node2 else None

        return distance if distance is not None else -1

    def tree2DOT(self, tree):
        """

        :param tree:
        :type tree:
        :return:
        :rtype:
        """
        if noGraphviz:
            return

        assert isinstance(tree, JavaParser.CompilationUnitContext)

        nodeStack = list()
        nodes = list()
        parent = dict()

        nodeStack.append(tree)

        nodes.append(type(tree).__name__ + " " + str(tree.nodeIndex))

        while len(nodeStack) > 0:

            tmp = nodeStack.pop()
            if tmp.getChildCount() > 0:
                nodeStack.extend(tmp.children)
                for child in tmp.children:
                    childID = type(child).__name__ + " " + str(child.nodeIndex)
                    nodes.append(childID)
                    parent[childID] = type(tmp).__name__ + " " + str(tmp.nodeIndex)

            if isinstance(tmp, TerminalNodeImpl):
                tokenID = "\"" + str(tmp.symbol.text) + "\" " + str(tmp.nodeIndex)
                nodes.append(tokenID)
                parent[tokenID] = type(tmp).__name__ + " " + str(tmp.nodeIndex)

        graph = graphviz.Digraph()

        for node in nodes:
            graph.node(node)
            try:
                graph.edge(parent[node], node)
            except KeyError as e:
                pass

        graph.render("img/tree")
