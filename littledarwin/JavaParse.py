from typing import Dict

from antlr4 import *
from antlr4.InputStream import InputStream
from antlr4.error.ErrorStrategy import BailErrorStrategy
from antlr4.tree.Tree import TerminalNodeImpl

from .JavaLexer import JavaLexer
from .JavaParser import JavaParser

try:
    import graphviz

    noGraphviz = False
except ImportError as e:
    noGraphviz = True


class LittleDarwinErrorStrategy(BailErrorStrategy):
    """
    This class is a custom error strategy for the ANTLR4 parser. It is used
    to handle parsing errors by throwing an exception, which allows the file
    to be safely ignored.
    """
    def recover(self, parser: Parser, exception: RecognitionException):
        """
        This method is called when the parser encounters a syntax error.

        :param parser: The parser that encountered the error.
        :type parser: antlr4.Parser
        :param exception: The recognition exception.
        :type exception: antlr4.RecognitionException
        """
        parser._errHandler.reportError(parser, exception)
        super().recover(parser, exception)


class JavaParse(object):
    """
    This class uses ANTLR4 to parse Java source code. It provides methods for
    traversing and analyzing the parse tree, such as finding nodes of a
    specific type, getting the cyclomatic complexity of a method, and getting
    the name of the method that contains a specific node.
    """

    def __init__(self, verbose=False):
        """
        Initializes the JavaParse object.

        :param verbose: A boolean indicating whether to print verbose output.
        :type verbose: bool
        """
        self.verbose = verbose
        self.lookupTable = dict()

    # antlr-based parser
    def parse(self, fileContent):
        """
        Parses the given Java source code and returns a parse tree.

        :param fileContent: A string containing the Java source code.
        :type fileContent: str
        :return: A parse tree representing the Java source code.
        :rtype: antlr4.tree.Tree.ParseTree
        """
        lexer = JavaLexer(InputStream(fileContent))
        parser = JavaParser(CommonTokenStream(lexer))
        parser._errHandler = LittleDarwinErrorStrategy()
        tree = parser.compilationUnit()
        self.lookupTable = dict()
        self.numerify(tree)

        return tree

    def numerify(self, tree):
        """
        Adds a unique ``nodeIndex`` to each node in the parse tree. This is
        used to identify nodes when creating mutations.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        """
        assert isinstance(tree, RuleContext)

        numerifyCounter = 1
        queue = [tree]

        while len(queue) > 0:
            node = queue.pop(0)
            node.nodeIndex = numerifyCounter
            numerifyCounter += 1
            queue.extend(getattr(node, 'children', []))

    def toString(self, tree):
        """
        Prints the text of all nodes in the parse tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        """
        try:
            for child in tree.getChildren():
                self.toString(child)
        except AttributeError:
            print("Index: ", tree.nodeIndex, "Text: ", tree.getText())

    def seekAllNodes(self, tree, nodeType):
        """
        Finds all nodes of a specific type in the parse tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param nodeType: The type of node to search for.
        :type nodeType: type
        :return: A list of nodes of the specified type.
        :rtype: list
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
        DEPRECATED. Finds all nodes of a specific type in the parse tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param type: The type of node to search for.
        :type type: type
        :return: A list of node indices of the specified type.
        :rtype: list
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

    def seekFirstMatchingParent(self, node, nodeType):
        """
        Finds the first parent of a node that matches the specified type.

        :param node: The node to start the search from.
        :type node: antlr4.tree.Tree.ParseTree
        :param nodeType: The type of parent node to search for.
        :type nodeType: type
        :return: The first matching parent node, or None if no matching parent
                 is found.
        :rtype: antlr4.tree.Tree.ParseTree
        """
        try:
            parent = node.parentCtx
        except:
            return None

        if isinstance(parent, nodeType):
            return parent

        return self.seekFirstMatchingParent(parent, nodeType)

    def seekNode(self, tree, nodeIndex):
        """
        Finds a node in the parse tree by its index.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param nodeIndex: The index of the node to find.
        :type nodeIndex: int
        :return: The depth of the node in the tree, or None if the node is not
                 found.
        :rtype: int
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
        Gets a node from the parse tree by its index.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param index: The index of the node to get.
        :type index: int
        :return: The node with the specified index, or None if the node is not
                 found.
        :rtype: antlr4.tree.Tree.ParseTree
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
        Sets a node in the parse tree at a specific index.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param index: The index of the node to set.
        :type index: int
        :param node: The new node.
        :type node: antlr4.tree.Tree.ParseTree
        """
        if tree.nodeIndex == index:
            tree = node

        if tree.getChildCount() != 0:
            for child in tree.children:
                # print myTree.nodeIndex, child.nodeIndex
                self.setNode(child, index, node)

    def distance(self, tree, node1, node2):
        """
        Calculates the distance between two nodes in the parse tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param node1: The index of the first node.
        :type node1: int
        :param node2: The index of the second node.
        :type node2: int
        :return: The distance between the two nodes, or -1 if they are not in
                 the same subtree.
        :rtype: int
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

    def getInMethodLines(self, tree: JavaParser.CompilationUnitContext) -> list:
        """
        Gets a list of all line numbers that are within a method.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :return: A sorted list of line numbers.
        :rtype: list
        """
        methodBodyList = self.seekAllNodes(tree, JavaParser.MethodBodyContext)
        methodBodyList.extend(self.seekAllNodes(tree, JavaParser.ConstructorBodyContext))

        lines = set()

        for methodBody in methodBodyList:
            terminalNodeList = self.seekAllNodes(methodBody, TerminalNodeImpl)
            for terminalNode in terminalNodeList:
                lines.add(terminalNode.symbol.line)

        return sorted(lines)

    def getLinesOfCodePerMethod(self, tree: JavaParser.CompilationUnitContext) -> dict:
        """
        Gets the number of lines of code for each method in the parse tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :return: A dictionary mapping method names to the number of lines of
                 code.
        :rtype: dict
        """
        methodBodyList = self.seekAllNodes(tree, JavaParser.MethodBodyContext)
        methodBodyList.extend(self.seekAllNodes(tree, JavaParser.ConstructorBodyContext))

        linesOfCodePerMethod = dict()

        for methodBody in methodBodyList:
            lines = set()
            terminalNodeList = self.seekAllNodes(methodBody, TerminalNodeImpl)
            for terminalNode in terminalNodeList:
                lines.add(terminalNode.symbol.line)

            linesOfCodePerMethod[self.getMethodNameForNode(tree, methodBody.nodeIndex)] = len(lines)

        return linesOfCodePerMethod

    def getText(self, tree: RuleContext):
        """
        Gets the text of a node and all its children.

        :param tree: The root of the node.
        :type tree: antlr4.tree.Tree.ParseTree
        :return: A string containing the text of the node and its children.
        :rtype: str
        """
        if tree is None:
            return None

        resultList = []
        childQueue = [tree]

        while len(childQueue) > 0:
            child = childQueue.pop(0)

            if isinstance(child, TerminalNodeImpl):
                resultList.append(str(child.getText()))
            try:
                childQueue[0:0] = child.getChildren()
            except AttributeError:
                pass

        return " ".join(resultList)

    def getMethodRanges(self, tree: JavaParser.CompilationUnitContext) -> dict:
        """
        Gets the start and end character indices for each method in the parse
        tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :return: A dictionary mapping method names to a tuple of (start, stop)
                 character indices.
        :rtype: dict
        """
        methodDeclarationList = self.seekAllNodes(tree, JavaParser.MethodDeclarationContext)
        methodDeclarationList.extend(self.seekAllNodes(tree, JavaParser.ConstructorDeclarationContext))
        resultDict = dict()

        for methodDeclaration in methodDeclarationList:
            gotName = False
            gotStartStop = False
            for index in range(0, len(methodDeclaration.children)):
                if isinstance(methodDeclaration.children[index], JavaParser.FormalParametersContext):
                    assert isinstance(methodDeclaration.children[index - 1], TerminalNodeImpl)
                    methodName = methodDeclaration.children[index - 1].symbol.text + self.getText(
                        methodDeclaration.children[index])
                    gotName = True

                if isinstance(methodDeclaration.children[index], JavaParser.MethodBodyContext):
                    methodStartStop = (
                        methodDeclaration.children[index].start.start, methodDeclaration.children[index].stop.stop)
                    gotStartStop = True

            if gotName and gotStartStop:
                resultDict[methodName] = methodStartStop

        return resultDict

    def getMethodNameForNode(self, tree: JavaParser.CompilationUnitContext, nodeIndex: int):
        """
        Gets the name of the method that contains the node with the specified
        index.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :param nodeIndex: The index of the node.
        :type nodeIndex: int
        :return: The name of the method, or "***not in a method***" if the node
                 is not in a method.
        :rtype: str
        """
        methodName = None
        node = self.getNode(tree, nodeIndex)
        methodDeclaration = self.seekFirstMatchingParent(node, JavaParser.MethodDeclarationContext)
        if methodDeclaration is None:
            methodDeclaration = self.seekFirstMatchingParent(node, JavaParser.ConstructorDeclarationContext)
        if methodDeclaration is None:
            return "***not in a method***"

        for index in range(0, len(methodDeclaration.children)):
            if isinstance(methodDeclaration.children[index], JavaParser.FormalParametersContext):
                assert isinstance(methodDeclaration.children[index - 1], TerminalNodeImpl)
                methodName = methodDeclaration.children[index - 1].symbol.text + self.getText(
                    methodDeclaration.children[index])

        classDeclaration = self.seekFirstMatchingParent(node, JavaParser.ClassDeclarationContext)
        if classDeclaration is None:
            return methodName

        for index in range(0, len(classDeclaration.children)):
            if isinstance(classDeclaration.children[index - 1], TerminalNodeImpl) and \
                    isinstance(classDeclaration.children[index], TerminalNodeImpl) and \
                    classDeclaration.children[index - 1].symbol.text == 'class':
                return classDeclaration.children[index].symbol.text + '.' + methodName

    def getMethodTypeForNode(self, node):
        """
        Gets the return type of the method that contains the specified node.

        :param node: The node to check.
        :type node: antlr4.tree.Tree.ParseTree
        :return: The return type of the method, or None if the node is not in a
                 method.
        :rtype: str
        """
        parentMethod = self.seekFirstMatchingParent(node, JavaParser.MethodDeclarationContext)
        if parentMethod is None:
            return None

        assert isinstance(parentMethod, JavaParser.MethodDeclarationContext)
        parentType = parentMethod.getChild(0)

        if isinstance(parentType, JavaParser.JTypeContext):
            methodType = parentType.getChild(0)
            if isinstance(methodType, JavaParser.PrimitiveTypeContext) or \
                    isinstance(methodType, JavaParser.ClassOrInterfaceTypeContext):
                return methodType.getText()

        elif isinstance(parentType, TerminalNodeImpl):
            return "void" if parentType.getText() == "void" else None

        return None

    def getCyclomaticComplexity(self, methodBody) -> int:
        """
        Calculates the cyclomatic complexity of a method.

        :param methodBody: The MethodBodyContext or ConstructorBodyContext of
                           the method.
        :type methodBody: antlr4.tree.Tree.ParseTree
        :return: The cyclomatic complexity of the method.
        :rtype: int
        """
        assert isinstance(methodBody, JavaParser.MethodBodyContext) or \
               isinstance(methodBody, JavaParser.ConstructorBodyContext)

        cyclomaticComplexity = 1
        keywordList = self.seekAllNodes(methodBody, TerminalNodeImpl)

        for keyword in keywordList:
            keywordText = keyword.getText()
            if keywordText == "if" or \
                    keywordText == "case" or \
                    keywordText == "for" or \
                    keywordText == "while" or \
                    keywordText == "catch" or \
                    keywordText == "&&" or \
                    keywordText == "||" or \
                    keywordText == "?" or \
                    keywordText == "foreach":
                cyclomaticComplexity += 1

        return cyclomaticComplexity

    def getCyclomaticComplexityAllMethods(self, tree) -> Dict[str, int]:
        """
        Calculates the cyclomatic complexity for all methods in the parse tree.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :return: A dictionary mapping method names to their cyclomatic
                 complexity.
        :rtype: dict
        """
        assert isinstance(tree, JavaParser.CompilationUnitContext)
        cyclomaticComplexityPerMethod = dict()

        methodBodyList = self.seekAllNodes(tree, JavaParser.MethodBodyContext)
        methodBodyList.extend(self.seekAllNodes(tree, JavaParser.ConstructorBodyContext))

        for methodBody in methodBodyList:
            cyclomaticComplexityPerMethod[
                self.getMethodNameForNode(tree, methodBody.nodeIndex)] = self.getCyclomaticComplexity(methodBody)

        return cyclomaticComplexityPerMethod

    def tree2DOT(self, tree):
        """
        Converts a parse tree to a DOT representation for visualization with
        Graphviz.

        :param tree: The root of the parse tree.
        :type tree: antlr4.tree.Tree.ParseTree
        :return: A Graphviz Digraph object, or None if Graphviz is not
                 installed.
        :rtype: graphviz.Digraph
        """
        if noGraphviz:
            return None

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
