"""High-level helpers for parsing Java code using ANTLR-generated classes."""
from typing import Dict

from antlr4 import *
from antlr4.InputStream import InputStream
from antlr4.error.ErrorStrategy import BailErrorStrategy
from antlr4.tree.Tree import TerminalNodeImpl
import antlr4.tree.Tree as Tree_
import inspect

from mediumdarwin.JavaLexer import JavaLexer
from mediumdarwin.JavaParser import JavaParser
import json

try:
    import graphviz

    noGraphviz = False
except ImportError as e:
    noGraphviz = True


class LittleDarwinErrorStrategy(BailErrorStrategy):
    """
    A class to handle parsing exceptions. Throws exceptions when occured so that the file can safely be ignored.
    """

    def recover(self, parser: Parser, exception: RecognitionException):
        """

        :param parser:
        :type parser:
        :param exception:
        :type exception:
        """
        parser._errHandler.reportError(parser, exception)
        super().recover(parser, exception)


class JavaParse(object):
    """ """

    ENUM_CONTEXT_ID = 1
    CLASS_BODY_CONTEXT_ID = 2

    MUTATION_TYPE_COMPILE_TIME = 6
    max_depth = 0

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.lookupTable = dict()
        self.generate_dict_of_classes()

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
        parser._errHandler = LittleDarwinErrorStrategy()
        tree = parser.compilationUnit()
        self.lookupTable = dict()
        (tree, json_result, index) = self.numerify(tree, 0, 0, 0)
        # self.numerify(tree)

        return tree

    def numerify(self, tree, index, contextID, mutationType, depth=0, timer=[0]):
        """

        :param tree:
        :type tree:
        :return:
        :rtype:
        """

        if (depth > self.max_depth):
            self.max_depth = depth

        # We need to treat the mutations in enum files differently as `static` keyword cannot be used to add `static ENV_VAR_MAP`
        if (isinstance(tree, JavaParser.ClassDeclarationContext) or isinstance(tree, JavaParser.InterfaceDeclarationContext)):
            contextID = JavaParse.CLASS_BODY_CONTEXT_ID
        if (contextID == 0 and isinstance(tree, JavaParser.EnumDeclarationContext)):
            contextID = JavaParse.ENUM_CONTEXT_ID

        if tree is None:
            return None
        try:
            tree.in_time = timer[0]
        except Exception:
            assert False
        timer[0] += 1
        if isinstance(tree, JavaParser.ConstantExpressionContext):
            mutationType = JavaParse.MUTATION_TYPE_COMPILE_TIME
        if isinstance(tree, JavaParser.MemberDeclarationContext):
            # check for variables in function as well. localVariableDeclaration
            for child in tree.parentCtx.getChildren():
                if isinstance(child, JavaParser.ModifierContext):
                    if child.getText() == "final":
                        mutationType = JavaParse.MUTATION_TYPE_COMPILE_TIME
        if isinstance(tree, JavaParser.InterfaceBodyDeclarationContext):
            # check for variables in function as well. localVariableDeclaration
            for child in tree.getChildren():
                if isinstance(child, JavaParser.ModifierContext):
                    if child.getText() == "final":
                        mutationType = JavaParse.MUTATION_TYPE_COMPILE_TIME
        if isinstance(tree, JavaParser.ExpressionContext):
            if mutationType == 0 or mutationType == 7:
                mutationType = 1
        if isinstance(tree, JavaParser.StatementExpressionContext):
            mutationType = 2
        if isinstance(tree, JavaParser.CreatorContext):

            mutationType = 10
            tree.parentCtx.mutationType = 10
        if isinstance(tree, JavaParser.ExpressionListContext):
            if mutationType != 5:

                mutationType = 3
        if isinstance(tree, JavaParser.VariableInitializerContext):
            if mutationType != JavaParse.MUTATION_TYPE_COMPILE_TIME:

                mutationType = 4
        if isinstance(tree, JavaParser.ForUpdateContext) or isinstance(tree, JavaParser.ForInitContext):

            mutationType = 5
        if isinstance(tree, JavaParser.MethodBodyContext):

            mutationType = 7
        if isinstance(tree, JavaParser.MethodDeclarationContext):

            mutationType = 9
        if isinstance(tree, TerminalNodeImpl):
            if tree.symbol.text == "return":
                mutationType = 1
                tree.parentCtx.mutationType = 1
                tree.parentCtx.getChild(1).mutationType = 8

        json_result = dict()
        json_result["type"] = type(tree).__name__
        tree.nodeIndex = index
        json_result["nodeIndex"] = index

        if (not hasattr(tree, "mutationType")):
            tree.mutationType = mutationType
        else:
            mutationType = tree.mutationType
        json_result["mutationType"] = tree.mutationType

        tree.contextID = contextID
        if (tree.getText() == "return"):
            tree.node_depth = depth-1
        else:
            tree.node_depth = depth
        json_result["contextID"] = contextID
        if isinstance(tree, TerminalNodeImpl):
            json_result["text"] = tree.getText()
            tree.out_time = timer[0]
            return (tree, json_result, index)
        else:
            json_result["text"] = "None"
        json_result["children"] = list()

        try:
            for child in tree.getChildren():
                index += 1
                (child, json_result_child, index) = self.numerify(
                    child, index, contextID, mutationType, depth=depth+1, timer=timer
                )
                if (mutationType == 2 or mutationType == 5):
                    if isinstance(child, TerminalNodeImpl):
                        if (child.getText() == '=' or child.getText() == '|=' or child.getText() == '*=' or child.getText() == '/=' or child.getText() == '+=' or child.getText() == '^=' or child.getText() == '-=' or child.getText() == '(' or child.getText() == "new" or child.getText() == '['):
                            mutationType = 0

                json_result["children"].append(json_result_child)
        except Exception as e:
            print(e)
        tree.out_time = timer[0]
        timer[0] += 1
        return (tree, json_result, index)

    def is_ancestor(self, node_parent, node_child):
        return node_parent.in_time <= node_child.in_time and node_child.out_time <= node_parent.out_time

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

    def seekAllNodes(self, tree, nodeType, search_children=True):
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
                if (search_children):
                    seekStack.extend(node.getChildren())
            except AttributeError:
                pass

        return resultList

    # Deprecated
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
        except Exception:
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

    def findNodeInSubtree(tree, index, index_identifier="nodeIndex"):
        """

        :param tree:
        :type tree:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        stack = list()
        stack.append(tree)

        while len(stack) > 0:
            tmp = stack.pop()

            if hasattr(tmp, index_identifier) and getattr(tmp, index_identifier) == index:
                return tmp
            else:
                if tmp.getChildCount() != 0:
                    stack.extend(tmp.children)

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
            if hasattr(tmp, "nodeIndex") and tmp.nodeIndex not in self.lookupTable:
                self.lookupTable[tmp.nodeIndex] = tmp

            if hasattr(tmp, "nodeIndex") and tmp.nodeIndex == index:
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
        methodBodyList.extend(
            self.seekAllNodes(tree, JavaParser.ConstructorBodyContext)
        )

        lines = set()

        for methodBody in methodBodyList:
            terminalNodeList = self.seekAllNodes(methodBody, TerminalNodeImpl)
            for terminalNode in terminalNodeList:
                if terminalNode.symbol.line != None:
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
        methodBodyList.extend(
            self.seekAllNodes(tree, JavaParser.ConstructorBodyContext)
        )

        linesOfCodePerMethod = dict()

        for methodBody in methodBodyList:
            lines = set()
            terminalNodeList = self.seekAllNodes(methodBody, TerminalNodeImpl)
            for terminalNode in terminalNodeList:
                lines.add(terminalNode.symbol.line)

            linesOfCodePerMethod[
                self.getMethodNameForNode(tree, methodBody.nodeIndex)
            ] = len(lines)

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
                if (str(child.getText()) != ">" and str(child.getText()) != "<"):
                    resultList.append(str(child.getText()+" "))
                else:
                    resultList.append(str(child.getText()))

            try:
                childQueue[0:0] = child.getChildren()
            except AttributeError:
                pass

        return "".join(resultList)

    def getMethodRanges(self, tree: JavaParser.CompilationUnitContext) -> dict:
        """

        :param tree:
        :type tree:
        :return:
        :rtype:
        """
        methodDeclarationList = self.seekAllNodes(
            tree, JavaParser.MethodDeclarationContext
        )
        methodDeclarationList.extend(
            self.seekAllNodes(tree, JavaParser.ConstructorDeclarationContext)
        )
        resultDict = dict()

        for methodDeclaration in methodDeclarationList:
            gotName = False
            gotStartStop = False
            for index in range(0, len(methodDeclaration.children)):
                if isinstance(
                    methodDeclaration.children[index],
                    JavaParser.FormalParametersContext,
                ):
                    assert isinstance(
                        methodDeclaration.children[index - 1], TerminalNodeImpl
                    )
                    methodName = methodDeclaration.children[
                        index - 1
                    ].symbol.text + self.getText(methodDeclaration.children[index])
                    gotName = True

                if isinstance(
                    methodDeclaration.children[index], JavaParser.MethodBodyContext
                ):
                    methodStartStop = (
                        methodDeclaration.children[index].start.start,
                        methodDeclaration.children[index].stop.stop,
                    )
                    gotStartStop = True

            if gotName and gotStartStop:
                resultDict[methodName] = methodStartStop

        return resultDict

    def getMethodNameForNode(
        self, tree: JavaParser.CompilationUnitContext, nodeIndex: int
    ):
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
        methodDeclaration = self.seekFirstMatchingParent(
            node, JavaParser.MethodDeclarationContext
        )
        if methodDeclaration is None:
            methodDeclaration = self.seekFirstMatchingParent(
                node, JavaParser.ConstructorDeclarationContext
            )
        if methodDeclaration is None:
            return "***not in a method***"

        for index in range(0, len(methodDeclaration.children)):
            if isinstance(
                methodDeclaration.children[index], JavaParser.FormalParametersContext
            ):
                assert isinstance(
                    methodDeclaration.children[index - 1], TerminalNodeImpl
                )
                methodName = methodDeclaration.children[
                    index - 1
                ].symbol.text + self.getText(methodDeclaration.children[index])

        classDeclaration = self.seekFirstMatchingParent(
            node, JavaParser.ClassDeclarationContext
        )
        if classDeclaration is None:
            return methodName

        for index in range(0, len(classDeclaration.children)):
            if (
                isinstance(
                    classDeclaration.children[index - 1], TerminalNodeImpl)
                and isinstance(classDeclaration.children[index], TerminalNodeImpl)
                and classDeclaration.children[index - 1].symbol.text == "class"
            ):
                return classDeclaration.children[index].symbol.text + "." + methodName

    def getMethodTypeForNode(self, node):
        """

        :param node:
        :type node:
        :return:
        :rtype:
        """
        parentMethod = self.seekFirstMatchingParent(
            node, JavaParser.MethodDeclarationContext
        )
        if parentMethod is None:
            return None

        assert isinstance(parentMethod, JavaParser.MethodDeclarationContext)
        parentType = parentMethod.getChild(0)
        returnValue = None
        if isinstance(parentType, JavaParser.JTypeContext):
            returnValue = parentType.getText()
            methodType = parentType.getChild(0)
            if isinstance(methodType, JavaParser.PrimitiveTypeContext):
                return returnValue

        elif isinstance(parentType, TerminalNodeImpl):
            if parentType.getText() == "void":
                return "void"
            returnValue = None

        parentMethodGeneric = self.seekFirstMatchingParent(
            parentMethod, JavaParser.GenericMethodDeclarationContext
        )
        if parentMethodGeneric != None:
            parentTypeGeneric = parentMethodGeneric.getChild(0).getText()
            returnValue = parentTypeGeneric+returnValue

        return returnValue

    def getCyclomaticComplexity(self, methodBody) -> int:
        """

        :param methodBody:
        :type methodBody:
        :return:
        :rtype:
        """
        assert isinstance(methodBody, JavaParser.MethodBodyContext) or isinstance(
            methodBody, JavaParser.ConstructorBodyContext
        )

        cyclomaticComplexity = 1
        keywordList = self.seekAllNodes(methodBody, TerminalNodeImpl)

        for keyword in keywordList:
            keywordText = keyword.getText()
            if (
                keywordText == "if"
                or keywordText == "case"
                or keywordText == "for"
                or keywordText == "while"
                or keywordText == "catch"
                or keywordText == "&&"
                or keywordText == "||"
                or keywordText == "?"
                or keywordText == "foreach"
            ):
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
        methodBodyList.extend(
            self.seekAllNodes(tree, JavaParser.ConstructorBodyContext)
        )

        for methodBody in methodBodyList:
            cyclomaticComplexityPerMethod[
                self.getMethodNameForNode(tree, methodBody.nodeIndex)
            ] = self.getCyclomaticComplexity(methodBody)

        return cyclomaticComplexityPerMethod

    Class_dict = dict()

    def generate_dict_of_classes(self):
        for name, obj in inspect.getmembers(Tree_):
            if inspect.isclass(obj):
                JavaParse.Class_dict[str(obj)] = obj
        for name, obj in inspect.getmembers(JavaParser):
            if inspect.isclass(obj):
                JavaParse.Class_dict[str(obj)] = obj

    def Json2Tree(self, json_string):
        """

        :param json:
        :type json:
        :return:
        :rtype:
        """

        def inner_loop(tree, j_dict):
            if "applied_node_id" in j_dict:
                tree.applied_node_id = j_dict["applied_node_id"]
            if "node_depth" in j_dict:
                tree.node_depth = j_dict["node_depth"]
            if "mutationType" in j_dict:
                tree.mutationType = j_dict["mutationType"]
            if "contextID" in j_dict:
                tree.contextID = j_dict["contextID"]
            if "nodeIndex" in j_dict:
                tree.nodeIndex = j_dict["nodeIndex"]
            if "mutationID" in j_dict:
                tree.mutationID = j_dict["mutationID"]
            if j_dict["type"] == "<class 'antlr4.tree.Tree.TerminalNodeImpl'>":
                tree.symbol.text = j_dict["text"]
            if "children" in j_dict:
                for child_dict in j_dict["children"]:
                    child = JavaParse.Class_dict[child_dict["type"]](tree)
                    if child_dict["type"] == "<class 'antlr4.tree.Tree.TerminalNodeImpl'>":
                        child = TerminalNodeImpl(Token())
                        child.symbol.text = child_dict["text"]
                    new_node = inner_loop(child, child_dict)
                    new_node.parentCtx = tree
                    tree.addChild(new_node)
            return tree
        # loop through every element in the tree in a DFS method and build the tree

        json_ = json.loads(json_string)
        if json_["type"] == "<class 'antlr4.tree.Tree.TerminalNodeImpl'>":
            tree = TerminalNodeImpl(Token())
        else:
            tree = JavaParse.Class_dict[json_["type"]](None)
        tree = inner_loop(tree, json_)
        return tree

    def tree2JSON_DFS(self, tree):
        """

        :param tree:
        :type tree:
        :return:
        :rtype:
        """
        def generate_dict(tree):
            result = dict()
            if tree is None:
                return result

            result["type"] = str(tree.__class__)
            if hasattr(
                    tree, "nodeIndex"):
                result["nodeIndex"] = tree.nodeIndex
            if hasattr(
                    tree, "contextID"):
                result["contextID"] = tree.contextID
            if hasattr(
                    tree, "mutationID"):
                result["mutationID"] = tree.mutationID
            if hasattr(tree, "mutationType"):
                result["mutationType"] = tree.mutationType
            if hasattr(tree, "node_depth"):
                result["node_depth"] = tree.node_depth
            if hasattr(tree, "applied_node_id"):
                result["applied_node_id"] = tree.applied_node_id
            result["text"] = tree.getText()
            if isinstance(tree, TerminalNodeImpl):
                return result

            result["children"] = list()

            try:
                for child in tree.getChildren():
                    result["children"].append(generate_dict(child))
            except Exception as e:
                print(e)
            return result
        result = generate_dict(tree)
        return json.dumps(result, separators=(',', ': '))

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

        nodes.append(type(tree).__name__ + "/" + str(tree.nodeIndex))

        while len(nodeStack) > 0:
            tmp = nodeStack.pop()
            if tmp.getChildCount() > 0:
                nodeStack.extend(tmp.children)
                for child in tmp.children:
                    childID = type(child).__name__ + "/" + str(child.nodeIndex)
                    nodes.append(childID)
                    parent[childID] = type(
                        tmp).__name__ + "/" + str(tmp.nodeIndex)
            if isinstance(tmp, TerminalNodeImpl):
                tokenID = str(tmp.symbol.text) + "/" + str(tmp.nodeIndex)
                nodes.append(tokenID)
                parent[tokenID] = type(tmp).__name__ + "/" + str(tmp.nodeIndex)

        graph = graphviz.Digraph()

        for node in nodes:
            graph.node(node)
            try:
                graph.edge(parent[node], node)
            except KeyError as e:
                pass

        graph.render(os.path.join(os.getcwd(), "LittleDarwinResults", "tree"))
