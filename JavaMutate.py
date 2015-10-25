import sys
from JavaParser import JavaParser
from JavaParse import JavaParse
import copy
from antlr4.tree.Tree import TerminalNodeImpl
from random import shuffle

sys.setrecursionlimit(50000)

# TODO: Every mutation operator must be implemented using this class in the future
# ---------------------------------------------------------------------------------------
class MutationOperator(object):
    def __init__(self):
        self.nodeIndexes = list()
        self.originalNodes = dict()
        self.mutatedNodes = dict()
        self.type = None
        self.tree = None

    def seekNodes(self):
        pass

    def filterNodes(self):
        pass

    def mutateNode(self, nodeIndex):
        pass

    def unmutateNode(self, nodeIndex):
        pass

    def getTree(self):
        assert isinstance(self.tree, JavaParser.CompilationUnitContext)
        return self.tree

    def getTexts(self):
        assert isinstance(self.tree, JavaParser.CompilationUnitContext)

        mutatedCode = list()

        for nodeIndex in self.nodeIndexes:
            mutationBefore = "----> before: " + self.originalNodes[nodeIndex].getText()
            mutationAfter = "----> after: " + self.mutatedNodes[nodeIndex].getText()

            self.mutateNode(nodeIndex)
            mutatedCode.append((
                               "/* LittleDarwin generated mutant \nmutant type: " + self.type + "\n" + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(
                                   self.mutatedNodes[nodeIndex].start.line) + "\n*/ \n\n" + (
                               " ".join(self.tree.getText().rsplit("<EOF>", 1)))))
            self.unmutateNode(nodeIndex)

        return mutatedCode

    def getNodes(self):
        return self.nodeIndexes

    def setTree(self, tree):
        assert isinstance(tree, JavaParser.CompilationUnitContext)
        self.tree = tree
# ---------------------------------------------------------------------------------------




class JavaMutate(object):
    def __init__(self, javaParseObjectInput=None, verbose=False):
        self.verbose = verbose

        if javaParseObjectInput is not None:
            self.javaParseObject = javaParseObjectInput
        else:
            self.javaParseObject = JavaParse(self.verbose)

    def findMutableNodes(self, tree):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        mutableNodes = list()
        mutableNodes.extend(self.arithmeticOperatorReplacementBinary(tree, "return_nodes"))
        mutableNodes.extend(self.arithmeticOperatorReplacementShortcut(tree, "return_nodes"))
        mutableNodes.extend(self.arithmeticOperatorReplacementUnary(tree, "return_nodes"))
        mutableNodes.extend(self.assignmentOperatorReplacementShortcut(tree, "return_nodes"))
        mutableNodes.extend(self.conditionalOperatorDeletion(tree, "return_nodes"))
        mutableNodes.extend(self.conditionalOperatorReplacement(tree, "return_nodes"))
        mutableNodes.extend(self.logicalOperatorReplacement(tree, "return_nodes"))
        mutableNodes.extend(self.relationalOperatorReplacement(tree, "return_nodes"))
        mutableNodes.extend(self.shiftOperatorReplacement(tree, "return_nodes"))

        return mutableNodes

    def runHigherOrderProcedure(self, tree, nodeGroup):
        assert isinstance(tree, JavaParser.CompilationUnitContext)
        assert isinstance(nodeGroup, list)
        steps = len(nodeGroup)
        assert steps >= 1

        # Store original nodes here
        originalNodes = dict()

        for node in nodeGroup:
            originalNodes[node] = copy.deepcopy(self.javaParseObject.getNode(tree, node))

        while steps >= 1:
            steps -= 1

            node = nodeGroup.pop()

            if node[1] == "ArithmeticOperatorReplacementBinary":
                tree = self.arithmeticOperatorReplacementBinary(tree, "return_tree", node[0])
            elif node[1] == "ArithmeticOperatorReplacementShortcut":
                tree = self.arithmeticOperatorReplacementShortcut(tree, "return_tree", node[0])
            elif node[1] == "ArithmeticOperatorReplacementUnary":
                tree = self.arithmeticOperatorReplacementUnary(tree, "return_tree", node[0])
            elif node[1] == "AssignmentOperatorReplacementShortcut":
                tree = self.assignmentOperatorReplacementShortcut(tree, "return_tree", node[0])
            elif node[1] == "ConditionalOperatorDeletion":
                tree = self.conditionalOperatorDeletion(tree, "return_tree", node[0])
            elif node[1] == "ConditionalOperatorReplacement":
                tree = self.conditionalOperatorReplacement(tree, "return_tree", node[0])
            elif node[1] == "LogicalOperatorReplacement":
                tree = self.logicalOperatorReplacement(tree, "return_tree", node[0])
            elif node[1] == "RelationalOperatorReplacement":
                tree = self.relationalOperatorReplacement(tree, "return_tree", node[0])
            elif node[1] == "ShiftOperatorReplacement":
                tree = self.shiftOperatorReplacement(tree, "return_tree", node[0])

        assert len(nodeGroup) == 0

        mutatedText = "/* LittleDarwin generated higher order mutant\n ----> line number in original file: " + str(
            [node.start.line for node in originalNodes.itervalues()]) + "\n*/ \n\n" + (
                          " ".join(tree.getText().rsplit("<EOF>", 1)))  # create compilable, readable code

        for nodeIndex in originalNodes.keys():
            self.javaParseObject.setNode(tree, nodeIndex, originalNodes[nodeIndex])

        return mutatedText

    def applyHigherOrderMutators(self, tree, higherOrder):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        # Find all mutable nodes
        nodes = self.findMutableNodes(tree)

        # Combine all nodes
        shuffle(nodes)
        nodeGroups = list()

        for i in range(0, len(nodes) - higherOrder + 1, higherOrder):
            nodeGroups.append([nodes[j] for j in range(i, i + higherOrder, 1)])

        # Run mutation operators

        mutatedTreeTexts = list()

        for nodeGroup in nodeGroups:
            mutatedTreeTexts.append(self.runHigherOrderProcedure(tree, nodeGroup))

    def applyMutators(self, tree, higherOrder, type):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if higherOrder > 1:
            return self.applyHigherOrderMutators(tree, higherOrder)


        mutatedTrees = list()
        mutationTypeCount = dict()

        # mutatedTrees.extend(self.arithmeticOperatorDeletionShortcut(tree))
        # mutatedTrees.extend(self.arithmeticOperatorDeletionUnary(tree))
        # mutatedTrees.extend(self.arithmeticOperatorInsertionShortcut(tree))
        # mutatedTrees.extend(self.arithmeticOperatorInsertionUnary(tree))
        # mutatedTrees.extend(self.conditionalOperatorInsertion(tree))
        # mutatedTrees.extend(self.logicalOperatorDeletion(tree))
        # mutatedTrees.extend(self.logicalOperatorInsertion(tree))

        if type == "classical" or type == "all":
            resultArithmeticOperatorReplacementBinary = self.arithmeticOperatorReplacementBinary(tree)
            mutatedTrees.extend(resultArithmeticOperatorReplacementBinary)
            mutationTypeCount["ArithmeticOperatorReplacementBinary"] = len(resultArithmeticOperatorReplacementBinary)

            resultArithmeticOperatorReplacementShortcut = self.arithmeticOperatorReplacementShortcut(tree)
            mutatedTrees.extend(resultArithmeticOperatorReplacementShortcut)
            mutationTypeCount["ArithmeticOperatorReplacementShortcut"] = len(
                resultArithmeticOperatorReplacementShortcut)

            resultArithmeticOperatorReplacementUnary = self.arithmeticOperatorReplacementUnary(tree)
            mutatedTrees.extend(resultArithmeticOperatorReplacementUnary)
            mutationTypeCount["ArithmeticOperatorReplacementUnary"] = len(resultArithmeticOperatorReplacementUnary)

            # currently generating too many mutations
            # resultNegateConditionalsMutator = self.negateConditionalsMutator(tree)
            # mutatedTrees.extend(resultNegateConditionalsMutator)
            # mutationTypeCount["NegateConditionalsMutator"] = len(resultNegateConditionalsMutator)

            resultLogicalOperatorReplacement = self.logicalOperatorReplacement(tree)
            mutatedTrees.extend(resultLogicalOperatorReplacement)
            mutationTypeCount["LogicalOperatorReplacement"] = len(resultLogicalOperatorReplacement)

            resultShiftOperatorReplacement = self.shiftOperatorReplacement(tree)
            mutatedTrees.extend(resultShiftOperatorReplacement)
            mutationTypeCount["ShiftOperatorReplacement"] = len(resultShiftOperatorReplacement)

            resultRelationalOperatorReplacement = self.relationalOperatorReplacement(tree)
            mutatedTrees.extend(resultRelationalOperatorReplacement)
            mutationTypeCount["RelationalOperatorReplacement"] = len(resultRelationalOperatorReplacement)

            resultConditionalOperatorReplacement = self.conditionalOperatorReplacement(tree)
            mutatedTrees.extend(resultConditionalOperatorReplacement)
            mutationTypeCount["ConditionalOperatorReplacement"] = len(resultConditionalOperatorReplacement)

            resultConditionalOperatorDeletion = self.conditionalOperatorDeletion(tree)
            mutatedTrees.extend(resultConditionalOperatorDeletion)
            mutationTypeCount["ConditionalOperatorDeletion"] = len(resultConditionalOperatorDeletion)

            resultAssignmentOperatorReplacementShortcut = self.assignmentOperatorReplacementShortcut(tree)
            mutatedTrees.extend(resultAssignmentOperatorReplacementShortcut)
            mutationTypeCount["AssignmentOperatorReplacementShortcut"] = len(
                resultAssignmentOperatorReplacementShortcut)

        elif type == "object-oriented" or type == "all":
            pass

        return (mutatedTrees, mutationTypeCount)

    # def negateConditionalsMutator(self, tree, mode="return_text"):
    #     assert isinstance(tree, JavaParser.CompilationUnitContext)
    #
    #
    #     if mode == "return_text":
    #
    #
    #         mutatedTreesTexts = list()
    #         expressionList = self.javaParseObject.seek(tree, JavaParser.ParExpressionContext)
    #
    #         while len(expressionList) > 0:
    #             # tmpTree = copy.deepcopy(tree)
    #             expressionIndex = expressionList.pop()
    #
    #             node = self.javaParseObject.getNode(tree, expressionIndex)
    #             assert isinstance(node, JavaParser.ParExpressionContext)
    #             assert isinstance(node.children[0], TerminalNodeImpl)
    #             assert isinstance(node.children[2], TerminalNodeImpl)
    #             mutationBefore = "----> before: " + node.getText()
    #             if self.verbose:
    #                 print mutationBefore
    #             originalText0 = copy.deepcopy(node.children[0].symbol.text)
    #             node.children[0].symbol.text = u"(!("
    #             originalText2 = copy.deepcopy(node.children[2].symbol.text)
    #             node.children[2].symbol.text = u"))"
    #             mutationAfter = "----> after: " + node.getText()
    #             if self.verbose:
    #                 print mutationAfter
    #             mutatedTreesTexts.append((
    #                 "/* LittleDarwin generated mutant\n mutant type: negateConditionalsMutator\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
    #                     " ".join(tree.getText().rsplit("<EOF>", 1)))))
    #             # mutatedTreesTexts.append(tree.getText())
    #             node.children[0].symbol.text = copy.deepcopy(originalText0)
    #             node.children[2].symbol.text = copy.deepcopy(originalText2)
    #
    #         return mutatedTreesTexts
    #
    #     elif mode == "return_nodes":
    #         nodeList = list()
    #         expressionList = self.javaParseObject.seek(tree, JavaParser.ParExpressionContext)
    #
    #         for exp in expressionList:
    #             nodeList.append([exp, "negateConditionalsMutator"])


    # Method Level Mutants """

    """
    Mutation operator guidelines:
    input: tree, mode, single node index
    output: tree, text, node list

    ----- mode: return_text
                return_nodes
                return_tree
    """

    def arithmeticOperatorReplacementBinary(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":

            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)
            # nodeList = list()

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"+" or node.children[1].symbol.text == u"-" or node.children[
                    1].symbol.text == u"*" or node.children[1].symbol.text == u"/" or node.children[1].symbol.text == u"%"):
                    continue  # not an arithmetic operator

                if node.children[0].getText()[0] == '\"' or node.children[2].getText()[0] == '\"':
                    continue  # string concatenation, don't change

                # nodeList.append([expressionIndex, "ArithmeticOperatorReplacementBinary"])

                mutationBefore = "----> before: " + node.getText()

                if self.verbose:
                    print mutationBefore

                # if mode == "return_text" or mode == "return_tree":
                originalText = copy.deepcopy(node.children[1].symbol.text)

                if originalText == u"+":
                    node.children[1].symbol.text = u"-"
                elif originalText == u"-":
                    node.children[1].symbol.text = u"+"
                elif originalText == u"/":
                    node.children[1].symbol.text = u"*"
                elif originalText == u"*":
                    node.children[1].symbol.text = u"/"
                elif originalText == u"%":
                    node.children[1].symbol.text = u"/"
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter
                mutatedTreesTexts.append((
                        "/* LittleDarwin generated mutant\n mutant type: arithmeticOperatorReplacementBinary\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[1].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts


        elif mode == "return_nodes":
            # mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)
            nodeList = list()

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"+" or node.children[1].symbol.text == u"-" or node.children[
                    1].symbol.text == u"*" or node.children[1].symbol.text == u"/" or node.children[1].symbol.text == u"%"):
                    continue  # not an arithmetic operator

                if node.children[0].getText()[0] == '\"' or node.children[2].getText()[0] == '\"':
                    continue  # string concatenation, don't change

                nodeList.append([expressionIndex, "ArithmeticOperatorReplacementBinary"])


            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1], TerminalNodeImpl) and isinstance(node.children[2], JavaParser.ExpressionContext)):
                    assert False

            except Exception, e:
                assert False

            if not (node.children[1].symbol.text == u"+" or node.children[1].symbol.text == u"-" or node.children[
                1].symbol.text == u"*" or node.children[1].symbol.text == u"/" or node.children[1].symbol.text == u"%"):
                assert False

            if node.children[0].getText()[0] == '\"' or node.children[2].getText()[0] == '\"':
                assert False

            originalText = node.children[1].symbol.text

            if originalText == u"+":
                node.children[1].symbol.text = u"-"
            elif originalText == u"-":
                node.children[1].symbol.text = u"+"
            elif originalText == u"/":
                node.children[1].symbol.text = u"*"
            elif originalText == u"*":
                node.children[1].symbol.text = u"/"
            elif originalText == u"%":
                node.children[1].symbol.text = u"/"
            else:
                assert False

            return tree




    def arithmeticOperatorReplacementUnary(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)
            mutatedTreesTexts = list()
            # nodeList = list()

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                      JavaParser.ExpressionContext)):
                        continue  # not a unary expression
                except Exception, e:
                    continue

                if not (node.children[0].symbol.text == u"+" or node.children[0].symbol.text == u"-"):
                    continue  # not an arithmetic operator

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore
                originalText = copy.deepcopy(node.children[0].symbol.text)

                if originalText == u"+":
                    node.children[0].symbol.text = u"-"
                elif originalText == u"-":
                    node.children[0].symbol.text = u"+"
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter
                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: arithmeticOperatorReplacementUnary\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[0].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":
            # mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)
            nodeList = list()

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                      JavaParser.ExpressionContext)):
                        continue  # not a unary expression
                except Exception, e:
                    continue

                if not (node.children[0].symbol.text == u"+" or node.children[0].symbol.text == u"-"):
                    continue  # not an arithmetic operator


                nodeList.append([expressionIndex, "ArithmeticOperatorReplacementUnary"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                      JavaParser.ExpressionContext)):
                    assert False

            except Exception, e:
                    assert False

            if not (node.children[0].symbol.text == u"+" or node.children[0].symbol.text == u"-"):
                assert False

            originalText = node.children[0].symbol.text

            if originalText == u"+":
                node.children[0].symbol.text = u"-"
            elif originalText == u"-":
                node.children[0].symbol.text = u"+"
            else:
                assert False

            return tree

    def arithmeticOperatorReplacementShortcut(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":

            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                 JavaParser.ExpressionContext):
                        terminalChild = 0
                    elif isinstance(node.children[1], TerminalNodeImpl) and isinstance(node.children[0],
                                                                                   JavaParser.ExpressionContext):
                        terminalChild = 1
                    else:
                        continue  # not a shortcut expression
                except Exception, e:
                    continue

                if not (node.children[terminalChild].symbol.text == u"++" or node.children[
                    terminalChild].symbol.text == u"--"):
                    continue  # not an arithmetic operator

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore
                originalText = copy.deepcopy(node.children[terminalChild].symbol.text)

                if originalText == u"++":
                    node.children[terminalChild].symbol.text = u"--"
                elif originalText == u"--":
                    node.children[terminalChild].symbol.text = u"++"
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter

                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: arithmeticOperatorReplacementShortcut\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[terminalChild].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":
            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                 JavaParser.ExpressionContext):
                        terminalChild = 0
                    elif isinstance(node.children[1], TerminalNodeImpl) and isinstance(node.children[0],
                                                                                   JavaParser.ExpressionContext):
                        terminalChild = 1
                    else:
                        continue  # not a shortcut expression
                except Exception, e:
                    continue

                if not (node.children[terminalChild].symbol.text == u"++" or node.children[
                    terminalChild].symbol.text == u"--"):
                    continue  # not an arithmetic operator

                nodeList.append([expressionIndex, "ArithmeticOperatorReplacementShortcut"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:

                if isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                 JavaParser.ExpressionContext):
                    terminalChild = 0
                elif isinstance(node.children[1], TerminalNodeImpl) and isinstance(node.children[0],
                                                                                   JavaParser.ExpressionContext):
                    terminalChild = 1
                else:
                    assert False
            except Exception, e:
                assert False

            if not (node.children[terminalChild].symbol.text == u"++" or node.children[
                    terminalChild].symbol.text == u"--"):
                assert False

            originalText = node.children[terminalChild].symbol.text

            if originalText == u"++":
                node.children[terminalChild].symbol.text = u"--"
            elif originalText == u"--":
                node.children[terminalChild].symbol.text = u"++"
            else:
                assert False

            return tree

    # def arithmeticOperatorInsertionUnary(self, tree):
    #     pass
    #
    # def arithmeticOperatorInsertionShortcut(self, tree):
    #     pass
    #
    # def arithmeticOperatorDeletionUnary(self, tree):
    #     pass
    #
    # def arithmeticOperatorDeletionShortcut(self, tree):
    #     pass

    def relationalOperatorReplacement(self, tree, mode="return_text", nodeIndex=None):  # covered by negateConditionals
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":
            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u">" or node.children[1].symbol.text == u"<" or node.children[
                    1].symbol.text == u">=" or node.children[1].symbol.text == u"<=" or node.children[
                    1].symbol.text == u"==" or node.children[1].symbol.text == u"!="):
                    continue  # not a relation operator

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore

                originalText = copy.deepcopy(node.children[1].symbol.text)

                if originalText == u">":
                    node.children[1].symbol.text = u"<="
                elif originalText == u"<":
                    node.children[1].symbol.text = u">="
                elif originalText == u"<=":
                    node.children[1].symbol.text = u">"
                elif originalText == u">=":
                    node.children[1].symbol.text = u"<"
                elif originalText == u"!=":
                    node.children[1].symbol.text = u"=="
                elif originalText == u"==":
                    node.children[1].symbol.text = u"!="
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()

                if self.verbose:
                    print mutationAfter

                mutatedTreesTexts.append((
                    (
                        "/* LittleDarwin generated mutant\n mutant type: relationalOperatorReplacement\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                            " ".join(tree.getText().rsplit("<EOF>", 1))))))  # create compilable, readable code

                node.children[1].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":
            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                      TerminalNodeImpl) and isinstance(
                                                                    node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u">" or node.children[1].symbol.text == u"<" or node.children[
                    1].symbol.text == u">=" or node.children[1].symbol.text == u"<=" or node.children[
                    1].symbol.text == u"==" or node.children[1].symbol.text == u"!="):
                    continue  # not a relation operator

                nodeList.append([expressionIndex, "RelationalOperatorReplacement"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                        node.children[2], JavaParser.ExpressionContext)):
                    assert False
            except Exception, e:
                assert False

            if not (node.children[1].symbol.text == u">" or node.children[1].symbol.text == u"<" or node.children[
                1].symbol.text == u">=" or node.children[1].symbol.text == u"<=" or node.children[
                1].symbol.text == u"==" or node.children[1].symbol.text == u"!="):
                assert False

            originalText = node.children[1].symbol.text

            if originalText == u">":
                node.children[1].symbol.text = u"<="
            elif originalText == u"<":
                node.children[1].symbol.text = u">="
            elif originalText == u"<=":
                node.children[1].symbol.text = u">"
            elif originalText == u">=":
                node.children[1].symbol.text = u"<"
            elif originalText == u"!=":
                node.children[1].symbol.text = u"=="
            elif originalText == u"==":
                node.children[1].symbol.text = u"!="
            else:
                assert False

            return tree

    def conditionalOperatorReplacement(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":

            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"&&" or node.children[1].symbol.text == u"||"):
                    continue  # not a conditional operator (non-lazy ones covered in logical operators)

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore

                originalText = copy.deepcopy(node.children[1].symbol.text)

                if originalText == u"&&":
                    node.children[1].symbol.text = u"||"
                elif originalText == u"||":
                    node.children[1].symbol.text = u"&&"
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter
                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: conditionalOperatorReplacement\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[1].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":

            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"&&" or node.children[1].symbol.text == u"||"):
                    continue  # not a conditional operator (non-lazy ones covered in logical operators)

                nodeList.append([expressionIndex, "ConditionalOperatorReplacement"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                    assert False
            except Exception, e:
                assert False

            if not (node.children[1].symbol.text == u"&&" or node.children[1].symbol.text == u"||"):
                assert False

            originalText = node.children[1].symbol.text

            if originalText == u"&&":
                node.children[1].symbol.text = u"||"
            elif originalText == u"||":
                node.children[1].symbol.text = u"&&"
            else:
                assert False

            return tree

    def conditionalOperatorDeletion(self, tree, mode="return_text", nodeIndex=None):  # covered by negateConditionals
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":

            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                      JavaParser.ExpressionContext)):
                        continue  # not a unary expression
                except Exception, e:
                    continue

                if not (node.children[0].symbol.text == u"!"):
                    continue  # not a unary conditional operator

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore
                originalText = copy.deepcopy(node.children[0].symbol.text)

                if originalText == u"!":
                    node.children[0].symbol.text = u" "
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter
                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: conditionalOperatorDeletion\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[0].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":

            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                # tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                      JavaParser.ExpressionContext)):
                        continue  # not a unary expression
                except Exception, e:
                    continue

                if not (node.children[0].symbol.text == u"!"):
                    continue  # not a unary conditional operator

                nodeList.append([expressionIndex, "ConditionalOperatorDeletion"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None
            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], TerminalNodeImpl) and isinstance(node.children[1],
                                                                                  JavaParser.ExpressionContext)):
                    assert False
            except Exception, e:
                assert False

            if not (node.children[0].symbol.text == u"!"):
                assert False

            originalText = node.children[0].symbol.text

            if originalText == u"!":
                node.children[0].symbol.text = u" "
            else:
                assert False

            return tree

    # def conditionalOperatorInsertion(self, tree):   # covered by negateConditionals, both generate too many mutations
    #     pass

    def shiftOperatorReplacement(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":

            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                #tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                              TerminalNodeImpl) and isinstance(
                        node.children[2], TerminalNodeImpl) and isinstance(node.children[3],
                                                                           JavaParser.ExpressionContext)):
                        threeTerminals = False
                    elif (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                TerminalNodeImpl) and isinstance(
                            node.children[2], TerminalNodeImpl) and isinstance(node.children[3],
                                                                           TerminalNodeImpl) and isinstance(
                            node.children[4], JavaParser.ExpressionContext)):
                        threeTerminals = True
                    else:
                        continue  # not a binary shift expression
                except Exception, e:
                    continue

                try:
                    if (threeTerminals is False) and (
                            (node.children[1].symbol.text == u"<" and node.children[2].symbol.text == u"<") or (
                                        node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">")):
                        pass

                    elif (threeTerminals is True) and (
                                    node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">" and
                                node.children[3].symbol.text == u">"):
                        pass

                    else:
                        continue  # not a shift operator

                except Exception, e:
                    continue

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore

                if threeTerminals:
                    originalText1 = copy.deepcopy(node.children[1].symbol.text)
                    originalText2 = copy.deepcopy(node.children[2].symbol.text)
                    originalText3 = copy.deepcopy(node.children[3].symbol.text)

                    if originalText1 == u">" and originalText2 == u">" and originalText3 == u">":
                        node.children[3].symbol.text = u" "
                    else:
                        assert False

                else:
                    originalText1 = copy.deepcopy(node.children[1].symbol.text)
                    originalText2 = copy.deepcopy(node.children[2].symbol.text)

                    if originalText1 == u">" and originalText2 == u">":
                        node.children[1].symbol.text = u"<"
                        node.children[2].symbol.text = u"<"
                    elif originalText1 == u"<" and originalText2 == u"<":
                        node.children[1].symbol.text = u">"
                        node.children[2].symbol.text = u">"
                    else:
                        assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter

                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: shiftOperatorReplacement\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                    " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[1].symbol.text = copy.deepcopy(originalText1)
                node.children[2].symbol.text = copy.deepcopy(originalText2)
                if threeTerminals:
                    node.children[3].symbol.text = copy.deepcopy(originalText3)

            return mutatedTreesTexts

        elif mode == "return_nodes":

            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                #tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                              TerminalNodeImpl) and isinstance(
                        node.children[2], TerminalNodeImpl) and isinstance(node.children[3],
                                                                           JavaParser.ExpressionContext)):
                        threeTerminals = False
                    elif (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                TerminalNodeImpl) and isinstance(
                            node.children[2], TerminalNodeImpl) and isinstance(node.children[3],
                                                                           TerminalNodeImpl) and isinstance(
                            node.children[4], JavaParser.ExpressionContext)):
                        threeTerminals = True
                    else:
                        continue  # not a binary shift expression
                except Exception, e:
                    continue

                try:
                    if (threeTerminals is False) and (
                            (node.children[1].symbol.text == u"<" and node.children[2].symbol.text == u"<") or (
                                        node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">")):
                        pass

                    elif (threeTerminals is True) and (
                                    node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">" and
                                node.children[3].symbol.text == u">"):
                        pass

                    else:
                        continue  # not a shift operator

                except Exception, e:
                    continue

                nodeList.append([expressionIndex, "ShiftOperatorReplacement"])

            return nodeList

        if mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                              TerminalNodeImpl) and isinstance(
                    node.children[2], TerminalNodeImpl) and isinstance(node.children[3],
                                                                           JavaParser.ExpressionContext)):
                    threeTerminals = False
                elif (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                TerminalNodeImpl) and isinstance(
                        node.children[2], TerminalNodeImpl) and isinstance(node.children[3],
                                                                           TerminalNodeImpl) and isinstance(
                        node.children[4], JavaParser.ExpressionContext)):
                    threeTerminals = True

                else:
                    assert False
            except Exception, e:
                assert False

            try:
                if (threeTerminals is False) and (
                        (node.children[1].symbol.text == u"<" and node.children[2].symbol.text == u"<") or (
                                    node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">")):
                    pass

                elif (threeTerminals is True) and (
                                node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">" and
                            node.children[3].symbol.text == u">"):
                    pass

                else:
                    assert False

            except Exception, e:
                assert False

            if threeTerminals:
                originalText1 = node.children[1].symbol.text
                originalText2 = node.children[2].symbol.text
                originalText3 = node.children[3].symbol.text

                if originalText1 == u">" and originalText2 == u">" and originalText3 == u">":
                    node.children[3].symbol.text = u" "
                else:
                    assert False

            else:
                originalText1 = node.children[1].symbol.text
                originalText2 = node.children[2].symbol.text

                if originalText1 == u">" and originalText2 == u">":
                    node.children[1].symbol.text = u"<"
                    node.children[2].symbol.text = u"<"
                elif originalText1 == u"<" and originalText2 == u"<":
                    node.children[1].symbol.text = u">"
                    node.children[2].symbol.text = u">"
                else:
                    assert False

            return tree

    def logicalOperatorReplacement(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":
            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                #tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"&" or node.children[1].symbol.text == u"|" or node.children[
                        1].symbol.text == u"^"):
                    continue  # not a logical operator

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore

                originalText = copy.deepcopy(node.children[1].symbol.text)

                if originalText == u"&":
                    node.children[1].symbol.text = u"|"
                elif originalText == u"|":
                    node.children[1].symbol.text = u"^"
                elif originalText == u"^":
                    node.children[1].symbol.text = u"&"
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter
                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: logicalOperatorReplacement\n " + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[1].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":
            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                #tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"&" or node.children[1].symbol.text == u"|" or node.children[
                        1].symbol.text == u"^"):
                    continue  # not a logical operator
                nodeList.append([expressionIndex, "LogicalOperatorReplacement"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None

            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(                            node.children[2], JavaParser.ExpressionContext)):
                    assert False
            except Exception, e:
                assert False

            if not (node.children[1].symbol.text == u"&" or node.children[1].symbol.text == u"|" or node.children[
                    1].symbol.text == u"^"):
                assert False

            originalText = node.children[1].symbol.text

            if originalText == u"&":
                node.children[1].symbol.text = u"|"
            elif originalText == u"|":
                node.children[1].symbol.text = u"^"
            elif originalText == u"^":
                node.children[1].symbol.text = u"&"
            else:
                assert False

            return tree



    # def logicalOperatorInsertion(self, tree):
    #     pass
    #
    # def logicalOperatorDeletion(self, tree):
    #     pass

    def assignmentOperatorReplacementShortcut(self, tree, mode="return_text", nodeIndex=None):
        assert isinstance(tree, JavaParser.CompilationUnitContext)

        if mode == "return_text":
            mutatedTreesTexts = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                #tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"+=" or node.children[1].symbol.text == u"-=" or node.children[
                        1].symbol.text == u"*=" or node.children[1].symbol.text == u"/=" or node.children[
                        1].symbol.text == u"%=" or node.children[1].symbol.text == u"&=" or node.children[
                        1].symbol.text == u"|=" or node.children[1].symbol.text == u"^=" or node.children[
                        1].symbol.text == u"<<=" or node.children[1].symbol.text == u">>=" or node.children[
                        1].symbol.text == u">>>="):
                    continue  # not an assignment operator

                mutationBefore = "----> before: " + node.getText()
                if self.verbose:
                    print mutationBefore

                originalText = copy.deepcopy(node.children[1].symbol.text)

                if originalText == u"+=":
                    node.children[1].symbol.text = u"-="
                elif originalText == u"-=":
                    node.children[1].symbol.text = u"+="
                elif originalText == u"/=":
                    node.children[1].symbol.text = u"*="
                elif originalText == u"*=":
                    node.children[1].symbol.text = u"/="
                elif originalText == u"%=":
                    node.children[1].symbol.text = u"/="
                elif originalText == u"&=":
                    node.children[1].symbol.text = u"|="
                elif originalText == u"|=":
                    node.children[1].symbol.text = u"^="
                elif originalText == u"^=":
                    node.children[1].symbol.text = u"&="
                elif originalText == u">>=":
                    node.children[1].symbol.text = u">>>="
                elif originalText == u"<<=":
                    node.children[1].symbol.text = u">>="
                elif originalText == u">>>=":
                    node.children[1].symbol.text = u">>="
                else:
                    assert False

                mutationAfter = "----> after: " + node.getText()
                if self.verbose:
                    print mutationAfter
                mutatedTreesTexts.append((
                    "/* LittleDarwin generated mutant\n mutant type: assignmentOperatorReplacementShortcut\n" + mutationBefore + "\n" + mutationAfter + "\n----> line number in original file: " + str(node.start.line) + "\n*/ \n\n" + (
                        " ".join(tree.getText().rsplit("<EOF>", 1)))))  # create compilable, readable code

                node.children[1].symbol.text = copy.deepcopy(originalText)

            return mutatedTreesTexts

        elif mode == "return_nodes":
            nodeList = list()
            expressionList = self.javaParseObject.seek(tree, JavaParser.ExpressionContext)

            while len(expressionList) > 0:
                #tmpTree = copy.deepcopy(tree)
                expressionIndex = expressionList.pop()

                node = self.javaParseObject.getNode(tree, expressionIndex)
                assert isinstance(node, JavaParser.ExpressionContext)

                try:
                    if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                                  TerminalNodeImpl) and isinstance(
                            node.children[2], JavaParser.ExpressionContext)):
                        continue  # not a binary expression
                except Exception, e:
                    continue

                if not (node.children[1].symbol.text == u"+=" or node.children[1].symbol.text == u"-=" or node.children[
                        1].symbol.text == u"*=" or node.children[1].symbol.text == u"/=" or node.children[
                        1].symbol.text == u"%=" or node.children[1].symbol.text == u"&=" or node.children[
                        1].symbol.text == u"|=" or node.children[1].symbol.text == u"^=" or node.children[
                        1].symbol.text == u"<<=" or node.children[1].symbol.text == u">>=" or node.children[
                        1].symbol.text == u">>>="):
                    continue  # not an assignment operator

                nodeList.append([expressionIndex, "AssignmentOperatorReplacementShortcut"])

            return nodeList

        elif mode == "return_tree":
            assert nodeIndex is not None
            node = self.javaParseObject.getNode(tree, nodeIndex)
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], JavaParser.ExpressionContext) and isinstance(node.children[1],
                                                                                              TerminalNodeImpl) and isinstance(
                        node.children[2], JavaParser.ExpressionContext)):
                    assert False
            except Exception, e:
                assert False

            if not (node.children[1].symbol.text == u"+=" or node.children[1].symbol.text == u"-=" or node.children[
                    1].symbol.text == u"*=" or node.children[1].symbol.text == u"/=" or node.children[
                    1].symbol.text == u"%=" or node.children[1].symbol.text == u"&=" or node.children[
                    1].symbol.text == u"|=" or node.children[1].symbol.text == u"^=" or node.children[
                    1].symbol.text == u"<<=" or node.children[1].symbol.text == u">>=" or node.children[
                    1].symbol.text == u">>>="):
                assert False

            originalText = node.children[1].symbol.text

            if originalText == u"+=":
                node.children[1].symbol.text = u"-="
            elif originalText == u"-=":
                node.children[1].symbol.text = u"+="
            elif originalText == u"/=":
                node.children[1].symbol.text = u"*="
            elif originalText == u"*=":
                node.children[1].symbol.text = u"/="
            elif originalText == u"%=":
                node.children[1].symbol.text = u"/="
            elif originalText == u"&=":
                node.children[1].symbol.text = u"|="
            elif originalText == u"|=":
                node.children[1].symbol.text = u"^="
            elif originalText == u"^=":
                node.children[1].symbol.text = u"&="
            elif originalText == u">>=":
                node.children[1].symbol.text = u">>>="
            elif originalText == u"<<=":
                node.children[1].symbol.text = u">>="
            elif originalText == u">>>=":
                node.children[1].symbol.text = u">>="
            else:
                assert False

            return tree

