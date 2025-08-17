import copy
import sys
from math import log10
from random import shuffle
from typing import List, Tuple, Dict

from antlr4 import Token
from antlr4.tree.Tree import TerminalNodeImpl
from littledarwin.JavaParse import JavaParse
from littledarwin.JavaParser import JavaParser

sys.setrecursionlimit(100000)


class Mutation(object):
    """
    This class represents a single mutation, which is a change to a small
    section of the source code. It contains information about the location of
    the mutation, the type of mutator used, and the text to replace the
    original code with.
    """

    def __init__(self, startPos: int, endPos: int, lineNumber: int, nodeID: int, mutatorType: str,
                 replacementText: str, color: str = "#FFFFFF"):
        """
        Initializes a Mutation object.

        :param startPos: The starting position of the mutation in the source
                         code.
        :type startPos: int
        :param endPos: The ending position of the mutation in the source code.
        :type endPos: int
        :param lineNumber: The line number of the mutation.
        :type lineNumber: int
        :param nodeID: The ID of the node being mutated.
        :type nodeID: int
        :param mutatorType: The type of mutator being used.
        :type mutatorType: str
        :param replacementText: The text to replace the original code with.
        :type replacementText: str
        :param color: The color to use for highlighting the mutation.
        :type color: str
        """
        assert endPos >= startPos

        self.startPos = startPos
        self.endPos = endPos
        self.lineNumber = lineNumber
        self.nodeID = nodeID
        self.mutatorType = mutatorType
        self.replacementText = replacementText
        self.color = color

    def __str__(self):
        text = "Mutated Text: {} \n".format(self.replacementText)
        text += "Mutation Operator Type: {} \n".format(self.mutatorType)
        text += "Node ID: {}".format(self.nodeID)
        return text

    def applyMutation(self, sourceCode: str, byteOffset: int = 0) -> str:
        """
        Applies the mutation to the given source code.

        :param sourceCode: The source code to apply the mutation to.
        :type sourceCode: str
        :param byteOffset: The byte offset to apply to the start and end
                           positions. This is used when applying multiple
                           mutations to the same file.
        :type byteOffset: int
        :return: The mutated source code.
        :rtype: str
        """
        return sourceCode[:self.startPos + byteOffset] + self.replacementText + sourceCode[
                                                                                self.endPos + byteOffset + 1:]

    def isInRange(self, start, end):
        """
        Checks if the mutation is within the given range.

        :param start: The start of the range.
        :type start: int
        :param end: The end of the range.
        :type end: int
        :return: True if the mutation is within the range, False otherwise.
        :rtype: bool
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
    This class represents a mutant, which is a version of the source code
    that has been modified by one or more mutations. It contains a list of
    mutations and the original source code, and it can be used to generate
    the mutated source code.
    """

    def __init__(self, mutantID: int, mutationList: List[Mutation], sourceCode: str):
        """
        Initializes a Mutant object.

        :param mutantID: The ID of the mutant.
        :type mutantID: int
        :param mutationList: The list of mutations to apply.
        :type mutationList: list
        :param sourceCode: The original source code.
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
        Gets a specific line from the source code.

        :param lineNumber: The line number to get.
        :type lineNumber: int
        :param code: The code to get the line from. If None, the original
                     source code is used.
        :type code: str, optional
        :return: The specified line of code.
        :rtype: str
        """
        if code is None:
            code = self.sourceCode

        return code.splitlines(keepends=False)[lineNumber - 1]

    def mutateCode(self):
        """
        Applies the mutations in the mutation list to the source code to
        generate the mutated code.
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
    def stub(self) -> str:
        """
        Generates the text stub that goes in the beginning of each mutant file.

        :return: Returns text stub on top of each mutant
        :rtype: str
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
                newMutant = Mutant(-1 * self.mutantID * other.mutantID, newMutationList, self.sourceCode)
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
    This is a base class for all mutation operators. A mutation operator is a
    class that knows how to find specific nodes in a parse tree and generate
    mutants from them.
    """
    instantiable = True
    metaTypes = ["Generic"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants=True):
        """
        Initializes a MutationOperator object.

        :param sourceTree: The root of the parse tree.
        :type sourceTree: antlr4.tree.Tree.ParseTree
        :param sourceCode: The source code to mutate.
        :type sourceCode: str
        :param javaParseObject: The JavaParse object to use for parsing.
        :type javaParseObject: littledarwin.JavaParse.JavaParse
        :param generateMutants: A boolean indicating whether to generate mutants.
        :type generateMutants: bool
        """
        self.sourceTree = sourceTree
        self.sourceCode = sourceCode
        self.color = "#FFFFF0"
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

    @property
    def cssClass(self):
        """
        Returns CSS Class for the mutation operator

        :return: CSS Class
        :rtype: str
        """

        return ".{classname} {{ background: {color}; }} ".format(classname=self.mutatorType, color=self.color)


#################################################
#       Method-level Mutation Operators         #
#################################################

class RemoveMethod(MutationOperator):
    """
    This mutation operator removes the body of a method and replaces it with a
    default return value. For example, a method that returns an ``int`` will be
    replaced with ``return 0;``.
    """
    instantiable = True
    metaTypes = ["Method", "All"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveMethod"
        self.color = "#FF00D4"
        self.mutableNodesWithTypes = list()
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def findNodes(self):
        """
        Finds all method and constructor bodies in the parse tree.
        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.MethodBodyContext)
        self.allNodes.extend(self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.ConstructorBodyContext))

    def filterCriteria(self):
        """
        Filters the found method bodies to include only those with a valid return type.
        It also filters out simple getters and setters and methods/constructors with @Inject annotation.
        """
        for node in self.allNodes:
            assert isinstance(node, (JavaParser.MethodBodyContext, JavaParser.ConstructorBodyContext))

            parent_declaration = self.javaParseObject.seekFirstMatchingParent(node, JavaParser.MethodDeclarationContext)
            if not parent_declaration:
                parent_declaration = self.javaParseObject.seekFirstMatchingParent(node,
                                                                                    JavaParser.ConstructorDeclarationContext)
            is_injected = False
            parent_declaration = self.javaParseObject.seekFirstMatchingParent(node, JavaParser.MethodDeclarationContext)
            if not parent_declaration:
                parent_declaration = self.javaParseObject.seekFirstMatchingParent(node,
                                                                                    JavaParser.ConstructorDeclarationContext)
            is_injected = False
            if parent_declaration:
                # The parent of a method/constructor declaration is a member declaration, which is inside a class body declaration.
                # The modifiers are children of the class body declaration.
                member_declaration = parent_declaration.parentCtx
                if member_declaration:
                    class_body_declaration = member_declaration.parentCtx
                    if class_body_declaration:
                        for child in class_body_declaration.getChildren():
                            if isinstance(child, JavaParser.ModifierContext):
                                if '@Inject' in child.getText():
                                    is_injected = True
                                    break

            block_statements = self.javaParseObject.seekAllNodes(node, JavaParser.BlockStatementContext)
            if len(block_statements) == 1:
                operators = self.javaParseObject.seekAllNodes(block_statements[0], TerminalNodeImpl)
                operator_texts = [op.getText() for op in operators]
                has_logic = any(
                    op in operator_texts for op in ['+', '-', '*', '/', '%', '&&', '||', '!', '?', 'instanceof', 'new'])

                if any(op.getText() == '(' for op in operators):
                    has_logic = True

                is_simple_setter = not has_logic and '=' in operator_texts and len(
                    self.javaParseObject.seekAllNodes(block_statements[0], JavaParser.ExpressionContext)) <= 4
                is_simple_getter = not has_logic and '=' not in operator_texts

                if is_injected:
                    if is_simple_setter:
                        continue
                else:
                    if is_simple_getter or is_simple_setter:
                        continue

            nodeType = self.javaParseObject.getMethodTypeForNode(node)
            # For constructors, nodeType will be None. We'll treat them as void.
            if nodeType is None and isinstance(node, JavaParser.ConstructorBodyContext):
                nodeType = 'void'

            if nodeType is not None:
                self.mutableNodes.append(node)
                self.mutableNodesWithTypes.append((node, nodeType))

    def generateMutants(self):
        """
        Generates mutants by replacing the method body with a default return value based on the method's return type.
        """
        id = 0
        for node, nodeType in self.mutableNodesWithTypes:
            if nodeType == "void":
                replacementTextList = ["{\n// void -- no return //\n}\n"]
            elif nodeType == "boolean":
                replacementTextList = ["{\n    return true;\n}\n", "{\n    return false;\n}\n"]
            elif nodeType == "byte" or nodeType == "short" or nodeType == "long" or nodeType == "int":
                replacementTextList = ["{\n    return 0;\n}\n", "{\n    return 1;\n}\n"]
            elif nodeType == "float" or nodeType == "double":
                replacementTextList = ["{\n    return 0.0;\n}\n", "{\n    return 0.1;\n}\n"]
            elif nodeType == "char":
                replacementTextList = ["{\n    return \'\';\n}\n", "{\n    return \'A\';\n}\n"]
            elif nodeType == "String":
                replacementTextList = ["{\n    return \"\";\n}\n", "{\n    return \"A\";\n}\n"]
            elif '[' in nodeType and ']' in nodeType:
                replacementTextList = ["{{\n    return new {} {{}};\n}}\n".format(nodeType)]
            else:
                replacementTextList = ["{\n    return null;\n}\n"]

            for replacementText in replacementTextList:
                id += 1
                mutation = Mutation(startPos=node.start.start, endPos=node.stop.stop,
                                    lineNumber=node.start.line, nodeID=node.nodeIndex,
                                    mutatorType=self.mutatorType, replacementText=replacementText)
                mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
                mutant.mutateCode()
                self.mutants.append(mutant)


#################################################
#          Null Mutation Operators              #
#################################################


class RemoveNullCheck(MutationOperator):
    """
    This mutation operator removes null checks by replacing them with ``true`` or
    ``false``. For example, ``if (x != null)`` will be replaced with ``if
    (true)``.
    """
    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RemoveNullCheck"
        self.color = "#ADD8E6"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def findNodes(self):
        """
        Finds all expression nodes in the parse tree.
        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.ExpressionContext)

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are null checks.
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
        Generates mutants by replacing the null check with true or false.
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
    This mutation operator nullifies object initializations by replacing them
    with ``null``. For example, ``new Foo()`` will be replaced with ``null``.
    """
    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyObjectInitialization"
        self.color = "#F08080"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def findNodes(self):
        """
        Finds all creator nodes in the parse tree.
        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.CreatorContext)

    def filterCriteria(self):
        """
        Filters the creator nodes to include only those that are object initializations.
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
        Generates mutants by replacing the object initialization with null.
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
    This mutation operator nullifies the return value of a method by
    replacing the return statement with ``return null;``.
    """
    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyReturnValue"
        self.color = "#E0FFFF"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def findNodes(self):
        """
        Finds all terminal nodes in the parse tree.
        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, TerminalNodeImpl)

    def filterCriteria(self):
        """
        Filters the terminal nodes to include only those that are 'return' statements with a non-primitive return type.
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
        Generates mutants by replacing the return statement with "return null;".
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
    This mutation operator nullifies input variables to a method by adding a
    statement at the beginning of the method to set the variable to ``null``.
    """
    instantiable = True
    metaTypes = ["Null", "All"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "NullifyInputVariable"
        self.color = "#90EE90"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def findNodes(self):
        """
        Finds all method declaration nodes in the parse tree.
        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.MethodDeclarationContext)

    def filterCriteria(self):
        """
        Filters the method declaration nodes to include only those with non-primitive input variables.
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

                if variablesPerNode.parentCtx.getChild(0, JavaParser.JTypeContext).getChild(0,
                                                                                            JavaParser.PrimitiveTypeContext) is not None:
                    continue  # primitive typed variable

                variablesPerNodeReplacementTextList.append('{ ' + variablesPerNode.getText() + ' = null;')

            self.replacementTextDict[node] = variablesPerNodeReplacementTextList
            self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by adding a statement to nullify each non-primitive input variable.
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
    A base class for all traditional mutation operators. These operators
    perform simple mutations, such as replacing one operator with another.
    """

    metaTypes = ["Traditional", "All"]

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        """
        Initializes a TraditionalMutationOperator object.

        :param sourceTree: The root of the parse tree.
        :type sourceTree: antlr4.tree.Tree.ParseTree
        :param sourceCode: The source code to mutate.
        :type sourceCode: str
        :param javaParseObject: The JavaParse object to use for parsing.
        :type javaParseObject: littledarwin.JavaParse.JavaParse
        :param generateMutants: A boolean indicating whether to generate mutants.
        :type generateMutants: bool
        """
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "GenericTraditionalMutationOperator"

    def findNodes(self):
        """
        Finds all expression nodes in the parse tree.
        """
        self.allNodes = self.javaParseObject.seekAllNodes(self.sourceTree, JavaParser.ExpressionContext)

    def filterCriteriaBinaryExpression(self, node: JavaParser.ExpressionContext, symbolList: List[str]):
        """
        A helper method to filter binary expressions based on a list of symbols.
        :param node: The expression node to check.
        :param symbolList: A list of symbols to match.
        :return: True if the node is a binary expression with a matching symbol, False otherwise.
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
        A helper method to filter unary expressions based on a list of symbols.
        :param node: The expression node to check.
        :param symbolList: A list of symbols to match.
        :return: True if the node is a unary expression with a matching symbol, False otherwise.
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
        A helper method to generate mutants for unary expressions.
        :param node: The expression node to mutate.
        :param symbolDict: A dictionary mapping original symbols to their replacements.
        :param id: The ID of the mutant.
        :return: A Mutant object.
        """
        replacementText = symbolDict[node.children[0].symbol.text]

        mutation = Mutation(startPos=node.children[0].symbol.start, endPos=node.children[0].symbol.stop,
                            lineNumber=node.start.line, nodeID=node.nodeIndex,
                            mutatorType=self.mutatorType, replacementText=replacementText, color=self.color)

        mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
        mutant.mutateCode()

        return mutant

    def generateMutantsBinaryExpression(self, node: JavaParser.ExpressionContext, symbolDict: dict, id: int):
        """
        A helper method to generate mutants for binary expressions.
        :param node: The expression node to mutate.
        :param symbolDict: A dictionary mapping original symbols to their replacements.
        :param id: The ID of the mutant.
        :return: A Mutant object.
        """
        replacementText = symbolDict[node.children[1].symbol.text]

        mutation = Mutation(startPos=node.children[1].symbol.start, endPos=node.children[1].symbol.stop,
                            lineNumber=node.start.line, nodeID=node.nodeIndex, mutatorType=self.mutatorType,
                            replacementText=replacementText, color=self.color)

        mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
        mutant.mutateCode()

        return mutant


class ArithmeticOperatorReplacementBinary(TraditionalMutationOperator):
    """
    This mutation operator replaces binary arithmetic operators. For example,
    ``+`` is replaced with ``-``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ArithmeticOperatorReplacementBinary"
        self.color = "#FFB6C1"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are binary arithmetic operations.
        """
        for node in self.allNodes:
            if (self.filterCriteriaBinaryExpression(node, ['+', '-', '*', '/', '%'])
                    and node.children[0].getText()[0] != '\"' and node.children[2].getText()[0] != '\"'):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by replacing the binary arithmetic operators.
        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'+': '-', '-': '+', '/': '*', '*': '/', '%': '/'}, id)
            self.mutants.append(mutant)


class RelationalOperatorReplacement(TraditionalMutationOperator):
    """
    This mutation operator replaces relational operators. For example, ``>`` is
    replaced with ``<=``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "RelationalOperatorReplacement"
        self.color = "#FFA07A"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are relational operations.
        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['>', '>=', '<', '<=', '==', '!=']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by replacing the relational operators.
        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'>': '<=', '<': '>=', '>=': '<', '<=': '>', '!=': '==',
                                                                 '==': '!='}, id)
            self.mutants.append(mutant)


class ConditionalOperatorReplacement(TraditionalMutationOperator):
    """
    This mutation operator replaces conditional operators. For example, ``&&``
    is replaced with ``||``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ConditionalOperatorReplacement"
        self.color = "#87CEFA"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are conditional operations.
        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['&&', '||']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by replacing the conditional operators.
        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'&&': '||', '||': '&&'}, id)
            self.mutants.append(mutant)


class LogicalOperatorReplacement(TraditionalMutationOperator):
    """
    This mutation operator replaces logical operators. For example, ``&`` is
    replaced with ``|``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "LogicalOperatorReplacement"
        self.color = "#F0E68C"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are logical operations.
        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['&', '|', '^']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by replacing the logical operators.
        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsBinaryExpression(node, {'&': '|', '|': '^', '^': '&'}, id)
            self.mutants.append(mutant)


class AssignmentOperatorReplacementShortcut(TraditionalMutationOperator):
    """
    This mutation operator replaces shortcut assignment operators. For example,
    ``+=`` is replaced with ``-=``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "AssignmentOperatorReplacementShortcut"
        self.color = "#B0C4DE"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are shortcut assignment operations.
        """
        for node in self.allNodes:
            if self.filterCriteriaBinaryExpression(node, ['+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=',
                                                          '>>>=']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by replacing the shortcut assignment operators.
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
    This mutation operator replaces unary arithmetic operators. For example, a
    unary ``+`` is replaced with a unary ``-``.
    """

    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ArithmeticOperatorReplacementUnary"
        self.color = "#DDA0DD"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are unary arithmetic operations.
        """
        for node in self.allNodes:
            if self.filterCriteriaUnaryExpression(node, ['+', '-']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by replacing the unary arithmetic operators.
        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsUnaryExpression(node, {'+': '-', '-': '+'}, id)
            self.mutants.append(mutant)


class ConditionalOperatorDeletion(TraditionalMutationOperator):
    """
    This mutation operator deletes conditional operators. For example, ``!a``
    is replaced with ``a``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ConditionalOperatorDeletion"
        self.color = "#FFD700"
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are conditional operations.
        """
        for node in self.allNodes:
            if self.filterCriteriaUnaryExpression(node, ['!']):
                self.mutableNodes.append(node)

    def generateMutants(self):
        """
        Generates mutants by deleting the conditional operators.
        """
        id = 0
        for node in self.mutableNodes:
            id += 1
            mutant = self.generateMutantsUnaryExpression(node, {'!': ' '}, id)
            self.mutants.append(mutant)


class ArithmeticOperatorReplacementShortcut(TraditionalMutationOperator):
    """
    This mutation operator replaces shortcut arithmetic operators. For example,
    ``++`` is replaced with ``--``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ArithmeticOperatorReplacementShortcut"
        self.color = "#FF00FF"
        self.terminalChild = dict()
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are shortcut arithmetic operations.
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
        Generates mutants by replacing the shortcut arithmetic operators.
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
                                nodeID=node.nodeIndex, mutatorType=self.mutatorType, replacementText=replacementText,
                                color=self.color)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


class ShiftOperatorReplacement(TraditionalMutationOperator):
    """
    This mutation operator replaces shift operators. For example, ``<<`` is
    replaced with ``>>``.
    """
    instantiable = True

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 generateMutants: bool = True):
        super().__init__(sourceTree, sourceCode, javaParseObject)
        self.mutatorType = "ShiftOperatorReplacement"
        self.color = "#9ACD32"
        self.threeTerminals = dict()
        self.findNodes()
        self.filterCriteria()
        if generateMutants:
            self.generateMutants()

    def filterCriteria(self):
        """
        Filters the expression nodes to include only those that are shift operations.
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
        Generates mutants by replacing the shift operators.
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
                                    replacementText=replacementText, color=self.color)

            mutant = Mutant(mutantID=id, mutationList=[mutation], sourceCode=self.sourceCode)
            mutant.mutateCode()
            self.mutants.append(mutant)


#################################################


def getAllInstantiableSubclasses(parentClass):
    """
    Gets all instantiable subclasses of a given class.
    :param parentClass: the class that all its subclasses must be returned
    :return: set of MutationOperator instantiable subclasses
    """
    allInstantiableSubclasses = set()

    for subClass in parentClass.__subclasses__():
        if subClass.instantiable:
            allInstantiableSubclasses.add(subClass)
        allInstantiableSubclasses.update(getAllInstantiableSubclasses(subClass))

    return allInstantiableSubclasses


class JavaMutate(object):
    """
    This class is the main entry point for the mutation of a Java source file.
    It takes a parse tree and the original source code, and then uses a
    collection of mutation operators to generate a list of mutants.
    """

    def __init__(self, sourceTree: JavaParser.CompilationUnitContext, sourceCode: str, javaParseObject: JavaParse,
                 verbose: bool = False):
        """
        Initializes a JavaMutate object.

        :param sourceTree: The root of the parse tree.
        :type sourceTree: antlr4.tree.Tree.ParseTree
        :param sourceCode: The source code to mutate.
        :type sourceCode: str
        :param javaParseObject: The JavaParse object to use for parsing.
        :type javaParseObject: littledarwin.JavaParse.JavaParse
        :param verbose: A boolean indicating whether to print verbose output.
        :type verbose: bool
        """
        self.verbose = verbose
        self.sourceCode = sourceCode
        self.sourceTree = sourceTree
        self.mutantsPerLine = dict()
        self.mutantsPerMethod = dict()
        self.averageDensity = -1
        self.mutants = list()
        self.mutationOperators = list()

        if isinstance(javaParseObject, JavaParse):
            self.javaParseObject = javaParseObject
        else:
            self.javaParseObject = JavaParse()

        # self.instantiateMutationOperators()

        self.inMethodLines = self.javaParseObject.getInMethodLines(self.sourceTree)

    def instantiateMutationOperators(self, metaTypes: List[str] = ["Traditional"], generateMutants: bool = True):
        """
        Instantiates all mutation operators of the specified meta types.

        :param metaTypes: A list of meta types to instantiate.
        :type metaTypes: list
        :param generateMutants: A boolean indicating whether to generate mutants.
        :type generateMutants: bool
        """
        for MO in getAllInstantiableSubclasses(MutationOperator):
            for metaType in metaTypes:
                if metaType in MO.metaTypes:
                    self.mutationOperators.append(
                        MO(self.sourceTree, self.sourceCode, self.javaParseObject, generateMutants))

    def countMutants(self, metaTypes: List[str] = ["Traditional"]):
        """
        Counts the number of mutants for each mutation operator type.

        :param metaTypes: The types of mutation operators to use.
        :type metaTypes: list
        :return: A dictionary mapping mutation operator types to the number of
                 mutants.
        :rtype: dict
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
                self.mutantsPerLine[lineNumber] = 1 + self.mutantsPerLine.get(lineNumber, 0)
                methodName = self.javaParseObject.getMethodNameForNode(self.sourceTree, mutableNode.nodeIndex)
                self.mutantsPerMethod[methodName] = 1 + self.mutantsPerMethod.get(methodName, 0)

        self.averageDensity = sum(self.mutantsPerLine.values()) / len(self.inMethodLines) if len(
            self.inMethodLines) > 0 else 0

        return mutationTypeCount

    def gatherMutants(self, metaTypes: List[str] = ["Traditional"]):
        """
        Gathers all mutants of the specified meta types.

        :param metaTypes: The types of mutation operators to use.
        :type metaTypes: list
        :return: A tuple containing a list of mutated source code and a
                 dictionary mapping mutation operator types to the number of
                 mutants.
        :rtype: tuple
        """
        mutationTypeCount = dict()
        mutantTexts = list()

        self.instantiateMutationOperators(metaTypes)

        for mO in self.mutationOperators:
            for metaType in metaTypes:
                if metaType in mO.metaTypes:
                    mutationTypeCount[mO.mutatorType] = len(mO.mutants)
                    for mutant in mO.mutants:
                        self.mutants.append(mutant)
                        mutantTexts.append(str(mutant))
                        for mutation in mutant.mutationList:
                            self.mutantsPerLine[mutation.lineNumber] = 1 + self.mutantsPerLine.get(mutation.lineNumber,
                                                                                                   0)
                            methodName = self.javaParseObject.getMethodNameForNode(self.sourceTree, mutation.nodeID)
                            self.mutantsPerMethod[methodName] = 1 + self.mutantsPerMethod.get(methodName, 0)

        self.averageDensity = sum(self.mutantsPerLine.values()) / len(self.inMethodLines) if len(
            self.inMethodLines) > 0 else 0

        return mutantTexts, mutationTypeCount

    def gatherHigherOrderMutants(self, higherOrderDirective: int, metaTypes: List[str] = ["Traditional"]):
        """
        Gathers all mutants and creates higher-order mutants.

        :param higherOrderDirective: The requested higher-order order.
        :type higherOrderDirective: int
        :param metaTypes: The type of mutation operators to use.
        :type metaTypes: list
        :return: A tuple containing a list of mutated source code and a
                 dictionary mapping mutation operator types to the number of
                 mutants.
        :rtype: tuple
        """
        selectedMutants = list()

        self.instantiateMutationOperators(metaTypes)

        for mO in self.mutationOperators:
            for metaType in metaTypes:
                if metaType in mO.metaTypes:
                    selectedMutants.extend(mO.mutants)

        higherOrder = max(int(log10(len(selectedMutants))) if higherOrderDirective == -1 else higherOrderDirective, 1)
        shuffle(selectedMutants)
        mutantTexts = list()

        while len(selectedMutants) > 0:
            higherOrderMutant = None
            for mutant in selectedMutants[:higherOrder]:
                higherOrderMutant += mutant

            mutantTexts.append(str(higherOrderMutant))
            self.mutants.append(higherOrderMutant)
            for mutation in higherOrderMutant.mutationList:
                self.mutantsPerLine[mutation.lineNumber] = 1 + self.mutantsPerLine.get(mutation.lineNumber, 0)
                self.mutantsPerMethod[self.javaParseObject.getMethodNameForNode(
                    self.sourceTree, mutation.nodeID)] = 1 + self.mutantsPerMethod.get(mutation.lineNumber, 0)

            selectedMutants = selectedMutants[higherOrder:]

        mutationTypeCount = {"Higher-Order": len(mutantTexts)}

        self.averageDensity = sum(self.mutantsPerLine.values()) / len(self.inMethodLines) if len(
            self.inMethodLines) > 0 else 0

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
        Generates an HTML report of all mutations for a file.

        :param littleDarwinVersion: The version of LittleDarwin.
        :type littleDarwinVersion: str
        :return: An HTML report of all mutations for a file.
        :rtype: str
        """
        lineNumber = 1
        col = 0
        maxLineLength = 0
        for l in self.sourceCode.expandtabs().splitlines(keepends=False):
            if len(l) > maxLineLength:
                maxLineLength = len(l)

        output = "<!DOCTYPE html><head><title>LittleDarwin Aggregate Mutation Report</title> <style type='text/css'>"
        output += self.cssStyle + "</style></head><body><h1>LittleDarwin Aggregate Mutation Report</h1>"
        output += "<p>Average Density: {:.2f}".format(self.averageDensity) + "</p><div><pre class=\"code\">"
        output += "<span class=\"{}\"><i>{:04d}</i> ".format(
            "methodLine" if lineNumber in self.inMethodLines else "outsideLine", lineNumber)

        mutationStartDict = dict()
        mutationEndList = list()
        for mutant in self.mutants:
            assert isinstance(mutant, Mutant)
            for mutation in mutant.mutationList:
                mutationStartDict[mutation.startPos] = (mutation.mutatorType, str(mutation))
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
                output += "<span class=\"{} tooltip\">".format(mutatorType)
                output += "<span class=\"tooltiptext\">{}</span>".format(tooltipText)

            if self.sourceCode[i] == "\n":
                output += " " * (maxLineLength - col + 1)

            output += self.sourceCode[i] if self.sourceCode[i] != "\t" else " " * colRemainder

            if i in mutationEndList:
                output += "</span>"

            if self.sourceCode[i] == "\n":
                lineNumber += 1
                col = 0
                output += "</span><span class=\"{}\"><i>{:04d}</i> ".format(
                    "methodLine" if lineNumber in self.inMethodLines else "outsideLine", lineNumber)

        output += " " * (maxLineLength - col)
        output += "</pre></div><footer><p style=\"font-size: small\">"
        output += "Report generated by LittleDarwin {} </p></footer></body></html>".format(littleDarwinVersion)

        return output
