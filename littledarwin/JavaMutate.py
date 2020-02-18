import copy
import sys
from math import log10
from random import shuffle
from typing import List, Tuple, Dict

from custom_antlr4 import Token
from custom_antlr4.tree import Tree
from custom_antlr4.tree.Tree import TerminalNodeImpl
from littledarwin.JavaParse import JavaParse
from littledarwin.JavaParser import JavaParser

sys.setrecursionlimit(100000)


class Mutation(object):
    """

    """
    def __init__(self, startPos: int, endPos: int, lineNumber: int, nodeID: int, mutatorType: str, replacementText: str):
        assert endPos >= startPos

        self.startPos = startPos
        self.endPos = endPos
        self.lineNumber = lineNumber
        self.nodeID = nodeID
        self.mutatorType = mutatorType
        self.replacementText = replacementText

    def applyMutation(self, sourceCode: str, byteOffset: int = 0) -> str:
        """

        :param byteOffset:
        :type byteOffset:
        :param sourceCode:
        :type sourceCode:
        :return:
        :rtype:
        """
        return sourceCode[:self.startPos + byteOffset] + self.replacementText + sourceCode[self.endPos + byteOffset + 1:]

    @property
    def byteOffset(self) -> int:
        """
        Returns the byte offset introduced by the mutation

        :return:  byte offset introduced by the mutation
        :rtype: int
        """
        return len(self.replacementText) - (self.endPos - self.startPos + 1)


class Mutant(object):
    """

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

        """
        code = self.sourceCode
        byteOffsetDict = dict()

        for mutation in self.mutationList:
            byteOffsetDict[mutation.startPos] = mutation.byteOffset
            for pos in sorted(byteOffsetDict.keys()):
                if pos < mutation.startPos:
                    byteOffsetDict[mutation.startPos] = byteOffsetDict[pos] + mutation.byteOffset
                elif pos > mutation.startPos:
                    byteOffsetDict[pos] += mutation.byteOffset

            code = mutation.applyMutation(code, byteOffsetDict[mutation.startPos] - mutation.byteOffset)

        self.mutatedCode = code

    @property
    def stub(self):
        """

        :return:
        :rtype:
        """
        assert len(self.mutationList) > 0
        assert self.mutatedCode is not None

        textStub = "/* LittleDarwin generated order-{0} mutant\n".format(str(len(self.mutationList)))  # type: str

        for mutation in self.mutationList:
            textStub += "mutant type: " + mutation.mutatorType + \
                        "\n----> before: " + self.getLine(mutation.lineNumber) + \
                        "\n----> after: " + self.getLine(mutation.lineNumber,
                                                         code=mutation.applyMutation(self.sourceCode)) + \
                        "\n----> line number in original file: " + str(mutation.lineNumber) + \
                        "\n----> mutated node: " + str(mutation.nodeID) + "\n\n"

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
                newMutant = Mutant(-1*self.mutantID*other.mutantID, newMutationList, self.sourceCode)
                newMutant.mutateCode()
                return newMutant
            else:
                raise ValueError("Only Mutant objects of the same source code can be added.")
        else:
            raise ValueError("Only Mutant objects can be added.")

    def __radd__(self, other):
        return self.__add__(other)

    def __str__(self):
        if self.mutatedCode is None:
            self.mutateCode()
        return self.stub + self.mutatedCode


class MutationOperator(object):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        self.sourceTree = sourceTree
        self.sourceCode = sourceCode
        self.metaType = "Generic"
        self.mutatorType = "GenericMutationOperator"
        self.allNodes = list()  # populated by findNodes
        self.mutableNodes = list()  # populated by filterCriteria
        self.mutants = list()  # populated by generateMutants
        self.javaParseObject = javaParseObject

    def findNodes(self):
        """
        Finds all nodes that match the search criteria
        """
        pass

    def filterCriteria(self):
        """
        Filters out the nodes that do not match the input critera
        """
        pass

    def generateMutants(self):
        """
        Generates the mutants
        """
        pass

#################################################
#          Null Mutation Operators              #
#################################################


class RemoveNullCheck(MutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveNullCheck"
        self.metaType = "Null"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def findNodes(self):
        """

        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.ExpressionContext)

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if not (isinstance(node.children[0], JavaParser.ExpressionContext) and
                        isinstance(node.children[1], TerminalNodeImpl) and
                        isinstance(node.children[2], JavaParser.ExpressionContext)):
                    continue  # not a binary expression

            except Exception as e:
                continue

            if not (node.children[1].symbol.text == "!=" or node.children[1].symbol.text == "=="):
                continue  # not a relational operator

            if 'null' not in node.getText():
                continue  # not a null check

            self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            replacementText = ""
            if node.children[1].symbol.text == "!=":
                replacementText = "true"
            elif node.children[1].symbol.text == "==":
                replacementText = "false"

            mutation = Mutation(startPos=node.start.start, endPos=node.stop.stop, lineNumber=node.start.line,
                                nodeID=node.nodeIndex, mutatorType=self.mutatorType, replacementText=replacementText)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


class NullifyObjectInitialization(MutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyObjectInitialization"
        self.metaType = "Null"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def findNodes(self):
        """

        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.CreatorContext)

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.CreatorContext)

            try:
                newStatement = node.parentCtx.getChild(0, TerminalNodeImpl)
                argumentsStatement = node.children[-1].children[-1]

                if newStatement.symbol.text != u'new':
                    continue

                if not isinstance(argumentsStatement, JavaParser.ArgumentsContext):
                    continue

                if argumentsStatement.children[-1].symbol.text != u')':
                    continue

            except:
                continue

            self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            replacementText = "null"
            newStatement = node.parentCtx.getChild(0, TerminalNodeImpl)
            argumentsStatement = node.children[-1].children[-1]

            mutation = Mutation(startPos=newStatement.symbol.start, endPos=argumentsStatement.stop.stop,
                                lineNumber=node.parentCtx.start.line, nodeID=node.nodeIndex,
                                mutatorType=self.mutatorType, replacementText=replacementText)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


class NullifyReturnValue(MutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyReturnValue"
        self.metaType = "Null"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def findNodes(self):
        """

        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, TerminalNodeImpl)

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            assert isinstance(node, TerminalNodeImpl)

            if node.symbol.text != u'return':
                continue

            if not isinstance(node.getParent().getChild(1), JavaParser.ExpressionContext):
                continue

            parentMethod = self.javaParseObject.seekFirstMatchingParent(node, JavaParser.MethodDeclarationContext)
            if parentMethod is None:
                continue

            assert isinstance(parentMethod, JavaParser.MethodDeclarationContext)

            parentType = parentMethod.getChild(0, JavaParser.JTypeContext)
            if not isinstance(parentType, JavaParser.JTypeContext):
                continue

            if parentType.getChild(0, JavaParser.PrimitiveTypeContext) is not None:
                continue  # primitive typed method

            self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            assert isinstance(node.symbol, Token)
            id += 1
            replacementText = "return null;"

            mutation = Mutation(startPos=node.symbol.start, endPos=node.getParent().getChild(2).symbol.stop,
                                lineNumber=node.getParent().start.line, nodeID=node.getParent().nodeIndex,
                                mutatorType=self.mutatorType, replacementText=replacementText)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


class NullifyInputVariable(MutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyInputVariable"
        self.metaType = "Null"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def findNodes(self):
        """

        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.MethodDeclarationContext)

    def filterCriteria(self):
        """

        """
        self.replacementTextDict = dict()

        for methodDeclaration in self.allNodes:
            try:
                variableList = self.javaParseObject.seekAllNodes(methodDeclaration.formalParameters(),
                                                                 JavaParser.VariableDeclaratorIdContext)

                if len(variableList) == 0:
                    continue  # no variables in this declaration

                # can fail on methods with no body
                node = methodDeclaration.methodBody().block().getChild(0, TerminalNodeImpl)

            except Exception as e:
                continue

            variablesPerNodeReplacementTextList = list()
            for variablesPerNode in variableList:
                assert isinstance(variablesPerNode, JavaParser.VariableDeclaratorIdContext)

                if variablesPerNode.parentCtx.getChild(0, JavaParser.JTypeContext).getChild(0, JavaParser.PrimitiveTypeContext) is not None:
                    continue  # primitive typed variable

                variablesPerNodeReplacementTextList.append('{ ' + variablesPerNode.getText() + ' = null;')

            self.replacementTextDict[node] = variablesPerNodeReplacementTextList
            self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            for replacementText in self.replacementTextDict[node]:
                id += 1

                mutation = Mutation(startPos=node.symbol.start, endPos=node.symbol.stop,
                                    lineNumber=node.parentCtx.start.line, nodeID=node.nodeIndex,
                                    mutatorType=self.mutatorType, replacementText=replacementText)

                mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
                mutant.mutateCode()
                self.mutants.append(mutant)



#################################################
#      Traditional Mutation Operators           #
#################################################

class TraditionalMutationOperator(MutationOperator):
    """

    """
    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "GenericTraditionalMutationOperator"

    def findNodes(self):
        """

        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.ExpressionContext)

    def filterCriteriaBinaryExpression(self, node: JavaParser.ExpressionContext, symbolList: List[str]):
        """

        """
        assert isinstance(node, JavaParser.ExpressionContext)

        try:
            if not (isinstance(node.children[0], JavaParser.ExpressionContext)
                    and isinstance(node.children[1], TerminalNodeImpl)
                    and isinstance(node.children[2], JavaParser.ExpressionContext)):
                return False

        except Exception as e:
            return False

        if node.children[1].symbol.text not in symbolList:
            return False

        return True

    def filterCriteriaUnaryExpression(self, node: JavaParser.ExpressionContext, symbolList: List[str]):
        """

        """
        assert isinstance(node, JavaParser.ExpressionContext)

        try:
            if not (isinstance(node.children[0], TerminalNodeImpl)
                    and isinstance(node.children[1], JavaParser.ExpressionContext)):
                return False
        except Exception as e:
            return False

        if node.children[0].symbol.text not in symbolList:
            return False

        return True

    def generateMutantsUnaryExpression(self, node: JavaParser.ExpressionContext, symbolDict: dict, id: int):
        """

        """
        replacementText = symbolDict[node.children[0].symbol.text]

        mutation = Mutation(startPos=node.children[0].symbol.start, endPos=node.children[0].symbol.stop,
                            lineNumber=node.start.line, nodeID=node.nodeIndex,
                            mutatorType=self.mutatorType, replacementText=replacementText)

        mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
        mutant.mutateCode()

        return mutant

    def generateMutantsBinaryExpression(self, node: JavaParser.ExpressionContext, symbolDict: dict, id: int):
        """

        """
        replacementText = symbolDict[node.children[1].symbol.text]

        mutation = Mutation(startPos=node.children[1].symbol.start, endPos=node.children[1].symbol.stop,
                            lineNumber=node.start.line, nodeID=node.nodeIndex,
                            mutatorType=self.mutatorType, replacementText=replacementText)

        mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
        mutant.mutateCode()

        return mutant


class ArithmeticOperatorReplacementBinary(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ArithmeticOperatorReplacementBinary"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if (self.filterCriteriaBinaryExpression(node, ['+', '-', '*', '/', '%'])
                    and node.children[0].getText()[0] != '\"' and node.children[2].getText()[0] != '\"'):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'+': '-', '-': '+', '/': '*', '*': '/', '%': '/'}, id)
            self.mutants.append(mutant)


class RelationalOperatorReplacement(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RelationalOperatorReplacement"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['>', '>=', '<', '<=', '==', '!=']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'>': '<=', '<': '>=', '>=': '<', '<=': '>', '!=': '==', '==': '!='}, id)
            self.mutants.append(mutant)


class ConditionalOperatorReplacement(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ConditionalOperatorReplacement"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['&&', '||']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'&&': '||', '||': '&&'}, id)
            self.mutants.append(mutant)


class LogicalOperatorReplacement(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "LogicalOperatorReplacement"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['&', '|', '^']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'&': '|', '|': '^', '^': '&'}, id)
            self.mutants.append(mutant)


class AssignmentOperatorReplacementShortcut(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "AssignmentOperatorReplacementShortcut"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>=']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'+=': '-=', '-=': '+=', '*=': '/=', '/=': '*=',
                                                                 '%=': '/=', '&=': '|=', '|=': '^=', '^=': '&=',
                                                                 '<<=': '>>=', '>>=': '>>>=', '>>>=': '>>='}, id)
            self.mutants.append(mutant)


class ArithmeticOperatorReplacementUnary(TraditionalMutationOperator):
    """

    """

    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ArithmeticOperatorReplacementUnary"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if self.filterCriteriaUnaryExpression(node, ['+', '-']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsUnaryExpression(node, {'+': '-', '-': '+'}, id)
            self.mutants.append(mutant)


class ConditionalOperatorDeletion(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ConditionalOperatorDeletion"
        self.metaType = "Traditional"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            if self.filterCriteriaUnaryExpression(node, ['!']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsUnaryExpression(node, {'!': ' '}, id)
            self.mutants.append(mutant)


class ArithmeticOperatorReplacementShortcut(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ArithmeticOperatorReplacementShortcut"
        self.metaType = "Traditional"
        self.terminalChild = dict()
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if (isinstance(node.children[0], TerminalNodeImpl)
                        and isinstance(node.children[1], JavaParser.ExpressionContext)):
                    self.terminalChild[node] = 0
                elif (isinstance(node.children[1], TerminalNodeImpl)
                        and isinstance(node.children[0], JavaParser.ExpressionContext)):
                    self.terminalChild[node] = 1
                else:
                    continue  # not a shortcut expression
            except Exception as e:
                continue

            if node.children[self.terminalChild[node]].symbol.text not in ["++", "--"]:
                continue  # not an arithmetic operator

            self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            replacementText = ""
            if node.children[self.terminalChild[node]].symbol.text == "++":
                replacementText = "--"
            elif node.children[self.terminalChild[node]].symbol.text == "--":
                replacementText = "++"

            mutation = Mutation(startPos=node.children[self.terminalChild[node]].symbol.start,
                                endPos=node.children[self.terminalChild[node]].symbol.stop, lineNumber=node.start.line,
                                nodeID=node.nodeIndex, mutatorType=self.mutatorType, replacementText=replacementText)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


class ShiftOperatorReplacement(TraditionalMutationOperator):
    """

    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ShiftOperatorReplacement"
        self.metaType = "Traditional"
        self.threeTerminals = dict()
        self.findNodes()
        self.filterCriteria()
        self.generateMutants()

    def filterCriteria(self):
        """

        """
        for node in self.allNodes:
            assert isinstance(node, JavaParser.ExpressionContext)

            try:
                if (isinstance(node.children[0], JavaParser.ExpressionContext)
                        and isinstance(node.children[1], TerminalNodeImpl)
                        and isinstance(node.children[2], TerminalNodeImpl)
                        and isinstance(node.children[3], JavaParser.ExpressionContext)):
                    self.threeTerminals[node] = False

                elif (isinstance(node.children[0], JavaParser.ExpressionContext)
                      and isinstance(node.children[1], TerminalNodeImpl)
                      and isinstance(node.children[2], TerminalNodeImpl)
                      and isinstance(node.children[3], TerminalNodeImpl)
                      and isinstance(node.children[4], JavaParser.ExpressionContext)):
                    self.threeTerminals[node] = True
                else:
                    continue  # not a binary shift expression

            except Exception as e:
                continue

            try:
                if not self.threeTerminals[node] \
                        and ((node.children[1].symbol.text == u"<" and node.children[2].symbol.text == u"<")
                             or (node.children[1].symbol.text == u">" and node.children[2].symbol.text == u">")):
                    pass

                elif self.threeTerminals[node] \
                        and (node.children[1].symbol.text == u">"
                             and node.children[2].symbol.text == u">"
                             and node.children[3].symbol.text == u">"):
                    pass

                else:
                    continue  # not a shift operator

            except Exception as e:
                continue

            self.mutableNodes.append(node)

    def generateMutants(self):
        """

        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            if self.threeTerminals[node]:
                replacementText = ">>"
                mutation = Mutation(startPos=node.children[1].symbol.start,
                                    endPos=node.children[3].symbol.stop, lineNumber=node.start.line,
                                    nodeID=node.nodeIndex, mutatorType=self.mutatorType,
                                    replacementText=replacementText)

            else:
                replacementText = ">>" if node.children[1].symbol.text == '<' else "<<"
                mutation = Mutation(startPos=node.children[1].symbol.start,
                                    endPos=node.children[2].symbol.stop, lineNumber=node.start.line,
                                    nodeID=node.nodeIndex, mutatorType=self.mutatorType,
                                    replacementText=replacementText)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


#################################################


def getAllInstantiableSubclasses(parentClass):
    """

    :param parentClass: the class that all its subclasses must be returned
    :type parentClass: Type[MutationOperator]
    :return: set of MutationOperator instantiable subclasses
    :rtype: set
    """
    allInstantiableSubclasses = set()

    for subClass in parentClass.__subclasses__():
        if subClass.instantiable:
            allInstantiableSubclasses.add(subClass)
        allInstantiableSubclasses.update(getAllInstantiableSubclasses(subClass))

    return allInstantiableSubclasses


class JavaMutate(object):
    """
    Main entry point for mutation of a Java source file.
    """
    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse, verbose: bool = False):
        self.verbose = verbose
        self.sourceCode = sourceCode
        self.sourceTree = sourceTree
        self.mutantsPerLine = dict()

        if isinstance(javaParseObject, JavaParse):
            self.javaParseObject = javaParseObject
        else:
            self.javaParseObject = JavaParse()

        # find all mutation operators and instantiate them
        self.mutationOperators = list()
        for MO in getAllInstantiableSubclasses(MutationOperator):
            self.mutationOperators.append(MO(sourceTree, sourceCode, javaParseObject))

    def gatherMutants(self, metaType: str = "Traditional"):
        """
        Gathers all mutants, creates desired higher-order mutants, and returns the mutated code

        :param metaType: type of mutation operators to use
        :type metaType: str
        :return: mutated source code for each mutant, number of types of mutants
        :rtype: Tuple[List, Dict]
        """
        mutationTypeCount = dict()
        mutantTexts = list()

        for mO in self.mutationOperators:
            if metaType == mO.metaType or metaType == "All":
                mutationTypeCount[mO.mutatorType] = len(mO.mutants)
                for mutant in mO.mutants:
                    mutantTexts.append(str(mutant))
                    for mutation in mutant.mutationList:
                        self.mutantsPerLine[mutation.lineNumber] = 1 + self.mutantsPerLine.get(mutation.lineNumber, 0)

        return mutantTexts, mutationTypeCount

    def gatherHigherOrderMutants(self, higherOrderDirective: int, metaType: str = "Traditional"):
        """
        Gathers all mutants, creates desired higher-order mutants, and returns the mutated code

        :param higherOrderDirective: The requested higher-order order
        :type higherOrderDirective: int
        :param metaType: type of mutation operators to use
        :type metaType: str
        :return: mutated source code for each mutant, number of types of mutants
        :rtype: Tuple[List, Dict]
        """
        selectedMutants = list()
        for mO in self.mutationOperators:
            if metaType == mO.metaType or metaType == "All":
                selectedMutants.extend(mO.mutants)

        higherOrder = max(int(log10(len(selectedMutants))) if higherOrderDirective == -1 else higherOrderDirective, 1)
        shuffle(selectedMutants)
        mutantTexts = list()

        while len(selectedMutants) > 0:
            higherOrderMutant = None
            for mutant in selectedMutants[:higherOrder]:
                higherOrderMutant += mutant

            mutantTexts.append(str(higherOrderMutant))
            for mutation in higherOrderMutant.mutationList:
                self.mutantsPerLine[mutation.lineNumber] = 1 + self.mutantsPerLine.get(mutation.lineNumber, 0)

            selectedMutants = selectedMutants[higherOrder:]

        mutationTypeCount = {"Higher-Order": len(mutantTexts)}

        return mutantTexts, mutationTypeCount


