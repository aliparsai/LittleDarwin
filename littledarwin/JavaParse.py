# from __future__ import print_function
# from __future__ import absolute_import
# from builtins import str
# from builtins import object
import antlr4
from antlr4 import *
from antlr4.InputStream import InputStream
from antlr4.tree.Tree import TerminalNodeImpl
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

    def parse(self, fileContent):
        """

        :param fileContent:
        :type fileContent:
        :return:
        :rtype:
        """
        lexer = JavaLexer(InputStream(fileContent))
        parser = JavaParser(CommonTokenStream(lexer))
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

    def seekAllNodes(self, tree, nodeType):
        """

        :param tree:
        :type tree:
        :param nodeType:
        :type nodeType:
        :return:
        :rtype:
        """
        resultList = list()
        seekStack = [tree]

        while len(seekStack) > 0:
            node = seekStack.pop()
            if isinstance(node, nodeType):
                resultList.append(node)

            try:
                seekStack.extend(node.getChildren())
            except AttributeError:
                pass

        return resultList

    ## Deprecated
    def seek(self, tree, type):
        """

        :param tree:
        :type tree:
        :param type:
        :type type:
        :return:
        :rtype:
        """
        seekList = list()

        if isinstance(tree, type):
            seekList.append(tree.nodeIndex)

        try:
            for child in tree.getChildren():
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

    def seekNode(self, tree, nodeIndex):
        """

        :param tree:
        :type tree:
        :param nodeIndex:
        :type nodeIndex:
        :return:
        :rtype:
        """
        if tree.nodeIndex == nodeIndex:
            return 0

        try:
            for child in tree.getChildren():
                nodeFound = self.seekNode(child, nodeIndex)
                if nodeFound is not None:
                    return nodeFound + 1
        except AttributeError:
            pass

        return None

    def getNode(self, tree, index):
        """

        :param tree:
        :type tree:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        if index in self.lookupTable:
            return self.lookupTable[index]

        stack = list()
        stack.append(tree)

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

    def setNode(self, tree, index, node):
        """

        :param tree:
        :type tree:
        :param index:
        :type index:
        :param node:
        :type node:
        """
        if tree.nodeIndex == index:
            tree = node

        if tree.getChildCount() != 0:
            for child in tree.children:
                # print myTree.nodeIndex, child.nodeIndex
                self.setNode(child, index, node)

    def distance(self, tree, node1, node2):
        """

        :param tree:
        :type tree:
        :param node1:
        :type node1:
        :param node2:
        :type node2:
        :return:
        :rtype:
        """
        rootDistance1 = self.seekNode(tree, node1)
        rootDistance2 = self.seekNode(tree, node2)

        if rootDistance1 > rootDistance2:
            distance = self.seekNode(self.getNode(tree, node2), node1)

        elif rootDistance1 < rootDistance2:
            distance = self.seekNode(self.getNode(tree, node1), node2)

        else:
            distance = 0 if node1 == node2 else None

        return distance if distance is not None else -1

    def getInMethodLines(self, tree: JavaParser.CompilationUnitContext):
        """

        :param tree:
        :type tree:
        :return:
        :rtype:
        """
        methodBodyList = self.seekAllNodes(tree, JavaParser.MethodBodyContext)
        methodBodyList.extend(self.seekAllNodes(tree, JavaParser.ConstructorBodyContext))

        lines = set()

        for methodBody in methodBodyList:
            terminalNodeList = self.seekAllNodes(methodBody, TerminalNodeImpl)
            for terminalNode in terminalNodeList:
                lines.add(terminalNode.symbol.line)

        return sorted(lines)

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
