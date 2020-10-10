from typing import Dict

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

    def seekFirstMatchingParent(self, node, nodeType):
        """

        :param node:
        :type node:
        :param nodeType:
        :type nodeType:
        :return:
        :rtype:
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

    def getInMethodLines(self, tree: JavaParser.CompilationUnitContext) -> list:
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

    def getLinesOfCodePerMethod(self, tree: JavaParser.CompilationUnitContext) -> dict:
        """

        :param tree:
        :type tree:
        :return:
        :rtype:
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

        :param tree:
        :type tree:
        :return:
        :rtype:
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

        :param tree:
        :type tree:
        :return:
        :rtype:
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

        :param tree:
        :type tree:
        :param nodeIndex:
        :type nodeIndex:
        :return:
        :rtype:
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

        :param node:
        :type node:
        :return:
        :rtype:
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

        :param methodBody:
        :type methodBody:
        :return:
        :rtype:
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

        :param tree:
        :type tree:
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

        :param tree:
        :type tree:
        :return:
        :rtype:
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
