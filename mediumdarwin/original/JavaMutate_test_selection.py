import copy
import sys
from math import log10
from random import shuffle
from typing import List, Tuple, Dict

from antlr4 import Token
from antlr4.tree.Tree import TerminalNodeImpl
from mediumdarwin.JavaParse import JavaParse
from mediumdarwin.JavaParser import JavaParser
from mediumdarwin.Database import Database
from mediumdarwin.SharedFunctions import getAllInstantiableSubclasses

sys.setrecursionlimit(100000)


class MutationOperator(object):
    """ """

    instantiable = True
    metaTypes = ["Generic"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants=False,
        generateMutations=True,
    ):
        self.sourceTree = sourceTree
        self.sourceCode = sourceCode
        self.color = "#FFFFF0"
        self.mutatorType = "GenericMutationOperator"
        self.allNodes = list()  # populated by findNodes
        self.mutableNodes = list()  # populated by filterCriteria
        self.mutations = list()  # populated by generateMutations
        self.mutants = list()  # populated by generateMutants
        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        self.mutations_searched = False
        if self.generateMutants_:
            self.generateMutations_ = True
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

    def generateMutations(self):
        pass

    def generateMutants(self):
        """
        Generates the mutants
        """
        pass

    @property
    def cssClass(self):
        """
        Returns CSS Class for the mutation operator

        :return: CSS Class
        :rtype: str
        """

        return ".{classname} {{ background: {color}; }} ".format(
            classname=self.mutatorType, color=self.color
        )


class Mutation(object):
    """
    Defines a single mutation.
    """

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
    ):
        """ """
        assert endPos >= startPos

        self.startPos = startPos
        self.endPos = endPos
        self.lineNumber = lineNumber
        self.nodeID = nodeID
        self.mutatorType = mutatorType
        self.replacementText = replacementText
        self.color = color
        self.mutationID = mutationID

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

        textStub = "/* LittleDarwin generated order-{0} mutant\n".format(
            str(len(self.mutationList))
        )  # type: str

        textStub += "\n----> mutantID: " + str(self.mutantID) + "\n\n"
        for mutation in self.mutationList:
            textStub += (
                "mutant type: "
                + mutation.mutatorType
                + "\n----> before: "
                + self.getLine(mutation.lineNumber)
                + "\n----> after: "
                + self.getLine(
                    mutation.lineNumber, code=mutation.applyMutation(
                        self.sourceCode)
                )
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
        return self.stub + self.mutatedCode


#################################################
#       Method-level Mutation Operators         #
#################################################


class RemoveMethod(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Method", "All"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveMethod"
        self.color = "#FF00D4"
        self.mutableNodesWithTypes = list()
        self.findNodes()
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.MethodBodyContext
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

    def generateMutations(self):
        for node, nodeType in self.mutableNodesWithTypes:
            if nodeType == "void":
                replacementTextList = ["{\n// void -- no return //\n}\n"]
            elif nodeType == "boolean":
                replacementTextList = [
                    "{\n    return true;\n}\n",
                    "{\n    return false;\n}\n",
                ]
            elif (
                nodeType == "byte"
                or nodeType == "short"
                or nodeType == "long"
                or nodeType == "int"
            ):
                replacementTextList = [
                    "{\n    return 0;\n}\n", "{\n    return 1;\n}\n"]
            elif nodeType == "float":
                replacementTextList = [
                    "{\n    return 0.0f;\n}\n",
                    "{\n    return 0.1f;\n}\n",
                ]
            elif nodeType == "double":
                replacementTextList = [
                    "{\n    return 0.0;\n}\n",
                    "{\n    return 0.1;\n}\n",
                ]
            elif nodeType == "char":
                replacementTextList = [
                    "{\n    return ' ';\n}\n",
                    "{\n    return 'A';\n}\n",
                ]
            elif nodeType == "String":
                replacementTextList = [
                    '{\n    return "";\n}\n',
                    '{\n    return "A";\n}\n',
                ]
            elif "[" in nodeType and "]" in nodeType:
                replacementTextList = [
                    "{{\n    return new {} {{}};\n}}\n".format(nodeType)
                ]
            else:
                replacementTextList = ["{\n    return null;\n}\n"]

            for replacementText in replacementTextList:
                mutation = Mutation(
                    startPos=node.start.start,
                    endPos=node.stop.stop,
                    lineNumber=node.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText=replacementText,
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveNullCheck"
        self.color = "#ADD8E6"
        self.findNodes()
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.ExpressionContext
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

    def generateMutations(self):
        for node in self.mutableNodes:
            replacementText = ""
            if node.children[1].symbol.text == "!=":
                replacementText = "true"
            elif node.children[1].symbol.text == "==":
                replacementText = "false"

            mutation = Mutation(
                startPos=node.start.start,
                endPos=node.stop.stop,
                lineNumber=node.start.line,
                nodeID=node.nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
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


class NullifyObjectInitialization(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyObjectInitialization"
        self.color = "#F08080"
        self.findNodes()
        self.filterCriteria()
        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.CreatorContext
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

            except:
                continue

            self.mutableNodes.append(node)

    def generateMutations(self):
        id = 0
        for node in self.mutableNodes:
            id += 1
            replacementText = "null"
            newStatement = node.parentCtx.getChild(0, TerminalNodeImpl)
            argumentsStatement = node.children[-1].children[-1]

            mutation = Mutation(
                startPos=newStatement.symbol.start,
                endPos=argumentsStatement.stop.stop,
                lineNumber=node.parentCtx.start.line,
                nodeID=node.nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
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


class NullifyReturnValue(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyReturnValue"
        self.color = "#E0FFFF"
        self.findNodes()
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, TerminalNodeImpl
        )

    def filterCriteria(self):
        """ """
        for node in self.allNodes:
            assert isinstance(node, TerminalNodeImpl)

            if node.symbol.text != "return":
                continue

            if not isinstance(
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
        for node in self.mutableNodes:
            assert isinstance(node.symbol, Token)
            replacementText = "return null;"

            mutation = Mutation(
                startPos=node.symbol.start,
                endPos=node.getParent().getChild(2).symbol.stop,
                lineNumber=node.getParent().start.line,
                nodeID=node.getParent().nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
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


class NullifyInputVariable(MutationOperator):
    """ """

    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyInputVariable"
        self.color = "#90EE90"
        self.findNodes()
        self.filterCriteria()

        self.generateMutants_ = generateMutants
        self.generateMutations_ = generateMutations
        if self.generateMutants_:
            self.generateMutations_ = True

        if self.generateMutants_:
            self.generateMutants()
        elif self.generateMutations_:
            self.generateMutations()

    def findNodes(self):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.MethodDeclarationContext
        )

    def filterCriteria(self):
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

        for methodDeclaration in self.allNodes:
            try:
                variableList = self.javaParseObject.seekAllNodes(
                    methodDeclaration.formalParameters(),
                    JavaParser.VariableDeclaratorIdContext,
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

            self.replacementTextDict[node] = variablesPerNodeReplacementTextList
            self.mutableNodes.append(node)

    def generateMutations(self):
        for node in self.mutableNodes:
            for replacementText in self.replacementTextDict[node]:
                mutation = Mutation(
                    startPos=node.symbol.start,
                    endPos=node.symbol.stop,
                    lineNumber=node.parentCtx.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText=replacementText,
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
#      Traditional Mutation Operators           #
#################################################


class TraditionalMutationOperator(MutationOperator):
    """ """

    metaTypes = ["Traditional", "All"]

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "GenericTraditionalMutationOperator"

    def findNodes(self):
        """ """
        self.allNodes = self.javaParseObject.seekAllNodes(
            self.sourceTree, JavaParser.ExpressionContext
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
        replacementText = symbolDict[node.children[0].symbol.text]

        mutation = Mutation(
            startPos=node.children[0].symbol.start,
            endPos=node.children[0].symbol.stop,
            lineNumber=node.start.line,
            nodeID=node.nodeIndex,
            mutatorType=self.mutatorType,
            replacementText=replacementText,
            color=self.color,
        )
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

    # def generateMutantsUnaryExpression(self, mutation: Mutation, id: int):
    #     """ """
    #     mutant = Mutant(
    #         mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode
    #     )
    #     mutant.mutateCode()

    #     return mutant

    # def generateMutantsUnaryExpression(
    #     self, node: JavaParser.ExpressionContext, symbolDict: dict, id: int
    # ):
    #     """ """
    #     mutation = self.generateMutantionsUnaryExpression(node, symbolDict, id)
    #     mutant = Mutant(
    #         mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode
    #     )
    #     mutant.mutateCode()

    #     return mutant

    def generateMutationsBinaryExpression(
        self, node: JavaParser.ExpressionContext, symbolDict: dict
    ):
        """ """
        replacementText = symbolDict[node.children[1].symbol.text]

        mutation = Mutation(
            startPos=node.children[1].symbol.start,
            endPos=node.children[1].symbol.stop,
            lineNumber=node.start.line,
            nodeID=node.nodeIndex,
            mutatorType=self.mutatorType,
            replacementText=replacementText,
            color=self.color,
        )

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

    # def generateMutantsBinaryExpression(self, mutation: Mutation, id: int):
    #     """ """
    #     mutant = Mutant(
    #         mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode
    #     )
    #     mutant.mutateCode()

    #     return mutant

    # def generateMutantsBinaryExpression(
    #     self, node: JavaParser.ExpressionContext, symbolDict: dict, id: int
    # ):
    #     """ """
    #     mutation = self.generateMutationsBinaryExpression(node, symbolDict)

    #     mutant = Mutant(
    #         mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode
    #     )
    #     mutant.mutateCode()

    #     return mutant


class ArithmeticOperatorReplacementBinary(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ArithmeticOperatorReplacementBinary"
        self.color = "#FFB6C1"
        self.findNodes()
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
            # mutant.mutateCode()
            self.mutants.append(mutant)


class RelationalOperatorReplacement(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "RelationalOperatorReplacement"
        self.color = "#FFA07A"
        self.findNodes()
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
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutation = self.generateMutationsBinaryExpression(
                node,
                {">": "<=", "<": ">=", ">=": "<",
                    "<=": ">", "!=": "==", "==": "!="},
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ConditionalOperatorReplacement"
        self.color = "#87CEFA"
        self.findNodes()
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "LogicalOperatorReplacement"
        self.color = "#F0E68C"
        self.findNodes()
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "AssignmentOperatorReplacementShortcut"
        self.color = "#B0C4DE"
        self.findNodes()
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ArithmeticOperatorReplacementUnary"
        self.color = "#DDA0DD"
        self.findNodes()
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ConditionalOperatorDeletion"
        self.color = "#FFD700"
        self.findNodes()
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ArithmeticOperatorReplacementShortcut"
        self.color = "#FF00FF"
        self.terminalChild = dict()
        self.findNodes()
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
        for node in self.mutableNodes:
            replacementText = ""
            if node.children[self.terminalChild[node]].symbol.text == "++":
                replacementText = "--"
            elif node.children[self.terminalChild[node]].symbol.text == "--":
                replacementText = "++"

            mutation = Mutation(
                startPos=node.children[self.terminalChild[node]].symbol.start,
                endPos=node.children[self.terminalChild[node]].symbol.stop,
                lineNumber=node.start.line,
                nodeID=node.nodeIndex,
                mutatorType=self.mutatorType,
                replacementText=replacementText,
                color=self.color,
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


class ShiftOperatorReplacement(TraditionalMutationOperator):
    """ """

    instantiable = True

    def __init__(
        self,
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        super().__init__(
            sourceTree, sourceCode, javaParseObject, generateMutants, generateMutations
        )
        self.mutatorType = "ShiftOperatorReplacement"
        self.color = "#9ACD32"
        self.threeTerminals = dict()
        self.findNodes()
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
        id = 0
        for node in self.mutableNodes:
            id += 1
            if self.threeTerminals[node]:
                replacementText = ">>"
                mutation = Mutation(
                    startPos=node.children[1].symbol.start,
                    endPos=node.children[3].symbol.stop,
                    lineNumber=node.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText=replacementText,
                )

            else:
                replacementText = ">>" if node.children[1].symbol.text == "<" else "<<"
                mutation = Mutation(
                    startPos=node.children[1].symbol.start,
                    endPos=node.children[2].symbol.stop,
                    lineNumber=node.start.line,
                    nodeID=node.nodeIndex,
                    mutatorType=self.mutatorType,
                    replacementText=replacementText,
                    color=self.color,
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
        sourceTree: JavaParser.CompilationUnitContext,
        sourceCode: str,
        javaParseObject: JavaParse,
        file_name: str,
        verbose: bool = False,
    ):
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
        metaTypes: List[str] = ["Traditional"],
        generateMutants: bool = False,
        generateMutations: bool = True,
    ):
        """

        :param generateMutants:
        :type generateMutants:
        :param metaTypes:
        :type metaTypes:
        """
        for MO in getAllInstantiableSubclasses(MutationOperator):
            for metaType in metaTypes:
                if metaType in MO.metaTypes:
                    self.mutationOperators.append(
                        MO(
                            self.sourceTree,
                            self.sourceCode,
                            self.javaParseObject,
                            generateMutants,
                            generateMutations,
                        )
                    )

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

    def gatherMutations(
        self,
        metaTypes: List[str] = ["Traditional"],
        database: Database = None,
        last_mutation_id: int = 0,
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
        file_id = database.fetch_data(
            "file", columns="id", condition=f"name = '{self.file_name}'"
        )[0][0]
        self.instantiateMutationOperators(metaTypes)

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
                        if database is not None:
                            # mutation.mutationID = last_mutation_id
                            operator_id = database.fetch_data(
                                "mutation_operator",
                                "id",
                                f"name = '{mutation.mutatorType}'",
                            )
                            operator_id = operator_id[0][0]
                            database.insert_mutation(
                                last_mutation_id,
                                file_id,
                                mutation.nodeID,
                                mutation.startPos,
                                mutation.endPos,
                                mutation.lineNumber,
                                mutation.replacementText,
                                mutation_operator_id=operator_id,
                            )
                            mutation.mutationID = last_mutation_id
                            last_mutation_id += 1

        self.averageDensity = (
            sum(self.mutantsPerLine.values()) / len(self.inMethodLines)
            if len(self.inMethodLines) > 0
            else 0
        )

        return mutationTypeCount

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

    def gatherHigherOrderMutants(
        self, higherOrderDirective: int, metaTypes: List[str] = ["Traditional"]
    ):
        """
        Gathers all mutants, creates desired higher-order mutants, and returns the mutated code

        :param higherOrderDirective: The requested higher-order order
        :type higherOrderDirective: int
        :param metaTypes: type of mutation operators to use
        :type metaTypes: List[str]
        :return: mutated source code for each mutant, number of types of mutants
        :rtype: Tuple[List, Dict]
        """
        selectedMutants = list()

        self.instantiateMutationOperators(metaTypes)

        for mO in self.mutationOperators:
            for metaType in metaTypes:
                if metaType in mO.metaTypes:
                    selectedMutants.extend(mO.mutants)

        higherOrder = max(
            (
                int(log10(len(selectedMutants)))
                if higherOrderDirective == -1
                else higherOrderDirective
            ),
            1,
        )
        shuffle(selectedMutants)
        mutantTexts = list()

        while len(selectedMutants) > 0:
            higherOrderMutant = None
            for mutant in selectedMutants[:higherOrder]:
                higherOrderMutant += mutant

            mutantTexts.append(str(higherOrderMutant))
            self.mutants.append(higherOrderMutant)
            for mutation in higherOrderMutant.mutationList:
                self.mutantsPerLine[mutation.lineNumber] = 1 + self.mutantsPerLine.get(
                    mutation.lineNumber, 0
                )
                self.mutantsPerMethod[
                    self.javaParseObject.getMethodNameForNode(
                        self.sourceTree, mutation.nodeID
                    )
                ] = 1 + self.mutantsPerMethod.get(mutation.lineNumber, 0)

            selectedMutants = selectedMutants[higherOrder:]

        mutationTypeCount = {"Higher-Order": len(mutantTexts)}

        self.averageDensity = (
            sum(self.mutantsPerLine.values()) / len(self.inMethodLines)
            if len(self.inMethodLines) > 0
            else 0
        )

        return mutantTexts, mutationTypeCount

    @property
    def cssStyle(self):
        """
        Returns CSS Style for the aggregate report

        :return: CSS Style
        :rtype: str
        """
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

        :param littleDarwinVersion: LittleDarwin Version
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

        output = "<!DOCTYPE html><head><title>LittleDarwin Aggregate Mutation Report</title> <style type='text/css'>"
        output += (
            self.cssStyle
            + "</style></head><body><h1>LittleDarwin Aggregate Mutation Report</h1>"
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
            "Report generated by LittleDarwin {} </p></footer></body></html>".format(
                littleDarwinVersion
            )
        )

        return output
