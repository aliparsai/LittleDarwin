"""Mutation representation and operators acting on ANTLR Java parse trees."""
import copy
import sys
from math import log10
from random import shuffle
from typing import List, Dict
import antlr4
from antlr4 import Token
from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl
from mediumdarwin.JavaParse import JavaParse
from mediumdarwin.JavaParser import JavaParser
from mediumdarwin.Database import Database
from mediumdarwin.SharedFunctions import getAllInstantiableSubclasses
from mediumdarwin.SharedFunctions import MutationOperator
from itertools import combinations

sys.setrecursionlimit(100000)


class Mutation(object):
    """
    Defines a single mutation.
    """
    mutation_dict = {}
    reverse_mutation_dict = {}
    STYLE_REPLACE = "replace"
    STYLE_APPEND = "append"
    # STYLE_INSERT = "insert"
    # STYLE_DELETE = "delete"
    applied_node_id = 0

    def __init__(
        self,
        startPos: int,
        endPos: int,
        lineNumber: int,
        nodeID: int,
        mutatorType: str,
        replacementText: str,
        color: str = "#FFFFFF",
        mutationID: int = None,
        # mutated_node=None,
        # replaced_node=None,
        # ------------------
        applied_node_id: list = None,
        applied_mutation_style: list = STYLE_REPLACE,
        applied_node_new: list = None,
    ):
        """ """
        assert endPos >= startPos
        self.startPos = startPos
        self.endPos = endPos
        self.lineNumber = lineNumber
        self.color = color
        self.replacementText = replacementText
        self.mutationID = mutationID

        self.mutatorType = mutatorType

        self.nodeID = nodeID

        Mutation.mutation_dict[mutationID] = (
            applied_node_id, applied_node_new, applied_mutation_style)

    def apply_mutation_in_place(self, original_tree):
        list_node_indexes = Mutation.mutation_dict[self.mutationID][0]
        list_nodes = Mutation.mutation_dict[self.mutationID][1]
        list_styles = Mutation.mutation_dict[self.mutationID][2]
        app_inds = list()
        app_nodes = list()

        update_indexes = False

        for i in range(len(list_node_indexes)):
            if list_styles[i] == Mutation.STYLE_REPLACE:
                m_node = JavaParse.findNodeInSubtree(
                    original_tree, list_node_indexes[i])
                if (not hasattr(m_node, "applied_node_id")):
                    update_indexes = True
                    list_nodes[i].applied_node_id = Mutation.applied_node_id
                    m_node.applied_node_id = Mutation.applied_node_id
                    app_inds.append(Mutation.applied_node_id)
                    app_nodes.append(
                        recursiveCloneANTLRNodeAndItsChildren(m_node))
                    Mutation.applied_node_id += 1
                else:
                    app_inds.append(m_node.applied_node_id)
                    app_nodes.append(
                        recursiveCloneANTLRNodeAndItsChildren(m_node))
                replaceNodes(m_node, list_nodes[i])
            elif list_styles[i] == Mutation.STYLE_APPEND:
                m_node = JavaParse.findNodeInSubtree(
                    original_tree, list_node_indexes[i])

                if (not hasattr(m_node, "applied_node_id")):
                    update_indexes = True
                    list_nodes[i].applied_node_id = Mutation.applied_node_id
                    # m_node.applied_node_id = Mutation.applied_node_id
                    app_inds.append(Mutation.applied_node_id)
                    app_nodes.append(None)
                    Mutation.applied_node_id += 1
                else:
                    app_inds.append(m_node.applied_node_id)
                    app_nodes.append(None)
                terminalNodeImpl1 = TerminalNodeImpl(Token())
                terminalNodeImpl1.symbol.text = "("
                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = ")"
                parExpressionContext = JavaParser.ParExpressionContext(m_node)
                parExpressionContext.addChild(terminalNodeImpl1)
                parExpressionContext.addChild(
                    recursiveCloneANTLRNodeAndItsChildren(m_node))
                parExpressionContext.addChild(list_nodes[i])
                parExpressionContext.addChild(terminalNodeImpl2)
                replaceNodes(m_node, parExpressionContext)
            if (update_indexes):
                Mutation.reverse_mutation_dict[self.mutationID] = (
                    app_inds, app_nodes)
        return (app_inds, app_nodes)

    def apply_reverse_mutation_in_place(self, mutated_tree, app_inds=None, app_nodes=None):
        list_node_indexes = Mutation.mutation_dict[self.mutationID][0]
        list_nodes = Mutation.mutation_dict[self.mutationID][1]
        list_styles = Mutation.mutation_dict[self.mutationID][2]

        list_rev_node_indexes = Mutation.reverse_mutation_dict[
            self.mutationID][0] if app_inds is None else app_inds
        list_rev_nodes = Mutation.reverse_mutation_dict[
            self.mutationID][1] if app_nodes is None else app_nodes
        for i in range(len(list_node_indexes)):
            if list_styles[i] == Mutation.STYLE_REPLACE:
                m_node = JavaParse.findNodeInSubtree(
                    mutated_tree, list_rev_node_indexes[i], "applied_node_id")
                if (m_node is None):
                    break
                replaceNodes(
                    m_node, list_rev_nodes[i])
            elif list_styles[i] == Mutation.STYLE_APPEND:
                m_node = JavaParse.findNodeInSubtree(
                    mutated_tree, list_rev_node_indexes[i], "applied_node_id")
                if (m_node is None):
                    break
                m_node.symbol.text = ""

    def __str__(self):
        text = "Mutated Text: {} \n".format(self.replacementText)
        text += "Mutation Operator Type: {} \n".format(self.mutatorType)
        text += "Node ID: {}".format(self.nodeID)
        return text

    def applyMutation(self, sourceCode: str, byteOffset: int = 0) -> str:
        """

        :param byteOffset:
        :type byteOffset:
        :param sourceCode:
        :type sourceCode:
        :return:
        :rtype:
        """
        return (
            sourceCode[: self.startPos + byteOffset]
            + self.replacementText
            + sourceCode[self.endPos + byteOffset + 1:]
        )

    def isInRange(self, start, end):
        """

        :param start:
        :type start:
        :param end:
        :type end:
        :return:
        :rtype:
        """
        return end >= self.startPos >= start

    @property
    def byteOffset(self) -> int:
        """
        Returns the byte offset introduced by the mutation.

        :return:  byte offset introduced by the mutation
        :rtype: int
        """
        return len(self.replacementText) - (self.endPos - self.startPos + 1)


class HOM(object):

    def __init__(self, mutationList: List[Mutation]):
        self.mutationList = mutationList

    def return_mutated_node(self, main_node, mutationList):
        """
        returns the mutated version of the main_node
        """
        for mutation in mutationList:
            assert isinstance(mutation, Mutation)
            mutation.apply_mutation_in_place(main_node)
        return main_node

    def return_original_node(self, mutated_tree, mutationList):
        """
        returns the mutated version of the main_node
        """

        for mutation in mutationList:
            assert isinstance(mutation, Mutation)
            mutation.apply_reverse_mutation_in_place(mutated_tree)

        return mutated_tree


class Mutant(object):
    """
    Defines a mutant consisting of one or several mutations.
    """

    def __init__(self, mutantID: int, mutationList: List[Mutation], sourceCode: str):
        """
        :param mutantID: the ID of mutant
        :type mutantID: int
        :param mutationList: The list containing all Mutation objects
        :type mutationList: list
        :param sourceCode: The source code for the current file
        :type sourceCode: str
        """
        self.mutantID = mutantID
        self.sourceCode = sourceCode
        self.mutatedCode = None

        for mutation in mutationList:
            assert isinstance(mutation, Mutation)

        self.mutationList = mutationList

    def getLine(self, lineNumber: int, code: str = None) -> str:
        """
        :returns the referenced line from source code.
        :param lineNumber: Desired line number.
        :param code: The code from which the line is taken. Defaults to original source code.
        """
        if code is None:
            code = self.sourceCode

        return code.splitlines(keepends=False)[lineNumber - 1]

    def mutateCode(self):
        """
        Applies the mutations in mutationList to the source code.
        """
        code = self.sourceCode
        byteOffsetDict = dict()

        for mutation in self.mutationList:
            byteOffsetDict[mutation.startPos] = mutation.byteOffset
            for pos in sorted(byteOffsetDict.keys()):
                if pos < mutation.startPos:
                    byteOffsetDict[mutation.startPos] = (
                        byteOffsetDict[pos] + mutation.byteOffset
                    )
                elif pos > mutation.startPos:
                    byteOffsetDict[pos] += mutation.byteOffset

            code = mutation.applyMutation(
                code, byteOffsetDict[mutation.startPos] - mutation.byteOffset
            )

        self.mutatedCode = code

    @property
    def stub(self) -> str:
        """
        Generates the text stub that goes in the beginning of each mutant file.

        :return: Returns text stub on top of each mutant
        :rtype: str
        """
        assert len(self.mutationList) > 0
        assert self.mutatedCode is not None

        textStub = "/* MediumDarwin generated order-{0} mutant\n".format(
            str(len(self.mutationList))
        )  # type: str

        textStub += "\n----> mutantID: " + str(self.mutantID) + "\n\n"
        for mutation in self.mutationList:
            a = self.getLine(mutation.lineNumber)
            a = a.replace("*/", r"*\/")

            b = self.getLine(
                mutation.lineNumber, code=mutation.applyMutation(
                    self.sourceCode)
            )
            b = b.replace("*/", r"*\/")
            textStub += (
                "mutant type: "
                + mutation.mutatorType
                + "\n----> before: "
                + a
                + "\n----> after: "
                + b
                + "\n----> line number in original file: "
                + str(mutation.lineNumber)
                + "\n----> mutated node: "
                + str(mutation.nodeID)
                + "\n----> mutation ID: "
                + str(mutation.mutationID)
                + "\n\n"
            )

        textStub += "*/\n\n"
        return textStub

    def __add__(self, other):
        if other is None:
            return copy.deepcopy(self)
        if isinstance(other, Mutant):
            if self.sourceCode == other.sourceCode:
                newMutationList = list()
                newMutationList.extend(self.mutationList)
                newMutationList.extend(other.mutationList)
                newMutant = Mutant(
                    -1 * self.mutantID * other.mutantID,
                    newMutationList,
                    self.sourceCode,
                )
                newMutant.mutateCode()
                return newMutant
            else:
                raise ValueError(
                    "Only Mutant objects of the same source code can be added."
                )
        else:
            raise ValueError("Only Mutant objects can be added.")

    def __radd__(self, other):
        return self.__add__(other)

    def __str__(self):
        if self.mutatedCode is None:
            self.mutateCode()
        return self.mutatedCode + "\n" + self.stub


#################################################
#       Method-level Mutation Operators         #
#################################################


class RemoveMethod(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Method", "All"]

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveMethod"
        self.color = "#FF00D4"
        self.mutableNodesWithTypes = list()
        self.mutation_id = mutation_id
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self, search_children=True):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.MethodBodyContext, search_children=search_children
        )

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.MethodBodyContext)
            nodeType = self.javaParseObject.getMethodTypeForNode(node)
            if nodeType is not None:
                self.mutableNodes.append(
                    node
                )  # No need to do this, but kept here for compatibility.
                self.mutableNodesWithTypes.append((node, nodeType))

    def generateBlockContext(expressionContext, node):
        blockContext = JavaParser.BlockContext(node)
        bracet1 = TerminalNodeImpl(Token())
        bracet1.symbol.text = "{"
        blockContext.addChild(bracet1)
        blockStatementContext = JavaParser.BlockStatementContext(node)
        statementContext = JavaParser.StatementContext(node)
        returnTerminal = TerminalNodeImpl(Token())
        returnTerminal.symbol.text = "return"
        statementContext.addChild(returnTerminal)

        statementContext.addChild(expressionContext)
        colonTerminal = TerminalNodeImpl(Token())
        colonTerminal.symbol.text = ";"
        statementContext.addChild(colonTerminal)

        blockStatementContext.addChild(statementContext)
        blockContext.addChild(blockStatementContext)
        bracet2 = TerminalNodeImpl(Token())
        bracet2.symbol.text = "}"
        blockContext.addChild(bracet2)
        return blockContext

    def generateMutations(self):
        # Sort mutableNodesWithTypes deterministically by lineNumber, startPos, nodeID
        self.mutableNodesWithTypes.sort(
            key=lambda item: (
                item[0].children[0].start.line if hasattr(item[0], 'children') and len(item[0].children) > 0 and hasattr(
                    item[0].children[0], 'start') and hasattr(item[0].children[0].start, 'line') else 0,
                item[0].children[0].start.start if hasattr(item[0], 'children') and len(item[0].children) > 0 and hasattr(
                    item[0].children[0], 'start') and hasattr(item[0].children[0].start, 'start') else 0,
                item[0].children[0].nodeIndex if hasattr(item[0], 'children') and len(
                    item[0].children) > 0 and hasattr(item[0].children[0], 'nodeIndex') else 0
            )
        )
        for node, nodeType in self.mutableNodesWithTypes:
            replacementNodeList = []
            replacementTextList = []
            mutationIndexList = []
            if nodeType == "void":
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + ""
                expressionContext = JavaParser.ExpressionContext(node)
                primaryContext = JavaParser.PrimaryContext(node)
                literalContext = JavaParser.LiteralContext(node)
                literalContext.addChild(terminalNodeImpl)
                primaryContext.addChild(literalContext)
                expressionContext.addChild(primaryContext)
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext, node))
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "return;}")
                mutationIndexList.append(self.mutation_id)

            elif nodeType == "boolean":
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "true"
                expressionContext = JavaParser.ExpressionContext(node)
                primaryContext = JavaParser.PrimaryContext(node)
                literalContext = JavaParser.LiteralContext(node)
                literalContext.addChild(terminalNodeImpl)
                primaryContext.addChild(literalContext)
                expressionContext.addChild(primaryContext)

                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return true;}")
                mutationIndexList.append(self.mutation_id)

                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext, node))
                self.mutation_id += 1

                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "false"
                expressionContext2 = JavaParser.ExpressionContext(node)
                primaryContext2 = JavaParser.PrimaryContext(node)
                literalContext2 = JavaParser.LiteralContext(node)
                literalContext2.addChild(terminalNodeImpl2)
                primaryContext2.addChild(literalContext2)
                expressionContext2.addChild(primaryContext2)

                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext2, node))
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return false;}")
                mutationIndexList.append(self.mutation_id)
                # self.mutation_id+=1
            elif (
                nodeType == "byte"
                or nodeType == "short"
                or nodeType == "long"
                or nodeType == "int"
            ):
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "0"

                expressionContext = JavaParser.ExpressionContext(node)
                primaryContext = JavaParser.PrimaryContext(node)
                literalContext = JavaParser.LiteralContext(node)
                literalContext.addChild(terminalNodeImpl)
                primaryContext.addChild(literalContext)
                expressionContext.addChild(primaryContext)

                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 0;}")
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(terminalNodeImpl, node))
                mutationIndexList.append(self.mutation_id)
                self.mutation_id += 1

                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "1"
                expressionContext2 = JavaParser.ExpressionContext(node)
                primaryContext2 = JavaParser.PrimaryContext(node)
                literalContext2 = JavaParser.LiteralContext(node)
                literalContext2.addChild(terminalNodeImpl2)
                primaryContext2.addChild(literalContext2)
                expressionContext2.addChild(primaryContext2)

                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(terminalNodeImpl2, node))
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 1;}")
                mutationIndexList.append(self.mutation_id)
                # self.mutation_id+=1

            elif nodeType == "float":
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "0.0f"
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 0.0f;}")
                mutationIndexList.append(self.mutation_id)
                self.mutation_id += 1

                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "0.1f"
                replacementNodeList = [RemoveMethod.generateBlockContext(
                    terminalNodeImpl, node), RemoveMethod.generateBlockContext(terminalNodeImpl2, node)]
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 0.1f;}")
                mutationIndexList.append(self.mutation_id)
                # self.mutation_id+=1
            elif nodeType == "double":
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "0.0"
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 0.0;}")
                mutationIndexList.append(self.mutation_id)
                self.mutation_id += 1

                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "0.1"
                replacementNodeList = [RemoveMethod.generateBlockContext(
                    terminalNodeImpl, node), RemoveMethod.generateBlockContext(terminalNodeImpl2, node)]
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 0.1;}")
                mutationIndexList.append(self.mutation_id)
                # self.mutation_id+=1
            elif nodeType == "char":
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "''"
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return '';}")
                mutationIndexList.append(self.mutation_id)

                expressionContext = JavaParser.ExpressionContext(node)
                primaryContext = JavaParser.PrimaryContext(node)
                literalContext = JavaParser.LiteralContext(node)
                literalContext.addChild(terminalNodeImpl)
                primaryContext.addChild(literalContext)
                expressionContext.addChild(primaryContext)
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext, node))

                self.mutation_id += 1
                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + "'A'"
                expressionContext2 = JavaParser.ExpressionContext(node)
                primaryContext2 = JavaParser.PrimaryContext(node)
                literalContext2 = JavaParser.LiteralContext(node)
                literalContext2.addChild(terminalNodeImpl2)
                primaryContext2.addChild(literalContext2)
                expressionContext2.addChild(primaryContext2)
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext2, node))
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "    return 'A';}")
                mutationIndexList.append(self.mutation_id)
                # self.mutation_id+=1
            elif nodeType == "String":
                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + '""'
                replacementTextList.append(
                    '{'+"/*MUT" + str(self.mutation_id) + "*/" + '    return "";}')
                mutationIndexList.append(self.mutation_id)

                expressionContext = JavaParser.ExpressionContext(node)
                primaryContext = JavaParser.PrimaryContext(node)
                literalContext = JavaParser.LiteralContext(node)
                literalContext.addChild(terminalNodeImpl)
                primaryContext.addChild(literalContext)
                expressionContext.addChild(primaryContext)
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext, node))
                self.mutation_id += 1

                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + '"A"'
                expressionContext2 = JavaParser.ExpressionContext(node)
                primaryContext2 = JavaParser.PrimaryContext(node)
                literalContext2 = JavaParser.LiteralContext(node)
                literalContext2.addChild(terminalNodeImpl2)
                primaryContext2.addChild(literalContext2)
                expressionContext2.addChild(primaryContext2)
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext2, node))
                replacementTextList.append(
                    '{'+"/*MUT" + str(self.mutation_id) + "*/" + '    return "A";}')
                mutationIndexList.append(self.mutation_id)
            elif "[" in nodeType and "]" in nodeType and "<" not in nodeType:

                terminalNodeImpl = TerminalNodeImpl(Token())
                terminalNodeImpl.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + \
                    "new {} {{}}".format(nodeType)
                expressionContext = JavaParser.ExpressionContext(node)
                expressionContext.addChild(terminalNodeImpl)

                creatorContext = JavaParser.CreatorContext(node)
                createdNameContext = JavaParser.CreatedNameContext(node)
                creatorContext.addChild(createdNameContext)
                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = nodeType
                createdNameContext.addChild(terminalNodeImpl2)

                classCreatorRestContext = JavaParser.ClassCreatorRestContext(
                    node)
                argumentsContext = JavaParser.ArgumentsContext(node)
                classCreatorRestContext.addChild(argumentsContext)
                terminalNodeImpl3 = TerminalNodeImpl(Token())
                terminalNodeImpl3.symbol.text = '('
                terminalNodeImpl4 = TerminalNodeImpl(Token())
                terminalNodeImpl4.symbol.text = ')'
                argumentsContext.addChild(terminalNodeImpl3)
                argumentsContext.addChild(terminalNodeImpl4)
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(expressionContext, node))
                replacementTextList.append(
                    "{{"+"/*MUT" + str(self.mutation_id) + "*/" +
                    "    return new {} {{}};}}".format(nodeType)
                )
                mutationIndexList.append(self.mutation_id)
                # self.mutation_id+=1
            else:
                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "/*MUT" + \
                    str(self.mutation_id) + "*/" + ' null'
                replacementNodeList.append(
                    RemoveMethod.generateBlockContext(terminalNodeImpl2, node))
                replacementTextList.append(
                    "{"+"/*MUT" + str(self.mutation_id) + "*/" + "return null;}")
                mutationIndexList.append(self.mutation_id)
            self.mutation_id += 1

            for i in range(len(replacementTextList)):
                # ---------------------------------------------
                mutation = Mutation(startPos=node.children[0].start.start, endPos=node.children[0].stop.stop,
                                    lineNumber=node.children[0].start.line,
                                    nodeID=node.children[0].nodeIndex,
                                    mutatorType=self.mutatorType,
                                    replacementText=replacementTextList[i],
                                    mutationID=mutationIndexList[i],
                                    color=self.color,
                                    applied_mutation_style=[
                    Mutation.STYLE_REPLACE],
                    applied_node_id=[node.children[0].nodeIndex],
                    applied_node_new=[replacementNodeList[i]]
                )
                self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


#################################################
#          Null Mutation Operators              #
#################################################


class RemoveNullCheck(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveNullCheck"
        self.color = "#ADD8E6"
        self.mutation_id = mutation_id
        self.mutableNodes_comparison = list()
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self, search_children=True):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.ExpressionContext, search_children=search_children
        )

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (
                    isinstance(node.children[0], JavaParser.ExpressionContext)
                    and isinstance(node.children[1], TerminalNodeImpl)
                    and isinstance(node.children[2], JavaParser.ExpressionContext)
                ):
                    continue  # not a binary expression

            except Exception as e:
                continue

            if not (
                node.children[1].symbol.text == "!="
                or node.children[1].symbol.text == "=="
            ):
                continue  # not a relational operator

            if "null" not in node.getText():
                continue  # not a null check

            self.mutableNodes.append(node)
            self.mutableNodes_comparison.append(
                (node, node.children[1].symbol.text))

    def generateMutations(self):
        # Sort mutableNodes_comparison deterministically by lineNumber, startPos, nodeID
        self.mutableNodes_comparison.sort(
            key=lambda item: (
                item[0].start.line if hasattr(item[0], 'start') and hasattr(
                    item[0].start, 'line') else 0,
                item[0].start.start if hasattr(item[0], 'start') and hasattr(
                    item[0].start, 'start') else 0,
                item[0].nodeIndex if hasattr(item[0], 'nodeIndex') else 0
            )
        )
        for (node, text) in self.mutableNodes_comparison:
            replacementText = ""
            if text == "!=":  # node.children[1].symbol.text == "!=":
                replacementText = node.getText() + " || /*MUT" + \
                    str(self.mutation_id) + "*/" + "true"
            elif text == "==":  # node.children[1].symbol.text
                replacementText = node.getText() + " && /*MUT" + \
                    str(self.mutation_id) + "*/" + "false"

            expressionContext = JavaParser.ExpressionContext(node)
            primaryContext = JavaParser.PrimaryContext(node)
            literalContext = JavaParser.LiteralContext(node)
            terminalNodeImpl = TerminalNodeImpl(Token())
            terminalNodeImpl.symbol.text = replacementText
            literalContext.addChild(terminalNodeImpl)
            primaryContext.addChild(literalContext)
            expressionContext.addChild(primaryContext)
            terminalNodeImpl2 = TerminalNodeImpl(Token())
            terminalNodeImpl2.symbol.text = " || /*MUT" + \
                str(self.mutation_id) + "*/" + "true" if text == "!=" else " && /*MUT" + \
                str(self.mutation_id) + "*/" + "false"

            terminalNodeImpl3 = TerminalNodeImpl(Token())
            terminalNodeImpl3.symbol.text = "("

            terminalNodeImpl4 = TerminalNodeImpl(Token())
            terminalNodeImpl4.symbol.text = ")"

            parExpressionContext = JavaParser.ParExpressionContext(node)
            parExpressionContext.addChild(terminalNodeImpl3)
            parExpressionContext.addChild(expressionContext)
            parExpressionContext.addChild(terminalNodeImpl2)
            parExpressionContext.addChild(terminalNodeImpl4)

            # ---------------------------------------------
            mutation = Mutation(
                mutationID=self.mutation_id,
                startPos=node.start.start,
                endPos=node.stop.stop,
                lineNumber=node.start.line,
                nodeID=node.nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
                color=self.color,
                applied_mutation_style=[Mutation.STYLE_APPEND],
                applied_node_id=[node.nodeIndex],
                applied_node_new=[terminalNodeImpl2]
            )
            # ---------------------------------------------
            self.mutation_id += 1
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


class NullifyObjectInitialization(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyObjectInitialization"
        self.color = "#F08080"
        self.findNodes(search_children=search_children)
        self.filterCriteria()
        self.mutation_id = mutation_id
        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self, search_children=True):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.CreatorContext, search_children=search_children
        )

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.CreatorContext)

            try:
                newStatement = node.parentCtx.getChild(0, TerminalNodeImpl)
                argumentsStatement = node.children[-1].children[-1]

                if newStatement.symbol.text != "new":
                    continue

                if not isinstance(argumentsStatement, JavaParser.ArgumentsContext):
                    continue

                if argumentsStatement.children[-1].symbol.text != ")":
                    continue

            except Exception:
                continue

            self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically by lineNumber, startPos, nodeID
        self.mutableNodes.sort(
            key=lambda node: (
                node.start.line if hasattr(node, 'start') and hasattr(
                    node.start, 'line') else 0,
                node.start.start if hasattr(node, 'start') and hasattr(
                    node.start, 'start') else 0,
                node.nodeIndex if hasattr(node, 'nodeIndex') else 0
            )
        )
        for node in self.mutableNodes:
            node = node.parentCtx
            replacementText = "/*MUT" + str(self.mutation_id) + "*/" + "null"
            expressionContext = JavaParser.ExpressionContext(node)
            terminalNode = TerminalNodeImpl(Token())
            terminalNode.symbol.text = replacementText
            expressionContext.addChild(terminalNode)

            # ---------------------------------------------
            mutation = Mutation(
                mutationID=self.mutation_id,
                startPos=node.start.start,
                endPos=node.stop.stop,
                lineNumber=node.start.line,
                nodeID=node.nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
                color=self.color,
                applied_mutation_style=[Mutation.STYLE_REPLACE],
                applied_node_id=[node.nodeIndex],
                applied_node_new=[expressionContext]
            )

            # ---------------------------------------------
            self.mutation_id += 1
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


class NullifyReturnValue(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyReturnValue"
        self.color = "#E0FFFF"
        self.findNodes(search_children=search_children)
        self.filterCriteria()
        self.mutation_id = mutation_id

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self, search_children=True):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, TerminalNodeImpl, search_children=search_children
        )

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, TerminalNodeImpl)

            if node.symbol.text != "return":
                continue

            if node.getParent() is None or not isinstance(
                node.getParent().getChild(1), JavaParser.ExpressionContext
            ):
                continue

            parentMethod = self.javaParseObject.seekFirstMatchingParent(
                node, JavaParser.MethodDeclarationContext
            )
            if parentMethod is None:
                continue

            assert isinstance(
                parentMethod, JavaParser.MethodDeclarationContext)

            parentType = parentMethod.getChild(0, JavaParser.JTypeContext)
            if not isinstance(parentType, JavaParser.JTypeContext):
                continue

            if parentType.getChild(0, JavaParser.PrimitiveTypeContext) is not None and "[" not in parentType.getText():
                continue  # primitive typed method

            self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically by lineNumber, startPos, nodeID
        self.mutableNodes.sort(
            key=lambda node: (
                node.getParent().start.line if hasattr(node, 'getParent') and node.getParent() and hasattr(
                    node.getParent(), 'start') and hasattr(node.getParent().start, 'line') else 0,
                node.symbol.start if hasattr(node, 'symbol') and hasattr(
                    node.symbol, 'start') else 0,
                node.getParent().nodeIndex if hasattr(node, 'getParent') and node.getParent(
                ) and hasattr(node.getParent(), 'nodeIndex') else 0
            )
        )
        for node in self.mutableNodes:
            assert isinstance(node.symbol, Token)
            replacementText = "return /*MUT" + \
                str(self.mutation_id) + "*/ null;"

            expressionContext = JavaParser.ExpressionContext(node)
            primaryContext = JavaParser.PrimaryContext(node)
            literalContext = JavaParser.LiteralContext(node)
            terminalNodeImpl_2 = TerminalNodeImpl(Token())
            terminalNodeImpl_2.symbol.text = "/*MUT" + \
                str(self.mutation_id) + "*/ null"
            literalContext.addChild(terminalNodeImpl_2)
            primaryContext.addChild(literalContext)
            expressionContext.addChild(primaryContext)

            # ---------------------------------------------
            mutation = Mutation(
                mutationID=self.mutation_id,
                startPos=node.symbol.start,
                endPos=node.getParent().getChild(2).symbol.stop,
                lineNumber=node.getParent().start.line,
                nodeID=node.getParent().nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
                color=self.color,
                applied_mutation_style=[Mutation.STYLE_REPLACE],
                applied_node_id=[node.getParent().getChild(1).nodeIndex],
                applied_node_new=[expressionContext]
            )
            # ---------------------------------------------

            self.mutation_id += 1
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


class NullifyInputVariable(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyInputVariable"
        self.color = "#90EE90"
        self.findNodes(search_children=search_children)
        self.filterCriteria()
        self.mutation_id = mutation_id

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self, search_children=True):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.MethodDeclarationContext, search_children=search_children
        )

    def filterCriteria(self, search_children=True):
        """ """

        def isInLambda(javaParseObject, methodBody, variableName):
            lambdaNodes = javaParseObject.seekAllNodes(
                methodBody, JavaParser.LambdaBodyContext)
            for lambdaNode in lambdaNodes:
                primaryContexts = javaParseObject.seekAllNodes(
                    lambdaNode, JavaParser.PrimaryContext)
                for prim_cont in primaryContexts:
                    if (prim_cont.getText() == variableName):
                        return True
            return False

        def isInInnerClass(javaParseObject, methodBody, variableName):
            methodNodes = javaParseObject.seekAllNodes(
                methodBody, JavaParser.MethodBodyContext, search_children=True)
            for methodNode in methodNodes:
                primaryContexts = javaParseObject.seekAllNodes(
                    methodNode, JavaParser.PrimaryContext)
                for prim_cont in primaryContexts:
                    if (prim_cont.getText() == variableName):
                        return True
            return False
        self.replacementTextDict = dict()
        self.replacementNodeDict = dict()

        for methodDeclaration in self.allNodes:
            try:
                variableList = self.javaParseObject.seekAllNodes(
                    methodDeclaration.formalParameters(),
                    JavaParser.VariableDeclaratorIdContext, search_children=search_children
                )

                if len(variableList) == 0:
                    continue  # no variables in this declaration

                # can fail on methods with no body
                node = (
                    methodDeclaration.methodBody().block().getChild(0, TerminalNodeImpl)
                )

            except Exception as e:
                continue

            variablesPerNodeReplacementTextList = list()
            variablesPerNodeReplacementNodeList = list()
            for variablesPerNode in variableList:
                assert isinstance(
                    variablesPerNode, JavaParser.VariableDeclaratorIdContext
                )

                if ((isInInnerClass(self.javaParseObject, methodDeclaration.methodBody().block(), variablesPerNode.getText())) or
                        (isInLambda(self.javaParseObject, methodDeclaration, variablesPerNode.getText())) or (
                        variablesPerNode.parentCtx.getChild(
                            0, JavaParser.JTypeContext
                            ).getChild(0, JavaParser.PrimitiveTypeContext)
                        is not None) or (variablesPerNode.parentCtx.getChild(0, JavaParser.VariableModifierContext) is not None)
                        ):
                    continue  # primitive typed variable

                variablesPerNodeReplacementTextList.append(
                    "{ " + variablesPerNode.getText() + " = null;"
                )

                blockStatementContext = JavaParser.BlockStatementContext(
                    methodDeclaration)
                statementContext = JavaParser.StatementContext(
                    methodDeclaration)
                statementExpressionContext = JavaParser.StatementExpressionContext(
                    methodDeclaration)
                expressionContext = JavaParser.ExpressionContext(
                    methodDeclaration)
                expressionContext2 = JavaParser.ExpressionContext(
                    methodDeclaration)
                primaryContext = JavaParser.PrimaryContext(methodDeclaration)
                terminalNodeImpl1 = TerminalNodeImpl(Token())
                terminalNodeImpl1.symbol.text = variablesPerNode.getText()
                primaryContext.addChild(terminalNodeImpl1)
                expressionContext2.addChild(primaryContext)

                terminalNodeImpl2 = TerminalNodeImpl(Token())
                terminalNodeImpl2.symbol.text = "="

                expressionContext3 = JavaParser.ExpressionContext(
                    methodDeclaration)
                primaryContext2 = JavaParser.PrimaryContext(methodDeclaration)
                literalContext = JavaParser.LiteralContext(methodDeclaration)
                terminalNodeImpl3 = TerminalNodeImpl(Token())
                terminalNodeImpl3.symbol.text = "null"
                literalContext.addChild(terminalNodeImpl3)
                primaryContext2.addChild(literalContext)
                expressionContext3.addChild(primaryContext2)

                expressionContext.addChild(expressionContext2)
                expressionContext.addChild(terminalNodeImpl2)
                expressionContext.addChild(expressionContext3)
                statementExpressionContext.addChild(expressionContext)
                statementContext.addChild(statementExpressionContext)
                blockStatementContext.addChild(statementContext)
                variablesPerNodeReplacementNodeList.append(
                    NullifyInputVariable.generateBlockContext(blockStatementContext, node))

            self.replacementTextDict[methodDeclaration] = variablesPerNodeReplacementTextList
            self.replacementNodeDict[methodDeclaration] = variablesPerNodeReplacementNodeList
            self.mutableNodes.append(methodDeclaration)

    def generateBlockContext(expressionContext, node):
        blockContext = JavaParser.BlockContext(node)
        bracet1 = TerminalNodeImpl(Token())
        bracet1.symbol.text = "{"
        blockContext.addChild(bracet1)
        blockStatementContext = JavaParser.BlockStatementContext(node)
        statementContext = JavaParser.StatementContext(node)

        statementContext.addChild(expressionContext)
        colonTerminal = TerminalNodeImpl(Token())
        colonTerminal.symbol.text = ";"
        statementContext.addChild(colonTerminal)

        blockStatementContext.addChild(statementContext)
        blockContext.addChild(blockStatementContext)
        bracet2 = TerminalNodeImpl(Token())
        bracet2.symbol.text = "}"
        blockContext.addChild(bracet2)
        return blockContext

    def generateMutations(self):
        # Sort mutableNodes deterministically by lineNumber, startPos, nodeID
        self.mutableNodes.sort(
            key=lambda node: (
                node.start.line if hasattr(node, 'start') and hasattr(
                    node.start, 'line') else 0,
                node.methodBody().start.start if hasattr(node, 'methodBody') and hasattr(
                    node.methodBody(), 'start') and hasattr(node.methodBody().start, 'start') else 0,
                node.nodeIndex if hasattr(node, 'nodeIndex') else 0
            )
        )
        for node in self.mutableNodes:
            for replacementText, mutated_node in zip(self.replacementTextDict[node], self.replacementNodeDict[node]):
                # ---------------------------------------------
                mutation = Mutation(
                    mutationID=self.mutation_id,
                    startPos=node.methodBody().start.start,
                    endPos=node.methodBody().stop.stop,
                    lineNumber=node.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText="/*MUT" +
                    str(self.mutation_id) + "*/" + replacementText,
                    color=self.color,
                    applied_mutation_style=[Mutation.STYLE_REPLACE],
                    applied_node_id=[node.methodBody().block().nodeIndex],
                    applied_node_new=[mutated_node]
                )
                self.mutation_id += 1
                self.mutations.append(mutation)

        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


#################################################
#      Traditional Mutation Operators           #
#################################################
def findNodesWithMutationID(tree, mutationID):
    """
    :param tree:
    :type tree:
    :return:
    :rtype:
    """
    if tree is None:
        return None
    nodes = []
    children = [tree]
    while len(children):
        child = children.pop()
        try:
            children.extend(child.getChildren())
            mutationIDs = str(child.mutationID).split(",")
            for child_mutationID in mutationIDs:
                if (child_mutationID == mutationID):
                    nodes.append(child)
        except Exception as e:
            pass
    return nodes


def findNodeAt(tree, line, column):
    """
    :param tree:
    :type tree:
    :return:
    :rtype:
    """
    if tree is None:
        return None

    children = [tree]
    while len(children):
        child = children.pop()
        try:
            if isinstance(child, TerminalNodeImpl):
                if child.symbol.line == line and child.symbol.column == column:
                    return child
            else:
                if child.start.line == line and child.start.column == column:
                    return child
            children.extend(child.getChildren())
        except Exception as e:
            pass


def replaceNodes(toNode, fromNode):
    if (hasattr(toNode, "applied_node_id")):
        del toNode.applied_node_id
    if (hasattr(toNode, "mutationID")):
        del toNode.mutationID
    toNode.parentCtx = fromNode.parentCtx
    if (hasattr(fromNode, "hom")):
        toNode.hom = fromNode.hom

    if (hasattr(fromNode, "mutationID")):
        toNode.mutationID = fromNode.mutationID
    if (hasattr(fromNode, "applied_node_id")):
        toNode.applied_node_id = fromNode.applied_node_id

    if (isinstance(toNode, TerminalNodeImpl) and isinstance(fromNode, TerminalNodeImpl)):
        del toNode.symbol
        toNode.symbol = CommonToken()
        toNode.symbol.text = fromNode.symbol.text

    if (hasattr(toNode, "children")):
        while len(toNode.children) > 0:
            del toNode.children[0]

    if (hasattr(fromNode, "children")):
        for child in fromNode.children:
            toNode.addChild(child)


def recursiveCloneANTLRNodeAndItsChildren(node):
    """ """

    if not hasattr(node, "children"):
        if isinstance(node.symbol, str):
            temp = node.symbol
            newSymbol = CommonToken()
            newSymbol.text = temp
        elif isinstance(node.symbol, Token):
            temp = node.symbol.text
            newSymbol = CommonToken()
            newSymbol.text = temp
        newTree = TerminalNodeImpl(newSymbol)

        newTree.parentCtx = node.parentCtx
        if hasattr(node, "nodeIndex"):
            newTree.nodeIndex = node.nodeIndex
            newTree.contextID = node.contextID
        if hasattr(node, "applied_node_id"):
            newTree.applied_node_id = node.applied_node_id
        return newTree

    newTree = node.__class__(node)
    newTree.copyFrom(node)
    newTree.parentCtx = node.parentCtx
    if hasattr(node, "hom"):
        newTree.hom = node.hom
    if hasattr(node, "mutationID"):
        newTree.mutationID = node.mutationID
    if hasattr(node, "nodeIndex"):
        newTree.nodeIndex = node.nodeIndex
        newTree.contextID = node.contextID
    if hasattr(node, "applied_node_id"):
        newTree.applied_node_id = node.applied_node_id
    for child in node.children:
        newTree.addChild(recursiveCloneANTLRNodeAndItsChildren(child))
    return newTree


class TraditionalMutationOperator(MutationOperator):
    """ """

    metaTypes = ["Traditional", "All"]

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children: bool = True
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "GenericTraditionalMutationOperator"
        self.mutation_id = mutation_id

    def _sort_mutable_nodes(self):
        """Sort mutableNodes deterministically by startPos, lineNumber, nodeID."""
        self.mutableNodes.sort(
            key=lambda node: (
                node.start.start if hasattr(node, 'start') and hasattr(
                    node.start, 'start') else 0,
                node.start.line if hasattr(node, 'start') and hasattr(
                    node.start, 'line') else 0,
                node.nodeIndex if hasattr(node, 'nodeIndex') else 0
            )
        )

    def findNodes(self, search_children=True):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.ExpressionContext, search_children=search_children
        )

    def filterCriteriaBinaryExpression(
        self, node: JavaParser.ExpressionContext, symbolList: List[str]
    ):
        """ """
        assert isinstance(node, JavaParser.ExpressionContext)

        try:
            if not (
                isinstance(node.children[0], JavaParser.ExpressionContext)
                and isinstance(node.children[1], TerminalNodeImpl)
                and isinstance(node.children[2], JavaParser.ExpressionContext)
            ):
                return False

        except Exception as e:
            return False

        if node.children[1].symbol.text not in symbolList:
            return False

        return True

    def filterCriteriaUnaryExpression(
        self, node: JavaParser.ExpressionContext, symbolList: List[str]
    ):
        """ """
        assert isinstance(node, JavaParser.ExpressionContext)

        try:
            if not (
                isinstance(node.children[0], TerminalNodeImpl)
                and isinstance(node.children[1], JavaParser.ExpressionContext)
            ):
                return False
        except Exception as e:
            return False

        if node.children[0].symbol.text not in symbolList:
            return False

        return True

    def generateMutantionsUnaryExpression(
        self, node: JavaParser.ExpressionContext, symbolDict: dict
    ):
        mutated_node = recursiveCloneANTLRNodeAndItsChildren(node)
        mutated_node.children[0].symbol.text = "/*MUT" + \
            str(self.mutation_id) + "*/" + \
            symbolDict[node.children[0].symbol.text]
        replacementText = "/*MUT" + \
            str(self.mutation_id) + "*/" + \
            symbolDict[node.children[0].symbol.text]

        mutation = Mutation(mutationID=self.mutation_id,
                            startPos=node.children[0].symbol.start,
                            endPos=node.children[0].symbol.stop,
                            lineNumber=node.start.line,
                            nodeID=node.nodeIndex,
                            mutatorType=self.mutatorType,
                            replacementText=replacementText,
                            color=self.color,
                            applied_mutation_style=[Mutation.STYLE_REPLACE],
                            applied_node_id=[node.children[0].nodeIndex], applied_node_new=[mutated_node.children[0]])
        self.mutation_id += 1
        return mutation

    def generateMutantsUnaryExpression(self, mutationOrNode, symbolDict=None, id=None):
        if isinstance(mutationOrNode, Mutation):
            mutation = mutationOrNode
        else:
            node = mutationOrNode
            mutation = self.generateMutantionsUnaryExpression(
                node, symbolDict, id)

        mutant = Mutant(
            mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode
        )
        mutant.mutateCode()

        return mutant

    def generateMutationsBinaryExpression(
        self, node: JavaParser.ExpressionContext, symbolDict: dict
    ):
        """ """
        mutated_node = recursiveCloneANTLRNodeAndItsChildren(node)
        mutated_node.children[1].symbol.text = "/*MUT" + \
            str(self.mutation_id) + "*/" + \
            symbolDict[node.children[1].symbol.text]
        replacementText = "/*MUT" + \
            str(self.mutation_id) + "*/" + \
            symbolDict[node.children[1].symbol.text]

        mutation = Mutation(mutationID=self.mutation_id,
                            startPos=node.children[1].symbol.start,
                            endPos=node.children[1].symbol.stop,
                            lineNumber=node.start.line,
                            nodeID=node.nodeIndex,
                            mutatorType=self.mutatorType,
                            replacementText=replacementText,
                            color=self.color,
                            applied_mutation_style=[Mutation.STYLE_REPLACE],
                            applied_node_id=[node.children[1].nodeIndex], applied_node_new=[mutated_node.children[1]])
        self.mutation_id += 1
        return mutation

    def generateMutantsBinaryExpression(
        self, mutationOrNode, symbolDict: dict = None, id: int = None
    ):
        if isinstance(mutationOrNode, Mutation):
            mutation = mutationOrNode
        else:
            node = mutationOrNode
            mutation = self.generateMutationsBinaryExpression(node, symbolDict)

        mutant = Mutant(
            mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode
        )
        mutant.mutateCode()

        return mutant


class ArithmeticOperatorReplacementBinary(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ArithmeticOperatorReplacementBinary"
        self.color = "#FFB6C1"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if (
                self.filterCriteriaBinaryExpression(
                    node, ["+", "-", "*", "/", "%"])
                and node.children[0].getText()[0] != '"'
                and node.children[2].getText()[0] != '"'
            ):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutation = self.generateMutationsBinaryExpression(
                node, {"+": "-", "-": "+", "/": "*", "*": "/", "%": "/"}
            )
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsBinaryExpression(
                mutationOrNode=mutation, id=id
            )
            self.mutants.append(mutant)


class RelationalOperatorReplacement(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "RelationalOperatorReplacement"
        self.color = "#FFA07A"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(
                node, [">", ">=", "<", "<=", "==", "!="]
            ):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            mutation = self.generateMutationsBinaryExpression(
                node,
                {">": ">=", "<": "<=", ">=": ">",
                    "<=": "<", "!=": "==", "==": "!="},
            )
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsBinaryExpression(
                mutationOrNode=mutation, id=id
            )
            self.mutants.append(mutant)


class ConditionalOperatorReplacement(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ConditionalOperatorReplacement"
        self.color = "#87CEFA"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ["&&", "||"]):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            mutation = self.generateMutationsBinaryExpression(
                node, {"&&": "||", "||": "&&"}
            )
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsBinaryExpression(
                mutationOrNode=mutation, id=id
            )
            self.mutants.append(mutant)


class LogicalOperatorReplacement(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "LogicalOperatorReplacement"
        self.color = "#F0E68C"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ["&", "|", "^"]):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            mutation = self.generateMutationsBinaryExpression(
                node, {"&": "|", "|": "^", "^": "&"}
            )
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsBinaryExpression(
                mutationOrNode=mutation, id=id
            )
            self.mutants.append(mutant)


class AssignmentOperatorReplacementShortcut(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "AssignmentOperatorReplacementShortcut"
        self.color = "#B0C4DE"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(
                node,
                ["+=", "-=", "*=", "/=", "%=", "&=",
                    "|=", "^=", "<<=", ">>=", ">>>="],
            ):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            mutation = self.generateMutationsBinaryExpression(
                node,
                {
                    "+=": "-=",
                    "-=": "+=",
                    "*=": "/=",
                    "/=": "*=",
                    "%=": "/=",
                    "&=": "|=",
                    "|=": "^=",
                    "^=": "&=",
                    "<<=": ">>=",
                    ">>=": ">>>=",
                    ">>>=": ">>=",
                },
            )
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsBinaryExpression(
                mutationOrNode=mutation, id=id
            )
            self.mutants.append(mutant)


class ArithmeticOperatorReplacementUnary(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ArithmeticOperatorReplacementUnary"
        self.color = "#DDA0DD"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if self.filterCriteriaUnaryExpression(node, ["+", "-"]):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            mutation = self.generateMutantionsUnaryExpression(
                node, {"+": "-", "-": "+"}
            )
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsUnaryExpression(
                mutationOrNode=mutation, id=id)
            self.mutants.append(mutant)


class ConditionalOperatorDeletion(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id, sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ConditionalOperatorDeletion"
        self.color = "#FFD700"
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            if self.filterCriteriaUnaryExpression(node, ["!"]):
                self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            mutation = self.generateMutantionsUnaryExpression(node, {"!": " "})
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = self.generateMutantsUnaryExpression(
                mutationOrNode=mutation, id=id)
            self.mutants.append(mutant)


class ArithmeticOperatorReplacementShortcut(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id,  sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ArithmeticOperatorReplacementShortcut"
        self.color = "#FF00FF"
        self.terminalChild = dict()
        self.findNodes(search_children=search_children)
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if isinstance(node.children[0], TerminalNodeImpl) and isinstance(
                    node.children[1], JavaParser.ExpressionContext
                ):
                    self.terminalChild[node] = 0
                elif isinstance(node.children[1], TerminalNodeImpl) and isinstance(
                    node.children[0], JavaParser.ExpressionContext
                ):
                    self.terminalChild[node] = 1
                else:
                    continue  # not a shortcut expression
            except Exception as e:
                continue

            if node.children[self.terminalChild[node]].symbol.text not in ["++", "--"]:
                continue  # not an arithmetic operator

            self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            replacementText = "/*MUT" + str(self.mutation_id) + "*/"
            if node.children[self.terminalChild[node]].symbol.text == "++":
                replacementText += "--"
            elif node.children[self.terminalChild[node]].symbol.text == "--":
                replacementText += "++"
            mutated_node = recursiveCloneANTLRNodeAndItsChildren(node)
            mutated_node.children[self.terminalChild[node]
                                  ].symbol.text = replacementText

            mutation = Mutation(mutationID=self.mutation_id,
                                startPos=node.children[self.terminalChild[node]
                                                       ].symbol.start,
                                endPos=node.children[self.terminalChild[node]
                                                     ].symbol.stop,
                                lineNumber=node.start.line,
                                nodeID=node.nodeIndex,
                                mutatorType=self.mutatorType,
                                replacementText=replacementText,
                                color=self.color,
                                applied_mutation_style=[
                                    Mutation.STYLE_REPLACE],
                                applied_node_id=[
                                    node.children[self.terminalChild[node]].nodeIndex],
                                applied_node_new=[mutated_node.children[self.terminalChild[node]]])

            self.mutation_id += 1
            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


class ShiftOperatorReplacement(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        mutation_id: int,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
        search_children=True
    ):
        super().__init__(
            mutation_id,  sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ShiftOperatorReplacement"
        self.color = "#9ACD32"
        self.threeTerminals = dict()
        self.findNodes(search_children=search_children)
        self.filterCriteria()
        self.mutation_id = mutation_id
        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if (
                    isinstance(node.children[0], JavaParser.ExpressionContext)
                    and isinstance(node.children[1], TerminalNodeImpl)
                    and isinstance(node.children[2], TerminalNodeImpl)
                    and isinstance(node.children[3], JavaParser.ExpressionContext)
                ):
                    self.threeTerminals[node] = False

                elif (
                    isinstance(node.children[0], JavaParser.ExpressionContext)
                    and isinstance(node.children[1], TerminalNodeImpl)
                    and isinstance(node.children[2], TerminalNodeImpl)
                    and isinstance(node.children[3], TerminalNodeImpl)
                    and isinstance(node.children[4], JavaParser.ExpressionContext)
                ):
                    self.threeTerminals[node] = True
                else:
                    continue  # not a binary shift expression

            except Exception as e:
                continue

            try:
                if not self.threeTerminals[node] and (
                    (
                        node.children[1].symbol.text == "<"
                        and node.children[2].symbol.text == "<"
                    )
                    or (
                        node.children[1].symbol.text == ">"
                        and node.children[2].symbol.text == ">"
                    )
                ):
                    pass

                elif self.threeTerminals[node] and (
                    node.children[1].symbol.text == ">"
                    and node.children[2].symbol.text == ">"
                    and node.children[3].symbol.text == ">"
                ):
                    pass

                else:
                    continue  # not a shift operator

            except Exception as e:
                continue

            self.mutableNodes.append(node)

    def generateMutations(self):
        # Sort mutableNodes deterministically before generating mutations
        self._sort_mutable_nodes()
        for node in self.mutableNodes:
            replacementText = "/*MUT" + str(self.mutation_id) + "*/"
            if self.threeTerminals[node]:
                mutated_node = recursiveCloneANTLRNodeAndItsChildren(node)
                replacementText += ">>"
                mutated_node.children[1].symbol.text = ">"
                mutated_node.children[2].symbol.text = ">"
                mutated_node.children[3].symbol.text = ""

                replacementText += ">>"

                mutation = Mutation(
                    mutationID=self.mutation_id,
                    startPos=node.children[1].symbol.start,
                    endPos=node.children[3].symbol.stop,
                    lineNumber=node.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText=replacementText,
                    color=self.color,
                    applied_mutation_style=[
                        Mutation.STYLE_REPLACE, Mutation.STYLE_REPLACE, Mutation.STYLE_REPLACE],
                    applied_node_id=[node.children[1].nodeIndex,
                                     node.children[2].nodeIndex,
                                     node.children[3].nodeIndex],
                    applied_node_new=[
                        mutated_node.children[1], mutated_node.children[2], mutated_node.children[3]]
                )

            else:
                mutated_node = recursiveCloneANTLRNodeAndItsChildren(node)
                if node.children[1].symbol.text == "<":
                    replacementText += ">>"
                    mutated_node.children[1].symbol.text = ">"
                    mutated_node.children[2].symbol.text = ">"
                else:
                    replacementText += "<<"
                    mutated_node.children[1].symbol.text = "<"
                    mutated_node.children[2].symbol.text = "<"

                mutation = Mutation(
                    mutationID=self.mutation_id,
                    startPos=node.children[1].symbol.start,
                    endPos=node.children[2].symbol.stop,
                    lineNumber=node.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText=replacementText,
                    color=self.color,
                    applied_mutation_style=[
                        Mutation.STYLE_REPLACE, Mutation.STYLE_REPLACE],
                    applied_node_id=[node.children[1].nodeIndex,
                                     node.children[2].nodeIndex],
                    applied_node_new=[
                        mutated_node.children[1], mutated_node.children[2]]
                )

            self.mutations.append(mutation)
        self.mutations_searched = True

    def generateMutants(self):
        """ """
        if self.mutations_searched == False:
            self.generateMutations()
        id = 0
        for mutation in self.mutations:
            id += 1
            mutant = Mutant(
                mutantID=id, mutationList=[
                    mutation], sourceCode=self.sourceCode
            )
            mutant.mutateCode()
            self.mutants.append(mutant)


#################################################


class JavaMutate(object):
    """
    Main entry point for mutation of a Java source file.
    """

    def __init__(
        self,
        sourceTree: antlr4.RuleContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        file_name: str,
        verbose: bool = False,
        metaTypes=["Traditional"]
    ):
        self.metaTypes = metaTypes
        self.verbose = verbose
        self.sourceCode = sourceCode
        self.sourceTree = sourceTree
        self.mutantsPerLine = dict()
        self.mutantsPerMethod = dict()
        self.averageDensity = -1
        self.mutants = list()
        self.mutations = list()
        self.mutationOperators = list()
        self.file_name = file_name

        if isinstance(javaParseObject, JavaParse):
            self.javaParseObject = javaParseObject
        else:
            self.javaParseObject = JavaParse()

        # self.instantiateMutationOperators()

        self.inMethodLines = self.javaParseObject.getInMethodLines(
            self.sourceTree)

    def instantiateMutationOperators(
        self,
        mutation_id: int = 0,
        metaTypes: List[str] = ["Traditional"],
        generateMutants: bool = False,
        generateMutations: bool = True,
        mutationOperator=MutationOperator
    ):
        """

        :param generateMutants:
        :type generateMutants:
        :param metaTypes:
        :type metaTypes:
        """
        self.mutationOperators.clear()
        # Sort mutation operator classes by name for deterministic ordering
        sorted_operators = sorted(
            getAllInstantiableSubclasses(mutationOperator),
            key=lambda cls: cls.__name__
        )
        for MO in sorted_operators:
            for metaType in metaTypes:
                if metaType in MO.metaTypes:
                    mO = MO(
                        mutation_id,
                        self.sourceTree,
                        self.sourceCode,
                        self.javaParseObject,
                        generateMutants,
                        generateMutations,
                    )
                    self.mutationOperators.append(mO)
                    mutation_id = mO.mutation_id

    def countMutants(self, metaTypes: List[str] = ["Traditional"]):
        """
        Gathers all mutants, creates desired higher-order mutants, and returns the mutated code

        :param metaTypes: types of mutation operators to use
        :type metaTypes: List[str]
        :return: mutated source code for each mutant, number of types of mutants
        :rtype: Tuple[List, Dict]
        """
        mutationTypeCount = dict()
        self.instantiateMutationOperators(metaTypes, generateMutants=False)

        for mO in self.mutationOperators:
            mutationTypeCount[mO.mutatorType] = len(mO.mutableNodes)
            for mutableNode in mO.mutableNodes:
                try:
                    lineNumber = mutableNode.start.line
                except Exception as e:
                    lineNumber = -1
                self.mutantsPerLine[lineNumber] = 1 + self.mutantsPerLine.get(
                    lineNumber, 0
                )
                methodName = self.javaParseObject.getMethodNameForNode(
                    self.sourceTree, mutableNode.nodeIndex
                )
                self.mutantsPerMethod[methodName] = 1 + self.mutantsPerMethod.get(
                    methodName, 0
                )

        self.averageDensity = (
            sum(self.mutantsPerLine.values()) / len(self.inMethodLines)
            if len(self.inMethodLines) > 0
            else 0
        )

        return mutationTypeCount

    def gatherMutants(self, metaTypes: List[str] = ["Traditional"]):
        """
        Gathers all mutants, creates desired higher-order mutants, and returns the mutated code

        :param metaTypes: types of mutation operators to use
        :type metaTypes: List[str]
        :return: mutated source code for each mutant, number of types of mutants
        :rtype: Tuple[List, Dict]
        """
        mutationTypeCount = dict()
        mutantTexts = list()

        self.instantiateMutationOperators(metaTypes, generateMutants=True)

        for mO in self.mutationOperators:
            for metaType in metaTypes:
                if metaType in mO.metaTypes:
                    mutationTypeCount[mO.mutatorType] = len(mO.mutants)
                    for mutant in mO.mutants:
                        self.mutants.append(mutant)
                        mutantTexts.append(str(mutant))
                        for mutation in mutant.mutationList:
                            self.mutantsPerLine[mutation.lineNumber] = (
                                1 +
                                self.mutantsPerLine.get(mutation.lineNumber, 0)
                            )
                            methodName = self.javaParseObject.getMethodNameForNode(
                                self.sourceTree, mutation.nodeID
                            )
                            self.mutantsPerMethod[methodName] = (
                                1 + self.mutantsPerMethod.get(methodName, 0)
                            )

        self.averageDensity = (
            sum(self.mutantsPerLine.values()) / len(self.inMethodLines)
            if len(self.inMethodLines) > 0
            else 0
        )

        return mutantTexts, mutationTypeCount

    def generateMutants(self, node, mutations):
        pass

    def add_ld_variable(method_body_context):

        blockContext = JavaParser.BlockContext(method_body_context)
        bracet1 = TerminalNodeImpl(Token())
        bracet1.symbol.text = "{"
        blockContext.addChild(bracet1)

        blockStatement = JavaParser.BlockStatementContext(method_body_context)
        localVariableDeclarationStatementContext = JavaParser.LocalVariableDeclarationStatementContext(
            method_body_context)

        localVariableDeclarationContext = JavaParser.LocalVariableDeclarationContext(
            method_body_context)

        jTypeContext = JavaParser.JTypeContext(method_body_context)

        classOrInterfaceTypeContext = JavaParser.ClassOrInterfaceTypeContext(
            method_body_context)
        classOrInterfaceTypeContext.addChild(TerminalNodeImpl(Token()))
        classOrInterfaceTypeContext.children[0].symbol.text = "Object"

        jTypeContext.addChild(classOrInterfaceTypeContext)
        localVariableDeclarationContext.addChild(jTypeContext)

        variableDeclaratorsContext = JavaParser.VariableDeclaratorsContext(
            method_body_context)

        localVariableDeclarationContext.addChild(variableDeclaratorsContext)
        variableDeclaratorContext = JavaParser.VariableDeclaratorContext(
            method_body_context)

        variableDeclaratorIdContext = JavaParser.VariableDeclaratorIdContext(
            method_body_context)
        variableDeclaratorIdContext.addChild(TerminalNodeImpl(Token()))
        variableDeclaratorIdContext.children[0].symbol.text = "LD_MUT_VAR_"+str(
            method_body_context.nodeIndex)

        variableDeclaratorContext.addChild(variableDeclaratorIdContext)
        variableDeclaratorContext.addChild(TerminalNodeImpl(Token()))
        variableDeclaratorContext.children[1].symbol.text = ";"

        variableDeclaratorsContext.addChild(variableDeclaratorContext)
        localVariableDeclarationStatementContext.addChild(
            variableDeclaratorsContext)

        blockStatement.addChild(localVariableDeclarationContext)

        if method_body_context.children[1].getText().startswith("super(") or method_body_context.children[1].getText().startswith("this("):
            blockContext.addChild(method_body_context.children[1])

        blockContext.addChild(blockStatement)

        for ind in range(len(method_body_context.children)):
            if ind != 0 and ind != (len(method_body_context.children)-1):
                if ind == 1 and (method_body_context.children[ind].getText().startswith("super(") or method_body_context.children[ind].getText().startswith("this(")):
                    continue
                blockContext.addChild(
                    method_body_context.children[ind])
        bracet2 = TerminalNodeImpl(Token())
        bracet2.symbol.text = "}"
        blockContext.addChild(bracet2)

        return blockContext

    def add_getEnv(original):
        classBodyDeclarationContext = JavaParser.ClassBodyDeclarationContext(
            original)
        modifierContext = JavaParser.ModifierContext(original)
        classOrInterfaceModifierContext = JavaParser.ClassOrInterfaceModifierContext(
            original)
        static = TerminalNodeImpl(Token())
        static.symbol.text = "static"
        classOrInterfaceModifierContext.addChild(static)
        modifierContext.addChild(classOrInterfaceModifierContext)
        classBodyDeclarationContext.addChild(modifierContext)

        memberDeclarationContext = JavaParser.MemberDeclarationContext(
            original)
        fieldDeclarationContext = JavaParser.FieldDeclarationContext(original)
        jTypeContext = JavaParser.JTypeContext(original)
        classOrInterfaceTypeContext = JavaParser.ClassOrInterfaceTypeContext(
            original)
        java = TerminalNodeImpl(Token())
        java.symbol.text = "java"
        dot1 = TerminalNodeImpl(Token())
        dot1.symbol.text = "."
        util = TerminalNodeImpl(Token())
        util.symbol.text = "util"
        dot2 = TerminalNodeImpl(Token())
        dot2.symbol.text = "."
        map = TerminalNodeImpl(Token())
        map.symbol.text = "Map"

        classOrInterfaceTypeContext.addChild(java)
        classOrInterfaceTypeContext.addChild(dot1)
        classOrInterfaceTypeContext.addChild(util)
        classOrInterfaceTypeContext.addChild(dot2)
        classOrInterfaceTypeContext.addChild(map)

        typeArgumentsContext = JavaParser.TypeArgumentsContext(original)
        smaller = TerminalNodeImpl(Token())
        smaller.symbol.text = "<"
        typeArgumentAnnotationContext = JavaParser.TypeArgumentAnnotationContext(
            original)
        typeArgumentContext = JavaParser.TypeArgumentContext(original)
        jTypeContext2 = JavaParser.JTypeContext(original)
        classOrInterfaceTypeContext2 = JavaParser.ClassOrInterfaceTypeContext(
            original)
        string1 = TerminalNodeImpl(Token())
        string1.symbol.text = "String"
        classOrInterfaceTypeContext2.addChild(string1)
        jTypeContext2.addChild(classOrInterfaceTypeContext2)
        typeArgumentContext.addChild(jTypeContext2)
        typeArgumentAnnotationContext.addChild(typeArgumentContext)
        virgul1 = TerminalNodeImpl(Token())
        virgul1.symbol.text = ","

        typeArgumentAnnotationContext2 = JavaParser.TypeArgumentAnnotationContext(
            original)
        typeArgumentContext2 = JavaParser.TypeArgumentContext(original)
        jTypeContext3 = JavaParser.JTypeContext(original)
        classOrInterfaceTypeContext3 = JavaParser.ClassOrInterfaceTypeContext(
            original)
        string2 = TerminalNodeImpl(Token())
        string2.symbol.text = "String"
        classOrInterfaceTypeContext3.addChild(string1)
        jTypeContext3.addChild(classOrInterfaceTypeContext3)
        typeArgumentContext2.addChild(jTypeContext3)
        typeArgumentAnnotationContext2.addChild(typeArgumentContext2)

        larger = TerminalNodeImpl(Token())
        larger.symbol.text = ">"

        typeArgumentsContext.addChild(smaller)
        typeArgumentsContext.addChild(typeArgumentAnnotationContext)
        typeArgumentsContext.addChild(virgul1)
        typeArgumentsContext.addChild(typeArgumentAnnotationContext2)
        typeArgumentsContext.addChild(larger)
        classOrInterfaceTypeContext.addChild(typeArgumentsContext)
        jTypeContext.addChild(classOrInterfaceTypeContext)

        variableDeclaratorsContext = JavaParser.VariableDeclaratorsContext(
            original)
        variableDeclaratorContext = JavaParser.VariableDeclaratorContext(
            original)
        variableDeclaratorIdContext = JavaParser.VariableDeclaratorIdContext(
            original)
        var_maps = TerminalNodeImpl(Token())
        var_maps.symbol.text = "ENV_VAR_MAPS_"+str(original.nodeIndex)
        equal = TerminalNodeImpl(Token())
        equal.symbol.text = "="
        variableInitializerContext = JavaParser.VariableInitializerContext(
            original)
        expressionContext1 = JavaParser.ExpressionContext(original)
        expressionContext2 = JavaParser.ExpressionContext(original)
        expressionContext3 = JavaParser.ExpressionContext(original)
        primaryContext = JavaParser.PrimaryContext(original)
        system = TerminalNodeImpl(Token())
        system.symbol.text = "System"
        primaryContext.addChild(system)
        expressionContext3.addChild(primaryContext)
        dot = TerminalNodeImpl(Token())
        dot.symbol.text = "."
        getEnv = TerminalNodeImpl(Token())
        getEnv.symbol.text = "getenv"
        expressionContext2.addChild(expressionContext3)
        expressionContext2.addChild(dot)
        expressionContext2.addChild(getEnv)
        open_paranthesis = TerminalNodeImpl(Token())
        open_paranthesis.symbol.text = "("
        close_paranthesis = TerminalNodeImpl(Token())
        close_paranthesis.symbol.text = ")"
        expressionContext1.addChild(expressionContext2)
        expressionContext1.addChild(open_paranthesis)
        expressionContext1.addChild(close_paranthesis)
        variableInitializerContext.addChild(expressionContext1)

        variableDeclaratorIdContext.addChild(var_maps)
        variableDeclaratorContext.addChild(variableDeclaratorIdContext)
        variableDeclaratorContext.addChild(equal)
        variableDeclaratorContext.addChild(variableInitializerContext)
        variableDeclaratorsContext.addChild(variableDeclaratorContext)

        comma = TerminalNodeImpl(Token())
        comma.symbol.text = ";"

        fieldDeclarationContext.addChild(jTypeContext)
        fieldDeclarationContext.addChild(variableDeclaratorsContext)
        fieldDeclarationContext.addChild(comma)
        memberDeclarationContext.addChild(fieldDeclarationContext)
        classBodyDeclarationContext.addChild(memberDeclarationContext)

        new_original = JavaParser.ClassBodyContext(original)
        ind = 0
        for node in original.children:
            if (ind == 1):
                new_original.addChild(classBodyDeclarationContext)
            new_original.addChild(recursiveCloneANTLRNodeAndItsChildren(node))
            ind += 1
        new_original.parentCtx = original.parentCtx
        replaceNodes(original, new_original)

    def generateGeneric(original):

        classBodyDeclarationContext = JavaParser.ClassBodyDeclarationContext(
            original)
        modifier = JavaParser.ModifierContext(original)
        classcontext = JavaParser.ClassOrInterfaceModifierContext(original)
        terminal = TerminalNodeImpl(Token())
        terminal.symbol.text = "static"
        classcontext.addChild(terminal)
        modifier.addChild(classcontext)
        classBodyDeclarationContext.addChild(modifier)

        copied = recursiveCloneANTLRNodeAndItsChildren(original.children[-1])
        del original.children[-1]
        original.addChild(classBodyDeclarationContext)
        original.addChild(copied)

        memberDeclaration = JavaParser.MemberDeclarationContext(original)
        classBodyDeclarationContext.addChild(memberDeclaration)

        classDeclaration = JavaParser.ClassDeclarationContext(original)
        memberDeclaration.addChild(classDeclaration)
        classDeclaration.addChild(TerminalNodeImpl(Token()))
        classDeclaration.children[0].symbol.text = "class"
        classDeclaration.addChild(TerminalNodeImpl(Token()))
        classDeclaration.children[1].symbol.text = "Generic"
        typeParam = JavaParser.TypeParametersContext(original)
        typeParam.addChild(TerminalNodeImpl(Token()))
        typeParam.children[0].symbol.text = "<"
        typeParamContext = JavaParser.TypeParameterContext(original)
        typeParamContext.addChild(TerminalNodeImpl(Token()))
        typeParamContext.children[0].symbol.text = "T"
        typeParam.addChild(typeParamContext)
        typeParam.addChild(TerminalNodeImpl(Token()))
        typeParam.children[2].symbol.text = ">"
        classDeclaration.addChild(typeParam)

        classBodyCntx = JavaParser.ClassBodyContext(original)
        memberDeclaration.addChild(classBodyCntx)
        classBodyCntx.addChild(TerminalNodeImpl(Token()))
        classBodyCntx.children[0].symbol.text = "{"
        classBodyDecCntx = JavaParser.ClassBodyDeclarationContext(original)
        classBodyCntx.addChild(classBodyDecCntx)
        memberDeclarationCntx = JavaParser.MemberDeclarationContext(original)
        classBodyDecCntx.addChild(memberDeclarationCntx)
        fieldDecContext = JavaParser.FieldDeclarationContext(original)
        memberDeclarationCntx.addChild(fieldDecContext)
        jType = JavaParser.JTypeContext(original)
        fieldDecContext.addChild(jType)
        classOrInterface = JavaParser.ClassOrInterfaceTypeContext(original)
        classOrInterface.addChild(TerminalNodeImpl(Token()))
        classOrInterface.children[0].symbol.text = "T"
        jType.addChild(classOrInterface)
        variableDeclaratorsContext = JavaParser.VariableDeclaratorsContext(
            original)
        fieldDecContext.addChild(variableDeclaratorsContext)
        variableDeclaratorContext = JavaParser.VariableDeclaratorContext(
            original)
        variableDeclaratorsContext.addChild(variableDeclaratorContext)
        variableDeclaratorIdContext = JavaParser.VariableDeclaratorIdContext(
            original)
        variableDeclaratorIdContext.addChild(TerminalNodeImpl(Token()))
        variableDeclaratorIdContext.children[0].symbol.text = "t"
        variableDeclaratorContext.addChild(variableDeclaratorIdContext)
        fieldDecContext.addChild(TerminalNodeImpl(Token()))
        fieldDecContext.children[2].symbol.text = ";"
        classBodyCntx.addChild(TerminalNodeImpl(Token()))
        classBodyCntx.children[2].symbol.text = "}"
        classBody = JavaParser.ClassBodyDeclarationContext(original)
        classBodyDeclarationContext.addChild(classBody)
        modifierPublic = JavaParser.ModifierContext(original)
        classcontextPublic = JavaParser.ClassOrInterfaceModifierContext(
            original)
        terminalPublic = TerminalNodeImpl(Token())
        terminalPublic.symbol.text = "public"
        classcontextPublic.addChild(terminalPublic)
        modifierPublic.addChild(classcontextPublic)

        classBody.addChild(modifierPublic)

        modifierStatic = JavaParser.ModifierContext(original)
        classcontextStatic = JavaParser.ClassOrInterfaceModifierContext(
            original)
        terminalStatic = TerminalNodeImpl(Token())
        terminalStatic.symbol.text = "static"
        classcontextStatic.addChild(terminalStatic)
        modifierStatic.addChild(classcontextStatic)

        classBody.addChild(modifierStatic)

        memberDeclarationVar = JavaParser.MemberDeclarationContext(original)
        classBody.addChild(memberDeclarationVar)
        fieldDeclarationContext = JavaParser.FieldDeclarationContext(original)
        memberDeclarationVar.addChild(fieldDeclarationContext)
        jTypeVar = JavaParser.JTypeContext(original)
        fieldDeclarationContext.addChild(jTypeVar)
        classOrInterfaceVar = JavaParser.ClassOrInterfaceTypeContext(original)
        classOrInterfaceVar.addChild(TerminalNodeImpl(Token()))
        classOrInterfaceVar.children[0].symbol.text = "Generic"
        jTypeVar.addChild(classOrInterfaceVar)

        variableDeclaratorsContextVar = JavaParser.VariableDeclaratorsContext(
            original)
        fieldDeclarationContext.addChild(variableDeclaratorsContextVar)
        variableDeclaratorContextVar = JavaParser.VariableDeclaratorContext(
            original)
        variableDeclaratorsContextVar.addChild(variableDeclaratorContextVar)
        variableDeclaratorIdContextVar = JavaParser.VariableDeclaratorIdContext(
            original
        )
        variableDeclaratorIdContextVar.addChild(TerminalNodeImpl(Token()))
        variableDeclaratorIdContextVar.children[0].symbol.text = "generic"
        variableDeclaratorContextVar.addChild(variableDeclaratorIdContextVar)
        variableDeclaratorContextVar.addChild(TerminalNodeImpl(Token()))
        variableDeclaratorContextVar.children[1].symbol.text = "="
        variableInitializerContextVar = JavaParser.VariableInitializerContext(
            original)
        variableDeclaratorContextVar.addChild(variableInitializerContextVar)
        expressionContext = JavaParser.ExpressionContext(original)
        variableInitializerContextVar.addChild(expressionContext)

        expressionContext.addChild(TerminalNodeImpl(Token()))
        expressionContext.children[0].symbol.text = "new"
        expressionContext.mutationType = "0"

        creatorContext = JavaParser.CreatorContext(original)
        expressionContext.addChild(creatorContext)
        createdNameContext = JavaParser.CreatedNameContext(original)
        createdNameContext.addChild(TerminalNodeImpl(Token()))
        createdNameContext.children[0].symbol.text = "Generic"
        creatorContext.addChild(createdNameContext)
        classCreatorRestContext = JavaParser.ClassCreatorRestContext(original)
        creatorContext.addChild(classCreatorRestContext)
        argumentsContext = JavaParser.ArgumentsContext(original)
        argumentsContext.addChild(TerminalNodeImpl(Token()))
        argumentsContext.children[0].symbol.text = "("
        argumentsContext.addChild(TerminalNodeImpl(Token()))
        argumentsContext.children[1].symbol.text = ")"
        classCreatorRestContext.addChild(argumentsContext)

        fieldDeclarationContext.addChild(TerminalNodeImpl(Token()))
        fieldDeclarationContext.children[-1].symbol.text = ";"

        return original

    def returnConditional(mutationID, node, original_nodeIndex, contextID):
        blockStatementContext = JavaParser.BlockStatementContext(node)
        statementContext = JavaParser.StatementContext(node)
        blockStatementContext.addChild(statementContext)
        terminalNodeImpl = TerminalNodeImpl(Token())
        terminalNodeImpl.symbol.text = "if"
        statementContext.addChild(terminalNodeImpl)
        parExpressionContext = JavaParser.ParExpressionContext(node)
        parExpressionContext.addChild(TerminalNodeImpl(Token()))
        parExpressionContext.children[0].symbol.text = "("+"/*MUT" + str(
            mutationID) + "*/"
        parExpressionContext.addChild(
            JavaMutate.returnCondition(mutationID=mutationID, node=node, original_nodeIndex=original_nodeIndex, contextID=contextID))
        parExpressionContext.addChild(TerminalNodeImpl(Token()))
        parExpressionContext.children[2].symbol.text = ")"
        statementContext.addChild(parExpressionContext)
        statementContext2 = JavaParser.StatementContext(node)
        statementContext2.addChild(node)
        statementContext.addChild(statementContext2)
        return blockStatementContext

    def addConditionals(mutations, original):
        blockContext = JavaParser.BlockContext(original)
        bracet1 = TerminalNodeImpl(Token())
        bracet1.symbol.text = "{"
        blockContext.addChild(bracet1)
        for mutation in mutations:
            tmp = JavaMutate.returnConditional(
                mutationID=mutation.mutationID, node=mutation.mutated_node, original_nodeIndex=JavaMutate.return_class_id(mutation.original_node), contextID=mutation.original_node.contextID)
            blockContext.addChild(tmp)
        for ind in range(len(original.children)):
            if ind != 0 and ind != (len(original.children)-1):
                blockContext.addChild(
                    original.children[ind])
        bracet2 = TerminalNodeImpl(Token())
        bracet2.symbol.text = "}"
        blockContext.addChild(bracet2)

        return blockContext

    def return_class_id(tree):
        """
        returns ClassBodyContext nodes of the AST tree
        """
        calss_id = -1
        parents = [tree]
        for parent in parents:
            if isinstance(parent, JavaParser.ClassBodyContext) or isinstance(parent, JavaParser.InterfaceBodyContext):
                calss_id = parent.nodeIndex
            try:
                parents.append(parent.parentCtx)
            except AttributeError:
                pass
        return calss_id

    def returnCondition(mutationID, node, original_nodeIndex,  contextID=JavaParse.ENUM_CONTEXT_ID):
        if contextID == JavaParse.CLASS_BODY_CONTEXT_ID:
            inner_expression = JavaParser.ExpressionContext(node)

            ExpressionContext_env_var_2 = JavaParser.ExpressionContext(
                node)
            expressionContext_env_var = JavaParser.ExpressionContext(node)
            primaryContext_env_var = JavaParser.PrimaryContext(node)
            ENV_VAR_MAPS_terminal = TerminalNodeImpl(Token())
            ENV_VAR_MAPS_terminal.symbol.text = "ENV_VAR_MAPS_" + \
                str(original_nodeIndex)
            primaryContext_env_var.addChild(ENV_VAR_MAPS_terminal)
            expressionContext_env_var.addChild(primaryContext_env_var)

            dot_terminal = TerminalNodeImpl(Token())
            dot_terminal.symbol.text = "."
            get_or_default_terminal = TerminalNodeImpl(Token())
            # get_or_default_terminal.symbol.text = "getOrDefault"
            get_or_default_terminal.symbol.text = "containsKey"
            ExpressionContext_env_var_2.addChild(expressionContext_env_var)
            ExpressionContext_env_var_2.addChild(dot_terminal)
            ExpressionContext_env_var_2.addChild(get_or_default_terminal)

            # }
            par_open = TerminalNodeImpl(Token())
            par_open.symbol.text = "("
            expressionListContext_env_var = JavaParser.ExpressionListContext(
                node)
            expressionContext_mut_id = JavaParser.ExpressionContext(node)
            primaryContext_mut_id = JavaParser.PrimaryContext(node)
            literalContext_mut_id = JavaParser.LiteralContext(node)
            terminal_mut_id = TerminalNodeImpl(Token())
            terminal_mut_id.symbol.text = ('"MUT' + str(mutationID) + '"')
            literalContext_mut_id.addChild(terminal_mut_id)
            primaryContext_mut_id.addChild(literalContext_mut_id)
            expressionContext_mut_id.addChild(primaryContext_mut_id)

            expressionListContext_env_var.addChild(expressionContext_mut_id)
            par_close = TerminalNodeImpl(Token())
            par_close.symbol.text = ")"

            inner_expression.addChild(ExpressionContext_env_var_2)
            inner_expression.addChild(par_open)
            inner_expression.addChild(expressionListContext_env_var)
            inner_expression.addChild(par_close)

            return inner_expression
        else:
            expression_context = JavaParser.ExpressionContext(node)

            expression_context.addChild(JavaParser.ExpressionContext(node))
            expression_context.children[0].addChild(
                JavaParser.ExpressionContext(node)
            )
            expression_context.children[0].children[0].addChild(
                JavaParser.ExpressionContext(node)
            )
            expression_context.children[0].children[0].children[0].addChild(
                JavaParser.PrimaryContext(node)
            )
            expression_context.children[0].children[0].children[0].children[0].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[0].children[0].children[0].children[
                0
            ].symbol.text = "java.lang.Boolean"
            expression_context.children[0].children[0].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[0].children[1].symbol.text = "."
            expression_context.children[0].children[0].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[0].children[
                2
            ].symbol.text = "valueOf"
            expression_context.children[0].addChild(TerminalNodeImpl(Token()))
            expression_context.children[0].children[1].symbol.text = "("
            expression_context.children[0].addChild(
                JavaParser.ExpressionListContext(node)
            )
            expression_context.children[0].children[2].addChild(
                JavaParser.ExpressionContext(node)
            )
            expression_context.children[0].children[2].children[0].addChild(
                JavaParser.ExpressionContext(node)
            )
            expression_context.children[0].children[2].children[0].children[0].addChild(
                JavaParser.ExpressionContext(node)
            )
            expression_context.children[0].children[2].children[0].children[0].children[
                0
            ].addChild(JavaParser.PrimaryContext(node))
            expression_context.children[0].children[2].children[0].children[0].children[
                0
            ].children[0].addChild(TerminalNodeImpl(Token()))
            expression_context.children[0].children[2].children[0].children[0].children[
                0
            ].children[0].children[0].symbol.text = "System"
            expression_context.children[0].children[2].children[0].children[0].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[2].children[0].children[0].children[
                1
            ].symbol.text = "."
            expression_context.children[0].children[2].children[0].children[0].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[2].children[0].children[0].children[
                2
            ].symbol.text = "getenv"
            expression_context.children[0].children[2].children[0].children[0]
            expression_context.children[0].children[2].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[2].children[1].symbol.text = "("
            expression_context.children[0].children[2].addChild(
                JavaParser.ExpressionListContext(node)
            )
            expression_context.children[0].children[2].children[2].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[2].children[2].children[
                0
            ].symbol.text = ('"MUT' + str(mutationID) + '"')
            expression_context.children[0].children[2].addChild(
                TerminalNodeImpl(Token())
            )
            expression_context.children[0].children[2].children[3].symbol.text = ")"
            expression_context.children[0].addChild(TerminalNodeImpl(Token()))
            expression_context.children[0].children[3].symbol.text = ")"
            return expression_context

    def returnTernary(self, mutants, mutation_type, body_ind=0):

        original = mutants["-1"]
        blockStatement = JavaParser.BlockStatementContext(
            original)  # BlockStatementContext

        statement = JavaParser.StatementContext(original)
        blockStatement.addChild(statement)
        statementExpression = JavaParser.StatementExpressionContext(original)
        statement.addChild(statementExpression)
        expression_0 = JavaParser.ExpressionContext(original)
        statementExpression.addChild(expression_0)

        expression_1 = JavaParser.ExpressionContext(original)
        expression_1.addChild(JavaParser.ExpressionContext(original))
        expression_1.children[0].addChild(JavaParser.PrimaryContext(original))
        expression_1.children[0].children[0].addChild(
            TerminalNodeImpl(Token()))
        expression_1.children[0].children[0].children[0].symbol.text = "LD_MUT_VAR_"+str(
            body_ind)

        expression_0.addChild(expression_1)
        expression_0.addChild(TerminalNodeImpl(Token()))
        expression_0.children[1].symbol.text = "="

        # done some test on mutant schemata
        primary_node = None

        del mutants["-1"]
        conditions = list()
        for mutated_version in mutants.keys():
            mutationIDs = mutated_version.split(",")
            condition_node = JavaParser.PrimaryContext(original)
            condition_node.addChild(TerminalNodeImpl(Token()))
            condition_node.children[0].symbol.text = "("
            myList = list()
            for i in range(len(mutationIDs)):
                node = JavaMutate.returnCondition(
                    mutationID=mutationIDs[i], node=original, original_nodeIndex=JavaMutate.return_class_id(original),  contextID=original.contextID if (hasattr(original, "contextID")) else JavaParse.ENUM_CONTEXT_ID)
                myList.append(node)
            while len(myList) > 1:
                firstNode = myList.pop()
                secondNode = myList.pop()
                andNode = TerminalNodeImpl(Token())
                andNode.symbol.text = "&&"
                expression_context = JavaParser.ExpressionContext(original)
                expression_context.addChild(firstNode)
                expression_context.addChild(andNode)
                expression_context.addChild(secondNode)
                myList.insert(0, expression_context)

            condition_node.addChild(myList[0])
            condition_node.addChild(TerminalNodeImpl(Token()))
            condition_node.children[2].symbol.text = ")"

            new_node = mutants[mutated_version]

            new_tree = node.__class__(node)
            new_tree.copyFrom(node)

            # add (Boolean.valueOf(System.getProperty("MUT0")) ? 0 : 1); to the tree
            primary_node = JavaParser.PrimaryContext(new_tree)
            primary_node.addChild(TerminalNodeImpl(Token()))
            primary_node.children[0].symbol.text = "("
            primary_node.addChild(condition_node)

            primary_node.addChild(TerminalNodeImpl(Token()))
            primary_node.children[2].symbol.text = ")"

            # ***

            primary_node.children[1].addChild(TerminalNodeImpl(Token()))
            primary_node.children[1].children[3].symbol.text = "?"

            primary_node.children[1].addChild(TerminalNodeImpl(Token()))
            primary_node.children[1].children[4].symbol.text = "("

            primary_node.children[1].addChild(new_node)

            primary_node.children[1].addChild(TerminalNodeImpl(Token()))
            primary_node.children[1].children[6].symbol.text = ")"

            primary_node.children[1].addChild(TerminalNodeImpl(Token()))
            primary_node.children[1].children[7].symbol.text = ":"

            primary_node.children[1].addChild(TerminalNodeImpl(Token()))
            primary_node.children[1].children[8].symbol.text = "("

            primary_node.children[1].addChild(original)

            primary_node.children[1].addChild(TerminalNodeImpl(Token()))
            primary_node.children[1].children[10].symbol.text = ")"
            conditions.append(primary_node)
        if len(conditions) == 0:
            conditions.append(original)
        else:
            while len(conditions) > 1:
                firstNode = conditions.pop()
                secondNode = conditions.pop()
                secondNode.children[1].children[9] = firstNode
                conditions.append(secondNode)
            if mutation_type == 2 or mutation_type == 5:
                expression_0.addChild(conditions[0])
                conditions[0] = expression_0
        return conditions[0]

    def gatherMutations(
        self,
        metaTypes: List[str] = ["Traditional"],
        database: Database = None,
        last_mutation_id: int = 0,
        mutationOperator=MutationOperator,
    ):
        """
        Gathers all mutations

        :param metaTypes: types of mutation operators to use
        :type metaTypes: List[str]
        :param database: Database object to store mutations
        :type Database: Database
        :return: number of types of mutants
        :rtype: Dict
        """
        mutationTypeCount = dict()
        if database is not None:
            file_id = database.fetch_data(
                "file", columns="id", condition=f"name = '{self.file_name}'"
            )[0][0]
        self.instantiateMutationOperators(
            last_mutation_id, metaTypes, mutationOperator=mutationOperator)

        for mO in self.mutationOperators:
            for metaType in metaTypes:
                if metaType in mO.metaTypes:
                    mutationTypeCount[mO.mutatorType] = len(mO.mutations)
                    for mutation in mO.mutations:
                        self.mutations.append(mutation)
                        self.mutantsPerLine[mutation.lineNumber] = (
                            1 + self.mutantsPerLine.get(mutation.lineNumber, 0)
                        )
                        methodName = self.javaParseObject.getMethodNameForNode(
                            self.sourceTree, mutation.nodeID
                        )
                        self.mutantsPerMethod[methodName] = (
                            1 + self.mutantsPerMethod.get(methodName, 0)
                        )
                        last_mutation_id = mutation.mutationID
                        if database is not None:
                            operator_id = database.fetch_data(
                                "mutation_operator",
                                "id",
                                f"name = '{mutation.mutatorType}'",
                            )
                            operator_id = operator_id[0][0]
                            database.insert_mutation(
                                mutation.mutationID,
                                file_id,
                                mutation.nodeID,
                                mutation.startPos,
                                mutation.endPos,
                                mutation.lineNumber,
                                mutation.replacementText,
                                mutation_operator_id=operator_id,
                            )
                            # mutation.mutationID = last_mutation_id

        self.averageDensity = (
            sum(self.mutantsPerLine.values()) / len(self.inMethodLines)
            if len(self.inMethodLines) > 0
            else 0
        )

        return mutationTypeCount

    def gatherMutableNodes(
        self,
        javaParseObject,
        metaTypes: List[str] = ["Traditional"],
        mutationOperator=MutationOperator,
        debug=False
    ):
        """
        Gathers all mutations

        :param metaTypes: types of mutation operators to use
        :type metaTypes: List[str]
        :param database: Database object to store mutations
        :type Database: Database
        :return: number of types of mutants
        :rtype: Dict
        """

        self.instantiateMutationOperators(
            metaTypes=metaTypes, mutationOperator=mutationOperator, generateMutations=False
        )

        node_dict = dict()
        depth_node_dict = dict()
        submutation_dict = dict()
        mutable_at_high_level = list()
        for mO in self.mutationOperators:
            for metaType in metaTypes:
                if metaType in mO.metaTypes:
                    for node in mO.mutableNodes:
                        if (isinstance(mO, ConditionalOperatorReplacement) or isinstance(mO, LogicalOperatorReplacement)):
                            # these operators change the predecence of operators
                            is_included = False
                            for high_level_node in mutable_at_high_level:
                                if (javaParseObject.is_ancestor(high_level_node, node)):
                                    submutation_dict[high_level_node.nodeIndex].append(
                                        node.nodeIndex)
                                    is_included = True
                                    continue
                            if is_included:
                                continue
                            mutable_at_high_level.append(node)
                        if (not node.nodeIndex in node_dict.keys()):
                            node_dict[node.nodeIndex] = list()
                            submutation_dict[node.nodeIndex] = list()
                        node_dict[node.nodeIndex].append(type(mO)(
                            generateMutations=False, mutation_id=0, sourceTree=node, sourceCode=javaParseObject.getText(node), javaParseObject=javaParseObject, search_children=(isinstance(mO, ConditionalOperatorReplacement) or isinstance(mO, LogicalOperatorReplacement))))
                        if (not node.node_depth in depth_node_dict.keys()):
                            depth_node_dict[node.node_depth] = set()
                        depth_node_dict[node.node_depth].add(node.nodeIndex)
        # use submutation_dict to store how many mutations a node's subtree has (example: submutation[node.nodeIndex]=3)
        for node_ind_i in node_dict.keys():
            if (submutation_dict[node_ind_i] == -1):
                continue
            if (type(node_dict[node_ind_i][0]) == NullifyInputVariable or type(node_dict[node_ind_i][0]) == RemoveMethod):
                submutation_dict[node_ind_i].append(node_ind_i)
                continue
            is_precedent_i = False
            if (type(node_dict[node_ind_i][0]) == ConditionalOperatorReplacement or type(node_dict[node_ind_i][0]) == LogicalOperatorReplacement):
                is_precedent_i = True
            for node_ind_j in node_dict.keys():
                is_precedent_j = False
                if (type(node_dict[node_ind_j][0]) == ConditionalOperatorReplacement or type(node_dict[node_ind_j][0]) == LogicalOperatorReplacement):
                    is_precedent_j = True
                if (not is_precedent_i and is_precedent_j):
                    continue
                if (not node_ind_i in submutation_dict.keys()):
                    submutation_dict[node_ind_i] = list()
                if javaParseObject.is_ancestor(
                        javaParseObject.getNode(self.sourceTree, node_ind_i), javaParseObject.getNode(self.sourceTree, node_ind_j)):
                    submutation_dict[node_ind_i].append(node_ind_j)
                    if (node_ind_j != node_ind_i):
                        submutation_dict[node_ind_j] = -1
        overloaded_mutations = list()
        for nodes in submutation_dict.keys():
            if (type(node_dict[nodes][0]) == ConditionalOperatorReplacement or type(node_dict[nodes][0]) == LogicalOperatorReplacement):
                i = 1
                for nodes_2 in [] if submutation_dict[nodes] == -1 else submutation_dict[nodes]:
                    try:
                        if (nodes_2 != nodes and (type(node_dict[nodes_2][0]) == ConditionalOperatorReplacement or type(node_dict[nodes_2][0]) == LogicalOperatorReplacement)):
                            i += 1
                    except Exception as e:
                        i += 1
                submutation_dict[nodes] = submutation_dict[nodes]*i
            if (submutation_dict[nodes] != -1 and len(submutation_dict[nodes]) > 10):
                if (debug):
                    print("Node: ", nodes, " ", javaParseObject.getNode(self.sourceTree, nodes).getText(), " has ", len(
                        submutation_dict[nodes]), " submutations")
                    print("Submutations: ", submutation_dict[nodes])
                overloaded_mutations.extend(submutation_dict[nodes])
        return (node_dict, depth_node_dict, set(overloaded_mutations))

    def gatherAllMutantsUpToTheOrderOf(
        self,
        cur_order: int = 1,
        order: int = 1,
        mutations: List[Mutation] = [],
        generated_mutants: List[Mutant] = [],
        id_counter=0,
    ):
        new_generated_mutants = list()
        if cur_order == 1:
            for mutation in mutations:
                new_generated_mutants.append(
                    Mutant(
                        mutantID=id_counter,
                        mutationList=[mutation],
                        sourceCode=self.sourceCode,
                    )
                )
                id_counter += 1
        else:
            for mutant in generated_mutants:
                for mutation in mutations:
                    already_mutated = False
                    for mutation_in_mutant in mutant.mutationList:
                        if (
                            mutation.nodeID == mutation_in_mutant.nodeID
                            and mutation.startPos == mutation_in_mutant.startPos
                        ):
                            already_mutated = True
                            break
                    if already_mutated == False:
                        new_generated_mutants.append(
                            Mutant(
                                mutantID=id_counter,
                                mutationList=mutant.mutationList + [mutation],
                                sourceCode=self.sourceCode,
                            )
                        )
                        id_counter += 1
        if cur_order != order:
            next_generation_mutants = self.gatherAllMutantsUpToTheOrderOf(
                cur_order=cur_order + 1,
                order=order,
                mutations=mutations,
                generated_mutants=new_generated_mutants,
                id_counter=id_counter,
            )
            next_generation_mutants.extend(new_generated_mutants)
            return next_generation_mutants
        return new_generated_mutants

    def all_mutations_pairs(
        self,
        order: int = 1,
        mutations: List[Mutation] = [],
    ):

        new_generated_mutants = list()
        for length in range(order, 0, -1):
            new_generated_mutants.append(list(combinations(mutations, length)))
        return new_generated_mutants

    @property
    def cssStyle(self):
        """
        Returns CSS Style for the aggregate report

        :return: CSS Style
        :rtype: str
        """
        self.instantiateMutationOperators(
            metaTypes=self.metaTypes, generateMutations=False)
        style = """ body { font-family: "Carlito", "Calibri", "Helvetica Neue", sans-serif;}
                    .code { font-family: monospace; font-size: medium; }
                    .methodLine { background: white; }
                    .outsideLine { background: lightgray; }
                    .tooltip { position: relative; display: inline-block; }
                    .tooltip .tooltiptext { visibility: hidden; display: block;
                        background-color: #006400; color: #ffffff; text-align: left;
                        border-radius: 0.3em; padding: 0.5em 0.5em; position: absolute; top: 125%; z-index: 200;}
                    .tooltip:hover .tooltiptext { visibility: visible; } """

        for mo in self.mutationOperators:
            assert isinstance(mo, MutationOperator)
            style += mo.cssClass

        return style

    def aggregateReport(self, littleDarwinVersion: str):
        """

        :param littleDarwinVersion: MediumDarwin Version
        :type littleDarwinVersion: str
        :return: Aggregate report on all mutations for a file
        :rtype: str
        """
        lineNumber = 1
        col = 0
        maxLineLength = 0
        for l in self.sourceCode.expandtabs().splitlines(keepends=False):
            if len(l) > maxLineLength:
                maxLineLength = len(l)

        output = "<!DOCTYPE html><head><title>MediumDarwin Aggregate Mutation Report</title> <style type='text/css'>"
        output += (
            self.cssStyle
            + "</style></head><body><h1>MediumDarwin Aggregate Mutation Report</h1>"
        )
        output += (
            "<p>Average Density: {:.2f}".format(self.averageDensity)
            + '</p><div><pre class="code">'
        )
        output += '<span class="{}"><i>{:04d}</i> '.format(
            "methodLine" if lineNumber in self.inMethodLines else "outsideLine",
            lineNumber,
        )

        mutationStartDict = dict()
        mutationEndList = list()
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            for mutation in mutant.mutationList:
                mutationStartDict[mutation.startPos] = (
                    mutation.mutatorType,
                    "mutant ID: " + str(mutant.mutantID) +
                    "\n" + str(mutation),
                )
                mutationEndList.append(mutation.endPos)

        for i in range(0, len(self.sourceCode)):
            colRemainder = 0
            if self.sourceCode[i] == "\t":
                colRemainder = 8 - (col % 8)
                col += colRemainder
            else:
                col += 1

            if i in mutationStartDict.keys():
                mutatorType, tooltipText = mutationStartDict[i]
                output += '<span class="{} tooltip">'.format(mutatorType)
                output += '<span class="tooltiptext">{}</span>'.format(
                    tooltipText)

            if self.sourceCode[i] == "\n":
                output += " " * (maxLineLength - col + 1)

            output += (
                self.sourceCode[i] if self.sourceCode[i] != "\t" else " " * colRemainder
            )

            if i in mutationEndList:
                output += "</span>"

            if self.sourceCode[i] == "\n":
                lineNumber += 1
                col = 0
                output += '</span><span class="{}"><i>{:04d}</i> '.format(
                    "methodLine" if lineNumber in self.inMethodLines else "outsideLine",
                    lineNumber,
                )

        output += " " * (maxLineLength - col)
        output += '</pre></div><footer><p style="font-size: small">'
        output += (
            "Report generated by MediumDarwin {} </p></footer></body></html>".format(
                littleDarwinVersion
            )
        )

        return output

    def aggregateReport_schemata(
        self, littleDarwinVersion: str, my_mutations: list, my_mutantsPerLine
    ):
        """

        :param littleDarwinVersion: MediumDarwin Version
        :type littleDarwinVersion: str
        :return: Aggregate report on all mutations for a file
        :rtype: str
        """

        self.averageDensity = (
            sum(my_mutantsPerLine.values()) / len(self.inMethodLines)
            if len(self.inMethodLines) > 0
            else 0
        )
        lineNumber = 1
        col = 0
        maxLineLength = 0
        for l in self.sourceCode.expandtabs().splitlines(keepends=False):
            if len(l) > maxLineLength:
                maxLineLength = len(l)

        output = "<!DOCTYPE html><head><title>MediumDarwin Aggregate Mutation Report</title> <style type='text/css'>"
        output += (
            self.cssStyle
            + "</style></head><body><h1>MediumDarwin Aggregate Mutation Report</h1>"
        )
        output += (
            "<p>Average Density: {:.2f}".format(self.averageDensity)
            + '</p><div><pre class="code">'
        )
        output += '<span class="{}"><i>{:04d}</i> '.format(
            "methodLine" if lineNumber in self.inMethodLines else "outsideLine",
            lineNumber,
        )

        mutationStartDict = dict()
        mutationEndList = list()
        for mutation in my_mutations:
            mutationStartDict[mutation.startPos] = (
                mutation.mutatorType,
                "mutation: " + str(mutation.mutationID) + "\n" + str(mutation),
            )
            mutationEndList.append(mutation.endPos)

        for i in range(0, len(self.sourceCode)):
            colRemainder = 0
            if self.sourceCode[i] == "\t":
                colRemainder = 8 - (col % 8)
                col += colRemainder
            else:
                col += 1

            if i in mutationStartDict.keys():
                mutatorType, tooltipText = mutationStartDict[i]
                output += '<span class="{} tooltip">'.format(mutatorType)
                output += '<span class="tooltiptext">{}</span>'.format(
                    tooltipText)

            if self.sourceCode[i] == "\n":
                output += " " * (maxLineLength - col + 1)

            output += (
                self.sourceCode[i] if self.sourceCode[i] != "\t" else " " * colRemainder
            )

            if i in mutationEndList:
                output += "</span>"

            if self.sourceCode[i] == "\n":
                lineNumber += 1
                col = 0
                output += '</span><span class="{}"><i>{:04d}</i> '.format(
                    "methodLine" if lineNumber in self.inMethodLines else "outsideLine",
                    lineNumber,
                )

        output += " " * (maxLineLength - col)
        output += '</pre></div><footer><p style="font-size: small">'
        output += (
            "Report generated by MediumDarwin {} </p></footer></body></html>".format(
                littleDarwinVersion
            )
        )

        return output
